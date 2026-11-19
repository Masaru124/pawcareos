# PawCare OS: UI/UX Specification & Ergonomics

**Focus:** Frictionless Clinical Ergonomics & Zero-Download Consumer Experience  
**Device Targets:** 
1. **Clinic Suite:** 10.2" iPad / Android Tablet (Primary), iPhone / Android Mobile (Secondary), Desktop Laptop (Tertiary).
2. **Pet Parent Passport:** Mobile Web (Safari / Chrome via WhatsApp Webview).

---

## 1. Core UX Philosophy: "The 30-Second Doctor Rule"

Veterinarians in urban India handle up to 35 high-stress clinical interactions daily. They handle squirming animals, barking dogs, and emergency bite wounds. 

**Cardinal Rule:** If a doctor has to tap more than 4 times or type more than 10 words to issue a prescription, the product has failed.

### Ergonomic Guidelines for the Doctor PWA:
- **One-Thumb Operation:** Critical actions (Search, Add Vaccine, Send Rx) anchored in bottom 40% of screen.
- **Tappable Quick-Chips:** 90% of routine clinical decisions pre-built into 1-tap chips:
  - *Diagnostics:* `Parvovirus Suspect`, `Tick Fever`, `Gastroenteritis`, `Atopic Dermatitis`, `Routine Annual Wellness`.
  - *Vaccines:* `Rabies (Nobivac)`, `DHPPiL (9-in-1)`, `Corona`, `KC (Kennel Cough)`, `Deworming (Drontal Plus)`.
- **High-Contrast Dark Mode & Clinical White:** Clean medical UI with 600-weight typography for legibility under bright clinical fluorescent lighting.
- **Zero Nested Menus:** No hamburger dropdowns for core clinical workflows.

---

## 2. Information Architecture (IA)

```
[ DOCTOR & CLINIC PWA ]
  ├── 1. Live Queue (Today's Outpatients & Surgeries)
  │    ├── Waiting (Color: Amber)
  │    ├── In Consult (Color: Emerald)
  │    └── Emergency Triage (Color: Crimson)
  │
  ├── 2. Rapid Consult Room (The Core Screen)
  │    ├── Patient Header (Weight, Age, Allergies Badge)
  │    ├── Diagnosis Selector (Search + Common Chips)
  │    ├── Vaccine Checklist (Batch selector, Next-due auto-calc)
  │    ├── Rx Pad (Voice dictation button + Smart auto-complete)
  │    └── [SEND RX VIA WHATSAPP] (Sticky bottom CTA)
  │
  ├── 3. Patient Medical Vault (Search by Phone / Microchip / Name)
  │    ├── Chronological Medical Timeline
  │    └── Diagnostic Attachments (X-Ray, Blood Reports)
  │
  └── 4. Clinic Revenue & Inventory Hub
       ├── Today's Collected UPI & Cash
       ├── Overdue Vaccines Recovered Tracker
       └── Low Stock Alerts (Rabies vials, Bravecto chews)
```

---

## 3. Screen-by-Screen UX Specifications

### Screen 1: The Rapid Consult Pad (Doctor View)

```
+-------------------------------------------------------------+
|  <- Back     Bruno (Golden Retriever, 3.5y, M)     [Allergy: None] |
+-------------------------------------------------------------+
|  Weight: [ 28.5 kg ]    Temp: [ 101.4 °F ]                  |
|                                                             |
|  DIAGNOSIS (Tap or Type)                                    |
|  [+ Routine Wellness]  [+ Tick Infestation]  [+ Ear Mites]  |
|  [ Selected: Routine Annual Booster + Tick Prophylaxis    ] |
|                                                             |
|  VACCINES ADMINISTERED TODAY                                |
|  [x] Nobivac DHPPiL (Batch: B7894) -> Next: Nov 19, 2027    |
|  [x] Nobivac Rabies (Batch: R2241) -> Next: Nov 19, 2027    |
|  [ ] Deworming (Drontal Plus)                               |
|                                                             |
|  PRESCRIPTION (Auto-completes Dosage)                       |
|  + Bravecto Chewable Tablet (20-40kg)                       |
|    1 Tab | Once Stat | 90-Day Protection                     |
|                                                             |
|  + Meloxicam 1.5ml                                          |
|    SID | After food | 5 Days                                |
|                                                             |
|  [ mic ] Hold to Dictate Instructions...                    |
+-------------------------------------------------------------+
|  [  GENERATE & SEND TO WHATSAPP (+91 98765 43210)  ]        |
+-------------------------------------------------------------+
```

### Screen 2: The Pet Health Passport (Pet Parent View via WhatsApp)

- **Access Method:** Pet parent clicks `pawcare.id/pet/bruno-7a8f` inside WhatsApp.
- **Authentication:** Tokenized URL with automatic phone session recognition. No passwords, no registration forms.
- **Visual Aesthetic:** Friendly, premium neo-banking style (similar to Apple Wallet / CRED).

```
+-------------------------------------------------------------+
|  PAWCARE VERIFIED HEALTH PASSPORT                           |
|                                                             |
|   (Photo)    BRUNO                                          |
|   [Dog]      Golden Retriever • 3.5 Years • Male (Neutered)  |
|              Microchip: #98102000482910                     |
|                                                             |
|  =========================================================  |
|  STATUS: FULLY VACCINATED  [Verified Green Shield]          |
|  =========================================================  |
|                                                             |
|  ACTIVE IMMUNIZATION BADGES:                                |
|  [✓] Anti-Rabies: Valid until Nov 19, 2027 (Dr. Rajesh)     |
|  [✓] 9-in-1 DHPPiL: Valid until Nov 19, 2027                |
|  [!] Deworming Due in: 14 Days                              |
|                                                             |
|  [ DOWNLOAD OFFICIAL TRAVEL & BOARDING CERTIFICATE (PDF) ]  |
|                                                             |
|  RECENT PRESCRIPTIONS                                       |
|  * Nov 19, 2026 - Dr. Rajesh Sharma (Shanti Vet Clinic)     |
|    View Digital Rx & Dosage Schedule >                      |
|                                                             |
|  PRIMARY CLINIC                                             |
|  Shanti Vet Clinic, Indiranagar, Bangalore                  |
|  [ Call Clinic ]    [ Book Next Slot via WhatsApp ]         |
+-------------------------------------------------------------+
```

---

## 4. WhatsApp Conversational Interaction Flow

```
[CLINIC TRIGGER]
Doctor completes consult.
       |
       v
[WHATSAPP MESSAGE TO PET PARENT]
Header: Official Prescription & Health Passport
Body:
"Hello Priya! 🐾
Dr. Rajesh Sharma has completed Bruno's checkup.
• Weight: 28.5 kg
• Vaccines given: Annual Rabies & DHPPiL
• Next Booster Due: Nov 19, 2027

View your digital prescription & official travel certificate here:
👉 pawcare.id/pet/bruno-7a8f"
       |
       +------------------------------------+
       |                                    |
(7 Months Later)                    (11 Months Later)
Deworming Reminder                  Annual Recall
       |                                    |
"Hi Priya! Bruno's                  "Hi Priya! Bruno's
deworming is due.                   annual Rabies shot is due
Tap to order Drontal."              in 7 days. Book slot?"
       |                                    |
[Order Now - ₹450]                  [Confirm Saturday 11am]
```
