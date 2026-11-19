"""Invite a pet parent to the portal by attaching an email to their family record.

    uv run python -m scripts.invite_parent --phone +919876543210 --email priya@example.com

The next verified sign-in with that address claims the account. Run it after the
migration that adds pet_parent_accounts.
"""

import argparse
import asyncio
import sys

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.config import get_settings
from app.db import build_engine
from app.models import PetParent, PetParentAccount


async def invite(phone: str, email: str) -> int:
    engine = build_engine(get_settings().database_url)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    try:
        async with factory() as session:
            parent = await session.scalar(select(PetParent).where(PetParent.phone == phone))
            if parent is None:
                print(f"No pet parent with phone {phone}.")
                return 1

            existing = await session.scalar(
                select(PetParentAccount).where(
                    func.lower(PetParentAccount.email) == email.lower()
                )
            )
            if existing is not None:
                print(
                    f"{email} is already linked to family {existing.pet_parent_id} "
                    f"(claimed={existing.auth_user_id is not None})."
                )
                return 0

            account = PetParentAccount(pet_parent_id=parent.id, email=email.lower())
            session.add(account)
            if parent.email is None:
                parent.email = email.lower()
            # The commit is the point: without it the row disappears with the session.
            await session.commit()
            print(f"Invited {parent.full_name} ({phone}) as {email.lower()} [{account.id}].")
            return 0
    finally:
        await engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phone", required=True, help="E.164 phone on the family record")
    parser.add_argument("--email", required=True, help="Address that will claim the portal")
    args = parser.parse_args()
    return asyncio.run(invite(args.phone, args.email))


if __name__ == "__main__":
    sys.exit(main())
