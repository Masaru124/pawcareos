# PawCare OS: Implementation Phases & Engineering Roadmap (v3.0)

**Roadmap Strategy:** B2B-First Wedge (The Practo Ray Path)  
**Milestone:** 150 Partner Clinics in Bangalore Cluster & 75,000 Verified Pet Passports  

---

## The 4-Phase Rollout Sequence

```
+---------------------------------------------------------------------------------------------------+
|  PHASE 1: THE CLINICAL WEDGE (Practo Ray for Vets)                                                |
|  - 20-second Doctor Quick Consult Pad (Next.js PWA) with SOAP Clinical Notes                     |
|  - VCI-compliant digital prescription PDF generation with SHA-256 hash                            |
|  - WhatsApp interactive Pet Health Passport delivery                                              |
|  - Automated T-7 & T-2 vaccine & deworming recalls (recovers ₹50,000/mo)                          |
|  - Daily Medication Reminders via WhatsApp (improves pet compliance)                              |
|  - Pet Parent Self-Signup & Hybrid Auth (OTP / Password / Google)                                 |
|  - Legacy Medical Record Vault (pet parents upload paper cards / past blood reports)              |
+---------------------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------------------+
|  PHASE 2: COMMERCE, RETENTION & CLIENT DELIGHT (PawCare Retention)                                |
|  - AI Scribe (Voice-to-SOAP note transcription for doctors)                                       |
|  - 30-day chronic care auto-refill engine (Royal Canin, Bravecto) with 10% vet split               |
|  - Clinic waiting room queue & Dynamic UPI QR billing                                             |
|  - Post-Visit Review Collection + Smart Google Business Profile Routing                           |
|  - Annual Wellness Care Plans (Puppy/Adult/Senior) with Monthly EMI Auto-Debit                    |
|  - Household Multi-Owner Access (co-owner/caretaker permissions)                                  |
|  - Pet Birthday & Gotcha Day automated cards with 10% wellness discount                           |
|  - Viral Referral Program (₹200 credit for referrer + friend)                                     |
+---------------------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------------------+
|  PHASE 3: CONSUMER DISCOVERY & 24/7 EMERGENCY TRIAGE (PawCare Search)                            |
|  - Public Doctor & Clinic SEO Profile Pages (`pawcare.id/dr/[slug]`)                              |
|  - PawPoints Loyalty System & Preventive Care Streak Badges                                       |
|  - 24/7 AI-assisted emergency & pet toxicity triage router                                        |
|  - Pet Insurance 1-Click Claim Filing (Digit, Bajaj Allianz, TATA AIG)                            |
|  - In-clinic lab diagnostic analyzer integration (bloodwork trends on WhatsApp)                   |
|  - Post-surgical photo healing check-ins via WhatsApp                                             |
+---------------------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------------------+
|  PHASE 4: NETWORK DATA MOAT & COMMUNITY (2,500 Clinics)                                           |
|  - Public Health Q&A Community Forum (Lybrate for Pets, answered by verified vets)               |
|  - Verified Pet Immunization Graph API for airlines, pet insurers & boarding kennels             |
|  - Bulk B2B pharmaceutical wholesale distributor hub (Zoetis, Virbac, Royal Canin)                |
+---------------------------------------------------------------------------------------------------+
```

---

## Detailed Sprint Plan

### Phase 1: Core Clinical MVP (Sprints 1–2 | Weeks 1–6)
*Goal: Enable Dr. Rajesh to write a digital prescription and send it to Priya's WhatsApp in under 30 seconds.*
- **Sprint 1.1:**
  - Setup Next.js 15 PWA repository with Tailwind CSS and shadcn/ui.
  - Setup PostgreSQL 16 database schema on Supabase (Mumbai) + FastAPI backend.
  - Build Doctor Quick Consult form with SOAP structure and formulary drug chips.
  - Implement Pet Parent self-registration & hybrid auth (WhatsApp OTP + Email/Password + Google).
- **Sprint 1.2:**
  - Build React-PDF prescription template with dynamic VCI license and clinic branding.
  - Configure Meta WhatsApp Cloud API credentials and register initial message templates.
  - Deploy mobile-web Pet Health Passport (`pawcare.id/pet/[slug]`) and Legacy Record Vault.
  - Deploy Daily Medication Reminders via WhatsApp scheduler.
  - Deploy to production; run live tests with 5 pioneer clinics.

### Phase 2: Retention, Commerce & AI Scribe (Sprints 3–4 | Weeks 7–12)
*Goal: Prove clinical revenue recovery, launch AI Scribe, and turn on recurring wellness commerce.*
- **Sprint 2.1:**
  - Setup Redis and Celery/BullMQ workers for 09:00 AM vaccine recall crons.
  - Build AI Scribe prototype (voice audio stream -> Whisper -> structured SOAP note).
  - Register Meta interactive WhatsApp templates for Post-Visit Reviews with Google routing.
  - Implement Annual Wellness Plans manager with monthly UPI mandate auto-debit.
- **Sprint 2.2:**
  - Build Chronic Care Auto-Refill (30-day consumable countdown + 1-tap Razorpay payment).
  - Implement Household multi-owner access and referral program (₹200 credits).
  - Deploy Dynamic UPI QR counter display for front-desk checkout.
  - Onboard 20 additional clinics via direct field sales.

### Phase 3: Consumer Discovery & Insurance (Sprints 5–6 | Weeks 13–18)
*Goal: Drive organic patient acquisition via Google SEO and unlock high-value insurance partnerships.*
- **Sprint 3.1:**
  - Launch SSR Public Doctor Profile Pages (`pawcare.id/dr/[slug]`) indexed for Google Local SEO.
  - Build PawPoints loyalty ledger and preventive care streak engine.
  - Build 24/7 AI Emergency & Poison Triage router on WhatsApp and Web.
- **Sprint 3.2:**
  - Launch 1-Click Pet Insurance Claim Package generation (Digit, Bajaj Allianz).
  - Integrate benchtop diagnostic analyzers for automatic bloodwork trend plotting.
  - Achieve cash-flow positive unit economics across initial clinic cluster.
