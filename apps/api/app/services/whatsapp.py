import logging

import httpx

from app.config import Settings, get_settings
from app.models import MessageOutbox

logger = logging.getLogger("pawcare.whatsapp")


class SendError(RuntimeError):
    """A send failed in a way the outbox should retry."""


class DemoWhatsAppSender:
    """Demo mode: nothing leaves the process. Every send is logged for the demo screen."""

    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send(self, message: MessageOutbox) -> str:
        record = {
            "idempotency_key": message.idempotency_key,
            "to": f"***{message.to_phone[-4:]}",
            "template": message.template_name,
            "payload": message.payload,
        }
        self.sent.append(record)
        logger.info("demo whatsapp send: %s", record)
        return f"demo.{message.idempotency_key}"


class GraphWhatsAppSender:
    """Live mode: Meta's Cloud API. Used only when WHATSAPP_MODE=live."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def send(self, message: MessageOutbox) -> str:
        url = f"https://graph.facebook.com/v21.0/{self.settings.whatsapp_phone_number_id}/messages"
        body = {
            "messaging_product": "whatsapp",
            "to": message.to_phone,
            "type": "template",
            "template": {
                "name": message.template_name,
                "language": {"code": "en"},
                "components": message.payload.get("components", []),
            },
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    url,
                    json=body,
                    headers={"Authorization": f"Bearer {self.settings.whatsapp_token}"},
                )
        except httpx.HTTPError as exc:
            raise SendError(str(exc)) from exc
        if response.status_code >= 500 or response.status_code == 429:
            raise SendError(f"provider {response.status_code}")
        if response.status_code >= 400:
            raise SendError(f"permanent provider error {response.status_code}")
        payload = response.json()
        return str(payload.get("messages", [{}])[0].get("id", ""))


_demo_sender = DemoWhatsAppSender()


def demo_sender() -> DemoWhatsAppSender:
    return _demo_sender


def get_default_sender():
    settings = get_settings()
    if settings.whatsapp_mode == "live":
        return GraphWhatsAppSender(settings)
    return _demo_sender
