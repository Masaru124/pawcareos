# PawCare OS: Technology Stack Specification & Architectural Decisions

**Status:** LOCKED & CONFIRMED ARCHITECTURE  
**Target Infrastructure Cost (MVP):** **$0 / month (100% Free Tier Stack)**  
**Scalability Ceiling:** 5,000+ Concurrent Clinics without re-architecting  

---

## 1. The $0 Zero-Dollar MVP Architecture

You can build and deploy the entire PawCare OS MVP at **exactly $0.00 / month**:

```
+---------------------------------------------------------------------------------------------------+
|  LAYER               |  $0 FREE TIER SELECTION         |  FREE TIER LIMITS & CAPACITY             |
+----------------------+---------------------------------+------------------------------------------+
|  Doctor PWA & Web    |  Vercel Hobby / Cloudflare Pages|  $0/mo • Unlimited bandwidth & SSL       |
|  Backend API Server  |  Render.com / Koyeb (Free Tier) |  $0/mo • 512MB RAM, web service          |
|  Primary Database    |  Supabase (Free Tier, Mumbai)   |  $0/mo • 500MB PostgreSQL, 50,000 MAU    |
|  Authentication      |  Supabase Auth                  |  $0/mo • 50,000 Monthly Active Users     |
|  Queue & Cache       |  Upstash Serverless Redis       |  $0/mo • 10,000 commands / day free      |
|  Cron Scheduler      |  Cron-Job.org / GitHub Actions  |  $0/mo • Scheduled daily 9 AM recalls    |
|  WhatsApp Gateway    |  Meta WhatsApp Cloud API        |  $0/mo • First 1,000 service convos/mo   |
|  PDF Engine          |  React-PDF (Serverless)         |  $0/mo • Runs inside free server runtime |
|  Object Storage      |  Cloudflare R2                  |  $0/mo • 10 GB free, $0 egress fees      |
|  Payments & UPI      |  Direct Dynamic UPI QR          |  $0/mo • Standard Indian UPI (0% MDR)    |
+----------------------+---------------------------------+------------------------------------------+
|  TOTAL OUT-OF-POCKET CASH SPEND FOR MVP                 |  $0.00 / MONTH                           |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Deep Dive: Architectural Justifications

### 2.1 Frontend: Next.js 15 (TypeScript) + Progressive Web App (PWA)
- **Why Web/PWA instead of React Native / Flutter?**
  1. *Zero Install Friction:* Doctor opens `pawcare.id` on any tablet, phone, or laptop and starts working instantly. No waiting for App Store / Play Store reviews.
  2. *Instant Updates:* Bug fixes and template adjustments deploy in seconds without forcing users to update mobile apps.
  3. *Service Workers for Offline Resilience:* Clinics in India often suffer intermittent Wi-Fi drops. Service workers cache patient search indexes and allow offline consult drafting with automatic background sync when reconnected.

### 2.2 Backend: FastAPI (Python 3.12)
- **Why FastAPI over Node.js / Express?**
  1. *Pydantic Type Safety:* Guarantees strict validation of clinical data (e.g. drug dosages, microchip numbers, phone numbers).
  2. *Asynchronous Throughput:* Python's `async/await` with `uvicorn` and `asyncpg` handles 15,000+ requests/sec per container with minimal memory footprint.
  3. *Future AI & Clinical Triage Support:* Python natively integrates with future veterinary diagnostics models (e.g. skin cytology classification, automated radiographic report generation via LLMs).

### 2.3 Database: PostgreSQL 16 (Hosted via Supabase Pro in Mumbai)
- **Why PostgreSQL?**
  - Healthcare and billing demand strict ACID transactional guarantees. If a vaccine is marked administered, the inventory decrement and recall job scheduling must commit atomically.
  - Indian Data Residency: Supabase / AWS RDS deployed directly in Mumbai (`ap-south-1`), fully compliant with India's DPDP Act 2023.

### 2.4 Messaging: Meta WhatsApp Business Cloud API (Direct Integration)
- **Why Direct Cloud API instead of Twilio or Gupshup?**
  - Third-party brokers (Twilio, Gupshup) add a ₹0.15–₹0.30 markup per conversation on top of Meta's base rate.
  - Direct Meta Cloud API provides direct webhooks, lower latency (< 1s delivery), and full support for interactive message buttons (`button_reply`) and document attachments.

### 2.5 Object Storage: Cloudflare R2
- **Why Cloudflare R2 instead of AWS S3?**
  - Every time a pet parent views their digital prescription or passport, a PDF/image is downloaded.
  - AWS S3 charges heavy egress bandwidth fees ($0.09/GB). Cloudflare R2 has **$0 egress fees**, saving thousands as pet parent traffic scales into millions of reads.

---

## 3. Infrastructure Cost Analysis (MVP vs Scale)

| Service | Tier / Provider | Cost at MVP (10 Clinics) | Cost at Scale (250 Clinics) |
| :--- | :--- | :--- | :--- |
| **Frontend Web Hosting** | Vercel Pro | $20 / month | $20 / month |
| **Backend API Server** | AWS EC2 (t4g.small) / Render | $15 / month | $120 / month (ECS Cluster) |
| **Database** | Supabase Pro (PostgreSQL) | $25 / month | $150 / month (Dedicated compute) |
| **Redis & Queue** | Upstash Serverless Redis | $0 (Free tier) | $40 / month |
| **Object Storage** | Cloudflare R2 (PDF Storage) | $0 (Within 10GB free) | $15 / month |
| **WhatsApp Messages** | Meta Cloud API (Utility & Service) | ~$10 / month | ~$350 / month |
| **Total Monthly Infrastructure** | | **~$70 / month** | **~$695 / month** |

*Note: At 250 clinics generating ₹50,00,000+ in monthly revenue, an infrastructure bill under $700/mo represents a 98.8% gross operating margin.*
