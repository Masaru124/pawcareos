import asyncio
import base64
import os
import subprocess
import sys
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import asyncpg
import httpx
import pytest
import pytest_asyncio
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import ASGITransport
from jose import jwt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

import app.auth as auth_module
from app.db import get_session
from app.domain.passport import make_passport_slug
from app.main import app
from app.models import (
    Clinic,
    ClinicUser,
    ConsentChannel,
    ConsentEvent,
    ConsentSource,
    Patient,
    PetParent,
    UserRole,
)

if sys.platform == "win32":
    # asyncpg is unreliable on the proactor loop; the selector loop is the supported pairing.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

API_ROOT = Path(__file__).resolve().parents[1]
ASYNC_PREFIX = "postgresql+asyncpg://postgres:pawcare@localhost:5433"
ADMIN_DSN = "postgresql://postgres:pawcare@localhost:5433/postgres"
TEST_DB = "pawcare_test"
TEST_URL = f"{ASYNC_PREFIX}/{TEST_DB}"

TABLES = (
    "clinics, clinic_users, pet_parents, patients, consultations, prescriptions, "
    "prescription_items, vaccine_events, recall_jobs, appointments, consent_events, "
    "message_outbox, job_runs, audit_log, clinical_counters, inbound_events"
)


async def _create_database() -> None:
    connection = await asyncpg.connect(ADMIN_DSN)
    try:
        exists = await connection.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", TEST_DB)
        if not exists:
            await connection.execute(f'CREATE DATABASE "{TEST_DB}"')
    finally:
        await connection.close()


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> None:
    """Prove the real migration applies, and keep tests off any ambient database."""
    os.environ["DATABASE_URL"] = TEST_URL
    asyncio.run(_create_database())
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=API_ROOT,
        env={**os.environ, "DATABASE_URL": TEST_URL},
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"alembic upgrade failed:\n{result.stdout}\n{result.stderr}")


@pytest_asyncio.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    created = create_async_engine(TEST_URL, poolclass=NullPool)
    yield created
    await created.dispose()


@pytest_asyncio.fixture
async def session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as db_session:
        try:
            yield db_session
        finally:
            await db_session.rollback()
            await db_session.execute(text(f"TRUNCATE {TABLES} RESTART IDENTITY CASCADE"))
            await db_session.commit()


@pytest_asyncio.fixture
async def client(session: AsyncSession) -> AsyncIterator[httpx.AsyncClient]:
    """Routes share the test session, so no route can open an engine of its own."""
    app.dependency_overrides[get_session] = lambda: session
    transport = ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as async_client:
            yield async_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def jwks(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Sign real ES256 tokens and serve the matching key as Supabase's JWKS."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_numbers = private_key.public_key().public_numbers()
    kid = "test-signing-key"

    def b64(value: int) -> str:
        return base64.urlsafe_b64encode(value.to_bytes(32, "big")).decode().rstrip("=")

    jwk = {
        "kty": "EC",
        "crv": "P-256",
        "kid": kid,
        "alg": "ES256",
        "use": "sig",
        "x": b64(public_numbers.x),
        "y": b64(public_numbers.y),
    }

    async def fake_fetch(_settings) -> list[dict]:
        return [jwk]

    monkeypatch.setattr(auth_module, "_fetch_jwks", fake_fetch)
    auth_module.reset_jwks_cache()

    def sign(
        subject: uuid.UUID | str,
        *,
        expired: bool = False,
        audience: str = "authenticated",
        email: str | None = None,
    ) -> str:
        now = datetime.now(UTC)
        claims = {
            "sub": str(subject),
            "aud": audience,
            "iat": now,
            "exp": now - timedelta(minutes=5) if expired else now + timedelta(hours=1),
        }
        if email:
            claims["email"] = email
        return jwt.encode(claims, private_key, algorithm="ES256", headers={"kid": kid})

    def headers(user: ClinicUser) -> dict[str, str]:
        return {"Authorization": f"Bearer {sign(user.auth_user_id)}"}

    return SimpleNamespace(sign=sign, headers=headers, kid=kid)


def _phone() -> str:
    return f"+9199{uuid.uuid4().int % 10**8:08d}"


async def _clinic(session: AsyncSession, name: str) -> Clinic:
    clinic = Clinic(
        name=name,
        phone=_phone(),
        email=f"{uuid.uuid4().hex[:10]}@example.com",
        address_street="100 Feet Road, Indiranagar",
        city="Bengaluru",
        state="Karnataka",
        pincode="560038",
    )
    session.add(clinic)
    await session.flush()
    return clinic


async def _user(
    session: AsyncSession,
    clinic: Clinic,
    *,
    role: UserRole,
    vci: str | None = "KAR-12345",
    is_active: bool = True,
) -> ClinicUser:
    user = ClinicUser(
        clinic_id=clinic.id,
        auth_user_id=uuid.uuid4(),
        full_name=f"{role.value.title()} User",
        email=f"{uuid.uuid4().hex[:10]}@example.com",
        phone=_phone(),
        vci_registration_no=vci,
        role=role,
        is_active=is_active,
    )
    session.add(user)
    await session.flush()
    return user


@pytest.fixture
def make_user(session: AsyncSession):
    async def build(
        clinic: Clinic,
        *,
        role: UserRole,
        vci: str | None = "KAR-12345",
        is_active: bool = True,
    ) -> ClinicUser:
        return await _user(session, clinic, role=role, vci=vci, is_active=is_active)

    return build


@pytest.fixture
def make_patient(session: AsyncSession):
    async def build(
        clinic: Clinic,
        *,
        name: str = "Bruno",
        consent: bool = True,
        microchip: str | None = None,
    ) -> SimpleNamespace:
        parent = PetParent(full_name="Priya Sharma", phone=_phone())
        session.add(parent)
        await session.flush()
        patient = Patient(
            parent_id=parent.id,
            primary_clinic_id=clinic.id,
            name=name,
            species="Canine",
            breed="Golden Retriever",
            gender="Male",
            microchip_number=microchip,
            passport_slug=make_passport_slug(),
        )
        session.add(patient)
        await session.flush()
        if consent:
            session.add(
                ConsentEvent(
                    pet_parent_id=parent.id,
                    channel=ConsentChannel.WHATSAPP,
                    granted=True,
                    source=ConsentSource.INTAKE_TAP,
                )
            )
            await session.flush()
        return SimpleNamespace(parent=parent, patient=patient)

    return build


@pytest_asyncio.fixture
async def seeded(session: AsyncSession, jwks: SimpleNamespace) -> SimpleNamespace:
    clinic_a = await _clinic(session, "Shanti Vet Clinic")
    clinic_b = await _clinic(session, "Other Clinic")
    doctor = await _user(session, clinic_a, role=UserRole.DOCTOR)
    receptionist = await _user(session, clinic_a, role=UserRole.RECEPTIONIST, vci=None)
    outsider = await _user(session, clinic_b, role=UserRole.OWNER, vci=None)

    parent = PetParent(full_name="Priya", phone=_phone())
    session.add(parent)
    await session.flush()
    patient = Patient(
        parent_id=parent.id,
        primary_clinic_id=clinic_a.id,
        name="Bruno",
        species="Canine",
        breed="Golden Retriever",
        gender="Male",
        passport_slug=uuid.uuid4().hex[:10].translate(str.maketrans("01", "23")),
    )
    session.add(patient)
    await session.flush()

    return SimpleNamespace(
        clinic_a=clinic_a,
        clinic_b=clinic_b,
        doctor=doctor,
        receptionist=receptionist,
        outsider=outsider,
        patient=patient,
        headers=jwks.headers,
        sign=jwks.sign,
    )
