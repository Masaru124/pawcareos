import io
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Clinic,
    ClinicUser,
    Consultation,
    Patient,
    PetParent,
    Prescription,
    PrescriptionItem,
    VaccineEvent,
)
from app.schemas.passport import PassportView

FONT_CANDIDATES = (
    Path("assets/fonts/NotoSans-Regular.ttf"),
    Path("C:/Windows/Fonts/Nirmala.ttf"),
    Path("C:/Windows/Fonts/mangal.ttf"),
    Path("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"),
)
FONT_NAME = "PawCareSans"

INR_SAFE_FALLBACK = "Helvetica"


def register_font() -> str:
    """Devanagari needs a real Unicode font; fall back to Helvetica rather than crash."""
    if FONT_NAME in pdfmetrics.getRegisteredFontNames():
        return FONT_NAME
    for candidate in FONT_CANDIDATES:
        if candidate.exists():
            pdfmetrics.registerFont(TTFont(FONT_NAME, str(candidate)))
            return FONT_NAME
    return INR_SAFE_FALLBACK


def _wrap(text: str, width: int) -> list[str]:
    words, lines, current = text.split(), [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def render_prescription_pdf(document: dict) -> bytes:
    font = register_font()
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    x = 20 * mm
    y = height - 25 * mm

    def write(text: str, *, size: int = 10, gap: float = 5 * mm, bold: bool = False) -> None:
        nonlocal y
        pdf.setFont(font, size)
        pdf.drawString(x, y, text)
        y -= gap
        del bold

    clinic = document["clinic"]
    pdf.setFont(font, 16)
    pdf.drawString(x, y, clinic["name"])
    y -= 7 * mm
    write(f"{clinic['address']} · {clinic['phone']}", size=9)
    y -= 4 * mm
    pdf.setFont(font, 13)
    pdf.drawString(x, y, "PRESCRIPTION")
    pdf.drawRightString(width - x, y, document["rx_code"])
    y -= 8 * mm
    write(f"Date: {document['date']}")
    y -= 2 * mm

    pet = document["pet"]
    write(f"Patient: {pet['name']}  ({pet['species']}, {pet['breed'] or '—'})", size=11)
    write(f"Sex: {pet['sex']}   Age: {pet['age']}   Weight: {pet['weight']}")
    write(f"Owner: {document['parent_name']}   Phone: {document['parent_phone']}")
    y -= 3 * mm

    pdf.line(x, y, width - x, y)
    y -= 8 * mm
    write("Rx", size=12)
    for index, item in enumerate(document["medications"], start=1):
        write(f"{index}. {item['name']} — {item['strength'] or ''}".strip(), size=10)
        write(
            f"    {item['frequency']} × {item['duration_days']} days, {item['route']}",
            size=9,
            gap=4 * mm,
        )
    y -= 3 * mm

    for title, key in (
        ("Diagnosis", "diagnosis"),
        ("Dietary advice", "dietary_advice"),
        ("Special instructions", "special_instructions"),
    ):
        value = document.get(key)
        if value:
            write(f"{title}:", size=10)
            for line in _wrap(value, 95):
                write(f"  {line}", size=9, gap=4 * mm)

    if document.get("vaccinations"):
        write("Vaccines administered:", size=10)
        for vaccine in document["vaccinations"]:
            write(
                f"  {vaccine['name']} · batch {vaccine['batch']} · next due {vaccine['next_due']}",
                size=9,
                gap=4 * mm,
            )

    y = 45 * mm
    pdf.line(x, y, x + 55 * mm, y)
    pdf.setFont(font, 9)
    pdf.drawString(x, y - 5 * mm, document["doctor_name"])
    pdf.drawString(x, y - 10 * mm, f"VCI: {document['vci'] or '—'}")
    pdf.setFont(font, 7)
    pdf.drawString(x, 20 * mm, f"Issued by PawCare OS · verify at {document['passport_url']}")
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def render_certificate_pdf(view: PassportView, *, issued_on: str) -> bytes:
    font = register_font()
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    x = 25 * mm
    y = height - 35 * mm

    pdf.setFont(font, 18)
    pdf.drawCentredString(width / 2, y, view.clinic.name)
    y -= 9 * mm
    pdf.setFont(font, 14)
    pdf.drawCentredString(width / 2, y, "VACCINATION RECORD")
    y -= 14 * mm
    pdf.setFont(font, 12)
    pdf.drawString(x, y, f"Patient: {view.pet.name}")
    pdf.drawString(x, y - 7 * mm, f"Species: {view.pet.species}   Breed: {view.pet.breed or '—'}")
    pdf.drawString(x, y - 14 * mm, f"Sex: {view.pet.sex_label}   Age: {view.pet.age_label}")
    y -= 26 * mm
    pdf.setFont(font, 11)
    for badge in view.badges:
        pdf.drawString(x, y, f"{badge.label}: valid until {badge.valid_until}")
        pdf.drawString(x + 115 * mm, y, badge.state.replace("_", " "))
        y -= 6 * mm
    y -= 8 * mm
    pdf.setFont(font, 9)
    pdf.drawString(x, y, f"Issued {issued_on} · {view.clinic.name} · {view.clinic.phone}")
    pdf.drawString(x, 20 * mm, f"Passport {view.pet.passport_slug} · issued by PawCare OS")
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


async def build_prescription_document(
    session: AsyncSession, *, rx_code: str, clinic_id
) -> dict | None:
    row = (
        await session.execute(
            select(Prescription, Consultation, Patient, PetParent, Clinic, ClinicUser)
            .join(Consultation, Prescription.consultation_id == Consultation.id)
            .join(Patient, Consultation.patient_id == Patient.id)
            .join(PetParent, Patient.parent_id == PetParent.id)
            .join(Clinic, Consultation.clinic_id == Clinic.id)
            .join(ClinicUser, Consultation.doctor_id == ClinicUser.id)
            .where(Prescription.rx_code == rx_code, Consultation.clinic_id == clinic_id)
        )
    ).first()
    if row is None:
        return None

    prescription, consultation, patient, parent, clinic, doctor = row
    items = (
        await session.execute(
            select(PrescriptionItem)
            .where(PrescriptionItem.prescription_id == prescription.id)
            .order_by(PrescriptionItem.created_at)
        )
    ).scalars().all()
    vaccinations = (
        await session.execute(
            select(VaccineEvent)
            .where(VaccineEvent.patient_id == patient.id)
            .order_by(VaccineEvent.administered_date.desc())
            .limit(4)
        )
    ).scalars().all()

    timezone = ZoneInfo(clinic.timezone or "Asia/Kolkata")
    from app.services.consult import passport_url

    return {
        "clinic": {
            "name": clinic.name,
            "address": f"{clinic.address_street}, {clinic.city} {clinic.pincode}",
            "phone": clinic.phone,
        },
        "rx_code": prescription.rx_code,
        "date": consultation.consult_date.astimezone(timezone).strftime("%d %b %Y"),
        "pet": {
            "name": patient.name,
            "species": patient.species,
            "breed": patient.breed,
            "sex": patient.gender,
            "age": patient.dob.isoformat() if patient.dob else "—",
            "weight": f"{patient.weight_kg} kg" if patient.weight_kg else "—",
        },
        "parent_name": parent.full_name,
        "parent_phone": parent.phone,
        "medications": [
            {
                "name": item.medication_name,
                "strength": item.dosage_strength,
                "frequency": item.frequency,
                "duration_days": item.duration_days,
                "route": item.route,
            }
            for item in items
        ],
        "diagnosis": consultation.provisional_diagnosis,
        "dietary_advice": prescription.dietary_advice,
        "special_instructions": prescription.special_instructions,
        "vaccinations": [
            {
                "name": event.vaccine_name,
                "batch": event.batch_number,
                "next_due": event.next_due_date.isoformat(),
            }
            for event in vaccinations
        ],
        "doctor_name": doctor.full_name,
        "vci": doctor.vci_registration_no,
        "passport_url": passport_url(patient.passport_slug),
        "issued_on": datetime.now(timezone).strftime("%d %b %Y"),
    }
