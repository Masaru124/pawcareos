"""Sign in through /api/session with a real Supabase account, then verify the claim.

    uv run python -m scripts.verify_claim --email you@example.com --password '...' 
    uv run python -m scripts.verify_claim --email new@example.com --password '...' --signup
    uv run python -m scripts.verify_claim --email you@example.com --password '...' --cleanup

The account must be able to sign in: with "Confirm email" on, Supabase returns no session
until the address is confirmed, and the script stops and says so.
"""

import argparse
import asyncio
import uuid

import asyncpg
import httpx

from app.config import get_settings
from app.db import ssl_context

WEB = "http://127.0.0.1:3000"
API = "http://127.0.0.1:8000"


async def database() -> asyncpg.Connection:
    url = get_settings().database_url.replace("postgresql+asyncpg://", "postgresql://")
    return await asyncpg.connect(url, ssl=ssl_context(), timeout=20)


async def invite(conn: asyncpg.Connection, email: str) -> uuid.UUID | None:
    """An unbound clinic_users row is what a first sign-in claims."""
    existing = await conn.fetchrow(
        "select id, auth_user_id from clinic_users where lower(email) = lower($1)", email
    )
    if existing is not None:
        state = "already bound" if existing["auth_user_id"] else "unbound, ready to claim"
        print(f"clinic_users row: {existing['id']} ({state})")
        return existing["id"]

    clinic = await conn.fetchval("select id from clinics order by created_at limit 1")
    if clinic is None:
        print("no clinic in the database; run scripts.seed_demo first")
        return None
    row_id = await conn.fetchval(
        """insert into clinic_users (clinic_id, auth_user_id, full_name, email, role, is_active)
           values ($1, null, 'Sign-in Check', $2, 'receptionist', true) returning id""",
        clinic,
        email,
    )
    print(f"invited {email} as an unbound user ({row_id})")
    return row_id


async def sign_in(email: str, password: str, *, signup: bool) -> tuple[int, dict, str | None]:
    payload = {"email": email, "password": password}
    if signup:
        payload["mode"] = "signup"
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(f"{WEB}/api/session", json=payload)
    return response.status_code, response.json(), response.cookies.get("pc_token")


async def main(email: str, password: str, *, signup: bool, cleanup: bool) -> int:
    conn = await database()
    try:
        row_id = await invite(conn, email)
        if row_id is None:
            return 1

        status, body, token = await sign_in(email, password, signup=signup)
        print(f"POST /api/session ({'signup' if signup else 'signin'}) -> {status} {body}")

        if not token:
            print("no session cookie: Supabase issued no access token.")
            print("=> if this says confirm, turn off 'Confirm email' or confirm the address first.")
            return 1

        async with httpx.AsyncClient(timeout=30) as client:
            me = await client.get(
                f"{API}/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
            )
        print(f"GET /api/v1/auth/me -> {me.status_code} {me.text[:160]}")
        if me.status_code != 200:
            return 1

        # The request session commits after the response is sent, so watch briefly for it.
        bound = None
        for _ in range(20):
            bound = await conn.fetchval(
                "select auth_user_id from clinic_users where id = $1", row_id
            )
            if bound is not None:
                break
            await asyncio.sleep(0.25)

        audits = await conn.fetchval(
            "select count(*) from audit_log where action = 'user.claimed' and subject_id = $1",
            row_id,
        )
        print(f"claimed in postgres: {bound is not None} | user.claimed audit rows: {audits}")
        if bound is None:
            print("the row is still unbound: the token's email did not match")
            return 1

        if cleanup:
            await conn.execute("delete from audit_log where subject_id = $1", row_id)
            await conn.execute("delete from clinic_users where id = $1", row_id)
            print("removed the clinic_users row and its audit entry")
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--signup", action="store_true", help="create the account first")
    parser.add_argument(
        "--cleanup", action="store_true", help="delete the clinic_users row afterwards"
    )
    arguments = parser.parse_args()
    raise SystemExit(
        asyncio.run(
            main(
                arguments.email,
                arguments.password,
                signup=arguments.signup,
                cleanup=arguments.cleanup,
            )
        )
    )
