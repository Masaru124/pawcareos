# PawCare OS: Complete System Architecture Document (v3.0)

**Architecture Model:** 3-Sided High-Throughput Modular Monolith with Event Workers  
**Cloud Hosting:** Cloudflare Edge + Supabase Mumbai (`ap-south-1`) / Koyeb / Render  
**Regulatory Standards:** VCI Code of Ethics, Indian DPDP Act 2023, ISO 27001  

---

## 1. System Topology & Data Flow Across 3 Surfaces

```
+---------------------------------------------------------------------------------------------------+
|                                      3-SURFACE CLIENT LAYER                                       |
|  [ 1. PET PARENT ]                  [ 2. DOCTOR WORKFLOW ]              [ 3. CLINIC ADMIN ]       |
|  pawcare.id                         clinic.pawcare.id                   admin.pawcare.id          |
|  - /dashboard (Personal Hub)        - /consult (SOAP Pad + AI Scribe)   - /queue (Live Kanban)    |
|  - /pet/[slug] (Passport)           - /patients (Chronological EMR)     - /checkout (Dynamic UPI) |
|  - /dr/[slug] (Doctor SEO Page)     - /profile (Public Profile Editor)  - /wellness-plans (EMI)   |
|  - /records (Legacy Upload Vault)   - Offline PWA (IndexedDB Sync)      - /reviews (Google Route) |
|  - WhatsApp Chatbot Hub             - Biometric Touch ID Login          - /inventory (Batch/Exp)  |
+---------------------------------------------------------------------------------------------------+
                                                 |
                                                 v HTTPS (TLS 1.3) / WSS
+---------------------------------------------------------------------------------------------------+
|                                 EDGE SECURITY & API GATEWAY                                       |
|  Cloudflare Edge WAF • SSL Termination • DDoS Shield • Token Bucket Rate Limiter (50 req/sec)    |
+---------------------------------------------------------------------------------------------------+
                                                 |
                                                 v
+---------------------------------------------------------------------------------------------------+
|                               APPLICATION SERVICES (FASTAPI / NEXT.JS)                            |
|  - Multi-Tenant RBAC: SuperAdmin, Doctor, Receptionist, Groomer, Pet Parent                       |
|  - Patient & Medical Record Service (EMR + SOAP Engine)                                           |
|  - AI Scribe Service (Whisper API -> Structured SOAP Extraction)                                  |
|  - Prescription & VCI Compliance Service (SHA-256 PDF generator)                                  |
|  - WhatsApp Webhook & Message Pipeline Controller (Meta Cloud API)                                |
|  - Dynamic UPI & Payment Service (Direct UPI QR + Razorpay Route)                                |
|  - Annual Wellness Subscriptions Engine (Monthly UPI Autopay)                                     |
|  - Smart Review Routing Engine (4-5 Stars -> Google Business; 1-3 Stars -> Private)               |
+---------------------------------------------------------------------------------------------------+
                      |                                                   |
                      v                                                   v
+--------------------------------------------+    +-------------------------------------------------+
|          PRIMARY PERSISTENCE LAYER         |    |              ASYNCHRONOUS QUEUE PIPELINE        |
|  - PostgreSQL 16 (Supabase Pro / Mumbai)   |    |  - Redis 7.2 Broker (Upstash Free)              |
|  - PgBouncer (Transaction Connection Pool) |    |  - Worker Pool (Async Python / Celery / ARQ):     |
|  - Row Level Security (RLS) Multi-Tenancy  |    |    * Task 1: Headless React-PDF Renderer        |
|  - Cloudflare R2 ($0 Egress PDF Storage)   |    |    * Task 2: Meta WhatsApp Cloud API Dispatcher |
|                                            |    |    * Task 3: 09:00 AM Daily Vaccine Recalls     |
|                                            |    |    * Task 4: Daily Medication Reminder Cron     |
|                                            |    |    * Task 5: 30-Day Chronic Refill Alerts       |
+--------------------------------------------+    +-------------------------------------------------+
```

---

## 2. Multi-Tenant Role-Based Access Control (RBAC) Matrix

| Resource / Capability | SuperAdmin (Owner) | Doctor (Veterinarian) | Receptionist (Front Desk) | Pet Parent (Tokenized) |
| :--- | :---: | :---: | :---: | :---: |
| **Write Prescriptions (Rx)** | No (unless Dr) | **YES (Full)** | NO | NO |
| **View Medical History** | YES | **YES** | Read-Only | **Own Pet Only** |
| **Upload Legacy Records** | YES | YES | YES | **YES (Own Pet)** |
| **Manage Clinic Staff / RBAC**| **YES** | NO | NO | NO |
| **Live Queue Check-In** | YES | YES | **YES (Primary)** | View Position Only |
| **Collect UPI Payments** | YES | YES | **YES (Primary)** | Pay Invoices Only |
| **Manage Wellness Plans** | **YES** | Read-Only | Read-Only | Subscribe Only |
| **Manage Reviews & Google Sync**| **YES** | Read-Only | NO | Submit Only |
| **P&L / Clinic Revenue Analytics**| **YES** | NO | NO | NO |
| **Manage Drug Inventory** | **YES** | Decrement Only | Check Stock | NO |
| **Download Official Vaccine Cert**| YES | YES | YES | **YES** |

---

## 3. Offline-First Resilience (Handling Clinic Wi-Fi Drops)

- **Service Worker Caching:** Doctor PWA caches active clinic roster, drug formulary list, and today's checked-in queue in `IndexedDB`.
- **Offline Consult Drafting:** If connection drops during an examination, the doctor enters vitals, SOAP notes, and prescriptions offline.
- **Background Sync Engine:** When connection restores, the browser `BackgroundSync` API flushes queued consults to the backend, commits the database transaction, decrements stock, and triggers WhatsApp dispatch.

---

## 4. Legal Compliance & Data Integrity

1. **VCI (Veterinary Council of India) Compliance:**
   - Digital prescriptions require attending doctor's VCI state registration number and digital signature.
   - Prescriptions are cryptographically signed: A SHA-256 hash of the generated PDF is saved in `prescriptions.pdf_hash`.
2. **Indian DPDP Act (Digital Personal Data Protection) 2023:**
   - Pet parent phone numbers are stored with AES-256 encryption at rest.
   - WhatsApp communications include explicit opt-in timestamps and 1-tap `STOP` opt-out commands.
   - Primary data storage remains within Mumbai (`ap-south-1`) region.
