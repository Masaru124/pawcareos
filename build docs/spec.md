# PawCare OS: Technical & Functional Specification (SPEC v3.0)

**Document:** Complete 3-Sided Architecture Specification (Pet Parent, Doctor, Admin)  
**Version:** 3.0.0  
**Target Architecture:** Next.js 15 PWA + FastAPI Python 3.12 + Supabase PostgreSQL 16  

---

## 1. Complete Database Schema (DDL for All 3 Surfaces)

```sql
-- =========================================================================
-- 1. CLINIC & ADMIN ENTITIES
-- =========================================================================

CREATE TABLE clinics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    gstin VARCHAR(15),
    drug_license_no VARCHAR(100),
    phone VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL,
    address_line1 TEXT NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    pincode VARCHAR(10) NOT NULL,
    geo_point POINT,
    upi_vpa VARCHAR(100), -- Clinic direct UPI VPA (e.g. shantivet@icici)
    logo_url TEXT,
    stamp_signature_url TEXT,
    consultation_fee NUMERIC(10,2) DEFAULT 500.00,
    emergency_fee NUMERIC(10,2) DEFAULT 1200.00,
    subscription_tier VARCHAR(50) DEFAULT 'starter', -- starter, pro, enterprise
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE clinic_staff (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role VARCHAR(50) NOT NULL, -- 'SUPERADMIN', 'DOCTOR', 'RECEPTIONIST', 'GROOMER'
    vci_registration_no VARCHAR(100), -- Mandatory for DOCTOR
    qualification VARCHAR(255),       -- e.g. 'B.V.Sc & A.H., M.V.Sc (Surgery)'
    digital_signature_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================================
-- 2. PATIENT & PET PARENT ENTITIES
-- =========================================================================

CREATE TABLE pet_parents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL UNIQUE, -- E.164: +919876543210
    whatsapp_opt_in BOOLEAN DEFAULT TRUE,
    email VARCHAR(255),
    password_hash TEXT,
    auth_provider VARCHAR(20) DEFAULT 'otp', -- 'otp', 'password', 'google'
    address TEXT,
    pincode VARCHAR(10),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id UUID NOT NULL REFERENCES pet_parents(id) ON DELETE CASCADE,
    primary_clinic_id UUID NOT NULL REFERENCES clinics(id),
    name VARCHAR(100) NOT NULL,
    species VARCHAR(50) NOT NULL, -- Canine, Feline, Avian, Exotic
    breed VARCHAR(100) NOT NULL,
    gender VARCHAR(20) NOT NULL,  -- Male, Female, Neutered Male, Spayed Female
    dob DATE,
    weight_kg NUMERIC(5,2),
    microchip_no VARCHAR(50) UNIQUE,
    color_markings VARCHAR(150),
    allergies TEXT[],
    chronic_conditions TEXT[],
    passport_slug VARCHAR(100) UNIQUE NOT NULL, -- e.g. 'bruno-7a8f'
    profile_photo_url TEXT,
    is_lost BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pet_weight_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pet_id UUID NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
    weight_kg NUMERIC(5,2) NOT NULL,
    logged_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    logged_by_doctor_id UUID REFERENCES clinic_staff(id)
);

CREATE TABLE household_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    primary_parent_id UUID NOT NULL REFERENCES pet_parents(id) ON DELETE CASCADE,
    member_parent_id UUID NOT NULL REFERENCES pet_parents(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'CO_OWNER', -- 'CO_OWNER', 'CARETAKER', 'VIEWER'
    permissions JSONB DEFAULT '{"view_records": true, "book_appointments": true, "make_payments": false}',
    status VARCHAR(20) DEFAULT 'PENDING', -- 'PENDING', 'ACCEPTED', 'REVOKED'
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(primary_parent_id, member_parent_id)
);

CREATE TABLE legacy_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pet_id UUID NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
    uploaded_by UUID NOT NULL REFERENCES pet_parents(id),
    record_type VARCHAR(50) NOT NULL, -- 'VACCINE_CARD', 'EXTERNAL_RX', 'LAB_REPORT', 'XRAY'
    description TEXT,
    file_url TEXT NOT NULL,
    file_hash VARCHAR(64),
    uploaded_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================================
-- 3. CLINICAL WORKFLOW: QUEUE, CONSULTS, SOAP & PRESCRIPTIONS
-- =========================================================================

CREATE TABLE queue_tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    pet_id UUID NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
    ticket_number INT NOT NULL,
    ticket_type VARCHAR(50) DEFAULT 'OPD', -- 'OPD', 'VACCINE', 'EMERGENCY', 'SURGERY'
    status VARCHAR(50) DEFAULT 'WAITING',   -- 'WAITING', 'IN_CONSULT', 'BILLING', 'COMPLETED'
    check_in_time TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    called_time TIMESTAMPTZ,
    completed_time TIMESTAMPTZ
);

CREATE TABLE consultations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID NOT NULL REFERENCES clinics(id),
    doctor_id UUID NOT NULL REFERENCES clinic_staff(id),
    pet_id UUID NOT NULL REFERENCES pets(id),
    weight_kg NUMERIC(5,2) NOT NULL,
    temperature_f NUMERIC(4,1),
    body_condition_score INT, -- 1 to 9
    heart_rate_bpm INT,
    crt_seconds NUMERIC(3,1),
    is_teleconsult BOOLEAN DEFAULT FALSE,
    consult_fee NUMERIC(10,2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE soap_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consultation_id UUID NOT NULL UNIQUE REFERENCES consultations(id) ON DELETE CASCADE,
    subjective TEXT,              -- Owner history & chief complaint
    objective TEXT,               -- Physical examination findings
    assessment TEXT NOT NULL,     -- Diagnoses (primary and differential)
    plan TEXT NOT NULL,           -- Medications, diagnostics, diet, follow-up
    ai_transcription_raw TEXT,    -- Speech-to-text transcript from consult
    is_ai_generated BOOLEAN DEFAULT FALSE,
    reviewed_by_doctor BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE prescriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consultation_id UUID NOT NULL REFERENCES consultations(id) ON DELETE CASCADE,
    rx_serial_no VARCHAR(50) UNIQUE NOT NULL, -- e.g. 'RX-BLR-2027-0482'
    dietary_advice TEXT,
    general_notes TEXT,
    pdf_url TEXT NOT NULL,
    pdf_hash VARCHAR(64) NOT NULL, -- SHA256 of PDF for tamper verification
    whatsapp_dispatch_id VARCHAR(100),
    whatsapp_status VARCHAR(50) DEFAULT 'PENDING',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE prescription_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prescription_id UUID NOT NULL REFERENCES prescriptions(id) ON DELETE CASCADE,
    medicine_name VARCHAR(255) NOT NULL,
    dosage_form VARCHAR(50) NOT NULL, -- 'Tablet', 'Syrup', 'Chewable', 'Spot-On', 'Injection'
    strength VARCHAR(50),             -- e.g. '200mg', '10mg/ml'
    dose_calculated VARCHAR(50) NOT NULL, -- e.g. '1.5ml', '1 tablet'
    frequency VARCHAR(50) NOT NULL,   -- 'Once Daily (SID)', 'Twice Daily (BID)', 'Thrice Daily (TID)'
    duration_days INT NOT NULL,
    special_instructions VARCHAR(255),
    is_chronic BOOLEAN DEFAULT FALSE,
    refill_due_date DATE
);

CREATE TABLE medication_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prescription_item_id UUID NOT NULL REFERENCES prescription_items(id) ON DELETE CASCADE,
    pet_id UUID NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
    medicine_name VARCHAR(255) NOT NULL,
    dose VARCHAR(100) NOT NULL,
    frequency VARCHAR(50) NOT NULL,
    scheduled_time TIME NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE', -- 'ACTIVE', 'PAUSED', 'COMPLETED'
    last_confirmed_at TIMESTAMPTZ,
    compliance_count INT DEFAULT 0,
    total_doses INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE vaccinations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pet_id UUID NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
    clinic_id UUID NOT NULL REFERENCES clinics(id),
    doctor_id UUID NOT NULL REFERENCES clinic_staff(id),
    vaccine_name VARCHAR(100) NOT NULL, -- 'Nobivac DHPPiL', 'Nobivac Rabies', 'Felocell 4'
    batch_lot_number VARCHAR(100) NOT NULL,
    manufacturer VARCHAR(100),
    administered_date DATE NOT NULL,
    next_booster_due_date DATE NOT NULL,
    certificate_id VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'ACTIVE' -- 'ACTIVE', 'OVERDUE', 'SUPERSEDED'
);

-- =========================================================================
-- 4. RECALLS, COMMERCE, WELLNESS, REVIEWS & INVENTORY
-- =========================================================================

CREATE TABLE recall_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vaccination_id UUID REFERENCES vaccinations(id) ON DELETE CASCADE,
    pet_id UUID NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
    trigger_type VARCHAR(20) NOT NULL, -- 'T-7', 'T-2', 'DAY_0', 'OVERDUE_3'
    scheduled_date DATE NOT NULL,
    whatsapp_template VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'SCHEDULED', -- 'SCHEDULED', 'SENT', 'RESPONDED', 'FAILED'
    response_payload JSONB
);

CREATE TABLE chronic_refill_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pet_id UUID NOT NULL REFERENCES pets(id),
    clinic_id UUID NOT NULL REFERENCES clinics(id),
    product_name VARCHAR(255) NOT NULL, -- 'Royal Canin Renal Dog Food 3kg'
    sku VARCHAR(100) NOT NULL,
    total_amount NUMERIC(10,2) NOT NULL,
    clinic_commission_amount NUMERIC(10,2) NOT NULL, -- 10%
    pawcare_margin_amount NUMERIC(10,2) NOT NULL,    -- 15%
    payment_status VARCHAR(50) DEFAULT 'PENDING',
    fulfillment_status VARCHAR(50) DEFAULT 'ORDERED', -- 'ORDERED', 'DISPATCHED', 'DELIVERED'
    courier_tracking_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE inventory_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    item_name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL, -- 'VACCINE', 'PHARMA', 'SURGICAL', 'DIET'
    batch_no VARCHAR(100),
    expiry_date DATE,
    current_stock INT NOT NULL DEFAULT 0,
    reorder_threshold INT NOT NULL DEFAULT 10,
    cost_price NUMERIC(10,2),
    mrp NUMERIC(10,2) NOT NULL
);

CREATE TABLE wellness_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    plan_name VARCHAR(255) NOT NULL,
    species VARCHAR(50) NOT NULL,
    description TEXT,
    includes JSONB NOT NULL, -- vaccines, dewormings, blood_tests, consults, dental
    annual_price NUMERIC(10,2) NOT NULL,
    monthly_emi NUMERIC(10,2) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pet_wellness_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pet_id UUID NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
    plan_id UUID NOT NULL REFERENCES wellness_plans(id),
    clinic_id UUID NOT NULL REFERENCES clinics(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    monthly_amount NUMERIC(10,2) NOT NULL,
    payments_completed INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'ACTIVE', -- 'ACTIVE', 'PAUSED', 'EXPIRED', 'CANCELLED'
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consultation_id UUID NOT NULL REFERENCES consultations(id),
    pet_parent_id UUID NOT NULL REFERENCES pet_parents(id),
    doctor_id UUID NOT NULL REFERENCES clinic_staff(id),
    clinic_id UUID NOT NULL REFERENCES clinics(id),
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review_text TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    google_review_redirected BOOLEAN DEFAULT FALSE,
    clinic_responded BOOLEAN DEFAULT FALSE,
    clinic_response TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE doctor_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    staff_id UUID NOT NULL UNIQUE REFERENCES clinic_staff(id) ON DELETE CASCADE,
    profile_slug VARCHAR(200) UNIQUE NOT NULL, -- e.g. 'dr-rajesh-sharma-bangalore'
    bio TEXT,
    years_experience INT,
    specializations TEXT[],
    languages TEXT[],
    education TEXT[],
    profile_photo_url TEXT,
    clinic_photos TEXT[],
    is_published BOOLEAN DEFAULT FALSE,
    avg_rating NUMERIC(2,1) DEFAULT 0.0,
    total_reviews INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================================
-- 5. LOYALTY, REFERRALS, MILESTONES, INSURANCE & Q&A
-- =========================================================================

CREATE TABLE loyalty_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pet_parent_id UUID NOT NULL REFERENCES pet_parents(id) ON DELETE CASCADE,
    clinic_id UUID NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    points_balance INT DEFAULT 0,
    lifetime_points INT DEFAULT 0,
    tier VARCHAR(20) DEFAULT 'BRONZE', -- 'BRONZE', 'SILVER', 'GOLD', 'PLATINUM'
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(pet_parent_id, clinic_id)
);

CREATE TABLE loyalty_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    loyalty_id UUID NOT NULL REFERENCES loyalty_points(id) ON DELETE CASCADE,
    points INT NOT NULL, -- positive for earn, negative for redeem
    type VARCHAR(20) NOT NULL, -- 'EARN_CONSULT', 'EARN_VACCINE', 'EARN_PRODUCT', 'REDEEM'
    description VARCHAR(255),
    reference_id UUID,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE referrals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    referrer_parent_id UUID NOT NULL REFERENCES pet_parents(id) ON DELETE CASCADE,
    referred_phone VARCHAR(20) NOT NULL,
    referred_parent_id UUID REFERENCES pet_parents(id),
    referral_code VARCHAR(20) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING', -- 'PENDING', 'COMPLETED', 'EXPIRED'
    referrer_credit NUMERIC(10,2) DEFAULT 200.00,
    referred_credit NUMERIC(10,2) DEFAULT 200.00,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pet_milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pet_id UUID NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
    milestone_type VARCHAR(50) NOT NULL, -- 'BIRTHDAY', 'GOTCHA_DAY', 'FLEA_FREE_STREAK'
    milestone_date DATE NOT NULL,
    message_sent BOOLEAN DEFAULT FALSE,
    discount_code VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE insurance_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pet_id UUID NOT NULL REFERENCES pets(id),
    pet_parent_id UUID NOT NULL REFERENCES pet_parents(id),
    clinic_id UUID NOT NULL REFERENCES clinics(id),
    provider VARCHAR(100) NOT NULL, -- 'Digit', 'Bajaj Allianz', 'TATA AIG'
    policy_number VARCHAR(100),
    claim_amount NUMERIC(10,2) NOT NULL,
    consultation_ids UUID[] NOT NULL,
    documents_url TEXT[],
    status VARCHAR(20) DEFAULT 'DRAFT', -- 'DRAFT', 'SUBMITTED', 'APPROVED', 'REJECTED'
    submitted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE qa_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pet_parent_id UUID NOT NULL REFERENCES pet_parents(id),
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    species VARCHAR(50),
    tags TEXT[],
    upvotes INT DEFAULT 0,
    answer_count INT DEFAULT 0,
    is_resolved BOOLEAN DEFAULT FALSE,
    slug VARCHAR(300) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE qa_answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID NOT NULL REFERENCES qa_questions(id) ON DELETE CASCADE,
    doctor_id UUID NOT NULL REFERENCES clinic_staff(id),
    body TEXT NOT NULL,
    upvotes INT DEFAULT 0,
    is_accepted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

---

## 2. API Endpoints by User Surface

### 2.0 Auth & Onboarding (`/api/v1/auth`)
- `POST /auth/patient/signup` — Pet parent registration (Name, Phone, Email, Password).
- `POST /auth/patient/login/password` — Password authentication.
- `POST /auth/patient/otp/send` — Send OTP to WhatsApp / SMS.
- `POST /auth/patient/otp/verify` — Verify OTP and set JWT cookie.
- `POST /auth/doctor/signup` — Doctor registration with VCI license verification.
- `POST /auth/doctor/login` — Clinical authentication.

### 2.1 Doctor & Clinical Suite (`/api/v1/doctor`)
- `POST /consultations` — Submit consult with SOAP note; triggers Rx PDF, inventory decrement, vaccine updates.
- `POST /consultations/ai-scribe` — Audio stream transcription into structured SOAP note.
- `GET /patients/search?q={phone|name|chip}` — Fast patient lookup with vital trends.
- `GET /patients/{id}/emr` — Chronological EMR timeline.
- `GET /formulary/drugs` — Veterinary drug database with weight-based dosage formulas.
- `POST /doctor-profile` — Update public SEO profile data.

### 2.2 Pet Parent & Passport (`/api/v1/patient`)
- `GET /patient/dashboard` — Authenticated parent hub (pets, reminders, active orders).
- `GET /pet/{slug}` — Public tokenized Pet Health Passport.
- `GET /pet/{slug}/certificate/pdf` — Verified travel certificate PDF.
- `POST /records/upload` — Upload legacy paper records (photos/PDFs).
- `POST /reminders/{id}/confirm` — Parent confirms medication administered.
- `POST /household/invite` — Invite co-owner/caretaker to pet profile.
- `POST /reviews` — Submit post-visit rating and feedback.
- `GET /rewards/balance` — PawPoints ledger and referral stats.
- `POST /emergency/triage` — AI emergency symptom and poison evaluation.

### 2.3 Admin & Practice Management (`/api/v1/admin`)
- `GET /queue` — Live Kanban waiting room queue.
- `POST /queue/checkin` — Check in walk-in patient.
- `POST /billing/checkout` — Generate dynamic UPI QR and GST invoice.
- `GET /inventory` — Real-time stock counts and 60-day expiry tracker.
- `POST /wellness-plans` — Create bundled wellness subscription packages.
- `GET /reviews/dashboard` — Review management and Google routing analytics.
- `GET /analytics/recalls` — Revenue recovered from automated vaccine recalls.
- `GET /analytics/chronic` — Monthly 10% commission payout breakdown.
