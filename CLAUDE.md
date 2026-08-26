# CLAUDE.md

Permanent engineering rules for KAMLA. This file governs how work is done in this repository. It reflects decisions already approved for the project and must not be silently reinterpreted.

## 1. Product purpose

KAMLA is a production-oriented academic decision-making and planning platform for college students. It helps students understand attendance risk, academic progress, priorities, constraints, study planning, PYQ (previous-year-question) patterns, and — eventually — provides an AI assistant that can reason over their academic context.

## 2. Architecture

- Frontend: Next.js App Router + TypeScript, deployed on Vercel
- Backend: FastAPI modular monolith, deployed on Fly.io
- Database: PostgreSQL 16 (Neon) as the source of truth
- Data access: SQLAlchemy 2 + Alembic
- Validation: Pydantic v2
- Authentication: Clerk JWTs, verified by FastAPI
- Authorization: PostgreSQL Row Level Security (RLS) for student-owned data
- AI: Anthropic, accessed behind an LLMPort abstraction
- Private files: Cloudflare R2
- Background jobs: Procrastinate (PostgreSQL-backed)
- Edge/security: Cloudflare
- Monitoring: Sentry
- Product analytics: PostHog
- CI: GitHub Actions

This architecture has been deliberately chosen and approved. See section 3.

## 3. Non-negotiable boundaries

- The frontend never connects directly to PostgreSQL.
- No database credentials or privileged secrets live in the frontend.
- FastAPI is the API and security boundary.
- PostgreSQL is the source of truth.
- RLS must protect all student-owned data.
- Deterministic calculations (attendance math, time/date math, constraint evaluation, schedule validity) must live in backend/domain engines — never in the LLM.
- LLMs interpret, explain, reason over context, and propose actions. They do not perform deterministic computation.
- AI must not silently modify consequential student plans.
- Student approval is required before consequential recommendations take effect.
- Do not introduce microservices, Redis, Kafka, Kubernetes, vector databases, OR-Tools, or multi-agent orchestration without explicit approval.
- Do not change the approved architecture without an explicit decision from the product owner.

## 4. Engineering principles

- Prefer simple, boring, production-grade solutions over clever ones.
- Strong typing and explicit validation throughout.
- Tests are required for security-sensitive logic and deterministic logic.
- Do not trust AI-generated calculations without tests.
- Keep domain logic separate from API routes.
- Keep database access behind the backend only.
- Never commit secrets.
- Never run destructive production operations without explicit approval.

## 5. Current state

The repository currently contains the initial foundation created before Claude Code took over:

- Next.js web scaffold (Clerk sign-in + a debug probe page only)
- FastAPI API
- Initial PostgreSQL/Alembic schema
- RLS implementation
- Clerk authentication foundation
- `GET /health` and `GET /v1/me`
- Initial security tests (auth, RLS isolation)
- CI configuration (GitHub Actions)

No feature engines have been implemented yet.

## 6. Current milestone

The next milestone is to fully verify the existing foundation locally — particularly PostgreSQL/RLS behavior and tests — before implementing product features.

## 7. Workflow

Before implementing a significant feature:

1. Inspect existing code.
2. Explain the proposed implementation.
3. Identify affected files.
4. Identify tests required.
5. Implement the smallest correct change.
6. Run relevant tests.
7. Report what changed.

Do not make unrelated refactors.

Do not modify the architecture silently.
