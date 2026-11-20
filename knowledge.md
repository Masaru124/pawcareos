# PawCare OS — working knowledge

Living state file. Update the three sections at the end of every multi-step task
(see the Anti-Context-Loss Protocol in `AGENTS.md`).

_Last updated: 2026-11-20_

## Current State

Working:

- Multi-role auth through Supabase (Google + password). Clinic staff are invite-gated;
  pet parents are self-serve per spec 2.1: `POST /api/v1/auth/parent` creates or attaches the
  family row from a verified address (`apps/api/app/routers/auth.py`), and
  `apps/web/src/lib/identity.ts` routes to `/portal`. A verified address with no PawCare row is
  sent to `/portal/join` for name + WhatsApp number, and gets nothing from clinic endpoints.
- Role homes: owner `/admin`, doctor `/doctor`, front desk `/frontdesk`, pet parent `/portal`.
- Verified end-to-end in the browser: self-serve signup created `demo.parent@pawcare.test`
  ("Demo Parent", +91 90000 00777) and landed on `/portal` with 0 pets.
- `/login` renders an "Already signed in" card when a session exists; Sign out is a full-page
  `<a href="/logout">`.
- Clinical: consult pad (`/consult`), SOAP-style consult record, prescription PDF with VCI
  details (`apps/api/app/services/pdf.py`, `apps/web/src/app/room`), vaccine events, T-7/T-2
  WhatsApp recalls with interactive buttons, appointment reminders, public passport `/p/[slug]`,
  public booking `/find-a-vet`.
- Pet parent portal: pets, records, passport link, and the **legacy record vault**
  (upload, view and delete photos/PDFs of paper vaccine cards, outside prescriptions and lab
  reports): `POST /api/v1/portal/pets/{id}/records` (multipart), `GET .../records/{record_id}/file`,
  `DELETE .../records/{record_id}`, `LegacyRecord` model + migration `0006_legacy_records`,
  UI in `apps/web/src/components/LegacyRecordUpload.tsx` and `DeleteRecordButton.tsx`.
- Demo video: `e2e/tests/demo.spec.ts` records a 9-step walkthrough (landing, directory, owner,
  doctor, parent records, legacy upload + delete, passport, self-serve signup) and the MP4 is
  kept at `demo/pawcare-demo.mp4` (`demo/pawcare-demo.webm` is the raw capture). Re-record with
  `cd e2e && npx playwright test tests/demo.spec.ts`, then convert the webm in
  `e2e/test-results/demo-PawCare-OS-walkthrough/` with ffmpeg.

Known rough edges:

- `e2e` pet-parent scenario fails at its last step when every doctor's online slots for the day
  are already booked by earlier runs ("every doctor is out of online slots today").
- Pet-parent invitations exist only as an API (`POST /api/v1/portal/invites`); no staff UI.
- Legacy uploads are stored on local disk (`record_storage_dir`, default `var/legacy-records`,
  gitignored). Object storage is still to do; the DB stores only an opaque key and a SHA-256.
- Local dev data is cluttered with `reception+…@pawcare.test` invites and `TestPup` appointments.

Checks at last run: API `ruff` clean, `pytest -q` **106 passed**, contract regenerated, web
`tsc --noEmit` clean, `vitest run` 36 passed, Playwright `roles.spec.ts` **3 passed** and
`demo.spec.ts` **1 passed**.

## Key Decisions

- **Gate at the session boundary, not in a page.** Identity is verified by the API before the
  cookie is written.
- **Self-serve pet parents, invite-only staff.** Registration asks name + email + WhatsApp number.
  A phone the clinic already knows attaches to that existing family (so their pets appear
  immediately); a second address offering the same number gets 409 instead of taking the login.
  Clinic routes stay 401 for parents, so an uninvited vet who signs up only gets a parent portal.
- **Clinic staff still need an invitation**, checked before the Supabase user is created.
- **`/login` is a sign-out surface when signed in**, and sign out is a real navigation, so the
  root layout stops showing stale role nav.
- **OpenAPI first.** `packages/contracts/openapi.json` is regenerated from FastAPI and drives the
  web types; API changes are not done until the contract is regenerated.
- **Warm cream/forest palette stays.** `design.md` specifies an emerald/slate token set
  (`#059669`, Outfit + Plus Jakarta Sans). The app ships an editorial cream + forest-green
  system (`apps/web/src/app/globals.css`). Treat the doc as a proposal, not a current
  requirement; repaint only if the user asks.
- **Type is Fraunces + Inter**, loaded through `next/font/google` in `apps/web/src/app/layout.tsx`
  and exposed as `--font-display` / `--font-body`. Body sans, display serif, mono only for times,
  codes and ids. Numerals in stats and the passport use `lining-nums tabular-nums`.
- **No eyebrow kickers.** Section labels use `.label` (sentence case, 12.5px, semi-bold) and sit
  only on product screens; the landing page carries its argument in headings instead. No 01/02/03
  numbering, no decorative gradients, no resting shadows on page-level cards (panels use a 1px
  border and a 1px shadow).
- **Landing photographs live in `apps/web/public/photos/`** (`exam`, `reception`, `cat-exam`,
  `parent-phone`). They are generated placeholders — a real clinic's own photographs should
  replace them one-for-one, keeping the aspect ratios.
- **Design review shots**: `cd e2e && node shots.mjs` writes `design/*.png` at 1440 and 390 for the
  landing, admin, front desk, doctor, portal and directory.
- **WhatsApp stays demo-only** until Meta templates are approved; copy must say so.

## Next Steps

1. Replace local disk storage for legacy records with object storage (R2/S3), keeping
   `storage_key` + `sha256`; add a per-account upload quota. Orphan files are left on disk when a
   row is removed outside the API.
2. Staff-side view of parent uploads so a doctor can mark one verified or supersede it with a
   clinic record.
3. Staff-side pet-parent invitation UI on top of `POST /api/v1/portal/invites`.
5. Remaining v3 gaps, in roadmap order: Phase 2 (AI scribe, chronic auto-refill, queue + dynamic
   UPI billing, reviews + Google routing, wellness plans/EMI, household access, referrals),
   Phase 3 (public doctor SEO pages `/dr/[slug]`, PawPoints, toxicity triage, insurance claims),
   Phase 4 (public Q&A, immunization graph API, B2B wholesale).
