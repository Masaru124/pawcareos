# PawCare OS: System Architecture Document

**Architecture Pattern:** Modern Modular Monolith & Event-Driven Asynchronous Workers  
**Hosting Environment:** Cloudflare Edge + AWS (Mumbai `ap-south-1`) / Supabase Managed Services  
**Compliance Baseline:** VCI (Veterinary Council of India), Indian DPDP Act (2023), ISO 27001 Security Standards  

---

## 1. High-Level Architectural Topology

```
+---------------------------------------------------------------------------------------+
|                                    CLIENT LAYER                                       |
|  [ Doctor / Reception PWA ]                [ Pet Parent Browser ]  [ WhatsApp Native] |
|   (Next.js 15 App Router)                   (Tailwind Mobile Web)   (Meta Messenger)  |
+---------------------------------------------------------------------------------------+
                                           | HTTPS / WSS
                                           v
+---------------------------------------------------------------------------------------+
|                           EDGE ROUTING & SECURITY LAYER                               |
|   Cloudflare Edge (WAF, SSL Termination, DDOS Protection, Static Asset CDN Cache)     |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                                API APPLICATION CORE                                   |
|   FastAPI (Python 3.12) / Node.js Next.js Serverless Routes                           |
|   - Auth & RBAC Middleware (JWT Bearer Tokens)                                        |
|   - Clinical Consultation & Rx Service                                                |
|   - Vaccine & Recall Scheduling Service                                               |
|   - Billing & Dynamic UPI Service (Razorpay / Cashfree)                               |
|   - Meta WhatsApp Cloud API Webhook Controller                                        |
+---------------------------------------------------------------------------------------+
                  |                                              |
                  v                                              v
+------------------------------------+         +----------------------------------------+
|          DATA & CACHE              |         |         EVENT & WORKER QUEUE           |
|  - PostgreSQL 16 (Primary DB)      |         |  - Redis 7.2 (Queue Broker & Cache)   |
|  - PgBouncer (Connection Pooling)  |         |  - Celery / BullMQ Background Workers  |
|  - Cloudflare R2 / AWS S3 (PDFs)   |         |    * T-7 / T-2 Cron Recall Schedulers  |
|                                    |         |    * PDF Generation Workers            |
|                                    |         |    * WhatsApp Dispatch Worker          |
+------------------------------------+         +----------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                              EXTERNAL INTEGRATIONS                                    |
|  [ Meta WhatsApp Cloud API ]  [ Razorpay Payment Gateway ]  [ Resend / AWS SES Mail ] |
+---------------------------------------------------------------------------------------+
```

---

## 2. Component Breakdown & Responsibilities

### 2.1 The Application Core (FastAPI / Next.js)
- **FastAPI Core (Backend):** High-throughput asynchronous Python framework providing strict Pydantic type safety, auto-generated OpenAPI documentation, and native async database sessions via `SQLAlchemy 2.0` / `asyncpg`.
- **Next.js 15 (Frontend PWA):** React Server Components (RSC) for rapid initial page loads on 4G networks; client components for the offline-capable Doctor Consult Pad.

### 2.2 The Asynchronous Event & Queue Pipeline
Veterinary consultations must never hang waiting for external PDF generation or WhatsApp network roundtrips.
1. When doctor completes a consult, the API commits the transaction to PostgreSQL in < 40ms.
2. An event `consultation.completed` is published to Redis.
3. **Worker 1 (PDF Renderer):** Renders the official VCI-compliant PDF using React-PDF / Headless Chromium, uploads binary to Cloudflare R2 object storage, and writes the signed URL to the database.
4. **Worker 2 (WhatsApp Dispatcher):** Ingests the signed PDF URL, retrieves pet parent phone number, and executes the Meta WhatsApp Cloud API template message.
5. **Worker 3 (Recall Scheduler):** Calculates `administered_date + 365 days` for rabies and `+ 90 days` for deworming; inserts corresponding jobs into the `recall_jobs` queue.

---

## 3. Storage & Database Architecture

- **Primary Relational Store:** AWS RDS PostgreSQL (or Supabase Pro) deployed in Mumbai (`ap-south-1`) to comply with Indian data residency norms.
- **Connection Pooling:** `PgBouncer` running transaction pooling to support 10,000+ concurrent connections from serverless edge instances.
- **Object Storage:** Cloudflare R2 for zero-egress fee storage of prescription PDFs, clinic logos, and diagnostic X-rays.
- **Read Cache:** Redis for storing doctor session states, clinic active hours, and frequently queried drug formulary templates.

---

## 4. Security, Privacy & Regulatory Compliance

1. **Veterinary Council of India (VCI) Compliance:**
   - Every digital prescription digitally hardcodes the attending doctor's VCI state registration number.
   - Digital prescriptions are immutable: once issued, modifications create a new revision record (`version_id`) preserving audit integrity.
2. **Indian Digital Personal Data Protection (DPDP) Act 2023:**
   - Explicit consent opt-ins for WhatsApp communications.
   - 1-click unsubscribe option in WhatsApp footer (*"Reply STOP to opt out"*).
   - Data stored inside India region with AES-256 encryption at rest.
3. **Role-Based Access Control (RBAC):**
   - `SUPERADMIN`: Platform management, clinic provisioning, wholesale catalog.
   - `CLINIC_OWNER`: Full billing, doctor accounts, financial reports.
   - `DOCTOR`: Clinical consults, patient history, Rx creation.
   - `RECEPTIONIST`: Patient intake, queue management, UPI payment collection.
