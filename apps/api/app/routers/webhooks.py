import hashlib
import hmac
import logging

from fastapi import APIRouter, Header, HTTPException, Query, Request, Response, status

from app.config import get_settings
from app.deps import SessionDep
from app.services.inbound import handle_button_reply
from app.services.ratelimit import allow

logger = logging.getLogger("pawcare.webhooks")
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.get("/whatsapp")
async def verify(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
) -> Response:
    if hub_mode != "subscribe" or hub_verify_token != get_settings().whatsapp_verify_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification failed")
    return Response(content=hub_challenge, media_type="text/plain")


def valid_signature(body: bytes, header: str | None) -> bool:
    secret = get_settings().whatsapp_app_secret
    if not secret or not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header.removeprefix("sha256="))


def extract_button_replies(payload: dict) -> list[tuple[str, str, str]]:
    """(provider_message_id, from_phone, button_id) for each quick reply."""
    found: list[tuple[str, str, str]] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                button_id = None
                if message.get("type") == "button":
                    button_id = message.get("button", {}).get("payload")
                elif message.get("type") == "interactive":
                    button_id = message.get("interactive", {}).get("button_reply", {}).get("id")
                if button_id:
                    found.append((message.get("id", ""), message.get("from", ""), button_id))
    return found


@router.post("/whatsapp")
async def receive(
    request: Request,
    session: SessionDep,
    signature: str | None = Header(default=None, alias="X-Hub-Signature-256"),
) -> dict:
    body = await request.body()
    if not valid_signature(body, signature):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bad signature")

    payload = await request.json()
    handled = 0
    for provider_message_id, from_phone, button_id in extract_button_replies(payload):
        if not allow(f"wa:{from_phone}"):
            logger.warning("inbound rate limit hit for %s", from_phone[-4:])
            continue
        if await handle_button_reply(
            session,
            provider_message_id=provider_message_id or None,
            from_phone=from_phone,
            button_id=button_id,
        ):
            handled += 1

    return {"handled": handled}
