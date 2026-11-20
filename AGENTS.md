# PawCare OS — agent guide

## Stack and layout

- `apps/api` — FastAPI + SQLAlchemy + Alembic, Python via `uv`. Postgres from `docker-compose.yml` on port **5433**.
- `apps/web` — Next.js (App Router) + TypeScript. Supabase Auth (Google + password) is used only as the identity provider; the app issues its own `pc_token` cookie.
- `packages/contracts` — generated `openapi.json`, the source of truth for web API types.
- `e2e` — Playwright specs (`tests/roles.spec.ts`), credentials in gitignored `e2e/.creds.json`.
- WhatsApp delivery is **demo-only** until Meta templates are approved. Never describe it as live.

## Commands

```bash
cd apps/api   && uv run ruff check app tests
cd apps/api   && uv run pytest -q                     # needs the 5433 Postgres up
cd apps/api   && uv run python -m app.export_openapi   # regenerate packages/contracts/openapi.json
cd apps/web   && npx tsc --noEmit
cd apps/web   && npx vitest run
cd e2e        && npx playwright test
```

- Do **not** run `next build` while `next dev` is running.
- Local dev: API on `127.0.0.1:8000`, web on `localhost:3000`.
- After editing an API route or schema, regenerate the OpenAPI contract in the same change.

## Invariants

- **Session boundary:** clinic staff may only sign up when their address is on a clinic's list (checked before the Supabase user is created). A pet parent is self-serve per the v3 spec: `POST /api/v1/auth/parent` creates or attaches their family row, and `resolveHome` then routes them to `/portal` (`apps/web/src/lib/identity.ts`).
- **Roles:** owner → `/admin`, doctor → `/doctor`, receptionist → `/frontdesk`, pet parent → `/portal`. A verified address with no PawCare row yet is sent to `/portal/join` to give a name and WhatsApp number; `/api/v1/auth/me` and every clinic route still answer 401 for it.
- **Sign out** must be a plain `<a href="/logout">`, not a client-side `<Link>`, so the server-rendered header updates.
- **Secrets** live only in gitignored `.env` files. Never print, log, commit, or paste a key; add new variables to `.env.example` with an empty value.

## Anti-Context-Loss Protocol

- At the start of every new session, read `knowledge.md` and call the `memory-keeper` MCP server (`context_session_start`, then `context_get` or `context_restore_checkpoint` for the latest checkpoint) to recover the active task, modified files and decisions.
- After completing any feature, bug fix, or architectural decision, update `knowledge.md` with:
  1. **Current State** — what works vs. what is broken.
  2. **Key Decisions** — why an approach was chosen, so it is not reverted later.
  3. **Next Steps** — exact file paths and remaining tasks.
- Never end a multi-step task without updating `knowledge.md`.
- Before a large refactor, or when the context window is filling, ask memory-keeper for `context_checkpoint` and report the checkpoint name to the user so a fresh session can restore it.

The server is declared in `.agents/mcp.json` (`memory-keeper`, `TOOL_PROFILE=minimal`, DB under
`.agents/memory-keeper/`). It is installed globally, not via `npx`: npm 12 blocks install scripts,
so `npx -y mcp-memory-keeper` crashes on the missing `better-sqlite3` binary. Reinstall with
`npm install -g --allow-scripts=better-sqlite3 mcp-memory-keeper`.

## Codebase graph (graphify)

The `graphify` skill is vendored at `.agents/skills/graphify/SKILL.md` and its graph lives in `graphify-out/` (gitignored).

- If `graphify-out/graph.json` exists, treat architecture questions ("how does booking work", "what calls X", "what breaks if I change Y") as `graphify query "<question>"` first, `graphify affected "X"` for blast radius, `graphify explain "X"` / `graphify path "A" "B"` for detail.
- After structural changes, refresh cheaply with `graphify update .` (AST only, no LLM). Use `/graphify .` for a full rebuild including docs and visualization.
- A graph is a map, not evidence: cite `source_location` and confirm anything surprising in the source before acting on it.
