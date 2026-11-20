# PawCare OS: Complete UI/UX Specification & Screen Wireframes (v3.0)

**Target Surfaces:**
1. **Pet Parent Surface:** Mobile Web (`pawcare.id`) + Meta WhatsApp Native Interface.
2. **Doctor Surface:** Touch-Optimized PWA for iPad / Android Tablet / Mobile (`clinic.pawcare.id`).
3. **Admin Surface:** High-Density Desktop & Tablet Practice Cockpit (`admin.pawcare.id`).

---

## 1. PET PARENT (PATIENT) USER INTERFACE & SCREENS

### Screen 1.0: Self-Serve Signup & Hybrid Login (`pawcare.id/login` & `/signup`)
```
+-------------------------------------------------------------+
|  [pawcare.id]                          PAWCARE PET PORTAL   |
+-------------------------------------------------------------+
|                                                             |
|                🐾 Welcome to Your Pet Portal                |
|           Sign in to access your pets' health records       |
|                                                             |
|   [  Login with WhatsApp OTP  ]   [  Login with Password  ] |
|                                                             |
|   -- TAB 1: WHATSAPP OTP --                                 |
|   Enter Phone: [ +91 98765 43210 ]                          |
|   [ SEND 4-DIGIT CODE TO WHATSAPP ]                         |
|                                                             |
|   -- TAB 2: PASSWORD LOGIN --                               |
|   Email or Phone: [ priya@example.com                     ] |
|   Password:       [ ************                          ] |
|   [ Forgot Password? ]                                      |
|   [ LOG IN ]                                                |
|                                                             |
|   ------------------------- OR ---------------------------- |
|   [ G  Continue with Google ]                               |
|                                                             |
|   New to PawCare? [ Create Free Account (Self-Signup) ]     |
|   Are you a Vet?  [ Doctor & Clinic Self-Registration > ]   |
+-------------------------------------------------------------+
```

### Screen 1.1: Pet Health Dashboard (Post-Login Home `pawcare.id/dashboard`)
```
+-------------------------------------------------------------+
|  [pawcare.id/dashboard]           Welcome, Priya! [⚙️] [🔔] |
+-------------------------------------------------------------+
|  YOUR PETS                                                   |
|  [🐕 Bruno]  [🐈 Luna]  [+ Add Pet]                          |
|                                                              |
|  BRUNO'S QUICK STATUS                                        |
|  🟢 Vaccines: Up to date    🟡 Deworming: Due in 12 days     |
|  💊 Meds Today: Meloxicam 1.5ml (dinner) [Given ✓] [Skip]   |
|  ⭐ PawPoints: 480 pts (Bronze)   🔥 Flea-Free Streak: 8 mo  |
|                                                              |
|  UPCOMING SCHEDULE                                           |
|  📅 Nov 27 — Annual Booster (Shanti Vet Clinic, 11:30 AM)   |
|  📅 Dec 2 — Deworming (Drontal Plus)                         |
|                                                              |
|  QUICK ACTIONS                                               |
|  [📋 Health Passport]  [📄 Upload Old Records]                |
|  [👨‍👩‍👧 Manage Household]  [🎁 Refer a Friend (₹200)]          |
|  [📞 Book Appointment]  [🚨 Emergency Triage]                 |
|                                                              |
|  RECENT ACTIVITY                                             |
|  Nov 20 — Consult: Atopic Dermatitis (Dr. Rajesh) [⭐ Rate]  |
|  Nov 15 — Refill: Royal Canin Renal 3kg (Delivered)          |
+-------------------------------------------------------------+
```

### Screen 1.2: The Digital "Pet Health Passport" (`pawcare.id/pet/[slug]`)
```
+-------------------------------------------------------------+
|  [pawcare.id/pet/bruno-7a8f]            [Switch Pet: Bruno v]|
+-------------------------------------------------------------+
|                                                             |
|   +-----------------------------------------------------+   |
|   |  (Photo)  BRUNO               [Microchip: #981020]  |   |
|   |  Golden Retriever • 3.5 yrs • Male (Neutered)       |   |
|   |                                                     |   |
|   |  IMMUNIZATION STATUS:                               |   |
|   |  [✓ VERIFIED IMMUNIZED] (Valid until Nov 20, 2027)  |   |
|   +-----------------------------------------------------+   |
|                                                             |
|  ACTIVE VACCINATION BADGES                                  |
|  +-------------------------------------------------------+  |
|  | [✓] Nobivac DHPPiL (9-in-1)   | Exp: Nov 20, 2027     |  |
|  | [✓] Nobivac Anti-Rabies       | Exp: Nov 20, 2027     |  |
|  | [!] Deworming (Drontal Plus)  | DUE IN 12 DAYS        |  |
|  +-------------------------------------------------------+  |
|                                                             |
|  [ DOWNLOAD AIRLINE & BOARDING TRAVEL CERTIFICATE (PDF) ]   |
|                                                             |
|  RECENT PRESCRIPTIONS                                       |
|  +-------------------------------------------------------+  |
|  | Nov 20, 2026 - Shanti Vet Clinic (Dr. Rajesh Sharma)  |  |
|  | Diagnosis: Acute Dermatitis + Tick Prophylaxis        |  |
|  | [ View Official PDF Rx ]   [ Daily Medication Plan ]  |  |
|  +-------------------------------------------------------+  |
|                                                             |
|  PRIMARY CLINIC & DOCTOR                                    |
|  Shanti Pet Clinic, Indiranagar, Bangalore                  |
|  [ 📞 Call Clinic ]   [ 💬 Chat on WhatsApp ]   [ Book ]     |
|                                                             |
|  EMERGENCY ASSISTANCE                                       |
|  [ 🚨 24/7 Pet Poison & Emergency Triage Assistant ]         |
+-------------------------------------------------------------+
```

### Screen 1.3: Medical Vault & Legacy Record Upload (`pawcare.id/pet/[slug]/records`)
```
+-------------------------------------------------------------+
|  [pawcare.id/pet/bruno-7a8f/records]   BRUNO'S MEDICAL VAULT |
+-------------------------------------------------------------+
|  CLINIC RECORDS (Auto-synced from PawCare Vets)              |
|  📋 Nov 20, 2026 — Atopic Dermatitis (Dr. Rajesh Sharma)    |
|  📋 Aug 15, 2026 — Annual Booster & Rabies (Dr. Rajesh)     |
|                                                              |
|  YOUR UPLOADED LEGACY RECORDS (Paper Records & Past Clinics) |
|  📸 Puppy Vaccine Card - 2023 [View Scan] [Delete]           |
|  📸 Renal Blood Panel - July 2025 [View PDF] [Delete]        |
|                                                              |
|  + UPLOAD NEW RECORD                                         |
|  [ 📷 Take Photo of Paper Card ]   [ 📄 Upload PDF Report ]  |
|  Tag Type: (•) Vaccine Card  ( ) Prescription  ( ) Blood Test|
|  Notes: [ Dr. Roy's clinic puppy booster card...           ] |
|  [ SAVE TO DIGITAL VAULT ]                                   |
+-------------------------------------------------------------+
```

### Screen 1.4: Household Multi-Owner Access (`pawcare.id/household`)
```
+-------------------------------------------------------------+
|  [pawcare.id/household]            HOUSEHOLD MEMBERS         |
+-------------------------------------------------------------+
|  PRIMARY ACCOUNT: Priya Sharma (+91 98765 43210)             |
|                                                              |
|  ACTIVE MEMBERS (2)                                          |
|  👤 Rahul Sharma (Spouse)                                    |
|     Access: Full Co-Owner (View, Book, Pay)    [ Manage ]   |
|  👤 Meera (Dog Walker)                                       |
|     Access: Caretaker (View Passport & Meds)   [ Manage ]   |
|                                                              |
|  + INVITE NEW MEMBER                                         |
|  Phone Number: [ +91 98111 22334 ]                           |
|  Role: (•) Co-Owner  ( ) Caretaker  ( ) Emergency Contact    |
|  Pets: [✓ Bruno]  [✓ Luna]                                   |
|  [ SEND WHATSAPP INVITATION ]                                |
+-------------------------------------------------------------+
```

### Screen 1.5: PawPoints Loyalty, Streaks & Referrals (`pawcare.id/rewards`)
```
+-------------------------------------------------------------+
|  [pawcare.id/rewards]              PAWPOINTS & REFERRALS     |
+-------------------------------------------------------------+
|  YOUR REWARDS WALLET                                         |
|  ⭐ 480 PawPoints (Bronze Tier) • Next Tier: Silver at 1,000 |
|                                                              |
|  PREVENTIVE CARE STREAKS                                     |
|  🏆 8-Month Continuous Flea/Tick Shield                      |
|  🛡️ 100% On-Time Vaccination Record                         |
|                                                              |
|  REDEEM REWARDS AT SHANTI VET CLINIC                         |
|  [ Free Nail Clipping & Ear Cleaning ] — 200 pts [ Redeem ]  |
|  [ 15% Off Royal Canin Food Refill ]   — 350 pts [ Redeem ]  |
|  [ Free Dental Wellness Exam ]         — 500 pts [ Locked ]  |
|                                                              |
|  REFER A PET PARENT FRIEND                                   |
|  Your Referral Code: [ PRIYA-PAWS-BLR ] [ 📋 Copy ]          |
|  "Your friend gets ₹200 off their first visit. You get ₹200  |
|   credited to your PawCare wallet when they complete visit." |
|  [ 💬 SHARE VIA WHATSAPP ]                                   |
+-------------------------------------------------------------+
```

---

## 2. DOCTOR (CLINICAL WORKFLOW) INTERFACE

### Screen 2.1: The 20-Second Rapid Consult Pad with SOAP Notes
```
+-------------------------------------------------------------------------+
| ← Back   BRUNO (Golden Retriever, 3.5y, M)   Weight: [28.5 kg]  T:[101.4F]|
+-------------------------------------------------------------------------+
|                                                                         |
|  📝 CLINICAL SOAP NOTES                                                 |
|                                                                         |
|  [S] SUBJECTIVE (Chief Complaint & History)                             |
|  "Severe itching around ventral abdomen and ears for past 4 days."      |
|  [ 🎙️ AI SCRIBE: Tap to Transcribe Doctor-Owner Dialogue ]              |
|                                                                         |
|  [O] OBJECTIVE (Clinical Findings & Vitals)                             |
|  Weight: [28.5 kg]  Temp: [101.4°F]  BCS: [6/9]  Heart Rate: [88 bpm]   |
|  "Erythematous papules on groin, bilateral ceruminous otitis externa."  |
|                                                                         |
|  [A] ASSESSMENT (Quick-Chips or ICD-Vet Search)                         |
|  [+ Atopic Dermatitis]  [+ Otitis Externa]  [+ Tick Fever]  [+ Parvo]   |
|  Primary: Atopic Dermatitis with Secondary Malassezia Otitis            |
|                                                                         |
|  [P] PLAN & MEDICATIONS (Smart Auto-Calculated for 28.5 kg)             |
|  • Bravecto Chewable Tablet (20-40kg) — 1 Tab Stat [x] Chronic 90-day   |
|  • Meloxicam 1.5mg/ml Oral Susp. — 1.9ml Once Daily (SID) x 5 days     |
|  • Otic Cleanser + Antibacterial Drops — 4 drops BID x 7 days          |
|                                                                         |
|  VACCINES ADMINISTERED TODAY                                            |
|  [x] Nobivac DHPPiL | Batch: [B89012] | Next Due: Nov 20, 2027          |
|  [x] Nobivac Rabies  | Batch: [R11422] | Next Due: Nov 20, 2027          |
|                                                                         |
+-------------------------------------------------------------------------+
|  [ ⚡ COMPLETE CONSULT & DISPATCH TO WHATSAPP (+91 98765 43210) ]       |
+-------------------------------------------------------------------------+
```

### Screen 2.2: Public Doctor SEO Profile (`pawcare.id/dr/[slug]`)
```
+-------------------------------------------------------------------------+
|  [pawcare.id/dr/rajesh-sharma-bangalore]        🔗 Share Profile        |
+-------------------------------------------------------------------------+
|                                                                         |
|  [Photo]  DR. RAJESH SHARMA, B.V.Sc & A.H., M.V.Sc (Surgery)          |
|           VCI Reg: KAR-V-12345 | 12 Years Experience                   |
|           Head Surgeon at Shanti Pet Clinic, Indiranagar, Bangalore     |
|                                                                         |
|  ⭐ 4.9 / 5.0 (184 Verified Pet Parent Reviews)                         |
|                                                                         |
|  SPECIALIZATIONS & CLINICAL FOCUS                                       |
|  [Soft Tissue Surgery] [Canine Dermatology] [Preventive Cardiology]     |
|                                                                         |
|  FACILITIES AT CLINIC                                                   |
|  [✓ Digital X-Ray] [✓ In-House Blood Analyzers] [✓ Surgical OT]        |
|                                                                         |
|  VERIFIED RECENT REVIEWS                                                |
|  ⭐⭐⭐⭐⭐ "Dr. Rajesh was extremely gentle with my nervous Golden..."  |
|  ⭐⭐⭐⭐⭐ "Immediate diagnosis and relief for severe ear infection."   |
|                                                                         |
|  [ 📞 Call Clinic ]   [ 💬 WhatsApp Clinic ]   [ 📅 Book Slot ]         |
+-------------------------------------------------------------------------+
```

---

## 3. ADMIN & PRACTICE MANAGEMENT INTERFACE

### Screen 3.1: Front-Desk Live Queue & Dynamic UPI Checkout
```
+-------------------------------------------------------------------------+
|  SHANTI VET CLINIC  |  TODAY: NOV 20, 2026  |  DOCTOR: Dr. Rajesh Sharma |
+-------------------------------------------------------------------------+
|  LIVE PATIENT QUEUE (12 Treated • 3 Waiting • 1 In Surgery)             |
|                                                                         |
|  Ticket #104  | Bruno (Golden Ret.) | Dr. Rajesh (IN CONSULT)           |
|  Ticket #105  | Simba (Persian Cat) | Annual Vaccines (WAITING: 8 mins) |
|  Ticket #106  | Rocky (Beagle)      | Ear Infection   (WAITING: 20 mins)|
|  Ticket #107  | Bella (Labrador)    | Emergency Trauma (PRIORITY RED)   |
|                                                                         |
|  [ + Check In New Walk-In Patient ]                                     |
+-------------------------------------------------------------------------+
|  RECEPTION CHECKOUT & DYNAMIC UPI QR GENERATOR                          |
|                                                                         |
|  Patient: Bruno (Priya Sharma)                                          |
|  Consult Fee:        ₹ 500.00                                           |
|  Nobivac Vaccines:   ₹1,200.00                                           |
|  Bravecto Chewable:  ₹2,100.00                                           |
|  TOTAL DUE:          ₹3,800.00                                           |
|                                                                         |
|  +-----------------------------+                                        |
|  |       [ DYNAMIC QR CODE ]   |  Scan with GPay, PhonePe, Paytm        |
|  |    upi://pay?pa=shanti@icici|  Amount: ₹3,800.00                     |
|  |    &am=3800&tr=INV-9021     |  Status: [ WAITING FOR SCAN... ]       |
|  +-----------------------------+                                        |
|  [ Print Receipt ]   [ Send GST Tax Invoice via WhatsApp ]              |
+-------------------------------------------------------------------------+
```

### Screen 3.2: Annual Wellness Plans & Subscriptions Manager
```
+-------------------------------------------------------------------------+
|  ANNUAL WELLNESS PLANS COCKPIT                   [ + Create New Plan ]  |
+-------------------------------------------------------------------------+
|  ACTIVE CLINIC WELLNESS TIERS                                           |
|                                                                         |
|  1. Puppy Shield (0–12 Months)                                          |
|     • Fee: ₹7,200/year (or ₹600/month EMI)                              |
|     • Includes: 4 Core Vaccines + 4 Dewormings + 1 Blood Panel + Spay 15%|
|     • Active Subscribers: 38 puppies (₹22,800/mo recurring)             |
|                                                                         |
|  2. Adult Companion Guard (1–7 Years)                                   |
|     • Fee: ₹8,400/year (or ₹700/month EMI)                              |
|     • Includes: Annual Rabies & DHPPiL + 4 Dewormings + 1 Dental Clean  |
|     • Active Subscribers: 84 dogs (₹58,800/mo recurring)                |
|                                                                         |
|  3. Senior Golden Years (7+ Years)                                      |
|     • Fee: ₹13,200/year (or ₹1,100/month EMI)                           |
|     • Includes: Bi-annual KFT/LFT Panels + Mobility Screen + Unlimited  |
|     • Active Subscribers: 22 seniors (₹24,200/mo recurring)             |
|                                                                         |
|  TOTAL RECURRING MONTHLY SUBSCRIPTION REVENUE: ₹1,05,800.00 / month     |
+-------------------------------------------------------------------------+
```

### Screen 3.3: Smart Review & Google Reputation Manager
```
+-------------------------------------------------------------------------+
|  REPUTATION & REVIEW MANAGER                         Avg: ⭐ 4.8 / 5.0  |
+-------------------------------------------------------------------------+
|  WHATSAPP REVIEW PIPELINE (This Month: 142 Consultations)               |
|                                                                         |
|  ✓ 5-Star Reviews (82): Auto-redirected to Google Business Profile      |
|  ✓ 4-Star Reviews (18): Auto-redirected to Google Business Profile      |
|  ⚠️ 1-3 Star Feedback (4): Intercepted Privately for Clinic Manager     |
|                                                                         |
|  PENDING PRIVATE RESOLUTIONS:                                           |
|  • Rocky (Beagle): "Waited 40 mins past appointment time."              |
|    [ 📞 Call Owner ]   [ Send Apology + ₹200 Credit via WhatsApp ]       |
|  • Milo (Indie): "Doctor was great, but medicine was expensive."        |
|    [ 📞 Call Owner ]   [ Explain Generic Alternatives ]                 |
+-------------------------------------------------------------------------+
```
