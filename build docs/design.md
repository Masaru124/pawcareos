# PawCare OS: Design System & Visual Specification

**Design Concept:** Clinical Trust Meets Friendly Consumer Warmth  
**Design Tokens Base:** Tailwind CSS v3.4 / CSS Variables  
**Primary Metaphor:** The "Digital Health Passport" (Clean, official, accessible, reassuring)  

---

## 1. Color Palette & Emotional Intent

Veterinary healthcare requires balancing clinical authority (doctors must trust the legal rigor of prescriptions) with consumer empathy (pet parents view pets as children).

```
+---------------------------------------------------------------------------------------------------+
|  CLINICAL EMERALD (Primary Brand)      |  HEX: #059669  |  Trust, Health, Verified Green Badges   |
|  DEEP SLATE NAVY (Authority/Text)      |  HEX: #0f172a  |  Official Medical Rigor, High Contrast  |
|  PET CARE TEAL (Secondary)             |  HEX: #0d9488  |  Interactive Buttons, Progress Rings    |
|  CALM AMBER (Alerts & Warnings)        |  HEX: #f59e0b  |  Overdue Vaccines, Low Stock Alerts     |
|  CRIMSON ROSE (Emergency Triage)       |  HEX: #e11d48  |  Urgent Poisoning, Severe Symptoms      |
|  SURFACE OFF-WHITE (Canvas Background) |  HEX: #f8fafc  |  Clean, Anti-Fatigue Clinic Background  |
+---------------------------------------------------------------------------------------------------+
```

### Color Variables (CSS / Tailwind):
```css
:root {
  --brand-primary: #059669;       /* Emerald 600 */
  --brand-primary-hover: #047857; /* Emerald 700 */
  --brand-secondary: #0d9488;     /* Teal 600 */
  --surface-bg: #f8fafc;          /* Slate 50 */
  --surface-card: #ffffff;
  --surface-border: #e2e8f0;      /* Slate 200 */
  --text-main: #0f172a;          /* Slate 900 */
  --text-muted: #64748b;         /* Slate 500 */
  --badge-verified: #10b981;     /* Green 500 */
  --badge-warning: #f59e0b;      /* Amber 500 */
  --badge-emergency: #e11d48;    /* Rose 600 */
}
```

---

## 2. Typography Hierarchy

- **Primary UI & Data Font:** `Plus Jakarta Sans` or `Inter` (Excellent legibility at small sizes, tabular figures for medication dosages).
- **Headings & Badges:** `Outfit` (Modern, rounded, friendly yet professional).

| Role | Font Family | Size / Weight | Line Height | Usage |
| :--- | :--- | :--- | :--- | :--- |
| **Display Header** | Outfit | 24pt (32px) / Bold 700 | 1.2 | Screen titles, Clinic Name |
| **Section Header** | Outfit | 16pt (22px) / SemiBold 600 | 1.3 | Patient Header, Diagnosis Block |
| **Card Header** | Plus Jakarta Sans | 13pt (18px) / Medium 600 | 1.4 | Medication Name, Vaccine Type |
| **Body Text** | Plus Jakarta Sans | 11pt (15px) / Regular 400 | 1.5 | Clinical Instructions, Diet advice |
| **Data & Microcopy** | Inter | 9pt (12px) / Regular 400 | 1.4 | Batch numbers, Date timestamps |

---

## 3. Touch Targets & Ergonomic Standards

- **Minimum Tap Target:** `48px × 48px` on all mobile and tablet touch points.
- **Form Inputs:** Height `52px` with large `16px` font size to prevent mobile browser auto-zoom on iOS Safari.
- **Button Radius:** `8px` (Slightly rounded, modern clinical aesthetic; avoids toy-like full pills for medical actions).
- **Sticky Actions:** The primary CTA (`Complete Consult & Send Rx`) is permanently docked to the bottom of the viewport with a frosted-glass backdrop (`backdrop-blur-md bg-white/90`).

---

## 4. UI Components

### 4.1 The Verified Immunization Badge (SVG Component)
- Distinct circular shield with checkmark.
- Gradient: `from-emerald-500 to-teal-600`.
- Text: "VCI Verified Immunization Record". Gives pet parents immense confidence when presenting at airports or boarding facilities.

### 4.2 Medication Chip Selector
```html
<!-- Interactive Quick-Chip -->
<button class="flex items-center gap-2 px-3.5 py-2.5 rounded-lg border border-slate-200 bg-white hover:border-emerald-500 hover:bg-emerald-50 active:scale-95 transition-all text-sm font-medium text-slate-800">
  <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
  Nobivac DHPPiL (9-in-1)
</button>
```

### 4.3 WhatsApp Interactive Button Cards
Strict compliance with Meta WhatsApp Cloud API specifications:
- Quick reply buttons limited to 20 characters.
- Clear action verbs: `Confirm Sat 11am`, `Reschedule`, `Order Refill`.
