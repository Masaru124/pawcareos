# PawCare OS: Implementation Phases & Engineering Roadmap

**Roadmap Strategy:** Rapid Field Deployment & Clinical Feedback Loops  
**Target Milestone:** 150 Partner Clinics in Bangalore Cluster within 9 Months  

---

## Roadmap Overview

```
+---------------------------------------------------------------------------------------------------+
|  PHASE 0: SPIKE & CLINIC PROTOTYPE (Weeks 1–2)                                                    |
|  - WhatsApp Business Cloud API sandbox setup                                                      |
|  - Clickable Doctor Consult UI prototype                                                          |
|  - In-person field validation with 3 friendly Bangalore clinics                                   |
+---------------------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------------------+
|  PHASE 1: CORE CLINICAL MVP (Weeks 3–6)                                                           |
|  - Doctor PWA (Mobile/Tablet Quick Consult Pad)                                                   |
|  - Automated VCI-compliant PDF Prescription generation                                            |
|  - Instant WhatsApp PDF & Web Passport delivery (`pawcare.id/pet/[slug]`)                        |
|  - Patient & Vaccination history database                                                         |
+---------------------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------------------+
|  PHASE 2: THE AUTOMATED RECALL ENGINE & BILLING (Weeks 7–10)                                      |
|  - Cron-based T-7, T-2, Day-0 WhatsApp booster recall jobs                                        |
|  - Interactive WhatsApp Quick-Reply booking confirmation webhook                                  |
|  - Clinic waiting room queue & Dynamic UPI QR billing integration                                 |
|  - First 25 paying clinics onboarded in Bangalore (Koramangala / Indiranagar)                     |
+---------------------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------------------+
|  PHASE 3: CHRONIC CARE COMMERCE & PILOT MONETIZATION (Weeks 11–16)                                 |
|  - 30-day chronic care prescription auto-refill engine (Royal Canin, Bravecto)                    |
|  - Clinic profit-sharing split engine (10% to vet, 15% to PawCare)                                |
|  - Hyperlocal distributor fulfillment pipeline                                                    |
|  - Micro-inventory tracking & low-stock alerts                                                    |
+---------------------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------------------+
|  PHASE 4: REGIONAL DOMINANCE & NETWORK MOAT (Months 5–12)                                         |
|  - Scale to 150 clinics across Bangalore & Mumbai                                                 |
|  - Verified Pet Immunization Graph API for Insurers (Digit / Bajaj) & Boarding Kennels            |
|  - Bulk Wholesale B2B Pharmaceutical Distributor Portal                                           |
+---------------------------------------------------------------------------------------------------+
```

---

## Detailed Sprint Plan

### Phase 1: Core Clinical MVP (Sprints 1–2 | Weeks 3–6)
*Goal: Enable Dr. Rajesh to write a digital prescription and send it to Priya's WhatsApp in under 30 seconds.*
- **Sprint 1.1:**
  - Setup Next.js 15 PWA repository with Tailwind CSS and shadcn/ui.
  - Setup PostgreSQL database schema and FastAPI backend on Supabase / AWS.
  - Build Doctor Quick Consult form with pre-populated drug and vaccine chips.
- **Sprint 1.2:**
  - Build React-PDF prescription template with dynamic VCI license and clinic branding.
  - Configure Meta WhatsApp Cloud API credentials and register initial message templates.
  - Deploy mobile-web Pet Health Passport (`pawcare.id/pet/[slug]`).
  - Deploy to production; run live tests with 5 pioneer clinics.

### Phase 2: Automated Recall & Reception Suite (Sprints 3–4 | Weeks 7–10)
*Goal: Prove clinical revenue recovery by automatically booking overdue vaccinations via WhatsApp.*
- **Sprint 2.1:**
  - Setup Redis and Celery/BullMQ workers.
  - Implement daily 09:00 AM cron scanning for upcoming and overdue vaccines.
  - Register Meta interactive WhatsApp templates with `Confirm Visit` and `Reschedule` quick-reply buttons.
- **Sprint 2.2:**
  - Build webhook controller to receive pet parent button clicks and write confirmed slots to appointment ledger.
  - Implement dynamic UPI QR code generator for clinic reception desk.
  - Onboard 20 additional clinics via direct field sales.

### Phase 3: Chronic Care Auto-Refill (Sprints 5–6 | Weeks 11–16)
*Goal: Turn on high-margin recurring commerce without clinic operational friction.*
- **Sprint 3.1:**
  - Build Chronic Prescription tag (`is_chronic=True`) on digital Rx pad.
  - Create 30-day consumable countdown worker for renal diets and tick/flea chews.
  - Build 1-click Razorpay payment link integration into WhatsApp refill message.
- **Sprint 3.2:**
  - Integrate backend webhook with regional veterinary pet food distributor for same-day delivery dispatch.
  - Build automated clinic ledger calculating the doctor's 10% commission on every completed delivery.
  - Achieve cash-flow positive unit economics across initial clinic cohort.
