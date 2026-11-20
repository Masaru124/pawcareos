# PawCare OS: Complete Product Requirements Document (PRD v3.0)

**Target Architecture:** 3-Sided Ecosystem (Pet Parent, Doctor, Clinic Admin)  
**Version:** 3.0.0  
**Target Market:** India Tier 1/2 Metros + Global Emerging Markets  

---

## 1. System Topology & User Surface Architecture

PawCare OS operates on three dedicated surfaces:

```
+---------------------------------------------------------------------------------------------------+
|                                     PAWCARE OS USER SURFACES                                      |
+---------------------------------------------------------------------------------------------------+
|  1. PET PARENT (CONSUMER)           |  2. DOCTOR (CLINICAL)             |  3. CLINIC ADMIN (OPS)  |
|  Domains:                           |  Domains:                         |  Domains:               |
|  - pawcare.id/login                 |  - clinic.pawcare.id/login        |  - admin.pawcare.id/    |
|  - pawcare.id/dashboard             |  - clinic.pawcare.id/consult      |  - /queue (Live Desk)   |
|  - pawcare.id/pet/[slug] (Passport) |  - clinic.pawcare.id/emr/[id]     |  - /checkout (UPI QR)   |
|  - pawcare.id/dr/[slug] (Doctor SEO)|  - clinic.pawcare.id/profile      |  - /inventory (Stock)   |
|  - WhatsApp Native Chatbot Hub      |  - PWA Offline Touch Pad (iPad)   |  - /wellness & /reviews |
+---------------------------------------------------------------------------------------------------+
```

### URL & Routing Structure

#### Surface 1: Pet Parent (`pawcare.id`)
- `pawcare.id/` — Marketing landing page + clinic search locator.
- `pawcare.id/login` & `/signup` — Hybrid authentication (WhatsApp OTP, Email/Password, Google OAuth).
- `pawcare.id/dashboard` — Authenticated parent hub (multi-pet selector, reminders, active orders).
- `pawcare.id/pet/[slug]` — Tokenized public/verified Pet Health Passport (airline/kennel verification).
- `pawcare.id/pet/[slug]/records` — Lifetime medical vault (clinic auto-synced + legacy user uploads).
- `pawcare.id/household` — Multi-owner family access (spouse, dog walker, caretaker permissions).
- `pawcare.id/rewards` — PawPoints loyalty ledger, preventive care streaks, referral program.
- `pawcare.id/dr/[slug]` — Public SEO-indexed doctor profile pages with verified reviews.
- `pawcare.id/qa` & `/qa/[slug]` — Community health Q&A forum answered by verified vets.
- `pawcare.id/emergency` — 24/7 AI-assisted poison and trauma triage router.

#### Surface 2: Doctor & Clinical Staff (`clinic.pawcare.id`)
- `clinic.pawcare.id/login` & `/signup` — Doctor self-serve onboarding + VCI registration verification.
- `clinic.pawcare.id/consult` — 20-second rapid consult pad with SOAP structure and AI Scribe.
- `clinic.pawcare.id/patients` & `/patients/[id]` — Chronological EMR timeline, lab trends, surgical logs.
- `clinic.pawcare.id/telehealth` — Post-op incision photo verification and remote follow-ups.
- `clinic.pawcare.id/profile` — Doctor public SEO profile editor and verification manager.

#### Surface 3: Admin & Reception Desk (`admin.pawcare.id`)
- `admin.pawcare.id/queue` — Live Kanban waiting room queue with priority triage tags.
- `admin.pawcare.id/checkout` — Reception billing with dynamic UPI QR generation and GST breakdown.
- `admin.pawcare.id/inventory` — Drug and vaccine inventory ledger with batch/expiry audits.
- `admin.pawcare.id/wellness-plans` — Annual wellness subscriptions manager (monthly EMI billing).
- `admin.pawcare.id/reviews` — Reputation manager (smart routing: 4-5 stars to Google, 1-3 stars private).
- `admin.pawcare.id/analytics` — Vaccine recall ROI tracker, chronic care commission payouts, P&L.
- `admin.pawcare.id/staff` — RBAC permission matrix (SuperAdmin, Associate Vet, Reception, Groomer).

---

## 2. Pet Parent (Patient) Requirements

### 2.1 Identity, Hybrid Auth & Dashboard
1. **Self-Serve Registration:** Pet parents sign up independently before clinic visits.
2. **Hybrid Login Options:**
   - WhatsApp / SMS OTP (1-tap frictionless entry).
   - Email + Password (standard credential entry).
   - Google 1-Tap OAuth.
3. **Multi-Pet Management:** Switch between up to 10 pets under single household.
4. **Household Multi-Owner Access:** Primary owner invites spouse or dog walker via WhatsApp with granular permissions (`view_records`, `book_appointments`, `make_payments`).

### 2.2 Digital Health Passport (`pawcare.id/pet/[slug]`)
1. **Identity & Bio Card:** Dynamic age, breed, microchip number with 1-tap copy, color markings.
2. **Immunization Badges:** Real-time visual status (Green = Active, Amber = Due < 30 days, Red = Overdue).
3. **Official PDF Certificate Generator:** 1-tap download of airline-compliant and boarding-verified vaccine certificates.
4. **Weight Tracking:** Visual growth curves against breed percentiles. Warns on >10% 30-day weight drops.
5. **Critical Medical Flags:** Red banner for drug allergies (Penicillin, Ivermectin) and chronic illnesses.

### 2.3 Medical Vault & Legacy Record Uploads
1. **Clinic Auto-Sync:** Prescriptions, lab reports, and vaccine records populate immediately post-consult.
2. **Legacy Record Upload:** Pet parents upload photos or PDFs of old paper vaccine cards, historical blood tests, and external clinic prescriptions before first PawCare visit.

### 2.4 WhatsApp Conversational Hub
1. **Automated Recalls:** T-7, T-2, Day-0 WhatsApp reminders for vaccines and deworming with `[Confirm]` / `[Reschedule]` buttons.
2. **Digital Prescription Delivery:** Branded, encrypted PDF delivered within 3 seconds of consult completion.
3. **Daily Medication Reminders:** Automated WhatsApp medication reminders (e.g., *"Time for Bruno's Meloxicam 1.5ml with dinner. Tap [Given ✓]"*). Logs adherence for the doctor.
4. **Chronic Care Auto-Refills:** 5 days before renal diets or flea/tick meds deplete, prompts 1-tap UPI reorder delivered from local distributor.
5. **24/7 AI Emergency & Poison Triage:** Free toxicity calculator (chocolate, lilies, paracetamol) with Green/Yellow/Red severity rating and 1-tap navigation to open 24/7 emergency trauma centers.
6. **Pet Birthday & Gotcha Day Delights:** Automated celebratory card with 10% clinic wellness discount code.
7. **Lost Pet Amber Alert:** 1-tap broadcast generates digital poster and notifies clinics within 5km radius.

### 2.5 Loyalty, Rewards & Community
1. **PawPoints System:** Earn points for consults (+50), vaccines (+100), diet purchases (+25). Redeem for free nail trims or grooming discounts.
2. **Preventive Care Badges:** Streak badges (e.g., *"12-Month Flea-Free Streak 🏆"*).
3. **Referral Program:** Refer a friend; both receive ₹200 clinic credits upon completed visit.
4. **Public Doctor Profiles:** View doctor credentials, photos, and verified reviews (`pawcare.id/dr/[slug]`).
5. **Community Health Q&A:** Public Q&A indexed on Google; verified vets provide answers (`pawcare.id/qa`).

---

## 3. Doctor (Clinical Workflow) Requirements

### 3.1 Self-Serve Onboarding
1. Direct doctor registration with VCI license validation.
2. Automatic tenant creation for independent private practice.
3. Configurable consultation fees, emergency fees, and working hours.

### 3.2 20-Second Rapid Consult Pad
1. **Vitals Quick-Entry:** Weight (kg), Temperature (°F/°C), Body Condition Score (1–9 scale), Heart Rate, CRT.
2. **SOAP Clinical Note Structure:**
   - **S (Subjective):** Chief complaint and owner history.
   - **O (Objective):** Clinical exam findings and vitals.
   - **A (Assessment):** Primary and differential diagnoses.
   - **P (Plan):** Prescriptions, diagnostics, diet, follow-up.
3. **AI Scribe (Voice-to-SOAP):** Real-time audio stream converts spoken doctor-owner dialogue into structured SOAP draft.
4. **Quick-Chip Diagnosis Engine:** 1-tap chips for 90% common cases (Parvovirus, Tick Fever, Atopic Dermatitis, Gastroenteritis, Annual Booster). Full ICD-Vet search.
5. **Smart Weight-Based Formulary:** Over 800 veterinary drugs with auto-calculated mg/kg dosages.
6. **Vaccine Batch Auto-Tracking:** Selects vaccine name, pulls current clinic batch number, auto-sets next booster date.
7. **1-Tap Complete & Dispatch:** Commits record, generates SHA-256 signed PDF, decrements inventory, and dispatches WhatsApp alert in under 50ms.

### 3.3 Patient Medical Vault & Diagnostics
1. **Chronological EMR Timeline:** Complete history filterable by consultations, vaccines, surgeries, and labs.
2. **Diagnostic Trends:** Interactive charts for recurring lab markers (Creatinine, BUN, ALT, Platelets).
3. **Specialist Referral Engine:** Generates formal referral summary with 1-click PDF export.

### 3.4 Surgical Suite & Telehealth Follow-Up
1. **Pre-Op Fasting & Consent:** Digital owner signature on pre-anesthetic clearance.
2. **Surgical Protocol Notes:** Logs anesthesia induction, maintenance gas, and vitals.
3. **Post-Op Healing Photo Checks:** Automated Day 1, Day 3, Day 7 WhatsApp photo requests displayed in doctor review queue.

### 3.5 Reputation & SEO Visibility
1. **Post-Visit Review Automation:** After consult, WhatsApp asks parent to rate visit (1–5 stars).
2. **Smart Reputation Routing:** 4–5 star reviews prompt 1-click Google Business redirect. 1–3 star ratings route to private clinic manager inbox for immediate recovery.
3. **Public Doctor SEO Profile:** Indexed page showing qualifications, specialties, and verified ratings.

---

## 4. Admin & Practice Management Requirements

### 4.1 Front-Desk & Live Queue
1. **Live Queue Kanban:** Tracks Checked In, In Consult, In Surgery, Billing, Completed.
2. **WhatsApp Queue Sync:** Displays live queue position to waiting pet parents.
3. **Dynamic UPI Reception Billing:** Displays on-counter dynamic UPI QR code (consult fee + pharmacy). Auto-verifies payment via webhook.
4. **GST Tax Invoice Generator:** Separates tax-exempt veterinary clinical services from taxable pet pharmacy products.
5. **End-of-Day Reconciliation:** Automated 9:00 PM reconciliation report (Cash vs UPI vs Card) sent to clinic owner.

### 4.2 Inventory & Wholesale Supply
1. **Automated Stock Decrement:** Real-time sync upon prescription issuance or retail checkout.
2. **Low-Stock & Expiry Alerts:** Alerts when inventory drops below threshold or expires within 60 days.
3. **B2B Wholesale Ordering:** 1-click purchase orders direct to pharma distributors (Zoetis, Virbac, Royal Canin) unlocking 30% margin.

### 4.3 Recurring Revenue & Wellness Subscriptions
1. **Annual Wellness Plans:** Bundled preventive care packages (e.g., Puppy Shield, Adult Guard, Senior Care).
2. **Monthly EMI Engine:** Auto-debited monthly via UPI mandate.
3. **Chronic Care Commission Ledger:** Tracks clinic's 10% cut on repeat food and medication refills fulfilled through network distributors.

### 4.4 Insurance & Legal Compliance
1. **1-Click Pet Insurance Claim Package:** Combines verified consultation history, itemized receipts, and doctor SOAP notes for Digit, Bajaj Allianz, and TATA AIG claims.
2. **Staff RBAC Control:** Strict permissions for SuperAdmin, Associate Vet, Receptionist, and Groomer.
3. **VCI & DPDP Act 2023 Compliance:** SHA-256 prescription integrity hashing, consent logging, and data residency in Mumbai (`ap-south-1`).
