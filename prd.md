# PawCare OS: Product Requirements Document (PRD)

**Status:** APPROVED FOR BUILD  
**Version:** 1.0.0  
**Target Market:** India (Initial: Tier-1 Metros) & Global Emerging Markets  
**Target Date:** Q1–Q2 2027  
**Owner:** Product & Engineering Core  

---

## 1. Vision & Executive Summary

PawCare OS is the **"Shopify + WhatsApp Operating System for Independent Veterinary Clinics"**. 

Independent veterinary practices in urban India treat over 85% of companion animals but operate on paper diaries, physical registers, and chaotic unorganized WhatsApp chats. Consequently, **42% of companion pets miss annual vaccination and deworming boosters**, leaving ₹40,000–₹75,000 in monthly recurring clinical revenue uncollected per clinic. Concurrently, $40M venture-backed corporate chains (e.g., Vetic) threaten neighborhood practices with capital-intensive physical rollouts.

PawCare OS provides independent veterinarians with an asset-light, zero-install clinical operating suite. The vet writes digital prescriptions in 20 seconds; the system schedules automated WhatsApp recall notifications; the pet parent accesses a frictionless, permanent **Pet Health Passport** natively in WhatsApp without downloading an app.

PawCare converts local clinics into zero-CAC distribution nodes, unlocking recurring high-margin commerce (chronic prescription diets and tick/flea medications) co-monetized with the treating doctor.

---

## 2. Target Personas

### Persona 1: Dr. Rajesh Sharma (The Independent Veterinarian)
- **Profile:** 48 years old, runs a busy neighborhood clinic in Indiranagar, Bangalore. 1 assistant, 1 receptionist.
- **Volume:** Treats 25–35 pets daily. Conducts surgeries in mornings (10 AM–1 PM), outpatient consults in evenings (4 PM–9 PM).
- **Pain Points:** 
  - Exhausted by end of day; refuses complex enterprise software with nested menus.
  - Loses track of patient vaccination schedules once they walk out the door.
  - Worried about client leakage to modern corporate clinics (Vetic).
- **Core Need:** A fast mobile/tablet tool that creates prescriptions in under 30 seconds, automates client follow-ups, and increases monthly clinic revenue without administrative overhead.

### Persona 2: Priya & Her Golden Retriever "Bruno" (The Millennial Pet Parent)
- **Profile:** 29 years old, product designer living in Koramangala. Treats Bruno as her first child.
- **Pain Points:** 
  - Constantly loses the crumpled paper/cardboard vaccination booklet.
  - Forgets booster due dates until the boarding kennel refuses Bruno for weekend travel.
  - Refuses to install another native single-use app from Play Store/App Store.
  - Frustrated by waiting room chaos with anxious, barking dogs.
- **Core Need:** A permanent digital record on WhatsApp, advance reminders before vaccines lapse, and seamless 1-tap reordering of Bruno's prescription renal diet.

### Persona 3: Anita (The Clinic Front-Desk Receptionist)
- **Profile:** 24 years old, manages appointments, registers, manual cash collection, and WhatsApp queries.
- **Pain Points:** Overwhelmed by phone calls asking "When is doctor free?" and "What was Bruno's last weight?"
- **Core Need:** Live waiting queue ledger, 1-click UPI billing, and automated appointment confirmations.

---

## 3. User Journeys & Critical Paths

### Journey 1: The 20-Second Digital Consultation & WhatsApp Dispatch
1. Dr. Rajesh opens `pawcare.id` on his iPad/phone browser.
2. Taps **"New Patient / Consult"** &rarr; Enters Pet Name ("Bruno"), Species ("Canine"), Breed ("Golden Retriever"), Owner Mobile Number.
3. System loads quick-select templates:
   - Taps *"Annual Booster Package"* (Auto-fills: DHPPiL + Anti-Rabies + Deworming).
   - Taps dosage & batch number.
4. Taps **"Complete & Send"**.
5. Backend generates VCI-compliant PDF prescription with Dr. Rajesh's digital signature and clinic letterhead.
6. WhatsApp Cloud API instantly delivers message to Priya:
   > *"Hi Priya! Dr. Rajesh Sharma has updated Bruno's Pet Passport. View official vaccination certificate & prescription: [pawcare.id/pet/bruno]. Next rabies booster scheduled for: Nov 22, 2027."*

### Journey 2: The Automated Booster Recall Loop
1. System cron job queries database daily at 09:00 AM IST for pets due in 7 days (`T-7`) and 2 days (`T-2`).
2. WhatsApp engine sends personalized template to Priya:
   > *"Hi Priya! Bruno's annual Rabies & 9-in-1 boosters are due this Saturday. Dr. Rajesh has reserved a 15-min priority slot. Tap below to confirm your visit: [Confirm Saturday 11:30 AM] [Reschedule]."*
3. Priya taps **[Confirm Saturday 11:30 AM]**.
4. Clinic ledger updates automatically; appointment confirmed with zero receptionist phone calls.

### Journey 3: Chronic Care Auto-Refill (Commerce Loop)
1. Dr. Rajesh diagnoses Bruno with early renal insufficiency; prescribes *Royal Canin Renal Dog Food (3kg)*.
2. System flags Bruno as a "Chronic Care Patient" (Lifelong diet, 30-day consumable cycle).
3. On Day 25, WhatsApp automated prompt triggers:
   > *"Hi Priya! Bruno's Royal Canin Renal food will run out in 5 days. Dr. Rajesh recommends continuous feeding. Tap to auto-deliver your fresh 3kg bag tomorrow: [Order Now - ₹3,400 via UPI]."*
4. Priya completes UPI payment via WhatsApp Pay / Razorpay link.
5. Partner distributor dispatches bag; 10% profit margin credited to Dr. Rajesh's clinic account; 15% net margin captured by PawCare OS.

---

## 4. Functional Scope (MVP vs. Phase 2)

| Module | MVP (Phase 1) | Phase 2 (Commercial Expansion) |
| :--- | :--- | :--- |
| **Clinic PWA** | Quick Consult, VCI Digital Rx, Patient Directory, WhatsApp dispatch | Surgery scheduler, multi-doctor permissions, multi-branch sync |
| **Recall Engine** | T-7, T-2, Day-0 WhatsApp vaccination reminders | Deworming cycles, chronic prescription auto-reminders, birthday messages |
| **Pet Passport** | Web-based digital vaccination card, weight logs, PDF download | Blood test trends, X-ray viewer, rabies travel boarding clearance badge |
| **Billing** | Dynamic UPI QR code generation, WhatsApp digital GST invoice | Split payments, card machine integration, automated accounting export (Tally/Zoho) |
| **Inventory** | Basic stock decrement on Rx generation, low-stock WhatsApp alerts | Direct wholesale supplier B2B ordering portal, batch expiry tracking |
| **Commerce** | Manual fulfillment coordination for chronic diets | Integrated distributor API, 24-hour hyperlocal doorstep delivery |

---

## 5. Non-Functional Requirements (NFRs)

- **Performance:** 
  - PWA First Contentful Paint (FCP) < 1.2s on 4G connections.
  - Rx generation to WhatsApp delivery P95 latency < 3 seconds.
  - Database queries P95 < 80ms.
- **Reliability & Availability:** 
  - 99.9% uptime for core API and clinic web portal.
  - Asynchronous queue with exponential backoff retry for WhatsApp webhook deliveries.
- **Security & Compliance:** 
  - Veterinary Council of India (VCI) code of ethics compliance.
  - AES-256 encryption at rest; TLS 1.3 in transit.
  - Role-based access control (RBAC): SuperAdmin, Clinic Owner, Associate Vet, Receptionist.
- **Device Support:** 
  - PWA must be 100% responsive across mobile (iOS Safari, Android Chrome), 10.2" iPads/tablets, and desktop laptops.

---

## 6. Success Metrics & North Star

- **North Star Metric:** Total Verified Vaccinations Administered & Tracked Monthly.
- **Clinic Adoption:** 150 Partner Clinics in Bangalore cluster within 9 months.
- **Recall Efficacy:** >= 35% of lapsed pet parents book appointment within 48 hours of WhatsApp recall message.
- **Clinic Revenue Delta:** Average ₹45,000+ incremental clinical revenue recovered per clinic per month.
- **Net Revenue Retention (NRR):** >= 120% by Month 12 via chronic care fulfillment.
