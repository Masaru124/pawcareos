"""Provision the three disposable logins the Playwright suite signs in as.

    uv run python -m scripts.provision_e2e

Creates (or reuses) one Supabase identity per role, the matching clinic_users /
pet_parent_accounts invitation, and writes e2e/.creds.json for the browser suite.
The accounts are demo fixtures: fixed passwords, no real data, safe to delete.
"""

import argparse
import asyncio
import json
from pathlib import Path

import httpx
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.config import get_settings
from app.db import build_engine
from app.models import Clinic, ClinicUser, PetParent, PetParentAccount

REPO = Path(__file__).resolve().parents[3]
CREDS = REPO / "e2e" / ".creds.json"

ACCOUNTS = {
    "owner": {
        "email": "owner.e2e@pawcare.test",
        "password": "PawCare!Owner2026",
        "full_name": "E2E Owner",
        "role": "owner",
    },
    "doctor": {
        "email": "doctor.e2e@pawcare.test",
        "password": "PawCare!Doctor2026",
        "full_name": "Dr. E2E Rao",
        "role": "doctor",
        "vci_registration_no": "KAR-E2E-0001",
    },
    # One portal account per family, so the parent fixture is the real invitation
    # already sitting on Priya's record; the suite claims it on first sign-in.
    "parent": {
        "email": "priya.demo@gmail.com",
        "password": "PawCare!Parent2026",
        "full_name": "Priya Sharma",
        "phone": "+919900011122",
    },
}


def supabase_keys() -> tuple[str, str]:
    url = key = None
    for line in (REPO / "apps" / "web" / ".env.local").read_text(encoding="utf-8").splitlines():
        name, _, value = line.partition("=")
        value = value.strip().strip('"').strip("'")
        if name.strip() == "SUPABASE_URL":
            url = value
        elif name.strip() == "SUPABASE_ANON_KEY":
            key = value
    if not url or not key:
        raise SystemExit("SUPABASE_URL / SUPABASE_ANON_KEY missing from apps/web/.env.local")
    return url.rstrip("/"), key


async def ensure_identity(client: httpx.AsyncClient, base: str, key: str, email: str, password: str) -> str:
    """Reuse the identity if it exists and the password matches, else sign up."""
    headers = {"apikey": key, "Content-Type": "application/json"}
    signin = await client.post(
        f"{base}/auth/v1/token?grant_type=password",
        headers=headers,
        json={"email": email, "password": password},
    )
    if signin.status_code == 200:
        return "existing"

    signup = await client.post(
        f"{base}/auth/v1/signup", headers=headers, json={"email": email, "password": password}
    )
    if signup.status_code in (200, 201):
        return "created"
    raise SystemExit(
        f"Could not create {email}: signin {signin.status_code}, signup {signup.status_code} "
        f"{signup.text[:200]}"
    )


async def cleanup(factory) -> None:
    """Drop the artifacts a run leaves behind: timestamped invites and the test booking."""
    phone = "+919900099001"
    async with factory() as session:
        invites = [
            row.email
            for row in await session.execute(
                text(
                    "delete from clinic_users where email like 'reception+%@pawcare.test' "
                    "returning email"
                )
            )
        ]

        family = await session.scalar(
            text("select id from pet_parents where phone = :phone"), {"phone": phone}
        )
        if family is not None:
            # These FKs are NO ACTION rather than cascade, so dependants go first.
            scope = "select id from patients where parent_id = :family"
            for statement, params in (
                ("delete from message_outbox where to_phone = :phone", {"phone": phone}),
                (f"delete from consultations where patient_id in ({scope})", {"family": family}),
                (f"delete from appointments where patient_id in ({scope})", {"family": family}),
                (f"delete from patients where parent_id = :family", {"family": family}),
                ("delete from pet_parents where id = :family", {"family": family}),
            ):
                await session.execute(text(statement), params)
        await session.commit()

    for email in invites:
        print(f"removed invite {email}")
    if family is not None:
        print(f"removed the test booking family {family}")


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cleanup", action="store_true", help="remove run artifacts and exit")
    args = parser.parse_args()

    base, key = supabase_keys()
    engine = build_engine(get_settings().database_url)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    summary: dict[str, object] = {"baseURL": "http://localhost:3000", "inviteEmail": "reception.e2e@pawcare.test"}

    try:
        if args.cleanup:
            await cleanup(factory)
            return 0

        async with httpx.AsyncClient(timeout=30) as client:
            states = {
                name: await ensure_identity(client, base, key, spec["email"], spec["password"])
                for name, spec in ACCOUNTS.items()
            }

        async with factory() as session:
            clinic = await session.scalar(select(Clinic).limit(1))
            if clinic is None:
                raise SystemExit("No clinic row; run the seed first.")
            summary["clinic"] = clinic.name

            for name in ("owner", "doctor"):
                spec = ACCOUNTS[name]
                row = await session.scalar(
                    select(ClinicUser).where(ClinicUser.email == spec["email"])
                )
                if row is None:
                    row = ClinicUser(
                        clinic_id=clinic.id,
                        email=spec["email"],
                        full_name=spec["full_name"],
                        role=spec["role"],
                        vci_registration_no=spec.get("vci_registration_no"),
                        qualification="B.V.Sc & A.H." if spec["role"] == "doctor" else None,
                        is_active=True,
                    )
                    session.add(row)
                summary[name] = {
                    "email": spec["email"],
                    "password": spec["password"],
                    "role": row.role,
                    "identity": states[name],
                }

            parent_spec = ACCOUNTS["parent"]
            parent = await session.scalar(
                select(PetParent).where(PetParent.phone == parent_spec["phone"])
            )
            if parent is None:
                raise SystemExit(f"No pet parent with phone {parent_spec['phone']}; run the seed first.")
            account = await session.scalar(
                select(PetParentAccount).where(PetParentAccount.email == parent_spec["email"])
            )
            if account is None:
                raise SystemExit(
                    f"{parent_spec['email']} is not invited; run scripts.invite_parent first."
                )
            if account.pet_parent_id != parent.id:
                raise SystemExit(
                    f"{parent_spec['email']} is linked to a different family than {parent.full_name}."
                )
            summary["parent"] = {
                "email": parent_spec["email"],
                "password": parent_spec["password"],
                "role": "pet_parent",
                "identity": states["parent"],
                "family": parent.full_name,
            }
            await session.commit()

        CREDS.parent.mkdir(parents=True, exist_ok=True)
        CREDS.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        for name in ("owner", "doctor", "parent"):
            entry = summary[name]
            print(f"{name:<7} {entry['email']:<26} {entry['role']:<10} identity={entry['identity']}")
        print(f"wrote {CREDS.relative_to(REPO)}")
        return 0
    finally:
        await engine.dispose()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
