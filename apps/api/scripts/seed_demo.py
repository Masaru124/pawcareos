"""Seed a demo clinic. Safe to run twice: it reuses the clinic by phone number."""

import argparse
import asyncio
import uuid
from datetime import datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import get_settings
from app.domain.passport import make_passport_slug
from app.models import (
    Appointment,
    Clinic,
    ClinicUser,
    ConsentChannel,
    ConsentEvent,
    ConsentSource,
    Patient,
    PetParent,
    UserRole,
    VaccineEvent,
)
from app.models.enums import AppointmentSource, AppointmentStatus, VaccineStatus

CLINIC_PHONE = "+918041234567"
TIMEZONE = ZoneInfo("Asia/Kolkata")


async def seed(auth_subject: str | None, doctor_email: str | None) -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    maker = async_sessionmaker(engine, expire_on_commit=False)

    async with maker() as session:
        clinic = await session.scalar(select(Clinic).where(Clinic.phone == CLINIC_PHONE))
        if clinic is None:
            clinic = Clinic(
                name="Shanti Vet Clinic",
                legal_entity_name="Shanti Veterinary Services",
                phone=CLINIC_PHONE,
                email="front.desk@shantivet.example",
                address_street="412, 100 Feet Road, Indiranagar",
                city="Bengaluru",
                state="Karnataka",
                pincode="560038",
                upi_vpa="shantivet@upi",
            )
            session.add(clinic)
            await session.flush()

        desired_email = (doctor_email or "ananya@shantivet.example").strip().lower()
        doctor = await session.scalar(
            select(ClinicUser).where(
                ClinicUser.clinic_id == clinic.id,
                ClinicUser.email.in_([desired_email, "ananya@shantivet.example"]),
            )
        )
        if doctor is None:
            doctor = ClinicUser(
                clinic_id=clinic.id,
                auth_user_id=uuid.UUID(auth_subject) if auth_subject else None,
                full_name="Dr. Ananya Rao",
                email=desired_email,
                phone="+919845012345",
                vci_registration_no="KAR-4821",
                role=UserRole.DOCTOR,
            )
            session.add(doctor)
            await session.flush()
        elif auth_subject:
            doctor.auth_user_id = uuid.UUID(auth_subject)
        elif doctor_email:
            # Unbound, so the first Supabase sign-in with this email claims the row.
            doctor.auth_user_id = None

        if doctor_email:
            doctor.email = desired_email

        receptionist = await session.scalar(
            select(ClinicUser).where(
                ClinicUser.clinic_id == clinic.id, ClinicUser.email == "meera@shantivet.example"
            )
        )
        if receptionist is None:
            session.add(
                ClinicUser(
                    clinic_id=clinic.id,
                    auth_user_id=uuid.uuid4(),
                    full_name="Meera Iyer",
                    email="meera@shantivet.example",
                    role=UserRole.RECEPTIONIST,
                )
            )

        today = datetime.now(TIMEZONE).date()
        plan = [
            ("Bruno", "Canine", "Golden Retriever", "Male", 4, 9, "Rabies"),
            ("Coco", "Feline", "Indie", "Female", 2, -4, "Rabies"),
            ("Simba", "Canine", "Labrador", "Male", 6, 240, "Rabies"),
        ]

        for index, (name, species, breed, gender, years, due_in, vaccine) in enumerate(plan):
            phone = ["+919900011122", "+919900011133", "+919900011144"][index]
            parent = await session.scalar(select(PetParent).where(PetParent.phone == phone))
            if parent is None:
                parent = PetParent(
                    full_name=["Priya Sharma", "Rahul Nair", "Fatima Khan"][index],
                    phone=phone,
                    city="Bengaluru",
                )
                session.add(parent)
                await session.flush()

            existing = await session.scalar(
                select(Patient).where(
                    Patient.primary_clinic_id == clinic.id, Patient.name == name
                )
            )
            if existing is not None:
                print(f"  {name:<6} passport /p/{existing.passport_slug} (kept)")
                continue

            session.add(
                ConsentEvent(
                    pet_parent_id=parent.id,
                    channel=ConsentChannel.WHATSAPP,
                    granted=True,
                    source=ConsentSource.INTAKE_TAP,
                    created_by=doctor.id,
                )
            )
            patient = Patient(
                parent_id=parent.id,
                primary_clinic_id=clinic.id,
                name=name,
                species=species,
                breed=breed,
                gender=gender,
                dob=today - timedelta(days=365 * years),
                dob_is_approximate=True,
                weight_kg=Decimal("24.50") if species == "Canine" else Decimal("4.10"),
                microchip_number=f"90012345{index}{index}{index}{index}012",
                passport_slug=make_passport_slug(),
            )
            session.add(patient)
            await session.flush()
            session.add(
                VaccineEvent(
                    patient_id=patient.id,
                    clinic_id=clinic.id,
                    doctor_id=doctor.id,
                    vaccine_name=vaccine,
                    brand_name="Nobivac",
                    batch_number=f"RAB-{2026}-{index}",
                    administered_date=today - timedelta(days=365),
                    next_due_date=today + timedelta(days=due_in),
                    status=VaccineStatus.ADMINISTERED,
                )
            )
            if index < 2:
                session.add(
                    Appointment(
                        clinic_id=clinic.id,
                        patient_id=patient.id,
                        starts_at=datetime.combine(
                            today, time(11 + index, 0), tzinfo=TIMEZONE
                        ),
                        status=AppointmentStatus.BOOKED,
                        source=AppointmentSource.RECALL,
                    )
                )
            await session.flush()
            print(f"  {name:<6} passport /p/{patient.passport_slug}")

        await session.commit()
        print(f"\nclinic: {clinic.name} ({clinic.city})")
        print(f"doctor: {doctor.full_name} · auth_user_id {doctor.auth_user_id}")

    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the PawCare demo clinic")
    parser.add_argument(
        "--auth-subject",
        help="Supabase auth user id (sub claim) to bind to the demo doctor",
    )
    parser.add_argument(
        "--email",
        help="real email to invite; the first sign-in with it claims the doctor row",
    )
    arguments = parser.parse_args()
    asyncio.run(seed(arguments.auth_subject, arguments.email))


if __name__ == "__main__":
    main()
