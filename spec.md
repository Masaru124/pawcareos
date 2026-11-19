# PawCare OS: Technical & Functional Specification (SPEC)

**Document:** System Technical Specification  
**Version:** 1.0.0  
**Target Architecture:** Modular Monolith (FastAPI / Next.js) transitioning to Event-Driven Microservices at Scale  

---

## 1. Domain Data Models & PostgreSQL Relational Schema

### 1.1 Relational Schema Diagram (Entity Relationships)

```
+--------------------+       1:N       +---------------------+
|      clinics       | <------------>  |       doctors       |
+--------------------+                 +---------------------+
          | 1:N                                   | 1:N
          v                                       v
+--------------------+       1:N       +---------------------+
|      patients      | <------------>  |    consultations    |
| (Pets & Pet Parents|                 +---------------------+
+--------------------+                            | 1:1
          | 1:N                                   v
          |                            +---------------------+
          |                            |    prescriptions    |
          |                            +---------------------+
          v                                       | 1:N
+--------------------+                            v
|   vaccine_events   |                 +---------------------+
|  & recall_tasks    |                 |   prescription_items|
+--------------------+                 +---------------------+
```

---

### 1.2 DDL Table Definitions (PostgreSQL 16)

```sql
-- 1. CLINICS
CREATE TABLE clinics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    legal_entity_name VARCHAR(255),
    gstin VARCHAR(15),
    phone VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL,
    address_street TEXT NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    pincode VARCHAR(10) NOT NULL,
    coordinates POINT,
    upi_vpa VARCHAR(100),
    subscription_tier VARCHAR(50) DEFAULT 'pro', -- starter, pro, enterprise
    subscription_status VARCHAR(50) DEFAULT 'active',
    logo_url TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 2. DOCTORS / CLINIC USERS
CREATE TABLE doctors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    vci_registration_no VARCHAR(100) NOT NULL, -- Veterinary Council of India Reg No
    qualification VARCHAR(255) DEFAULT 'B.V.Sc & A.H.',
    role VARCHAR(50) DEFAULT 'doctor', -- admin, doctor, receptionist
    signature_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 3. PET PARENTS (CONSUMERS)
CREATE TABLE pet_parents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL UNIQUE, -- E.164 format: +919876543210
    whatsapp_enabled BOOLEAN DEFAULT TRUE,
    email VARCHAR(255),
    city VARCHAR(100),
    address TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 4. PATIENTS (COMPANION ANIMALS)
CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id UUID NOT NULL REFERENCES pet_parents(id) ON DELETE RESTRICT,
    primary_clinic_id UUID NOT NULL REFERENCES clinics(id),
    name VARCHAR(100) NOT NULL,
    species VARCHAR(50) NOT NULL, -- Canine, Feline, Avian, Exotic
    breed VARCHAR(100),
    gender VARCHAR(10) NOT NULL, -- Male, Female, Neutered Male, Spayed Female
    dob DATE,
    approximate_age_years NUMERIC(4, 1),
    weight_kg NUMERIC(5, 2),
    color VARCHAR(100),
    microchip_number VARCHAR(100) UNIQUE,
    chronic_conditions TEXT[], -- e.g. ['Renal Failure', 'Cardiac', 'Atopic Dermatitis']
    allergies TEXT[],
    photo_url TEXT,
    passport_slug VARCHAR(100) UNIQUE NOT NULL, -- e.g. 'bruno-7a8f'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 5. CONSULTATIONS
CREATE TABLE consultations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID NOT NULL REFERENCES clinics(id),
    doctor_id UUID NOT NULL REFERENCES doctors(id),
    patient_id UUID NOT NULL REFERENCES patients(id),
    consult_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    temperature_f NUMERIC(4, 1),
    weight_kg NUMERIC(5, 2),
    symptoms TEXT,
    clinical_examination TEXT,
    provisional_diagnosis TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'completed', -- waiting, in_consult, completed, cancelled
    consult_fee NUMERIC(10, 2) DEFAULT 500.00,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 6. PRESCRIPTIONS (VCI COMPLIANT)
CREATE TABLE prescriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consultation_id UUID NOT NULL REFERENCES consultations(id) ON DELETE CASCADE,
    rx_code VARCHAR(50) UNIQUE NOT NULL, -- e.g. 'RX-IND-2027-0042'
    dietary_advice TEXT,
    special_instructions TEXT,
    pdf_storage_url TEXT NOT NULL,
    whatsapp_dispatch_status VARCHAR(50) DEFAULT 'pending', -- pending, sent, delivered, failed
    whatsapp_message_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 7. PRESCRIPTION ITEMS
CREATE TABLE prescription_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prescription_id UUID NOT NULL REFERENCES prescriptions(id) ON DELETE CASCADE,
    medication_name VARCHAR(255) NOT NULL,
    active_ingredient VARCHAR(255),
    dosage_form VARCHAR(50) NOT NULL, -- Tablet, Syrup, Spot-on, Injection, Feed
    dosage_strength VARCHAR(50),      -- e.g. '200mg', '10mg/ml'
    frequency VARCHAR(50) NOT NULL,    -- Once daily, Twice daily (BID), Stat
    duration_days INT NOT NULL,
    route VARCHAR(50) DEFAULT 'Oral',  -- Oral, SC, IM, IV, Topical
    is_chronic BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 8. VACCINATIONS & RECALL TASKS
CREATE TABLE vaccine_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    clinic_id UUID NOT NULL REFERENCES clinics(id),
    doctor_id UUID NOT NULL REFERENCES doctors(id),
    vaccine_name VARCHAR(100) NOT NULL, -- DHPPiL, Rabies, Tricat, Deworming
    brand_name VARCHAR(100),            -- Nobivac, Vanguard, Defensor
    batch_number VARCHAR(100) NOT NULL,
    administered_date DATE NOT NULL,
    next_due_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'administered', -- administered, overdue, cancelled
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE recall_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vaccine_event_id UUID NOT NULL REFERENCES vaccine_events(id) ON DELETE CASCADE,
    scheduled_dispatch_time TIMESTAMPTZ NOT NULL,
    recall_trigger VARCHAR(20) NOT NULL, -- 'T-7', 'T-2', 'DAY_0', 'OVERDUE'
    whatsapp_template_name VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'queued', -- queued, sent, failed, responded
    response_action VARCHAR(50),         -- booked, postponed, opted_out
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

---

## 2. Core API Specifications (RESTful / OpenAPI 3.1)

### 2.1 Doctor Consultation & Rx Creation

```http
POST /api/v1/consultations
Content-Type: application/json
Authorization: Bearer <DOCTOR_JWT>

{
  "patient_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "weight_kg": 28.5,
  "temperature_f": 101.4,
  "symptoms": "Lethargy, tick infestation on ears",
  "provisional_diagnosis": "Tick-borne dermatitis & preventive prophylaxis",
  "vaccinations": [
    {
      "vaccine_name": "Anti-Rabies (Annual)",
      "brand_name": "Nobivac Rabies",
      "batch_number": "B78942",
      "next_due_date": "2027-11-19"
    }
  ],
  "medications": [
    {
      "name": "Bravecto Chewable Tablet",
      "dosage": "1 tablet (20-40kg)",
      "frequency": "Stat (Single Dose)",
      "duration_days": 90,
      "is_chronic": true
    },
    {
      "name": "Meloxicam Oral Suspension",
      "dosage": "1.5ml",
      "frequency": "Once daily with food",
      "duration_days": 5,
      "is_chronic": false
    }
  ],
  "dietary_advice": "High protein recovery diet. Avoid chicken bones."
}
```

#### Response (201 Created):
```json
{
  "status": "success",
  "consultation_id": "c1a2b3c4-1122-3344-5566-778899aabbcc",
  "rx_code": "RX-BLR-2027-0891",
  "pdf_url": "https://cdn.pawcare.id/prescriptions/RX-BLR-2027-0891.pdf",
  "passport_url": "https://pawcare.id/pet/bruno-7a8f",
  "whatsapp_status": "queued",
  "vaccine_recalls_scheduled": 2
}
```

---

### 2.2 WhatsApp Cloud API Webhook Controller

```http
POST /api/v1/webhooks/whatsapp
Content-Type: application/json
X-Hub-Signature-256: sha256=...
```

#### Inbound Payload (Pet Parent Clicks Quick Reply):
```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "918000012345",
              "phone_number_id": "PHONE_NUMBER_ID"
            },
            "messages": [
              {
                "from": "919876543210",
                "id": "wamid.HBgLMTE...",
                "timestamp": "1732014000",
                "type": "interactive",
                "interactive": {
                  "type": "button_reply",
                  "button_reply": {
                    "id": "CONFIRM_BOOSTER_SLOT_NOV22",
                    "title": "Confirm Saturday 11am"
                  }
                }
              }
            ]
          },
          "field": "messages"
        }
      ]
    }
  ]
}
```

#### Webhook Handler Logic:
1. Verify `X-Hub-Signature-256` using App Secret.
2. Parse `button_reply.id`:
   - Match `CONFIRM_BOOSTER_SLOT_<SLOT_ID>`.
   - Update `recall_jobs.status = 'responded'`, `recall_jobs.response_action = 'booked'`.
   - Insert confirmed slot into clinic appointment ledger.
   - Dispatch immediate confirmation message via WhatsApp:
     > *"Appointment Confirmed! Bruno is booked with Dr. Rajesh for Saturday, Nov 22 at 11:00 AM. See you at the clinic!"*

---

## 3. Background Job & Scheduling Engine (Temporal / BullMQ)

- **Daily Cron Runner (09:00 IST):**
  - Scans `vaccine_events` for `next_due_date = CURRENT_DATE + INTERVAL '7 days'` &rarr; Enqueues `T-7` WhatsApp messages.
  - Scans `vaccine_events` for `next_due_date = CURRENT_DATE + INTERVAL '2 days'` &rarr; Enqueues `T-2` WhatsApp messages.
  - Scans `vaccine_events` for `next_due_date = CURRENT_DATE - INTERVAL '3 days'` AND `status = 'administered'` &rarr; Enqueues `OVERDUE` urgent recovery notice.
- **Rate-Limiting & Throughput:**
  - WhatsApp Meta Cloud API limits: Tier 2 (10,000 business-initiated conversations/day).
  - Rate-limiter configured to 50 requests/sec with Token Bucket algorithm in Redis.

---

## 4. Digital Prescription PDF Generation Pipeline

1. **Trigger:** Doctor hits "Complete Consultation".
2. **Renderer:** React-PDF / Headless Chromium renders serverless HTML template with:
   - Dynamic Clinic Logo, Name, Address, GSTIN, UPI QR Code.
   - Doctor Name, Qualification, VCI Registration ID, Digital Signature PNG.
   - Pet Name, Species, Breed, Age, Weight, Owner Name & Phone.
   - Formatted Rx Table with Medication, Form, Dosage, Frequency, Duration.
   - QR Code linking to live web passport (`pawcare.id/pet/bruno-7a8f`).
3. **Storage:** PDF uploaded to Cloudflare R2 / AWS S3 (Encrypted at rest).
4. **Delivery:** Signed public CDN link sent via WhatsApp Document Message API.
