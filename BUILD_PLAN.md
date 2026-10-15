# AS — System Analysis and Step-by-Step Build Plan

> **AI-Powered Academic Assessment and School Platform**: a build guide for one developer working with Claude Code.

| | |
|---|---|
| Version | 1.1 (15 Oct 2026) |
| Changes in 1.1 | Back end moved from NestJS + Prisma to **Django + Django REST Framework**, with **PostgreSQL** as the database. Background jobs moved from BullMQ to **Celery**. The web app stays on Next.js and now uses an API client generated from the Django OpenAPI schema |
| Based on | The original *System Analysis of AS* and the *SRS v1.0*. Requirement IDs such as `FR-EXAM-026` come from the SRS |
| Save as | `docs/BUILD_PLAN.md` in your repository |
| Covered in detail | **Release 1 (MVP pilot)**, about 24 weeks. Releases 2 and 3 are outlined in §15 |
| **[Proposed]** | Marks a default value to confirm with your team or pilot school (SRS open issue OI-12) |

## Contents

- [0. How to use this document](#0-how-to-use-this-document)
- [1. System summary](#1-system-summary)
- [2. Objectives and success measures](#2-objectives-and-success-measures)
- [3. Key decisions and technology stack](#3-key-decisions-and-technology-stack)
- [4. Architecture](#4-architecture)
- [5. Data model](#5-data-model)
- [6. Core algorithms](#6-core-algorithms)
- [7. Security, privacy and AI-safety design](#7-security-privacy-and-ai-safety-design)
- [8. Repository layout and conventions](#8-repository-layout-and-conventions)
- [9. Testing strategy](#9-testing-strategy)
- [10. Environments, CI/CD and deployment](#10-environments-cicd-and-deployment)
- [11. Working with Claude Code](#11-working-with-claude-code)
- [12. Timeline and milestones](#12-timeline-and-milestones)
- [13. Phase-by-phase build plan](#13-phase-by-phase-build-plan)
- [14. Pilot plan](#14-pilot-plan)
- [15. Release 2 and Release 3 roadmap](#15-release-2-and-release-3-roadmap)
- [16. Risks and mitigations](#16-risks-and-mitigations)
- [Appendix A. Claude Code kit](#appendix-a-claude-code-kit)
- [Appendix B. API surface (R1)](#appendix-b-api-surface-r1)
- [Appendix C. UI routes (R1)](#appendix-c-ui-routes-r1)
- [Appendix D. Permission catalog](#appendix-d-permission-catalog)
- [Appendix E. Seed data and golden fixtures](#appendix-e-seed-data-and-golden-fixtures)
- [Appendix F. UAT scripts](#appendix-f-uat-scripts)
- [Appendix G. Definition of Ready and Done](#appendix-g-definition-of-ready-and-done)
- [Appendix H. SRS coverage by phase](#appendix-h-srs-coverage-by-phase)

---

## 0. How to use this document

**If you're the developer:** read §1–§3 once, then §11 on working with Claude Code and §12 on the timeline. After that, work through §13 one task at a time.

**If you're Claude Code:** this file is a reference, so don't read all of it at once. Look up only what you need:

- **A task:** run `grep -n "^#### P3-T04" docs/BUILD_PLAN.md` and read that section only. It ends at the next `####` heading.
- **A phase and its exit criteria:** run `grep -n "^### Phase 3" docs/BUILD_PLAN.md`.
- **Algorithms:** §6. **Conventions:** §8. **Testing rules:** §9.
- **Which source wins:** the SRS decides *what* to build, this plan decides *how*, and your own defaults come last. The rules in `CLAUDE.md` are non-negotiable. If two sources conflict, stop and ask the human.

**Fields used in each task:**

| Field | Meaning |
|---|---|
| Owner | 🧑 you, 🤖 Claude Code, 🤝 both |
| SRS | The requirement IDs the task implements. Tests must be tagged with these IDs (§9.2) |
| Depends on | Tasks that must be marked ✅ in `docs/PROGRESS.md` first |
| Build | What to implement |
| Acceptance criteria (AC) | Testable checks. Each one needs an automated test unless it is marked *(manual)* |

### Quick start (day 1)

1. Do **P0-T01** and **P0-T02**: install the tools, create the repo and add the docs.
2. Start `claude` in the repo and paste the **P0-T03** prompt. It creates the Claude Code kit described in Appendix A.
3. Restart `claude` and run `/context` to check that `CLAUDE.md` and the rules loaded.
4. Run the decision interview in §11.5, then run `/task P0-T05`.

---

## 1. System summary

### 1.1 What we are building

AS connects schools, teachers and students around one loop:

1. Exam evidence is recorded.
2. The system diagnoses likely learning gaps.
3. The student gets targeted learning and practice.
4. A reassessment measures progress.

Teachers remain the authority on official marks. Anything the AI produces is labelled, can be reviewed, and can be traced back to its evidence.

```mermaid
flowchart LR
  A["1. Exam recorded<br/>question-level marks + topics"] --> B["2. Teacher validates<br/>official result"]
  B --> C["3. Released to student<br/>per component"]
  B --> D["4. Diagnosis<br/>rules on validated evidence"]
  D --> E["5. Teacher review<br/>accept / edit / reject"]
  E --> F["6. Learning path<br/>resources + targeted practice"]
  F --> G["7. Reassessment<br/>compare with baseline"]
  G --> D
```

### 1.2 Users and roles

| Role | In R1? | Main jobs |
|---|---|---|
| School administrator | ✅ | Set up the school structure and people; manage the portal, notices, settings and reports |
| Teacher | ✅ | Run exams and marks; validate and release results; review findings; manage resources and practice; view class insights |
| Student | ✅ | See results, the learning-gap report, the learning plan, practice tests and progress |
| Platform operator (the AS team) | ✅ internal only | Provision schools; give support only with access the school has approved |
| Parent / guardian | ❌ R3 | Permissions not yet decided (open issue OI-05) |

### 1.3 SRS modules mapped to code and phases

| SRS module | Code (apps / packages / modules) | Built in |
|---|---|---|
| M1 School portal | api (Django apps): `portal`, `notices`. web: `/s/[school]`, `/app/admin/notices` | P2, P6 |
| M2 Accounts, roles and structure | api: `accounts`, `academic`. web: `/app/admin/structure`, `/app/admin/people` | P1, P2 |
| M3 Exams and answer scripts | api: `exams`, `results`, `scripts`, `files`. web: `/app/teacher/exams` | P3 |
| M4 AI assessment intelligence | domain: `diagnosis`. `backend/ai` gateway. api: `analysis`. web: `/app/teacher/review`, `/app/student/gaps` | P4 |
| M5 Learning resources | api: `resources`, `recommendations`. domain: `recommend` | P5 |
| M6 Practice and mock tests | api: `practice`, `question_bank`, `progress`. domain: `practice`, `scoring`, `progress` | P5 |
| M7 Student dashboard | web: `/app/student/*` | P3–P6 |
| M8 Teacher dashboard | web: `/app/teacher/*` | P3–P6 |
| M9 Administrator dashboard | web: `/app/admin/*`. api: `reports`, `school_settings`, `audit` | P2, P6 |

"api" means a Django app in `backend/modules/<name>/`, and "domain" means a pure Python package in `backend/domain/<name>/` (§8.1).

### 1.4 Scope

**Release 1 (this plan, in detail):**

- Accounts and roles, with MFA for administrators.
- A configurable school structure, with CSV import.
- A basic portal and notices.
- Exam records with question-level topics.
- Manual mark entry (Option A) and digital script upload (Option B).
- Teacher validation and per-component release.
- Deterministic weakness analysis with optional AI wording, and a teacher review workflow.
- Learning resources and a question bank.
- Targeted practice with automatic scoring of objective questions.
- Baseline-versus-reassessment progress, role dashboards, and hardening.

**Not in Release 1:**

- Scanned scripts (Option C) come in R2.
- AI-assisted marking (Option D) gets a limited pilot in R2 and fuller support in R3.
- AI-generated questions come in R2.
- The parent portal and single sign-on (SSO) come in R3.
- Fees, payroll, HR, attendance and accounting are not confirmed scope and are never assumed.

---

## 2. Objectives and success measures

### 2.1 Goal

By the end of **week 24**, deliver an MVP that a pilot school can use for one real exam cycle:

- Teachers record and validate results.
- Students receive their released results and a learning-gap report that a teacher has reviewed.
- Students then follow a learning path, take targeted practice and complete a measured reassessment.

### 2.2 Release 1 objectives

| ID | Objective | Measure and target | By | How it's verified |
|---|---|---|---|---|
| O1 | Ship the core loop | The Sara end-to-end test (P5-T10) passes on every build of `main` | W15 (M5) | CI |
| O2 | Complete the R1 scope | 100% of SRS **Must/R1** requirements are implemented, each with at least one passing test or a recorded manual check | W20 (M7) | `pnpm req:trace --release R1 --fail-on-missing` |
| O3 | Keep teachers in charge | No code path lets AI or analysis write an official result. Students never see AI text that hasn't been reviewed, unless the school turned on auto-release | W12, then ongoing | P3-T11 architecture test, P4-T06 tests |
| O4 | Isolate schools and roles | No unexpected access in the cross-tenant and cross-role test suite. OWASP ASVS L2 checklist complete. No High or Medium findings from the ZAP scanner | W20 | P7-T01, P7-T03 |
| O5 | Build privacy in | No real student data before the legal gate. AI requests contain no direct identifiers | W21 | P8-T01, P4-T04 property test |
| O6 | Meet performance targets | 95th-percentile API response ≤ 1.0 s with 1,000 concurrent sessions. Saving a 60-student × 20-question mark sheet takes ≤ 3 s at the 95th percentile | W20 | k6 (P7-T05) |
| O7 | Be accessible | Zero serious or critical axe violations. Manual WCAG 2.2 AA checks pass on the core flows | W20 | P7-T06 |
| O8 | Keep test coverage high | Line coverage ≥ 90% in `backend/domain` and ≥ 80% in `backend/modules` | Ongoing | CI coverage gate |
| O9 | Go live in a pilot | At least one school runs at least one real exam cycle through AS | W24 (M8) | P8-T05 |

### 2.3 Pilot KPIs [Proposed]

| KPI | Target | Why it matters |
|---|---|---|
| Pilot exams released through AS | ≥ 90% | Adoption |
| Median teacher time to enter and validate marks for 30 students × 10 questions | ≤ 20 min | Teacher workload |
| Exams with question-level marks and topic tags | ≥ 80% | Diagnosis depends on them (FR-AI-007) |
| Findings accepted without edits | Report it; ≥ 60% is healthy | Quality of the diagnosis rules |
| Students who start recommended practice within 7 days of release | ≥ 50% | Engagement |
| Practice tests completed | ≥ 60% | Engagement |
| Monthly availability | ≥ 99.5% | NFR-AVL-001 |
| Severity-1 security or privacy incidents | 0 | Trust |

These KPIs measure how the pilot goes. They are not promises about learning outcomes. A better score on practice is reported only as a better score on practice, not as mastery (FR-PRAC-011).

### 2.4 Non-goals for Release 1

- Automated marking of handwritten answers.
- Any claim of long-term mastery.
- General school-management features (fees, payroll, HR, attendance, accounting).

---

## 3. Key decisions and technology stack

### 3.1 Architecture decisions

Record each of these as an ADR (architecture decision record) in P0-T04.

| ADR | Decision (default) | Why | SRS |
|---|---|---|---|
| 0001 | **One repository, two languages.** The back end is Python, managed with **uv** (`backend/`). The web app and E2E tests are TypeScript, managed with **pnpm** (`apps/web`, `tests/e2e`). Root `pnpm` scripts run both, so `pnpm verify` stays the single gate | Django for the back end (ADR-0002), and Next.js stays for the UI. Python also suits the R2 work (QWK metrics, OCR, evaluation harness). The type gap between the two languages is closed by ADR-0009 | NFR-MNT-001 |
| 0002 | Web app in **Next.js** (App Router) with Tailwind and shadcn/ui. API in **Django + Django REST Framework (DRF)**, serving REST under `/api/v1`. The web app proxies `/api/*` to Django so both share one origin | Django's ORM, migrations, auth, i18n, email and admin are mature and built in. DRF permission classes give deny-by-default authorisation. Cookies stay first-party, so no CORS setup is needed | COM-002 |
| 0003 | **PostgreSQL + the Django ORM** (psycopg 3). Every tenant table has a `school` foreign key, and tenant models inherit from `TenantModel`, whose default manager scopes every query to the current school. App-level scoping from day 1, with Postgres row-level security (RLS) added in P7. The app connects as a role that is not the table owner. Migrations run as a separate owner role | Leaking data between schools is the top risk. Adding the column later would be expensive; adding policies later isn't. A separate migration role lets the database itself refuse audit-log updates and enforce RLS | NFR-SEC-002/003 |
| 0004 | **First-party auth built on Django's auth framework**: a custom `User` model, Django's `Argon2PasswordHasher` (argon2id), our own opaque server-side `Session` model (only a hash of the token is stored) and TOTP MFA via `pyotp`. Students without email sign in with a username. Django admin is **off in staging and production** | Implements the SRS session rules exactly. Django's built-in session table stores raw keys and has no role, re-auth or MFA fields, so we use our own. Schools often lack student email addresses. Django admin would bypass tenancy and audit. SSO comes in R3 | FR-AUTH-*, NFR-SEC-005..008 |
| 0005 | **Hybrid intelligence**: deterministic rules decide which topics are weak or strong. An LLM only writes the wording, with a template as fallback. AI is optional per school | Testable, auditable and cheap. Works with AI turned off, and the AI can't invent a diagnosis | FR-AI-007..009, NFR-PRIV-005 |
| 0006 | Store marks as **integers in hundredths** (`marksCenti`) | Avoids floating-point errors in totals and percentages | FR-EXAM-010/012 |
| 0007 | Files go to private S3-compatible storage, are scanned by ClamAV and are served through signed URLs that expire within 5 minutes. In R1, uploads pass through the API | Prevents unauthorised file access | NFR-SEC-009..011 |
| 0008 | Background jobs use **Celery** with Redis as the broker. Celery beat runs scheduled jobs. The worker and beat use the same image and code as the API, with a different command. Jobs are queued with `transaction.on_commit` so a worker never sees uncommitted data | AI calls and file scans never block teacher actions | NFR-SCAL-003, NFR-REL-001 |
| 0009 | **Contract from the API schema**: DRF serializers validate all input and output. **drf-spectacular** generates `backend/openapi.yaml`, which is committed. **orval** turns it into typed TanStack Query hooks and zod schemas for the web (`apps/web/src/api/generated`). CI fails if the schema or the generated client is out of date | One source of truth for data shapes across Python and TypeScript, with contract tests | — |
| 0010 | A **modular monolith**: one Django project with one Django app per module. Module boundaries are enforced by **import-linter** contracts, rather than separately deployed services | The right size for a small team. Deviates from NFR-MNT-001 (a Should requirement), so log an SRS change request | NFR-MNT-001 |
| 0011 | Prompt templates are versioned files selected by configuration. The model ID comes from an environment variable | You can switch model or prompt version without a code deploy, but a brand-new prompt ships with a release. Only partly meets NFR-MNT-002, so log it | NFR-MNT-002 |

### 3.2 Decisions to confirm in week 1

These come from the SRS open issues.

| OI | Question | Default for building | Final by |
|---|---|---|---|
| OI-04 | Which AI provider, and on what terms? | Claude API via the `anthropic` Python SDK, behind the gateway. `AI_PROVIDER=fake` in development and tests. Model set in `AI_MODEL`, for example a current Claude Haiku or Sonnet model | Provider by the start of P4 (W10); terms by P7-T08 |
| OI-07 | Which languages? | English UI, ready for translation. Add a second language if the pilot needs it | P6 (W16) |
| OI-08 | Where do curriculum topics come from? | Each school maintains topic lists per subject, with CSV import. Align with the national syllabus later | P2 (W5) |
| OI-11 | Where do question-bank items come from? | Written by teachers, plus seed items. Licensing for external items is to be decided | P5 (W13) |
| OI-05 | Parent role? | Not in R1 | — |
| OI-06 | Can administrators see identifiable student results? | Off by default, controlled by a school setting | P6 |
| OI-09 | How is AI feedback released? | Teacher review is required by default. Auto-release is an optional school setting | P4 |
| OI-10 | Hosting region? | The nearest region that satisfies the applicable law (OI-01) | P1-T11 (staging), P8-T02 (production) |
| OI-13 | Diagnosis thresholds? | The §6 defaults | Tune during the pilot |
| OI-01/02/03 | Applicable law, retention and consent | Start in week 1. **The G-LEGAL gate must pass before any real student data enters the system** | P8-T01 (W21) |

### 3.3 Technology stack

| Layer | Choice | Notes |
|---|---|---|
| Back-end runtime | Python 3.13 (or the newest version your Django release supports) | Pin it in `backend/.python-version` and `requires-python` |
| Back-end packages | uv (`backend/pyproject.toml`, `backend/uv.lock`) | |
| Web runtime | Node.js 24 LTS (or the newest LTS) | Pin it in `.nvmrc` and `engines` |
| Web packages | pnpm (via corepack) workspaces: `apps/web`, `tests/e2e` | Root scripts also call the back end through `uv` |
| Web | Next.js App Router, React, Tailwind CSS, shadcn/ui (Radix), TanStack Query, react-hook-form, next-intl, Recharts | Radix primitives are accessible by default |
| API | **Django 5.2 LTS** + **Django REST Framework**, drf-spectacular (OpenAPI), djangorestframework-camel-case (camelCase JSON), django-environ (settings), gunicorn | Use the newest Django LTS available when you scaffold |
| API client (web) | orval, generating TanStack Query hooks and zod schemas from `backend/openapi.yaml` | |
| Background jobs | Celery + Celery beat on Redis 7+ (or Valkey) | |
| Database | PostgreSQL 17+ with the Django ORM and psycopg 3, using Django's built-in connection pool | Two roles: `as_owner` runs migrations, `as_app` runs the app |
| File storage | S3-compatible via boto3: a managed service in production, SeaweedFS locally. ClamAV for virus scanning. `filetype` for magic-byte checks | Don't use MinIO's community edition. It has been archived and no longer gets Docker images |
| Auth | Django auth with a custom `User`, `Argon2PasswordHasher` (`argon2-cffi`), our own opaque `Session` model, `pyotp` for TOTP, `cryptography` (AES-GCM) for MFA secrets | |
| AI | The `anthropic` Python SDK behind `backend/ai`, with outputs validated by pydantic, plus a `FakeAiProvider` for tests | |
| Imports and content | `openpyxl` (XLSX), the standard `csv` module, `nh3` (HTML sanitising) | |
| Email | Django's SMTP email backend. Mailpit locally | |
| Testing (back end) | pytest, pytest-django, Hypothesis (property tests), factory_boy, pytest-cov, time-machine (only where an injected clock isn't possible), openapi-core (contract checks), schemathesis (API fuzzing in P7) | |
| Testing (web and system) | Vitest, Playwright with `@axe-core/playwright`, k6, Lighthouse CI | |
| Code quality | Ruff (lint and format), mypy with django-stubs and djangorestframework-stubs, import-linter, ESLint, Prettier, gitleaks, pip-audit and osv-scanner / `pnpm audit` | |
| CI/CD | GitHub Actions and container images | |
| Observability | structlog JSON logs, health checks, sentry-sdk (Django and Celery integrations), django-prometheus | |

When you scaffold in P0-T05, install the current stable versions, let `uv.lock` and `pnpm-lock.yaml` pin them, and record the major versions in ADR-0001.

**Running on Windows.** Celery's default worker pool doesn't run on Windows. Either develop in **WSL2** (recommended: everything then behaves like CI and production) or start the local worker with `--pool=solo`. Docker Desktop runs the Compose services either way.

---
## 4. Architecture

### 4.1 Logical and physical view

```mermaid
flowchart LR
  subgraph Client
    B["Browser<br/>portal + role dashboards"]
  end
  subgraph Web["apps/web · Next.js"]
    N["Pages, components,<br/>/api/* proxy"]
  end
  subgraph API["backend · Django + DRF (gunicorn)"]
    M1["accounts · academic"]
    M2["exams · results · scripts · files"]
    M3["analysis · resources · practice · progress"]
    M4["portal · notices · reports · audit · school_settings"]
  end
  subgraph Worker["backend · Celery worker + beat"]
    J1["analysis jobs"]
    J2["file scan jobs"]
    J3["email · notification · retention jobs"]
  end
  subgraph Data
    PG[("PostgreSQL")]
    RD[("Redis")]
    S3[("S3-compatible storage")]
  end
  AV["ClamAV"]
  AI["AI provider<br/>via backend/ai gateway"]
  B --> N
  N -- "same-origin /api/v1" --> M1
  N --> M2
  N --> M3
  N --> M4
  M1 --> PG
  M2 --> PG
  M2 --> S3
  M3 --> PG
  M4 --> PG
  M2 --> RD
  M3 --> RD
  RD --> J1
  RD --> J2
  RD --> J3
  J1 --> PG
  J1 --> AI
  J2 --> S3
  J2 --> AV
  J3 --> PG
```

Pure business logic lives in `backend/domain`: state machines, marks arithmetic, diagnosis, recommendations, practice assembly, scoring, progress and permissions. It is plain Python with no Django imports and no input/output, so every rule can be tested without a database or network.

### 4.2 Request lifecycle

Every API call goes through these steps:

1. The browser calls `/api/v1/...` on the web origin, and Next.js forwards the request to Django. The session cookie is `as_session`. Requests that change data also send the `X-CSRFToken` header.
2. `SessionAuthMiddleware` hashes the cookie, loads the `Session`, applies the idle and absolute timeouts, and sets the `RequestContext` (a `contextvars.ContextVar`): request ID, school ID, user ID, roles, active role and session ID. Django's `CsrfViewMiddleware` and our Origin check reject cross-site writes.
3. DRF's default permission class, `PolicyPermission`, checks the view:
   - The view action must declare `@public` or `@require_permission(key, scope=…)`. Anything else is refused (deny by default).
   - If the role doesn't have that permission, it returns **403**.
   - Otherwise the scope resolver loads the target record through the tenant-scoped manager. If the record is outside the user's scope, it returns **404**.
4. A DRF serializer validates the input. Request serializers never accept `schoolId`, `userId` or the actor's role.
5. The module's service function applies the rules from `backend/domain` inside `transaction.atomic()`. Any state change is recorded with `audit.record(…)` in the same transaction. Jobs are queued with `transaction.on_commit`.
6. The response is rendered with its output serializer, which is what the OpenAPI schema describes. Anything sent to a student first passes through `VisibilityService`.
7. structlog records the request ID, school ID, user ID, route, status and latency. Logs never contain names, emails, marks, tokens or file URLs.

### 4.3 AI analysis flow

This implements the ten steps in SRS §6.5.

```mermaid
sequenceDiagram
  autonumber
  actor T as Teacher
  participant W as Web
  participant A as API (Django)
  participant Q as Queue (Redis)
  participant K as Celery worker
  participant D as Diagnosis engine
  participant G as AI gateway
  participant DB as PostgreSQL
  T->>W: Request analysis for a validated exam
  W->>A: POST /api/v1/analysis-runs
  A->>A: Authenticate, check permission and assignment
  A->>DB: Verify associations and VALIDATED status, store snapshot
  A->>Q: Enqueue run (snapshot id) on commit
  Q->>K: Deliver job
  K->>D: Compute findings from snapshot (deterministic)
  K->>G: Optional wording request with pseudonymised, allow-listed facts
  G-->>K: Validated text, or rejection so template text is used
  K->>DB: Store run + findings (GENERATED) + audit in one transaction
  T->>W: Review findings: accept, edit or reject, then release
  W->>A: PATCH /findings/:id and POST /findings/release
  Note over A,DB: Students see only RELEASED findings, through VisibilityService
```

If anything fails (an AI timeout, invalid output or a database error), the run is marked `FAILED`, the teacher is notified, and **no official record changes** (NFR-REL-001).

### 4.4 Exam and result states

```mermaid
stateDiagram-v2
  direction LR
  [*] --> DRAFT
  DRAFT --> PUBLISHED: publish (questions and topics set)
  PUBLISHED --> CLOSED: all enrolled results validated or absent
  CLOSED --> PUBLISHED: reopen (audited)
  DRAFT --> CANCELLED
  PUBLISHED --> CANCELLED: only if no validated results
```

```mermaid
stateDiagram-v2
  direction LR
  [*] --> NOT_STARTED
  NOT_STARTED --> IN_PROGRESS: first mark saved
  IN_PROGRESS --> EVALUATED: all marks entered, teacher marks complete
  EVALUATED --> IN_PROGRESS: teacher reopens
  EVALUATED --> VALIDATED: teacher validates (official result)
  VALIDATED --> VALIDATED: amend with reason (revision + audit)
```

Results are released **per component**: marks, answer script, comments and AI feedback. Each component has its own `...ReleasedAt` timestamp, which is set on release and cleared on withdrawal. Both actions are audited.

How these states map to the SRS model in §6.3:

| SRS state | Implementation |
|---|---|
| Draft | `Exam.status = DRAFT` |
| Marks In Progress | `Exam.status = PUBLISHED` and `Result.status = IN_PROGRESS` |
| Evaluated | `Result.status = EVALUATED` |
| Returned | `Result.status`: `EVALUATED` → `IN_PROGRESS` |
| Validated | `Result.status = VALIDATED`, meaning the official result exists |
| Released | `VALIDATED` with at least one component release timestamp set |
| Withdrawn | Component release timestamp cleared, plus an audit event with a reason |
| Amended | New `ResultRevision`, `version` increased, status stays `VALIDATED` |
| Cancelled | `Exam.status = CANCELLED`, allowed only if no result is `VALIDATED` |

### 4.5 Analysis and finding states

```mermaid
stateDiagram-v2
  direction LR
  [*] --> REQUESTED
  REQUESTED --> RUNNING
  RUNNING --> GENERATED
  RUNNING --> FAILED: error, timeout or invalid output
  FAILED --> REQUESTED: retry
  GENERATED --> SUPERSEDED: newer run for same scope
```

```mermaid
stateDiagram-v2
  direction LR
  [*] --> GENERATED
  GENERATED --> UNDER_REVIEW: teacher opens
  UNDER_REVIEW --> ACCEPTED
  UNDER_REVIEW --> EDITED: original text kept
  UNDER_REVIEW --> REJECTED: reason required
  ACCEPTED --> RELEASED: teacher releases
  EDITED --> RELEASED: teacher releases
  GENERATED --> RELEASED: school auto-release policy, labelled
  GENERATED --> SUPERSEDED
  RELEASED --> SUPERSEDED: newer evidence
```

The two diagrams map to SRS §6.4 as follows. `AnalysisRun.status` covers Requested, Failed and Generated (with `RUNNING` added for the job). `Finding.reviewStatus` covers Under Review, Accepted, Edited, Rejected, Released and Superseded.

---

## 5. Data model

### 5.1 Identity and academic structure

```mermaid
erDiagram
  SCHOOL ||--o{ USER : has
  USER ||--o{ ROLE_ASSIGNMENT : holds
  USER ||--o{ SESSION : opens
  SCHOOL ||--o{ ACADEMIC_YEAR : runs
  ACADEMIC_YEAR ||--o{ CLASS_GROUP : contains
  SCHOOL ||--o{ SUBJECT : offers
  SUBJECT ||--o{ TOPIC : "divided into"
  TOPIC |o--o{ TOPIC : "parent of"
  CLASS_GROUP ||--o{ CLASS_SUBJECT : studies
  SUBJECT ||--o{ CLASS_SUBJECT : "taught as"
  CLASS_SUBJECT ||--o{ TEACHER_ASSIGNMENT : "taught by"
  USER ||--o{ TEACHER_ASSIGNMENT : teaches
  CLASS_GROUP ||--o{ ENROLLMENT : enrolls
  USER ||--o{ ENROLLMENT : "enrolled as student"
  SCHOOL ||--o{ NOTICE : publishes
  SCHOOL ||--o{ AUDIT_EVENT : records
  SCHOOL ||--o{ FILE_OBJECT : stores
```

### 5.2 Assessment and analysis

```mermaid
erDiagram
  CLASS_SUBJECT ||--o{ EXAM : "assessed by"
  EXAM ||--o{ QUESTION : contains
  QUESTION }o--o{ TOPIC : "tagged with"
  EXAM ||--o{ ASSESSMENT_RESULT : produces
  USER ||--o{ ASSESSMENT_RESULT : "result of student"
  ASSESSMENT_RESULT ||--o{ QUESTION_MARK : "itemised as"
  QUESTION ||--o{ QUESTION_MARK : "scored in"
  ASSESSMENT_RESULT ||--o{ RESULT_REVISION : "amended by"
  ASSESSMENT_RESULT ||--o{ TEACHER_FEEDBACK : "commented by"
  EXAM ||--o{ ANSWER_SCRIPT : "evidenced by"
  ANSWER_SCRIPT }o--|| FILE_OBJECT : "stored as"
  ANALYSIS_RUN ||--o{ FINDING : generates
  FINDING }o--o| TOPIC : about
  FINDING ||--o{ FINDING_EVIDENCE : "supported by"
  FINDING_EVIDENCE }o--o| QUESTION_MARK : cites
  FINDING_EVIDENCE }o--o| ATTEMPT_RESPONSE : cites
  ANALYSIS_RUN ||--o{ AI_CALL : "may use"
```

### 5.3 Learning and practice

```mermaid
erDiagram
  FINDING ||--o{ RECOMMENDATION : "leads to"
  RECOMMENDATION }o--o| RESOURCE : suggests
  RECOMMENDATION }o--o| PRACTICE_TEST : assigns
  RESOURCE }o--o{ TOPIC : covers
  QUESTION_BANK_ITEM }o--o{ TOPIC : covers
  PRACTICE_TEST ||--o{ PRACTICE_TEST_ITEM : contains
  PRACTICE_TEST_ITEM }o--|| QUESTION_BANK_ITEM : uses
  PRACTICE_TEST ||--o{ PRACTICE_ASSIGNMENT : "assigned via"
  PRACTICE_TEST ||--o{ PRACTICE_ATTEMPT : "attempted in"
  PRACTICE_ATTEMPT ||--o{ ATTEMPT_RESPONSE : records
  USER ||--o{ PRACTICE_ATTEMPT : takes
  PROGRESS_RECORD }o--|| TOPIC : tracks
  PROGRESS_RECORD }o--|| USER : "for student"
  PROGRESS_RECORD }o--o| PRACTICE_ATTEMPT : "baseline or follow-up"
  USER ||--o{ RESOURCE_ENGAGEMENT : logs
  RESOURCE ||--o{ RESOURCE_ENGAGEMENT : "engaged in"
```

### 5.4 Key fields

Every tenant-owned model inherits from `TenantModel`, so it also has `id` (UUID), `school` (a foreign key; the column is `school_id`), `created_at` and `updated_at`, and its indexes start with `school`.

**Naming:** this table uses the camelCase names that appear in the JSON API. Django models use snake_case (`marksCenti` → `marks_centi`, `scriptReleasedAt` → `script_released_at`), and the camel-case renderer and parser convert between them. Enums are `models.TextChoices`. JSON fields (`settings`, `config`, `snapshot`, `metrics`, `blueprint`) are `JSONField`s validated by pydantic models before they are saved.

| Entity | Key fields | Notes |
|---|---|---|
| School | `slug` (unique), `name`, `description`, `logoFileId?`, `locale`, `timezone`, `settings` (JSON validated by pydantic), `status` | The tenant root. Has no `schoolId` |
| User | `email?`, `username`, `displayName`, `status` (INVITED · ACTIVE · DEACTIVATED), `password` (Django's argon2 hash; unusable until set), `mfaEnabled`, `mfaSecretEnc?`, `failedLogins`, `lockedUntil?` | `AUTH_USER_MODEL`, built on `AbstractBaseUser`. Unique on (`schoolId`, `username`) and (`schoolId`, `email`), so usernames are unique per school only. Sign-in goes through a custom authentication backend that takes the school slug |
| RoleAssignment | `userId`, `role` (SCHOOL_ADMIN · TEACHER · STUDENT) | `PARENT` is reserved for R3 |
| OperatorAccount | `email`, `passwordHash`, `mfaSecretEnc` | Not a tenant user. Never sees tenant data without a grant |
| Session | `userId?` / `operatorId?`, `tokenHash`, `activeRole`, `mfaVerifiedAt?`, `reauthAt?`, `idleExpiresAt`, `absoluteExpiresAt`, `revokedAt?` | Stores only the SHA-256 of the token |
| Invitation, PasswordResetToken | `userId`, `tokenHash`, `expiresAt`, `usedAt?` | Single use |
| AuditEvent | `actorType`, `actorId`, `actorRole`, `action`, `entityType`, `entityId`, `before?`, `after?`, `reason?`, `ip`, `requestId`, `prevHash`, `hash` | Append-only, hash-chained per school |
| FileObject | `storageKey` (random), `mimeType`, `sizeBytes`, `sha256`, `scanStatus` (PENDING · CLEAN · INFECTED · ERROR), `purpose`, `createdById` | Holds no file bytes |
| AcademicYear | `label`, `startDate`, `endDate`, `status` (PLANNED · ACTIVE · CLOSED) | At most one ACTIVE year per school |
| ClassGroup | `academicYearId`, `gradeLabel`, `sectionLabel?`, `displayName` | For example "Class 9 – A" |
| Subject, ClassSubject | `name`, `code` / `classGroupId`, `subjectId` | ClassSubject is unique on (`classGroupId`, `subjectId`) |
| TeacherAssignment | `teacherId`, `classSubjectId` | Defines what a teacher can access |
| Enrollment, SubjectEnrollment | `studentId`, `classGroupId`, `startDate`, `endDate?` / `studentId`, `classSubjectId` | History is kept when students move |
| Topic | `subjectId`, `parentId?`, `name`, `code?`, `gradeLevel?`, `sortOrder`, `archivedAt?` | Forms a tree |
| Notice | `title`, `body`, `audience` (school · class group · class subject), `visibility` (PUBLIC · SIGNED_IN), `publishAt`, `expiresAt?`, `status` | |
| Exam | `classSubjectId`, `academicYearId`, `name`, `examDate`, `totalMarksCenti`, `markingSchemeText?`, `markingSchemeFileId?`, `status`, `announce` | |
| Question, QuestionTopic | `examId`, `number`, `section?`, `type` (OBJECTIVE · SHORT · LONG · NUMERICAL · DIAGRAM), `maxMarksCenti`, `order` / `questionId`, `topicId` | Only teachers set topics |
| AssessmentResult | `examId`, `studentId`, `status`, `absent`, `totalCenti`, `version`, `validatedById?`, `validatedAt?`, `marksReleasedAt?`, `scriptReleasedAt?`, `commentsReleasedAt?`, `aiFeedbackReleasedAt?` | **The official result.** Unique on (`examId`, `studentId`) |
| QuestionMark | `resultId`, `questionId`, `marksCenti`, `notAttempted` | Unique on (`resultId`, `questionId`) |
| ResultRevision | `resultId`, `version`, `before` (JSON), `reason`, `actorId` | Amendment history |
| TeacherFeedback | `resultId`, `questionId?`, `authorId`, `body` | |
| AnswerScript | `examId`, `studentId`, `fileId`, `source` (DIGITAL; SCAN arrives in R2), `status` | Raw evidence |
| AnalysisRun | `scope` (STUDENT · CLASS), `examId?`, `classSubjectId`, `studentId?`, `status`, `engineVersion`, `config`, `snapshot`, `snapshotHash`, `aiProvider?`, `aiModel?`, `promptVersion?`, `error?` | The snapshot never changes (DR-003) |
| Finding | `runId`, `studentId?`, `topicId?`, `type` (WEAKNESS · STRENGTH · TREND_UP · TREND_DOWN · INSUFFICIENT_DETAIL · CLASS_TOPIC_FLAG), `evidenceLevel`, `rulesFired`, `metrics`, `textGenerated`, `textSource` (TEMPLATE · AI), `textFinal?`, `reviewStatus`, `reviewedById?`, `rejectReason?`, `usefulness?`, `releasedAt?` | |
| FindingEvidence | `findingId`, `kind` (QUESTION_MARK · ATTEMPT_RESPONSE), `refId`, `examId?`, `attemptId?` | |
| AiCall | `purpose`, `provider`, `model`, `promptVersion`, `payloadHash`, `status` (OK · REJECTED · FAILED), `reasonCodes`, `tokensIn`, `tokensOut`, `latencyMs`, `payload?`, `output?` | Payload and output are deleted after a retention period [Proposed: 90 days] |
| Resource, ResourceTopic | `title`, `type` (LINK · FILE · NOTE · WORKED_EXAMPLE · VIDEO_LINK), `url?`, `fileId?`, `body?`, `subjectId`, `gradeLevel`, `objective?`, `difficulty?`, `origin`, `status`, `showOnPortal` | |
| ResourceEngagement | `resourceId`, `studentId`, `openedAt`, `completedAt?` | |
| QuestionBankItem, ItemTopic | `subjectId`, `gradeLevel`, `stem` (markdown, sanitised), `type` (MCQ_SINGLE · MCQ_MULTI · TRUE_FALSE · NUMERIC · SHORT_TEXT), `options`, `answerKey`, `explanation?`, `difficulty` (1–3), `status`, `origin` | |
| Recommendation | `studentId`, `findingId`, `step`, `kind` (RESOURCE · PRACTICE · TEACHER_SUPPORT), `resourceId?`, `practiceTestId?`, `order`, `status` (PROPOSED · APPROVED · REMOVED · COMPLETED) | |
| PracticeTest, PracticeTestItem | `purpose` (BASELINE · PRACTICE · REASSESSMENT · MOCK), `blueprint`, `blueprintHash`, `seed`, `rules`, `status` / `itemId`, `order`, `points` | |
| PracticeAssignment | `practiceTestId`, `studentId?` / `classGroupId?`, `dueAt?`, `source` (TEACHER · RECOMMENDATION) | |
| PracticeAttempt, AttemptResponse | `studentId`, `status`, `startedAt`, `submittedAt?`, `scorePoints`, `maxPoints`, `timeLimitSec?` / `itemId`, `response`, `isCorrect`, `points` | |
| ProgressRecord | `studentId`, `topicId`, `blueprintHash`, `baselineAttemptId?`, `baselineSource` (PRACTICE · EXAM), `followupAttemptId`, `baselinePct`, `followupPct`, `deltaPp`, `label`, `nextStep`, `comparability` (HIGH · LOW) | |
| Notification | `userId`, `type`, `payload`, `idempotencyKey`, `readAt?` | |
| SupportAccessGrant (P7) | `operatorId`, `scope`, `approvedById`, `expiresAt` | |

### 5.5 Invariants

The code and the tests must both enforce these:

1. **I1.** A tenant row's `schoolId` always equals the session's school. The `TenantModel` manager and `save()` enforce this now, and RLS does too from P7.
2. **I2.** There is exactly one `AssessmentResult` per (exam, student) and one `QuestionMark` per (result, question).
3. **I3.** `0 ≤ marksCenti ≤ maxMarksCenti`. When an exam has questions, their maximum marks add up to the exam total.
4. **I4.** Only `ResultsService` (`modules/results/services.py`) writes results. A `VALIDATED` result changes only through an amendment, which needs a reason, a `ResultRevision` and an audit event.
5. **I5.** A student can read a result component only if the result is `VALIDATED` and that component's release timestamp is set.
6. **I6.** A finding cites only evidence from its own run's snapshot, and snapshots never change.
7. **I7.** Students see a finding only when it is `RELEASED`.
8. **I8.** Recommendations shown to students are `APPROVED`, or auto-approved under the school's policy and labelled as such.
9. **I9.** The application never updates or deletes `AuditEvent` rows.
10. **I10.** A reassessment shares no items with its baseline unless a teacher allows reuse.

---

## 6. Core algorithms

All thresholds below are **[Proposed]** defaults. They are stored in the school settings within fixed bounds (P6-T05), and each `AnalysisRun.config` records the values it used. The algorithms are pure Python functions in `backend/domain`, taking and returning frozen dataclasses.

### 6.1 Student-level diagnosis (`backend/domain/diagnosis`)

**Input.** A snapshot of one student's assessments in one subject during the current academic year, using at most the last 6 assessments per topic. Each assessment contains:

- `kind` (EXAM or PRACTICE), `date`, `totalCenti`, `maxCenti`
- `questions[]`, each with `id`, `number`, `maxCenti`, `marksCenti` and `topicIds[]`

Results marked absent are excluded. Questions without topic tags are ignored for topic findings. Marks that are missing are never estimated or filled in.

**Definitions** for topic `T` and assessment `a`:

- `score_a(T)` = the sum of marks divided by the sum of maximum marks, over the questions in `a` tagged `T`. A question tagged with *k* topics counts in full towards each of them.
- `q_a(T)` = the number of questions in `a` tagged `T`.
- `A(T)` = the assessments where `q_a(T) ≥ 1`, newest first. `latest = A(T)[0]` and `prev = A(T)[1]`.
- `overall_a` = `a.total / a.max`.

| Rule | Condition (defaults) | Finding |
|---|---|---|
| **A**: low in the latest assessment | `q_latest ≥ 2` and `score_latest < 0.50` | WEAKNESS |
| **B**: low repeatedly | `score_a < 0.50` in at least 2 of the last 3 assessments in `A(T)` | WEAKNESS |
| **C**: low relative to the student's own overall score | `q_latest ≥ 2` and `score_latest ≤ overall_latest − 0.20` | WEAKNESS |
| **S**: strength | `q_latest ≥ 2`, `score_latest ≥ 0.80`, average of the last ≤ 3 scores ≥ 0.80, and no WEAKNESS on this topic | STRENGTH |
| **T**: trend | `q ≥ 2` in both `latest` and `prev`, and `abs(score_latest − score_prev) ≥ 0.20` | TREND_UP or TREND_DOWN |
| **I**: not enough detail | The latest exam in the subject has only total marks, or no topic tags | One INSUFFICIENT_DETAIL note per run, and no topic findings from that exam (FR-AI-007) |

**Evidence level.** *HIGH* when `|A(T)| ≥ 2` and the topic has at least 4 questions in total. *MEDIUM* when `q_latest ≥ 2`. Anything below MEDIUM produces no finding.

**Output.** One finding per (student, topic, type). Each finding includes:

- `rulesFired`
- `metrics`: each assessment's score, question count, marks out of maximum, and overall score
- `evidence`: the question-mark IDs it relied on

Show weaknesses first, with HIGH evidence before MEDIUM, then the lowest latest score. Show strengths after them, highest score first.

**Worked example: Sara (golden fixture `sara-core`, Appendix E)**

| Topic | Class Test 2 (20 marks) | Term 1 Mathematics (40 marks, Sara 27/40 = 67.5%) | Rules fired | Expected finding |
|---|---|---|---|---|
| Forming equations from word problems | 4.5/10 = **45%** (2 questions) | 3/11 = **27.3%** (2 questions) | A, B, C | **WEAKNESS, HIGH** |
| Algebraic simplification | 9/10 = 90% (1 question) | 7.5/8 = 93.8% (2 questions) | S | **STRENGTH, MEDIUM** (only 3 questions in total) |
| Solving linear equations | — | 4/5 = 80% (1 question) | none (only 1 question) | — |
| Triangles | — | 12.5/16 = 78.1% (2 questions) | none | — |

There is no trend finding for "forming equations": the change is 45% → 27.3%, or −17.7 points, which is under the 20-point threshold. The engine must return **exactly these two findings**.

### 6.2 Class-level aggregation

For a class subject `C` over a window (by default the latest exam, or optionally the last 3):

- `n_T` = the number of students with evidence on topic `T`.
- `weak_T` = the number of those students with a WEAKNESS on `T`.
- `share_T = weak_T / n_T`.
- `mean_T` = the average of each student's latest score on `T`.
- Flag the topic (`CLASS_TOPIC_FLAG`) when `share_T ≥ 0.40` and `n_T ≥ 5`.
- The output also includes the score distribution (0–49%, 50–79%, 80–100%). The list of student IDs is visible to teachers only.

Example (fixture `class-9a-triangles`): 13 of 30 students are weak on Triangles, so 43% and the topic is flagged. With 11 of 30 (37%) it is not flagged.

### 6.3 Explanations

Every finding gets **template text** (localised, deterministic). If the school has AI enabled, the system can also produce **AI wording**, which goes through §6.4.

Student-facing template for a WEAKNESS (English):

> On questions about {topic}, you scored {marks} out of {max} in {exam} ({pct}%){, and {marks2} out of {max2} in {exam2} ({pct2}%)}. That's lower than your overall result ({overall}%). This suggests {topic} may be worth practising. Start with the worked example, then try the practice set. Your next assessment will help show whether it has improved.

Sara would see: *"On questions about forming equations from word problems, you scored 3 out of 11 in Term 1 Mathematics (27%), and 4.5 out of 10 in Class Test 2 (45%). That's lower than your overall result (68%)…"*

Teachers see a terse version with question numbers and the rules that fired, for example: *"Forming equations from word problems: 27% (Q4, Q5, Term 1) and 45% (Q1, Q2, Class Test 2). Rules A, B, C. Evidence HIGH."*

Percentages are rounded half-up to whole numbers for display.

For AI wording, the prompt `explain-findings/v1` receives only the finding facts: topic names, numbers, question numbers, exam names, the evidence level, and the allowed next steps. It returns `{ findingId, studentText, teacherText }` for each finding. Students are referred to as "you". The app swaps the `S1…Sn` pseudonyms back to names locally and never sends names to the provider.

### 6.4 Validating AI text

The gateway runs these checks in order. If any check fails, the template text is used and the `AiCall` is logged as `REJECTED` with reason codes.

1. **Schema:** the output must match the task's pydantic model, and the student text must be at most 600 characters [Proposed].
2. **References:** every `findingId` must exist in the input, and every topic name mentioned must be one of the input topics.
3. **Numbers:** every number in the text must be in the allowed set. That set is the metric percentages (±1), the marks and maximum marks, question numbers, counts, and numbers that appear in exam names.
4. **Banned phrases** (a configurable list, matched case-insensitively). Examples:
   - Certainty words: "definitely", "certainly", "guaranteed".
   - Labels: "lazy", "weak student", "bad at", "can't do", "fail".
   - Clinical terms: "disorder", "diagnos", "dyslexia", "dyscalculia", "ADHD".
5. **No unsafe content:** no URLs, email addresses or HTML, and no pseudonym tokens left in the student text.

### 6.5 Recommendations and learning path

For each **released** WEAKNESS on topic `T`, the engine proposes this path. A teacher can approve, reorder, replace or remove any step (FR-RES-005).

| Step | Content | How it's chosen |
|---|---|---|
| 1. Quick check (baseline) | A BASELINE practice test using blueprint *B* = {topic T, 10 items, difficulty mix 4 easy / 4 medium / 2 hard} | Assembled through §6.6. The teacher can turn it off, in which case the exam score becomes the baseline with LOW comparability |
| 2. Understand | 1–2 `WORKED_EXAMPLE` or `NOTE` resources on T | APPROVED, same subject, grade level ≤ the student's. Teacher-made first, then newest |
| 3. Explanation | 1 teacher `NOTE` or `VIDEO_LINK` on T | Same filters |
| 4. Practise (basic) | 6 items at difficulty 1–2 | May reuse baseline items, but never items reserved for step 6 |
| 5. Practise (harder) | 6 items at difficulty 2–3 | Same rule as step 4 |
| 6. Reassess | A REASSESSMENT test using the same blueprint *B*, with no items shared with step 1 | Reserved when the path is created |

If there aren't enough resources or items, the teacher gets a task such as *"Add resources or items for {topic} (missing: 2 hard items)"*. The system never quietly fills gaps from other topics.

### 6.6 Practice assembly, scoring and progress

- **Blueprint:** `{ topicId (including child topics), itemCount, mix: {1: n1, 2: n2, 3: n3}, types: objective only in R1 }`. `blueprintHash` identifies tests that are comparable.
- **Selection:** take APPROVED items whose grade is at or below the student's. Exclude reserved items, and for a reassessment, the baseline items. Fill each difficulty quota using a shuffle seeded by `seed = hash(studentId, purpose, findingId)`, so the same inputs always give the same test. If a quota can't be filled, return `INSUFFICIENT_ITEMS { difficulty: shortfall }`. Fill from neighbouring difficulty levels only if the teacher allows it.
- **Scoring** (R1, objective items only):

  | Type | Rule |
  |---|---|
  | MCQ_SINGLE | Exact match |
  | MCQ_MULTI | All correct options and nothing else [Proposed] |
  | TRUE_FALSE | Exact match |
  | NUMERIC | `abs(x − key) ≤ tolerance` |
  | SHORT_TEXT | Match an accepted answer after normalising case, whitespace and Unicode |

- **Progress** (computed when a reassessment is scored): `deltaPp = followupPct − baselinePct`.

  | Label | Rule |
  |---|---|
  | `IMPROVED_ON_PRACTICE` | `deltaPp ≥ +15` |
  | `NO_CLEAR_CHANGE` | `−15 < deltaPp < +15` |
  | `LOWER_ON_PRACTICE` | `deltaPp ≤ −15` |
  | `CONSISTENT_IMPROVEMENT` | At least 2 *later* comparable checks are each ≥ baseline + 15 points. "Comparable" means the same blueprint, or a later exam with at least 2 questions on the topic |

  The system **never** labels anything "mastered" (FR-PRAC-011).

- **Next step:**
  - `ADVANCE` when the follow-up is ≥ 70% and the label is improved. The new blueprint mix is 2 easy / 4 medium / 4 hard.
  - `PRACTISE_AGAIN` otherwise.
  - `TEACHER_SUPPORT` is flagged after 2 reassessments in a row without improvement.
- **Student copy** (UI-005): *"Your score on these questions went from 4/10 (40%) to 8/10 (80%). That's a good sign from practice. It isn't proof you've mastered the topic, and your next class test will show more."*

---

## 7. Security, privacy and AI-safety design

| Concern | How it's handled | Built in | Proven by |
|---|---|---|---|
| Keeping schools' data apart | Tenant taken from the session only; `TenantModel` scoped managers; Postgres RLS added later | P1-T02, P7-T02 | Cross-tenant suite (P7-T03) |
| Who can do what | DRF default permission class that denies by default; permission catalog (Appendix D); scope resolvers; 404 for records out of scope | P1-T06 | Route-registry test, IDOR tests |
| Sign-in | argon2id; server-side sessions with idle and absolute timeouts; MFA for administrators; account lockout; re-authentication for sensitive actions; Django CSRF protection | P1-T03..05 | Auth integration tests |
| Integrity of official results | Only `ResultsService` writes results; import-linter contracts; a runtime write guard on result models; revision history | P3-T08, T09, T11 | `[FR-EXAM-026]` tests |
| What students can see | `VisibilityService`; per-component release timestamps; only RELEASED findings | P3-T10, P4-T08 | Release-matrix test |
| Audit trail | Events written in the same transaction; hash chain; database grants that allow only appends | P1-T07 | Tamper-detection test |
| Files | Private bucket; virus scan; signed URLs that expire within 5 minutes; URLs never logged | P1-T08 | EICAR, expiry and IDOR tests |
| What the AI receives | Allow-list mappers; pseudonyms; no free text in R1 | P4-T04 | Property test for personal data |
| What the AI produces | Schema, reference, number and banned-phrase checks; template fallback; teacher review by default; UI labels | P4-T04..06 | Validator tests |
| AI outages and cost | Queue with retries and timeouts; per-school budget; kill switch; working path with AI disabled | P4-T03/04, P7-T07 | Fault injection |
| Web attacks | CSP, HSTS, SameSite cookies, Django CSRF and Origin checks, markdown sanitised with `nh3`, no `dangerouslySetInnerHTML`, ORM only (raw SQL banned outside reviewed modules) | P1-T09, P7-T01 | ZAP, XSS tests |
| Privacy over the data's lifetime | Data inventory, retention purge, deletion, consent status, operator access grants | P7-T04 | Deletion test |
| Secrets | Secret stores; gitleaks in CI; Claude is denied `Read(./.env)`; Django admin disabled outside local development | P0-T06, P1-T11 | CI scan |
| How the team develops | No real student data in development, tests or prompts | CLAUDE.md rule 10 | Code review |

---
## 8. Repository layout and conventions

### 8.1 Layout

```text
as-platform/
├── CLAUDE.md                     # Claude Code project memory (Appendix A.1)
├── .claude/
│   ├── settings.json             # permissions + hooks (A.2)
│   ├── hooks/                    # protect-files.mjs, format-file.mjs (A.3)
│   ├── rules/                    # path-scoped rules: backend, web, db, ai, testing (A.4)
│   ├── skills/                   # /task, /phase-gate (A.5)
│   └── agents/                   # security-reviewer, requirements-auditor (A.6)
├── docs/
│   ├── BUILD_PLAN.md             # this file
│   ├── SRS.md                    # requirements (source of truth for "what")
│   ├── PROGRESS.md               # task status, SRS change requests, follow-ups
│   ├── adr/                      # 0001-…md decisions
│   ├── design/reference/         # dashboard reference screenshots (inspiration only)
│   ├── gates/                    # phase gate reports (P1.md …)
│   ├── verification/manual.md    # manual verification records with requirement IDs
│   ├── security/ privacy/ perf/ a11y/ runbooks/ guides/ uat/
├── backend/                      # Django project (Python, uv)
│   ├── pyproject.toml            # deps + ruff, mypy, pytest, import-linter config
│   ├── uv.lock
│   ├── manage.py
│   ├── openapi.yaml              # generated by drf-spectacular; committed; CI checks drift
│   ├── config/                   # settings/{base,dev,test,prod}.py, urls.py, celery.py, wsgi.py, asgi.py
│   ├── core/                     # cross-cutting: tenancy (context, TenantModel, managers), policy (permissions,
│   │                             #   decorators, scope resolvers), problem+json errors, pagination, clock, logging
│   ├── modules/                  # one Django app per module (§1.3)
│   │   ├── accounts/             # users, roles, sessions, auth, MFA, invitations, operator accounts
│   │   ├── audit/  files/  academic/  portal/  notices/  imports/
│   │   ├── exams/  results/  scripts/  analysis/
│   │   ├── resources/  question_bank/  recommendations/  practice/  progress/
│   │   └── reports/  school_settings/  notifications/  operator/
│   │       # each app: models.py, selectors.py (reads), services.py (writes), serializers.py,
│   │       #           views.py, urls.py, permissions.py (scope resolvers), tasks.py (Celery),
│   │       #           migrations/, tests/
│   ├── domain/                   # pure Python: permissions, exams, results, diagnosis, recommend, practice,
│   │   │                         #   scoring, progress, metrics (no Django, no I/O)
│   │   └── tests/fixtures/       # golden fixtures (Appendix E.4)
│   ├── ai/                       # gateway, providers (fake, anthropic), payload mappers, validators, prompts, evals
│   └── tests/                    # cross-cutting: security/ (route registry, IDOR generator), contract helpers
├── apps/
│   └── web/                      # Next.js: app/s/[school]/… (portal), app/app/(admin|teacher|student)/…
│       └── src/api/generated/    # orval output from backend/openapi.yaml (never edited by hand)
├── tests/
│   ├── e2e/                      # Playwright specs per area + core-loop/sara.spec.ts (@as/e2e)
│   ├── fixtures/                 # shared JSON vectors used by both pytest and Vitest (e.g. marks formatting)
│   └── load/                     # k6 scripts
├── scripts/                      # req_trace.py, i18n-check.ts
├── package.json                  # root pnpm scripts that orchestrate web and backend
├── pnpm-workspace.yaml
├── docker-compose.yml
├── .env.example
└── .github/workflows/ci.yml
```

### 8.2 Module boundaries

**import-linter** enforces these in `pnpm lint` (contracts live in `backend/pyproject.toml`). The web side is checked by ESLint's `no-restricted-imports`.

| From | May import | Must not import |
|---|---|---|
| `domain` | the Python standard library only | `django`, `rest_framework`, `celery`, `psycopg`, `boto3`, `httpx`, `anthropic`, `core`, `modules`, `ai`, and any I/O modules (`socket`, `subprocess`, `urllib.request`) |
| `ai` | `domain`, `pydantic`, `anthropic`, `httpx` | `modules`, `django.db` (it receives plain dataclasses, never model instances) |
| `modules.analysis` and `ai` | `modules.results.selectors` (reads that return dataclasses) | `modules.results.models` and `modules.results.services`, so they can never write `AssessmentResult`, `QuestionMark` or `ResultRevision` |
| `modules.<x>` | its own app, `core`, `domain`, `ai`, and other apps' `selectors` and `services` | other apps' `models`, `views`, `serializers` and `tasks`. Foreign keys to other apps use string references (`"academic.ClassSubject"`) |
| `core` | `domain`, Django, DRF | `modules` |
| `apps/web` | `src/api/generated`, its own code | anything under `backend/` |

Ruff's banned-API rule (`TID251`) also blocks `django.db.connection.cursor`, `QuerySet.raw` and `.extra` everywhere except an allow-list of reviewed files (migrations, RLS setup, the audit-chain checker).

### 8.3 Commands

Make these work in P0-T05, and keep the copy in `CLAUDE.md` up to date. Root `pnpm` scripts call the back end through `uv run --directory backend …`, so the same commands work on Windows, macOS, Linux and CI.

| Command | What it does |
|---|---|
| `docker compose up -d` | Starts Postgres (dev and test), Redis, SeaweedFS (S3), Mailpit and ClamAV |
| `pnpm dev` | Runs the web app on :3000, Django on :8000 and a Celery worker, with `/api` proxied through the web app |
| `pnpm verify` | **The gate:** Ruff + mypy + import-linter + `makemigrations --check` + OpenAPI drift check + pytest (unit and integration), then ESLint + `tsc` + Vitest for the web |
| `uv run --directory backend pytest domain -k "<name>"` | Runs one pure unit test |
| `uv run --directory backend pytest modules/<app>/tests/<file>.py` | Runs integration tests against the real test database |
| `pnpm test:e2e` / `pnpm --filter @as/e2e exec playwright test <spec>` | Runs end-to-end tests (Playwright with axe) |
| `pnpm db:makemigrations <app> --name <change>` | Creates a migration (`manage.py makemigrations`) |
| `pnpm db:migrate` | Applies migrations as the owner role (`manage.py migrate`) |
| `pnpm db:seed [--scenario core-loop]` | Loads the Greenfield seed (`manage.py seed`, idempotent) |
| `pnpm db:reset` | Drops the dev database and reseeds it. Refuses outside `dev`. Claude asks before running this |
| `pnpm api:schema` | Regenerates `backend/openapi.yaml` and the orval client in `apps/web/src/api/generated` |
| `pnpm req:trace [--release R1] [--fail-on-missing]` | Reports which requirements have tests (`scripts/req_trace.py`) |
| `pnpm eval:ai` | Runs AI wording evals against the real provider (`manage.py eval_ai`). Manual only; needs a key |
| `pnpm test:load` | Runs k6 scenarios against `LOAD_BASE_URL` |
| `pnpm build` | Builds the web app and the back-end image |

### 8.4 Conventions

- **Python:** type hints everywhere; mypy in strict mode with the Django and DRF stubs; no `Any` or `# type: ignore` without a `# reason:` comment. Ruff formats and lints. Serializers validate input at every HTTP boundary, and pydantic validates JSON fields and AI output.
- **Module shape:** views stay thin. Reads go in `selectors.py`, and writes go in `services.py`, which own transactions and audit. Business rules go in `domain`. Views never call `Model.objects.create()` or `.save()` directly.
- **TypeScript (web):** `strict` mode; no `any` without a `// reason:` comment; API types and zod schemas come only from the generated client.
- **API:** REST under `/api/v1` with kebab-case paths, camelCase JSON and no trailing slashes (`APPEND_SLASH = False`, routers with `trailing_slash=False`). Errors use `application/problem+json` (RFC 9457) through a custom DRF exception handler, with a stable `code`. Lists use DRF cursor pagination.
- **Marks:** integers in hundredths (`marks_centi`). The back end formats them with `domain.format.format_marks()`. The web has a matching `formatMarks()` in `apps/web/src/lib/format.ts`. Both are tested against the same vectors in `tests/fixtures/format-marks.json`.
- **Time:** store UTC (`USE_TZ = True`, `timestamptz`) and display in the school's time zone. Code gets the time from the injectable `core.clock`, never `timezone.now()` or `datetime.now()` directly (a Ruff banned-API rule enforces this).
- **Text:** every user-facing string in the web goes through next-intl. API errors use stable codes. Emails use Django templates with `gettext`.
- **Git:** one branch per task (`task/P3-T04-mark-grid`); commit messages start with the task ID (`P3-T04: mark-entry grid`); merge into `main` through a PR with green CI.
- **IDs in tests:** requirement or task IDs go in a `@pytest.mark.req(...)` marker in Python, or in square brackets in the test name in TypeScript (§9.2).

---

## 9. Testing strategy

### 9.1 Test layers

| Layer | Tool | Location | What it covers | When it runs | Gate |
|---|---|---|---|---|---|
| Unit | pytest + Hypothesis | `backend/domain/**/tests/test_*.py`, `backend/ai/tests/` | Domain rules: state machines, marks arithmetic, diagnosis, recommendations, practice assembly, scoring, progress, permissions, AI validators. No database | Constantly while Claude works; in CI | ≥ 90% lines in `domain` |
| Integration | pytest-django + real Postgres and Redis (Compose `postgres-test`, or service containers in CI) | `backend/modules/<app>/tests/`, `backend/core/tests/` | Endpoints (through DRF's `APIClient`), authorisation, tenancy, transactions, audit, Celery tasks (run eagerly) | `pnpm verify`, CI | ≥ 80% lines in `modules` |
| Contract | openapi-core against `backend/openapi.yaml`; the drift check | Inside integration tests (`expect_contract(response, operation_id)`) and in `pnpm verify` | Response shapes match the published schema, and the web client matches the schema | CI | Every endpoint |
| Web unit | Vitest | `apps/web/src/**/*.test.ts(x)` | Formatting helpers, hooks and components | CI | — |
| End-to-end | Playwright | `tests/e2e/**` | Journeys per role, plus the Sara core loop | CI on PRs to `main` | Green, and no flaky tests (retries = 0 locally) |
| Accessibility | `@axe-core/playwright` plus manual checks | Inside E2E specs; P7-T06 | WCAG 2.2 AA | CI and P7 | No serious or critical violations |
| Security | Route registry, IDOR generator, schemathesis, OWASP ZAP baseline, gitleaks, pip-audit, osv-scanner | `backend/tests/security`, CI | Access control and OWASP top risks | CI; ZAP weekly from P7 | No unexpected access |
| AI evals | `pnpm eval:ai` | `backend/ai/evals` | Faithfulness, tone and length on fixtures, using the real provider | Manually, before any prompt or model change | No unfaithful text accepted |
| Performance | k6, Lighthouse CI, pytest query-count assertions | `tests/load`, integration tests | NFR-PERF targets; no N+1 queries | P7 and before each release | Thresholds met |
| Manual and UAT | Scripts in Appendix F | `docs/uat` | Real-world flows and usability | P6 and P8 | Sign-off |

### 9.2 Requirement-tagged tests and `pnpm req:trace`

- Tag every test that proves a requirement or acceptance criterion:
  - **Python:** `@pytest.mark.req("FR-EXAM-026")` above the test (the marker is registered in `pyproject.toml`, with `--strict-markers` on). A marker can carry several IDs: `@pytest.mark.req("FR-EXAM-012", "P3-T03-AC1")`.
  - **TypeScript:** put the ID in square brackets in the test name: `test('[FR-AUTH-004] each role lands on its dashboard', …)`.
- `scripts/req_trace.py` works like this:
  1. It parses `docs/SRS.md` for requirement rows (`| FR-XXX-nnn | … | M | R1 |` and `**DR-nnn (M, R1):**`).
  2. It collects Python tags by running `pytest --collect-only -q` with a small plugin that prints each test's `req` marker, and it scans `**/*.{spec,test}.{ts,tsx}` and `tests/**` for `[ID]` tags.
  3. It reads `docs/verification/manual.md` for manual evidence, in lines such as `- [NFR-PRIV-010] DPIA signed 2027-03-10 — link`.
  4. It prints a table of `ID | priority | release | status (TESTED n / MANUAL / MISSING)`.
- **Flags:** `--release R1`, `--priority M`, `--module FR-EXAM`, and `--fail-on-missing`. That last flag is the M7 gate.
- If `docs/SRS.md` is missing, the script falls back to the SRS IDs cited in this plan's task headers. Tasks are written to be self-contained.

### 9.3 Fixtures and seeds

- **Greenfield seed** (Appendix E): one fictional school with year 2026–27, classes 9A and 9B, and Mathematics and Science. It has an admin, 2 teachers and 30 students, including **Sara** in 9A. It's used in development, E2E and demos, and is loaded by `manage.py seed`.
- **Golden fixtures** live in `backend/domain/tests/fixtures/`:
  - `sara-core.json`
  - `total-only.json`
  - `multi-topic.json`
  - `class-9a-triangles.json`
  - `practice-bank-forming-eq.json`

  Each has an `expected` block. Any change to the rules must update the expected output in the same commit, with the reason.
- **Test data in integration tests** comes from factory_boy factories in each app's `tests/factories.py`. Factories create rows inside an explicit tenant context.
- **Large synthetic dataset** (P7-T05): a `manage.py seed_large` generator for 10 schools, 10,000 users and about 200,000 marks, seeded and deterministic.
- **Real student data never goes into fixtures, seeds, prompts, screenshots or logs.**

### 9.4 Security tests

1. **Route registry test:** walk Django's URL resolver (`get_resolver().url_patterns`, recursively) and inspect every view and every action. Each must be marked `@public` or carry `@require_permission`. Plain Django views outside DRF (health checks) must be in an explicit allow-list. The test fails on any route that doesn't qualify (fail closed). `PolicyPermission` also refuses unmarked actions at runtime.
2. **IDOR generator** (P7-T03; started in P1): `backend/tests/security/route_fixtures.py` maps each URL name to a factory that creates the target record in another school and in another class. For every route × role × target, it asserts the expected status from the permission catalog. A new route without a factory fails the test.
3. **Visibility matrix:** for every combination of release timestamps, check that the student response contains exactly the released components.
4. **Audit tamper test:** change one audit row through the owner-role connection, and `verify_audit_chain` must report the break.
5. **Result write guard:** saving, updating or deleting `AssessmentResult`, `QuestionMark` or `ResultRevision` outside `ResultsService` raises `ResultWriteForbidden` (P3-T11).

### 9.5 AI testing

- Unit and integration tests use **`FakeAiProvider`** only. It returns canned outputs keyed by payload hash, plus "bad output" modes: malformed JSON, invented topics, wrong numbers, banned phrases and timeouts. A pytest fixture fails any test that tries to construct the real provider.
- **Property test (Hypothesis):** generate students with random names, emails and usernames. Build every AI payload and assert that none of those strings appear in it.
- **Fault injection:** make the provider raise at each stage. Official records must stay byte-identical, the run must be `FAILED`, and the template text must still be available.
- **`pnpm eval:ai`:** runs the real provider over about 30 fixture findings. It reports schema failures, faithfulness failures (blocked and replaced by templates), banned phrases, length, and a simple readability score. Save the report to `docs/ai/evals/<date>-<prompt>-<model>.md`.

### 9.6 Rules for Claude when testing

1. Write the failing test for each acceptance criterion **before** implementing it.
2. While working, run the narrowest relevant command. Run `pnpm verify` before saying a task is done, and run the E2E spec for any UI change.
3. Show evidence: the commands you ran and their pass/fail summaries.
4. Never skip, weaken or delete a test to get a green run. If a test is wrong, explain why in the commit message.
5. Flaky tests are bugs. Fix the cause (time, ordering, shared state) instead of adding retries.

---

## 10. Environments, CI/CD and deployment

### 10.1 Environments

| Environment | Purpose | Data | How it's deployed | AI provider |
|---|---|---|---|---|
| Local | Development | Greenfield seed | `docker compose up -d` and `pnpm dev` | `fake` by default; `anthropic` with your own key for manual checks |
| CI | Automated tests | Fixtures and seed | Created fresh for each run | `fake` |
| Staging | Demos, UAT and performance tests | **Synthetic only** | Automatically on merge to `main` | Real provider with a test key and budget, or `fake` |
| Production | The pilot | Real data, only after G-LEGAL | Manual approval of a tagged release | Set per school |

### 10.2 Local services (`docker-compose.yml`)

| Service | Image (pin the version) | Port | Notes |
|---|---|---|---|
| postgres | `postgres:17` | 5432 | Development database. An init script creates the `as_owner` and `as_app` roles |
| postgres-test | `postgres:17` | 5433 | Uses tmpfs for speed. pytest-django creates and reuses the test database (`--reuse-db`) |
| redis | `redis:7` (or Valkey) | 6379 | Celery broker, Django cache and rate limits |
| seaweedfs | `chrislusf/seaweedfs` (`server -s3`) | 8333 | S3 API; create the bucket on startup |
| mailpit | `axllent/mailpit` | 8025 (UI), 1025 (SMTP) | Catches all outgoing email |
| clamav | `clamav/clamav` | 3310 | Takes a few minutes to load its signatures on first start |

Django, the Celery worker and Next.js run on your machine through `pnpm dev`. On Windows without WSL2, the worker runs with `--pool=solo` (§3.3).

### 10.3 CI pipeline (`.github/workflows/ci.yml`)

| Job | Steps | Runs on |
|---|---|---|
| `checks` | Set up Python with uv (cached) and Node with pnpm (cached). Ruff, mypy, import-linter, `makemigrations --check --dry-run`, OpenAPI drift check (`spectacular` + orval, then `git diff --exit-code`), unit tests with coverage, ESLint, `tsc`, Vitest, build | Every push and PR |
| `integration` | Postgres and Redis service containers, `migrate`, pytest integration tests with coverage | Every push and PR |
| `e2e` | Compose stack, migrate, seed, start Django, the worker and Next.js, then Playwright with axe; upload the report and traces | PRs to `main` |
| `security` | gitleaks, pip-audit, osv-scanner or `pnpm audit --prod`; ZAP baseline against staging (weekly, from P7) | PRs and a schedule |
| `trace` | `pnpm req:trace --release R1`, uploaded as an artifact. Blocking from M7 | PRs to `main` |
| `deploy-staging` | Build images, run `manage.py migrate` as the owner role, roll out `web`, `api`, `worker` and `beat`, smoke test | Merge to `main` |
| `deploy-prod` | Same steps on a tag, with manual approval in the `production` environment | Tags `v*` |

Protect `main` so that `checks`, `integration`, `e2e` and `security` must pass before merging. Use the current major versions of the official GitHub Actions, plus `astral-sh/setup-uv`.

### 10.4 Deployments and migrations

- Use the **expand → migrate → contract** pattern so each release can run against both the previous and the new schema. Use separate Django migrations for schema changes and data changes (`RunPython`), and give every `RunPython` a reverse function or `migrations.RunPython.noop`.
- Run `manage.py migrate` with `DATABASE_MIGRATE_URL` (the owner role) before the app rolls out. The app itself connects with `DATABASE_URL` (the `as_app` role). To roll back, redeploy the previous image; migrations stay backward-compatible for one release.
- Run `manage.py check --deploy` in the deploy job and fail on warnings.
- Roll features out with school settings, for example `aiEnabled` and the AI release policy, rather than code branches.

### 10.5 Configuration (`.env.example`)

```dotenv
# Core
DJANGO_SETTINGS_MODULE=config.settings.dev   # dev | test | prod
DJANGO_SECRET_KEY=           # 50+ random characters; different per environment
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
APP_URL=http://localhost:3000
CSRF_TRUSTED_ORIGINS=http://localhost:3000
API_PORT=8000
DATABASE_URL=postgres://as_app:as_app@localhost:5432/as            # app role: no DDL, no BYPASSRLS
DATABASE_MIGRATE_URL=postgres://as_owner:as_owner@localhost:5432/as # owner role: migrations only
DATABASE_URL_TEST=postgres://as_owner:as_owner@localhost:5433/as_test
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
APP_ENCRYPTION_KEY=          # 32 random bytes, base64 — encrypts TOTP secrets (AES-GCM)
# Storage and scanning
S3_ENDPOINT=http://localhost:8333
S3_REGION=us-east-1
S3_BUCKET=as-dev
S3_ACCESS_KEY_ID=dev
S3_SECRET_ACCESS_KEY=dev-secret
S3_FORCE_PATH_STYLE=true
SIGNED_URL_TTL_SECONDS=300
CLAMAV_HOST=localhost
CLAMAV_PORT=3310
# Email
EMAIL_URL=smtp://localhost:1025
DEFAULT_FROM_EMAIL="AS Platform <no-reply@as.local>"
# AI (optional; R1 works with AI_PROVIDER=fake or disabled)
AI_PROVIDER=fake             # fake | anthropic | disabled
AI_MODEL=claude-haiku-5-5    # pick per OI-04; check the provider's current model IDs
ANTHROPIC_API_KEY=
AI_TIMEOUT_SECONDS=30
AI_KILL_SWITCH=false
AI_PROMPT_EXPLAIN_FINDINGS=v1
AI_PAYLOAD_RETENTION_DAYS=90
# Observability
LOG_LEVEL=INFO
SENTRY_DSN=
# Local/test only
DJANGO_ADMIN_ENABLED=true    # always false in staging and production
SEED_PASSWORD=Local-Only-Seed-Password-2026
```

### 10.6 Hosting

- **Pilot (simple):** a container platform for `web` (Next.js), `api` (gunicorn), `worker` (Celery) and `beat` (Celery beat, exactly one instance), plus managed PostgreSQL with point-in-time recovery, managed Redis and an S3-compatible bucket, all in **one region** chosen under OI-10. Examples include a container PaaS such as Render, Railway or Fly.io, or a cloud provider's managed services.
- **Scale (R2+):** the same components on AWS, GCP or Azure, defined as infrastructure-as-code with Terraform or OpenTofu. Add PgBouncer in transaction mode if connection counts grow; the RLS setting is transaction-local, so it is safe with it.
- **Checklist for any host:**
  - The region satisfies OI-01/10.
  - Data is encrypted at rest (NFR-SEC-012).
  - Point-in-time recovery is kept for at least 7 days (NFR-AVL-003).
  - The database is on a private network, and the app uses the `as_app` role.
  - TLS 1.2+ (COM-001), with `SECURE_PROXY_SSL_HEADER`, `SECURE_HSTS_SECONDS` and secure cookies set.
  - Secrets live in a secrets manager (NFR-SEC-013).
  - Django admin is disabled, and `manage.py check --deploy` passes.
  - Log retention is configurable.

---

## 11. Working with Claude Code

This section is based on the official Claude Code documentation (code.claude.com/docs): best practices, memory/CLAUDE.md, skills, subagents, hooks, permissions and `/goal`.

### 11.1 One-time setup

P0-T03 installs the kit from Appendix A:

| File | What it does |
|---|---|
| `CLAUDE.md` | Short project memory loaded every session: stack, commands, the 10 non-negotiable rules, workflow. Keep it under about 100 lines. **Don't** `@import` this plan into it, because imports load at launch and would fill the context |
| `.claude/rules/*.md` | Path-scoped rules (Django back end, web, database, AI, testing) that load only when Claude touches matching files |
| `.claude/skills/task/` | `/task <ID>`: the standard implementation loop |
| `.claude/skills/phase-gate/` | `/phase-gate <P#>`: checks exit criteria and writes a gate report |
| `.claude/agents/security-reviewer.md` | A fresh-context reviewer for tenancy, authorisation, visibility, audit, AI payloads and files |
| `.claude/agents/requirements-auditor.md` | Checks a task's acceptance criteria against tests and the diff |
| `.claude/settings.json` | Pre-approved safe commands, prompts for risky ones, denies reading `.env`, and runs the hooks |
| `.claude/hooks/protect-files.mjs` | Blocks edits to `.env*` files, `docs/SRS.md`, committed Django migrations and the generated API client |
| `.claude/hooks/format-file.mjs` | Runs Ruff on every Python file and Prettier on every web file Claude edits |

After installing, restart `claude`. Run `/context` to check that `CLAUDE.md` and the rules loaded, and check that `/task` and `/phase-gate` appear in the `/` menu.

### 11.2 The loop for each task

1. In the repo root, run `claude`. For tasks marked 🔒 below, which touch auth, tenancy, results, AI or files, start in plan mode with `claude --permission-mode plan`, or press `Shift+Tab` until it shows *plan mode on*.
2. Name the session: `/rename P3-T04`.
3. Run `/task P3-T04`. Claude reads only that task and its SRS IDs, checks dependencies, explores the code and proposes a plan.
4. **You review the plan.** Press `Ctrl+G` to edit it in your editor, then approve it.
5. Claude writes the failing tests, implements, runs `pnpm verify`, runs the reviewers, updates `docs/PROGRESS.md` and commits.
6. **You review the evidence and the diff.** For UI work, also try the feature in the browser. Then push, open a PR, wait for green CI and merge.
7. Run `/clear` and start the next task.

To keep Claude working on its own until the checks pass, add a goal after approving the plan:

```text
/goal pnpm verify exits 0 and every acceptance criterion of P3-T04 in docs/BUILD_PLAN.md has a passing test tagged with its ID; only files for this task changed; or stop after 25 turns
```

### 11.3 Session hygiene

- Do **one task per session**, and run `/clear` between tasks. Context is the scarcest resource.
- If you've corrected Claude twice on the same thing, run `/clear` and restart with a better prompt that includes what you learned.
- Use `Esc` to stop Claude, and `Esc Esc` or `/rewind` to roll back conversation or code to a checkpoint. **Git is still the real safety net**, so commit after every task.
- `claude --continue` and `claude --resume` pick up a session you named earlier.
- Ask Claude to delegate wide investigations to subagents, for example *"use subagents to investigate how sessions are refreshed"*, so your main context stays clean.
- When Claude keeps repeating a mistake, add a one-line rule to `CLAUDE.md`, or better, a hook or a test. Prune `CLAUDE.md` regularly.

### 11.4 Prompt library

Start a task when the `/task` skill isn't available:

```text
Implement task P3-T04 from docs/BUILD_PLAN.md. Read only that section (grep "^#### P3-T04") and the SRS IDs it cites in docs/SRS.md. Check its dependencies in docs/PROGRESS.md. Plan first; then write failing tests tagged with the IDs; then implement. Run pnpm verify and the related e2e spec. Update docs/PROGRESS.md and commit as "P3-T04: <title>". Show me the evidence.
```

Fix a bug:

```text
This test fails: <paste output>. Reproduce it, find the root cause, and fix it without weakening the test. Explain the cause in the commit message.
```

Review in a fresh context:

```text
Use the security-reviewer subagent on the current diff, then the requirements-auditor subagent for P3-T04. Fix every FAIL / NOT MET item and re-run both.
```

Run the bundled correctness review on the diff:

```text
/code-review
```

Check a UI page:

```text
Start the app with the Greenfield seed. Open /app/teacher/exams/<id>/marks as the Mathematics teacher. Take screenshots at 1280px and 360px. Compare the layout ideas with docs/design/reference/02-exam-records.jpg (inspiration only, no branding). List the differences and any accessibility problems, fix the accessibility problems first, then re-run the page's Playwright spec.
```

Run a phase gate:

```text
/phase-gate P3
```

Fix a repeated mistake:

```text
You keep <mistake>. Propose the smallest fix that prevents it permanently: a test, a lint or dependency rule, a hook, or one line in CLAUDE.md.
```

### 11.5 Decision interview (P0-T04)

```text
Read docs/BUILD_PLAN.md section 3 and the open-issues table in docs/SRS.md (Appendix C). Interview me with the AskUserQuestion tool about every decision listed in §3.2 and any ADR in §3.1 where I might want to deviate. Skip obvious questions; dig into tradeoffs I might not have considered. Then write docs/adr/0001…0011 using docs/adr/template.md, record any SRS change requests in docs/PROGRESS.md, and summarise what changed from the defaults.
```

### 11.6 Parallel work and automation (optional)

- **Writer/reviewer:** one session implements; a second, fresh session reviews the diff against the task. The same idea works for tests: one session writes them and another makes them pass.
- **Worktrees:** run separate sessions in separate git worktrees for independent tasks, for example a web page and an unrelated API module. Don't run two tasks in parallel if they touch the same Django app's models: both branches would add a migration with the same number. If it happens anyway, run `manage.py makemigrations --merge` on the second branch after rebasing.
- **GitHub:** `/install-github-app` lets you mention `@claude` in PRs and issues and add an automated review workflow, which uses the `ANTHROPIC_API_KEY` or `CLAUDE_CODE_OAUTH_TOKEN` repository secret.
- **Headless batch jobs** with `claude -p`, for example filling in missing translation keys:

  ```bash
  claude -p "Add missing keys to apps/web/messages/<locale>.json from en.json. Keep ICU placeholders. Do not change en.json." --allowedTools "Read,Edit"
  ```

### 11.7 What only you can do

- Approve plans for 🔒 tasks, and review every diff that touches auth, tenancy, results, analysis/AI or files.
- Make the decisions in §3.2, own the legal gate (P8-T01), and talk to pilot teachers.
- Keep real student data out of prompts, fixtures, screenshots and logs.
- Demo each milestone to a teacher adviser, and write their feedback into `docs/PROGRESS.md`.

---

## 12. Timeline and milestones

### 12.1 Assumptions

- **Team:** one developer working full-time (about 6 focused hours a day) with Claude Code, plus a part-time teacher adviser for reviews and demos.
- **Task size:** 0.5–2 days. Your own time per task is about 30–60 minutes reviewing the plan, the diff and the feature.
- **Calendar:** the example dates assume week 1 starts on **Monday 19 October 2026**. Shift them for your start date and holidays. Weeks 10–11 cover the end-of-year holidays.

### 12.2 Phases and milestones

| Phase | Weeks | Example dates | Milestone at the end | Demo |
|---|---|---|---|---|
| P0 Decisions and setup | 1 | 19 Oct – 23 Oct 2026 | **M0** Repo ready: CI green, Claude kit, ADRs | `pnpm verify` green in CI |
| P1 Foundation | 2–4 | 26 Oct – 13 Nov | **M1** Walking skeleton on staging | Three roles sign in on staging |
| P2 Academic structure and school setup | 5–6 | 16 Nov – 27 Nov | **M2** A school can be set up from CSV | Admin imports Greenfield |
| P3 Exams, marks and release | 7–9 | 30 Nov – 18 Dec | **M3** Results released to students | Teacher enters, validates and releases; Sara sees her marks |
| P4 Assessment intelligence | 10–12 | 21 Dec – 8 Jan 2027 | **M4** Findings reviewed and released | Teacher reviews; Sara sees her gap report |
| P5 Learning, practice and progress | 13–15 | 11 Jan – 29 Jan | **M5 Core loop**: the Sara E2E test passes | Full loop demo |
| P6 Dashboards and reports | 16–17 | 1 Feb – 12 Feb | **M6** Feature complete (R1) | Usability dry run |
| P7 Hardening | 18–20 | 15 Feb – 5 Mar | **M7** Release candidate: all gates GO | Security, performance and accessibility reports |
| P8 Pilot and launch | 21–24 | 8 Mar – 2 Apr | **M8** Pilot live and R1 signed off | First real exam cycle |
| R2 (outline) | 25–40 | 5 Apr – 23 Jul | R2 releases (§15) | |

```mermaid
gantt
  title AS Release 1 (example start Mon 19 Oct 2026)
  dateFormat YYYY-MM-DD
  axisFormat %d %b
  section Setup
  P0 Decisions and setup          :p0, 2026-10-19, 7d
  section Build
  P1 Foundation                   :p1, after p0, 21d
  P2 Academic structure           :p2, after p1, 14d
  P3 Exams and results            :p3, after p2, 21d
  P4 Assessment intelligence      :p4, after p3, 21d
  P5 Learning and practice        :p5, after p4, 21d
  P6 Dashboards and reports       :p6, after p5, 14d
  section Release
  P7 Hardening                    :p7, after p6, 21d
  P8 Pilot and launch             :p8, after p7, 28d
  section Milestones
  M1 Walking skeleton             :milestone, m1, 2026-11-13, 0d
  M3 Results released             :milestone, m3, 2026-12-18, 0d
  M5 Core loop                    :milestone, m5, 2027-01-29, 0d
  M7 Release candidate            :milestone, m7, 2027-03-05, 0d
  M8 Pilot live                   :milestone, m8, 2027-04-02, 0d
```

### 12.3 Weekly rhythm

- **Monday:** pick the week's tasks from §13 and mark them 🔄 in `docs/PROGRESS.md`.
- **Daily:** 2–4 tasks using the §11.2 loop, merging each one when CI is green.
- **Friday:** update `PROGRESS.md`, run `pnpm req:trace`, and note risks. Every other week, demo to your teacher adviser.
- **At the end of each phase:** run `/phase-gate P#` and fix anything blocking before starting the next phase.

### 12.4 If your capacity is different

| Team | Approximate R1 duration | How to organise |
|---|---|---|
| 1 developer, part-time (~20 h/week) | 40–48 weeks | Same order. Keep tasks small and merge every session |
| 1 developer, full-time (baseline) | 24 weeks | As planned |
| 2–3 developers | 14–16 weeks | Split into parallel tracks after P1: **A** domain and Django API (P3–P5 back end), **B** web (screens and E2E), **C** platform (CI, staging, security, performance). Agree the serializers and commit `openapi.yaml` first, so track B can build against the generated client |

### 12.5 What to cut if you fall behind

If you are more than 2 weeks behind at M3 or M5, defer these to R2 instead of extending the date. They are listed in the order to cut them:

1. P3-T05: importing marks from CSV. Keep the grid.
2. Teacher-side CSV import of question-bank items (P5-T02).
3. The auto-release policy for findings (FR-AI-016, a Should). Keep teacher review.
4. P6-T06: portal resource links (FR-PORT-007, a Should).
5. Email notifications for releases. Keep in-app notifications only.
6. The class insights heatmap. A plain table is enough.

**Never cut:** tenancy and authorisation tests, audit, `VisibilityService`, the FR-EXAM-026 guards, backups, the legal gate or accessibility basics.

### 12.6 Faster demo track (10–12 weeks, demo only)

This track is for a thesis or investor demo that will **never hold real student data**. It covers P0, P1 (skipping T05 and T11), P3 (skipping T05 and T06), P4 (skipping T04, so templates only), and P5 (skipping T02's import), all on a single seeded school. It omits RLS, load testing, ClamAV, staging and the legal gate. **Before any real data goes in, go back and complete every skipped task and all of P7 and P8.**

---
## 13. Phase-by-phase build plan

Every task follows the loop in §11.2 and the Definition of Done in Appendix G. 🔒 marks a sensitive task: start it in plan mode, and the security-reviewer must PASS before it is done. Estimates are in working days for one developer with Claude Code.

### Phase 0. Decisions and setup (week 1)

**Objective:** a repository where Claude Code knows the rules, the stack (Django + PostgreSQL back end, Next.js web) is set up, and `pnpm verify` passes in CI.
**Milestone:** M0 (repo ready).

#### P0-T01 · Prepare your machine and accounts
**Owner** 🧑 · **SRS** none · **Depends on** none · **Est.** 0.5 d

**Build**
- Install:
  - Git and the GitHub CLI (`gh auth login`).
  - On Windows: WSL2 with Ubuntu (recommended for the back end, see §3.3). Install the tools below inside WSL2.
  - Python 3.13 and **uv** (`curl -LsSf https://astral.sh/uv/install.sh | sh`, or `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"` on Windows). uv can install Python for you with `uv python install 3.13`.
  - Node.js 24 LTS; run `corepack enable` for pnpm.
  - Docker with Compose.
  - Claude Code. On macOS, Linux or WSL run `curl -fsSL https://claude.ai/install.sh | bash`; in Windows PowerShell run `irm https://claude.ai/install.ps1 | iex`.
- Accounts:
  - A private GitHub repo.
  - A Claude plan that includes Claude Code (Pro, Max, Team or Enterprise), or a Console account.
- Later, not now: an AI provider key for the product (P4), hosting (P1-T11), and SMTP and error tracking (P1).

**Acceptance criteria**
- [ ] `git --version`, `uv --version`, `uv run --python 3.13 python --version`, `node -v`, `pnpm -v`, `docker compose version`, `gh auth status` and `claude --version` all succeed *(manual)*.

#### P0-T02 · Create the repository and add the planning docs
**Owner** 🧑 · **SRS** none · **Depends on** P0-T01 · **Est.** 0.25 d

**Build**
- `mkdir as-platform && cd as-platform && git init`, then create the GitHub repo with `gh repo create`.
- Add these files:
  - `docs/BUILD_PLAN.md` (this file).
  - `docs/SRS.md` (SRS v1.0).
  - `docs/design/reference/01-overview.jpg` … `05-progress.jpg`: the five dashboard screenshots from your original description, renamed to match the five student-dashboard areas (overview, exam records, learning gaps, learning plan, progress).
- Commit with the message `docs: add SRS, build plan and design references`.

**Acceptance criteria**
- [ ] The docs are on `main` *(manual)*.

#### P0-T03 · Install the Claude Code kit
**Owner** 🤖 (plain prompt, because `/task` doesn't exist yet) · **SRS** none · **Depends on** P0-T02 · **Est.** 0.25 d

**Build.** Paste this prompt into `claude`:

```text
Read docs/BUILD_PLAN.md Appendix A. Create every file it lists with exactly the content given (CLAUDE.md, .claude/settings.json, .claude/hooks/*.mjs, .claude/rules/*.md, .claude/skills/*/SKILL.md, .claude/agents/*.md, docs/adr/template.md, .github/pull_request_template.md). Then create docs/PROGRESS.md in the format of Appendix A.9 with one row per task heading "#### Px-Tyy" found in docs/BUILD_PLAN.md, all ⬜. Do not create application code. Commit as "P0-T03: Claude Code kit".
```

Then quit, restart `claude` and run `/context`.

**Acceptance criteria**
- [ ] `/context` lists `CLAUDE.md`. `/task` and `/phase-gate` appear in the `/` menu *(manual)*.
- [ ] Asking Claude to edit `.env` is blocked by the hook *(manual)*.
- [ ] `docs/PROGRESS.md` has a row for every task heading.

#### P0-T04 · Confirm key decisions and write the ADRs
**Owner** 🤝 · **SRS** OI-04, OI-05..11, C-01..C-07 · **Depends on** P0-T03 · **Est.** 1 d

**Build**
- Run the interview prompt in §11.5.
- Start the legal track (OI-01/02/03) with the school or your adviser now, because it gates P8.
- Write `docs/adr/0001…0011` with status *Accepted*.
- Add any SRS change requests to `docs/PROGRESS.md`. These include NFR-MNT-001/002, which are partly met (see ADR-0010/0011).

**Acceptance criteria**
- [ ] Every item in §3.2 has a decision or an owner and a date.
- [ ] Every ADR names the SRS IDs it affects *(manual)*.

#### P0-T05 · Scaffold the repository (Django back end, Next.js web)
**Owner** 🤖 `/task P0-T05` · **SRS** NFR-MNT-001, NFR-MNT-004 · **Depends on** P0-T04 · **Est.** 2 d

**Build**
- **Workspace:** a root `package.json` and `pnpm-workspace.yaml` covering `apps/web` and `tests/e2e`. Root scripts (§8.3) call the back end with `uv run --directory backend …`. Use `concurrently` for `pnpm dev`.
- **backend/** (uv project, `backend/.python-version`):
  - Django 5.2 LTS project in `config/`, with split settings `config/settings/{base,dev,test,prod}.py` read through django-environ.
  - DRF configured with: `DEFAULT_PERMISSION_CLASSES = ["core.policy.PolicyPermission"]` (a stub that denies everything not marked `@public` for now), no default authentication classes yet, the camel-case renderer and parser, cursor pagination, and a problem+json exception handler.
  - drf-spectacular serving the schema at `/api/v1/schema` in dev only, plus `manage.py spectacular --file openapi.yaml`.
  - Celery app in `config/celery.py`, a `ping` task, and Celery beat with `django-celery-beat` or a static schedule in settings.
  - `core/` with the clock, the `RequestContext` contextvar stub, and structlog configuration.
  - Empty `domain/` and `ai/` packages, and a `modules/health` app serving `/api/v1/healthz`.
  - Database roles: the app connects with `DATABASE_URL` (`as_app`). When `DJANGO_MIGRATE=1` is set, settings use `DATABASE_MIGRATE_URL` (`as_owner`) instead, and `pnpm db:migrate` sets it. Enable Django's psycopg connection pool.
  - `pyproject.toml` with Ruff, mypy (strict, django-stubs plugin), pytest (`--strict-markers`, the `req` marker, `DJANGO_SETTINGS_MODULE=config.settings.test`), coverage and the import-linter contracts in §8.2.
  - `Dockerfile` for the back end (one image for `api`, `worker` and `beat`).
- **apps/web:** Next.js App Router with TypeScript strict, Tailwind and shadcn/ui initialised. orval configured to read `../../backend/openapi.yaml` and write TanStack Query hooks and zod schemas to `src/api/generated`. The API client sends cookies and the `X-CSRFToken` header.
- **docker-compose.yml:** the services in §10.2, with health checks and a Postgres init script that creates `as_owner` and `as_app`. Also `.env.example` (§10.5) and `.nvmrc`.
- **Tests:** pytest in `backend` (one pure test in `domain`, one DB test in `modules/health`), Vitest in `apps/web`, and the Playwright workspace `@as/e2e` in `tests/e2e`.
- **Lint:** import-linter, Ruff banned-API rules (§8.2, §8.4) and ESLint, all wired into `pnpm lint`.
- **Scripts:** the root scripts in §8.3. Stub `req:trace` and `eval:ai` for now.
- **Proxy:** Next.js rewrites `/api/:path*` to `http://localhost:8000/api/:path*`. Django trusts the proxy headers (`USE_X_FORWARDED_HOST`, `SECURE_PROXY_SSL_HEADER`) and lists the web origin in `CSRF_TRUSTED_ORIGINS`.
- **README:** quick-start steps, including the Windows/WSL2 note.

**Acceptance criteria**
- [ ] On a fresh clone, `pnpm i && (cd backend && uv sync) && docker compose up -d && pnpm db:migrate && pnpm dev` serves `http://localhost:3000`, and `/api/v1/healthz` returns 200 through the proxy.
- [ ] `pnpm verify` passes with the placeholder tests.
- [ ] Importing `django` from `backend/domain` makes `pnpm lint` fail (import-linter), and a test shows this.
- [ ] `pnpm api:schema` produces `openapi.yaml` and a generated client, and the drift check passes.
- [ ] The Celery worker runs the `ping` task locally.
- [ ] Every command in `CLAUDE.md` works. Update the file if the scaffolding differs.

#### P0-T06 · CI pipeline
**Owner** 🤖 · **SRS** NFR-MNT-004 · **Depends on** P0-T05 · **Est.** 1 d

**Build**
- `.github/workflows/ci.yml` with the `checks`, `integration`, `e2e`, `security` and `trace` jobs in §10.3. The `trace` job doesn't block merges yet.
- uv and pnpm caching, coverage reports for Python and TypeScript, and branch protection on `main`.
- Optional: `/install-github-app`.

**Acceptance criteria**
- [ ] A PR shows all the jobs.
- [ ] A deliberately failing unit test blocks the merge *(manual)*.
- [ ] gitleaks catches a dummy secret in a test branch *(manual)*.

**Phase 0 exit criteria (M0)**
- [ ] `pnpm verify` passes locally and in CI.
- [ ] The Claude kit is working (`/context`, `/task`, and the hooks block edits).
- [ ] ADRs 0001–0011 are accepted.
- [ ] The §3.2 decisions are recorded.
- [ ] `/phase-gate P0` reports GO.

---

### Phase 1. Foundation (weeks 2–4)

**Objective:** a secure multi-tenant skeleton. Users sign in and land on their role's dashboard, and every request is tenant-scoped, authorised and audited. It runs on staging.
**Milestone:** M1 (walking skeleton).

#### P1-T01 · Core schema and migration conventions 🔒
**Owner** 🤖 · **SRS** DR-002, DR-005, NFR-AUD-002 · **Depends on** P0-T06 · **Est.** 1.5 d

**Build**
- Base classes in `core/models.py`: `BaseModel` (UUID primary key, `created_at`, `updated_at`) and an abstract `TenantModel(BaseModel)` with `school = ForeignKey("accounts.School", on_delete=PROTECT)`. Its manager is wired up in P1-T02.
- Django models from §5.4: `School`, `User` (set as `AUTH_USER_MODEL` before the first migration — it can't be changed later), `RoleAssignment`, `OperatorAccount`, `Session`, `Invitation`, `PasswordResetToken`, `AuditEvent` and `FileObject`. Follow the conventions in `.claude/rules/db.md`.
- `PASSWORD_HASHERS` with `Argon2PasswordHasher` first.
- A `TENANT_MODELS` registry computed from `apps.get_models()`: every concrete subclass of `TenantModel`.
- Grant `as_app` only `SELECT, INSERT, UPDATE, DELETE` on the app tables (a `RunSQL` migration, plus default privileges for future tables).
- A seed skeleton as the management command `manage.py seed`, which creates the Greenfield school and one user per role, with passwords from `SEED_PASSWORD`.

**Acceptance criteria**
- [ ] `manage.py migrate` applies to an empty database, and `makemigrations --check` reports no changes.
- [ ] `[DR-002]`: every model with a `school` foreign key is in `TENANT_MODELS`, and every entry in `TENANT_MODELS` has one.
- [ ] The `as_app` role can't create or drop tables.
- [ ] The seed is idempotent: running it twice gives the same row counts.

**Tests** `backend/core/tests/test_schema.py`

#### P1-T02 · Request context and tenant-scoped data access 🔒
**Owner** 🤖 · **SRS** NFR-SEC-002, NFR-SEC-003, C-01 · **Depends on** P1-T01 · **Est.** 1.5 d

**Build**
- A `RequestContext` dataclass in a `contextvars.ContextVar` holding `{request_id, school_id, user_id, roles, active_role, session_id}`, read through `ctx()`. Context managers `tenant_context(school_id)` (for tests, seeds and Celery tasks) and `request_context(...)` (used by middleware). Celery tasks receive `school_id` as an argument and enter `tenant_context` themselves; context never leaks between tasks.
- `TenantManager` / `TenantQuerySet`, the default manager (`objects`) of every `TenantModel`. They must:
  - filter every queryset by `school_id = ctx().school_id`, which covers `get`, `filter`, `update`, `delete`, `count`, `exists` and reverse related managers;
  - raise `MissingTenantContextError` when there is no context;
  - in `TenantModel.save()`, set `school_id` from the context on insert and refuse a mismatch on update;
  - refuse to save a row whose foreign keys point to another school's `TenantModel` row (checked in `save()`, and in `bulk_create` / `bulk_update` overrides).
- Set `Meta.base_manager_name` on `TenantModel` so forward foreign-key access also uses a scoped manager.
- `system_scope(reason)` for system jobs: a context manager that allows the unscoped manager `all_schools` for its duration. Every use is audited.
- A Ruff banned-API rule for `all_schools` outside `system_scope` call sites, and for raw SQL (§8.2).

**Acceptance criteria**
- [ ] `[NFR-SEC-002]`: a `schoolId` sent in a request body or query is ignored, and the data stays in the caller's school.
- [ ] `[NFR-SEC-003]`: `Model.objects.filter(pk=<another school's id>).first()` returns `None`, and `get()` raises `DoesNotExist`.
- [ ] A query without context raises `MissingTenantContextError`.
- [ ] Saving a row that points to another school's row is refused.
- [ ] `QuerySet.update()` and `delete()` never touch another school's rows.

**Tests** unit tests for the manager and `save()` rules; integration tests with two schools in `backend/core/tests/test_tenancy.py`.

#### P1-T03 · Sign-in, sessions and password policy 🔒
**Owner** 🤖 · **SRS** FR-AUTH-003, NFR-SEC-005, NFR-SEC-006, NFR-SEC-007, NFR-SEC-008, NFR-ACC-003 · **Depends on** P1-T02 · **Est.** 2 d

**Build**
- `POST /auth/login {schoolSlug, identifier, password}`. The identifier can be a username or an email. A custom authentication backend (`accounts.backends.SchoolAuthBackend`) looks the user up within the school.
- argon2id hashing through Django's `make_password` / `check_password`. Wrong passwords and unknown users get the same response and similar timing: for unknown users, run the hasher against a dummy hash.
- Lockout and backoff: at most 10 failures per account in 15 minutes (fields on `User`), plus IP throttling through a DRF throttle class backed by the Redis cache.
- Session token: 32 random bytes from `secrets.token_urlsafe` in the cookie `as_session` (HttpOnly, Secure, SameSite=Lax, Path=/). The `Session` model stores only its SHA-256.
- `SessionAuthMiddleware` plus a DRF authentication class that set `request.user` and the `RequestContext`. Don't use `django.contrib.sessions` for sign-in.
- Session timeouts: 30 minutes idle for staff, 60 minutes for students, 12 hours absolute.
- `POST /auth/logout`.
- Password policy as Django password validators (`AUTH_PASSWORD_VALIDATORS`), with the pure rules in `domain/auth/password_policy.py`:
  - at least 15 characters without MFA, or at least 8 with MFA;
  - accept up to at least 64 characters;
  - check against a blocklist of common or breached passwords (Django's `CommonPasswordValidator` plus our own list);
  - no composition rules and no forced rotation;
  - pasting is allowed.
- CSRF: keep Django's `CsrfViewMiddleware` on. Our authentication class enforces CSRF on unsafe methods (as DRF's `SessionAuthentication` does). Add an explicit `Origin` check middleware against `CSRF_TRUSTED_ORIGINS`.

**Acceptance criteria**
- [ ] Each timeout and limit has a test that uses a fake clock.
- [ ] The token never appears in logs (log-capture test).
- [ ] An unknown user and a wrong password return the same error code.
- [ ] A cross-origin POST is rejected, and so is a POST without a CSRF token.

**Tests** `backend/modules/accounts/tests/test_auth.py`, `backend/domain/auth/tests/test_password_policy.py`

#### P1-T04 · Invitations, password reset and email
**Owner** 🤖 · **SRS** FR-AUTH-001, FR-AUTH-006, SW-006 · **Depends on** P1-T03 · **Est.** 1 d

**Build**
- Invitations: single-use tokens that expire after 7 days [Proposed]. Accepting one sets a password and makes the user `ACTIVE`.
- `forgot` always returns 202. The reset link is single-use and expires after 30 minutes [Proposed]. A reset revokes all other sessions.
- An `email` service on Django's SMTP email backend (Mailpit locally), with localised Django templates (`gettext`). Emails are sent from a Celery task queued with `transaction.on_commit`. Tests use Django's `locmem` backend (`mail.outbox`).

**Acceptance criteria**
- [ ] A reused or expired token is rejected.
- [ ] A password reset revokes existing sessions.
- [ ] An E2E test reads the email from the Mailpit API.

#### P1-T05 · MFA (TOTP) and re-authentication 🔒
**Owner** 🤖 · **SRS** FR-AUTH-007, NFR-SEC-007 · **Depends on** P1-T03 · **Est.** 1.5 d

**Build**
- TOTP enrolment with `pyotp`: the secret is encrypted with AES-GCM using `APP_ENCRYPTION_KEY` (`cryptography`), shown as a QR code, confirmed with a code, and backed by 10 single-use recovery codes stored hashed. Reject a code that was already used in the same time step.
- MFA is required for `SCHOOL_ADMIN` and for operators.
- `POST /auth/reauth` sets `reauth_at`.
- A `@require_recent_auth(minutes=5)` decorator for view actions.

**Acceptance criteria**
- [ ] An administrator without MFA can reach only the MFA-setup endpoints.
- [ ] A sensitive endpoint called without recent authentication returns 401 `reauth_required`.
- [ ] A recovery code works only once.

#### P1-T06 · Authorisation framework (deny by default) 🔒
**Owner** 🤖 · **SRS** FR-AUTH-005, COM-002, NFR-SEC-003 · **Depends on** P1-T02 · **Est.** 2 d

**Build**
- A permission catalog (Appendix D) as pure code in `backend/domain/permissions`, exposing `can(actor, key, scope)`.
- `@require_permission(key, scope=resolver)` and `@public` decorators for DRF view actions (`core/policy.py`). They attach metadata to the action.
- `PolicyPermission`, the DRF default permission class, which refuses any action without metadata. It implements `has_permission` (role check, 403) and calls the scope resolver for object lookups (404).
- Scope resolvers `school`, `assigned_class_subject`, `own_student` and `own_user`. Each one filters a queryset, so `get_queryset()` and `get_object()` return 404 for out-of-scope records instead of loading them first.
- Status codes: 403 when the role lacks the permission, 404 when the record is out of scope.
- A route-registry test (§9.4) and the start of `backend/tests/security/route_fixtures.py`.

**Acceptance criteria**
- [ ] `[COM-002]`: every route is `@public` or has a permission, and adding an undecorated route makes the test fail.
- [ ] `[FR-AUTH-005]`: a teacher of 9B asking for a 9A resource gets 404 with no hint that it exists.
- [ ] A unit test covers every catalog entry for every role.

#### P1-T07 · Audit log 🔒
**Owner** 🤖 · **SRS** NFR-AUD-001, NFR-AUD-002, NFR-AUD-003 · **Depends on** P1-T02 · **Est.** 1 d

**Build**
- `audit.record(event)` in `modules/audit/services.py` records the fields in §5.4. It must be called inside `transaction.atomic()` and raises if it isn't (`connection.in_atomic_block`).
- A per-school hash chain: `hash = sha256(prev_hash + canonical_json(event))`. Take a per-school advisory lock (`pg_advisory_xact_lock`) while appending so concurrent writes can't fork the chain.
- A `RunSQL` migration that revokes `UPDATE` and `DELETE` on the audit table from `as_app`. `AuditEvent.save()` refuses updates and `delete()` always raises.
- `manage.py verify_audit_chain [--school <slug>]`.
- Audit login success and failure, and authorisation failures. Never record passwords.

**Acceptance criteria**
- [ ] `[NFR-AUD-003]`: a tampered row is detected.
- [ ] An `UPDATE` by the app role fails.
- [ ] A failed login creates an event without any secret in it.

#### P1-T08 · File storage service 🔒
**Owner** 🤖 · **SRS** NFR-SEC-009, NFR-SEC-010, NFR-SEC-011, C-04, DR-005 · **Depends on** P1-T06 · **Est.** 1.5 d

**Build**
- `POST /files` (multipart, DRF `MultiPartParser`) with a 20 MB limit [Proposed] (`DATA_UPLOAD_MAX_MEMORY_SIZE` and `FILE_UPLOAD_MAX_MEMORY_SIZE` set so large files stream to a temp file). Allow PDF, JPEG, PNG and DOCX, checked by magic bytes with `filetype` rather than file extension.
- Store files with boto3 under the random key `schools/{school_id}/{uuid}`, starting in quarantine.
- A Celery scan task that streams the object to ClamAV over the `INSTREAM` protocol (a small client in `modules/files/clamav.py`): clean files become `CLEAN` and available; infected files are deleted and flagged.
- `GET /files/:id/url`: authorises through the policy of the record that owns the file, then returns a presigned GET (`generate_presigned_url`) valid for at most 300 s.
- A structlog processor that redacts URLs and query strings.

**Acceptance criteria**
- [ ] `[NFR-SEC-011]`: the EICAR test file is rejected.
- [ ] `[NFR-SEC-009]`: reading the bucket without a signature returns 403, and a signed URL expires (test with a short TTL).
- [ ] A user without access gets 404.
- [ ] `[NFR-SEC-010]`: signed URLs never appear in logs.

#### P1-T09 · Web shell, auth screens and design basics
**Owner** 🤖 · **SRS** UI-001, UI-002, UI-006, UI-007, FR-AUTH-004, NFR-ACC-001..004, NFR-LOC-001, NFR-LOC-002, NFR-USE-004 · **Depends on** P1-T05, P1-T06 · **Est.** 1.5 d

**Build**
- Layouts for `/app/(admin|teacher|student)` with role navigation and a role switcher.
- Auth pages: login (school, identifier, password), MFA, invitation accept, forgot password and reset.
- Data: the orval-generated TanStack Query hooks, react-hook-form with the generated zod schemas, and next-intl with `en` plus a stub for a second locale. Map problem+json error codes to translated messages.
- Shared components: `OfficialBadge`, `AiBadge`, `EvidenceList`, `DataTable` (accessible), `EmptyState` and `ErrorState`.
- Date and number formatting by school locale and time zone.
- A Playwright helper, `expectNoA11yViolations`.

**Acceptance criteria**
- [ ] `[FR-AUTH-004]`: an E2E test signs in as each seeded role and lands on that role's dashboard.
- [ ] A student who opens `/app/teacher` gets a not-found page.
- [ ] `[NFR-ACC-001]`: the auth pages have no serious or critical axe violations.
- [ ] `[UI-006]`: there is no horizontal scrolling at 360 px.

#### P1-T10 · Observability baseline
**Owner** 🤖 · **SRS** NFR-MNT-005, NFR-AUD-002 · **Depends on** P1-T03 · **Est.** 0.5 d

**Build**
- structlog JSON logs carrying `request_id`, `school_id` and `user_id` (bound from the `RequestContext`, and in Celery tasks from the task's context), with names, emails, tokens and URLs redacted. Route Django's and Celery's own loggers through the same processors.
- `/healthz` (liveness) and `/readyz` (checks the database, Redis and S3).
- sentry-sdk with the Django and Celery integrations, only when `SENTRY_DSN` is set, with `send_default_pii=False`.
- Request latency and job count metrics through django-prometheus and Celery events.

**Acceptance criteria**
- [ ] A redaction unit test passes.
- [ ] `/readyz` returns 503 when the database is down (integration test).

#### P1-T11 · Containerise and deploy staging (walking skeleton)
**Owner** 🤝 · **SRS** COM-001, NFR-SEC-012, NFR-SEC-013 · **Depends on** P1-T09, P1-T10 · **Est.** 1 d

**Build**
- Dockerfiles for `web` (Next.js standalone output) and `api` (Python slim image, `uv sync --frozen --no-dev`, non-root user, gunicorn). The `worker` (`celery -A config worker`) and `beat` (`celery -A config beat`) services use the API image with a different command.
- Staging (§10.6): managed Postgres with point-in-time recovery and the two roles, Redis, a private bucket, TLS, and secrets in the host's secret store. `DJANGO_ADMIN_ENABLED=false`.
- The `deploy-staging` CI job: `manage.py check --deploy`, `manage.py migrate` as the owner role, roll-out and a smoke test.

**Acceptance criteria**
- [ ] The staging URL serves the login page over HTTPS, and the three seeded roles can sign in *(manual)*.
- [ ] Staging holds only synthetic data.
- [ ] A merge to `main` deploys automatically.

**Phase 1 exit criteria (M1)**
- [ ] The walking skeleton is on staging.
- [ ] The route-registry and tenancy tests pass.
- [ ] `verify-audit-chain` passes.
- [ ] A file upload is scanned and served through a signed URL.
- [ ] Coverage is at least 80% in the auth and tenancy modules.
- [ ] The security-reviewer reports PASS on the P1 diff.
- [ ] `/phase-gate P1` reports GO.

---

### Phase 2. Academic structure and school setup (weeks 5–6)

**Objective:** an administrator can set up a real school's structure and people (including by CSV), publish notices, and show a public portal that exposes no student data.
**Milestone:** M2.

#### P2-T01 · Academic structure: domain and API 🔒
**Owner** 🤖 · **SRS** FR-ACAD-001..006, FR-ACAD-008, FR-ADM-003, NFR-LOC-002, DR-004 · **Depends on** P1-T06, P1-T07 · **Est.** 2 d

**Build**
- Models:
  - `AcademicYear`, with at most one ACTIVE year per school.
  - `ClassGroup`, `Subject`, `ClassSubject` and `TeacherAssignment`.
  - `Enrollment`, which automatically creates `SubjectEnrollment` rows for the class's subjects. These can be edited for electives.
  - `Topic`, as a tree.
- School-setting labels, such as "Grade" vs "Class" and whether sections are used.
- CRUD endpoints (Appendix B) behind `academic.manage`. Teachers can add topics under subjects they're assigned to (`topic.manage`).
- Moving a student ends the old enrollment and creates a new one.
- Closing an academic year makes its records read-only.

**Acceptance criteria**
- [ ] `[FR-ACAD-006]` `[DR-004]`: after Sara moves from 9A to 9B, her 9A results stay linked to 9A and to the academic year they were recorded in.
- [ ] `[FR-ACAD-003]`: a closed year rejects writes.
- [ ] Duplicate class subjects and duplicate assignments are rejected.
- [ ] `[FR-ACAD-008]`: a teacher can add a topic to their own subject but gets 404 for another subject.

#### P2-T02 · Admin UI: structure
**Owner** 🤖 · **SRS** FR-ACAD-001..003, FR-ACAD-008, FR-ADM-003 · **Depends on** P2-T01 · **Est.** 1.5 d

**Build**
- `/app/admin/structure` with screens for years, classes and sections, subjects, and a class-by-subject matrix.
- A topic tree editor: add, rename, reorder (with the keyboard too), archive.
- Topic CSV import (Should).

**Acceptance criteria**
- [ ] An E2E test creates a year, Class 9 with sections A and B, Mathematics and Science, and their topic trees.
- [ ] No axe violations.
- [ ] Topics can be reordered using only the keyboard.

#### P2-T03 · People management 🔒
**Owner** 🤖 · **SRS** FR-AUTH-001, FR-AUTH-009, FR-ACAD-004, FR-ACAD-005, FR-ADM-002 · **Depends on** P2-T01, P1-T04 · **Est.** 1.5 d

**Build**
- `/app/admin/people`:
  - a users table with search and filters;
  - invite, deactivate and reactivate;
  - editors for teacher assignments and enrollments.
- Deactivating a user deletes all their sessions immediately.
- Printable credential slips for students without email, each with a one-time invitation code [Proposed].

**Acceptance criteria**
- [ ] `[FR-AUTH-009]`: a deactivated user's next request returns 401.
- [ ] Role changes and deactivations are audited.

#### P2-T04 · Bulk import (CSV/XLSX) 🔒
**Owner** 🤖 · **SRS** FR-AUTH-002, SW-003 · **Depends on** P2-T03 · **Est.** 2 d

**Build**
- Downloadable templates: `students.csv`, `staff.csv`, `enrollments.csv` and `assignments.csv`.
- Parse CSV (the `csv` module, UTF-8 with or without BOM) and XLSX (`openpyxl` in read-only mode, values only, never formulas), then validate:
  - required fields and formats;
  - duplicates within the file and against the database;
  - unknown classes or subjects.
- A dry run that reports errors row by row.
- Commit in one transaction, all-or-nothing by default, with an "import only valid rows" option.
- Re-importing the same file creates no duplicates.
- Audit the summary.

**Acceptance criteria**
- [ ] Fixture files cover 500 valid rows, 25 kinds of invalid row, and duplicates.
- [ ] A 2,000-row import takes under 30 s [Proposed].
- [ ] By default nothing is committed if any row has an error.

#### P2-T05 · School profile and public portal
**Owner** 🤖 · **SRS** FR-PORT-001, FR-PORT-002, FR-PORT-009, FR-PORT-010, FR-ADM-001 · **Depends on** P2-T01, P1-T08 · **Est.** 1 d

**Build**
- The administrator can edit the school's name, description, logo (image only) and contact details.
- `/s/[school]` is server-rendered and shows the profile, public notices and a sign-in button.
- `/s/[school]/login` pre-fills the school.
- An unknown school slug returns 404.

**Acceptance criteria**
- [ ] `[FR-PORT-010]`: the public page's HTML contains no seeded student names or usernames.
- [ ] `[FR-PORT-001]`: each school's portal works at its own address.

#### P2-T06 · Notices
**Owner** 🤖 · **SRS** FR-PORT-003, FR-PORT-004, FR-PORT-005, FR-ADM-004 · **Depends on** P2-T01 · **Est.** 1 d

**Build**
- Notice CRUD with:
  - an audience (the school, a class group or a class subject);
  - visibility (public or signed-in);
  - `publishAt` and `expiresAt`;
  - a status (DRAFT, SCHEDULED, PUBLISHED or ARCHIVED).
- Teachers can post to the class subjects they're assigned.
- `GET /notices/feed` filters by the user's enrollments and assignments.

**Acceptance criteria**
- [ ] `[FR-PORT-005]`: a 9A student sees school notices and 9A notices, but not 9B notices.
- [ ] A scheduled notice stays hidden until `publishAt` (fake clock).

#### P2-T07 · Demo seed (Greenfield School)
**Owner** 🤖 · **SRS** none (test support) · **Depends on** P2-T01..T06 · **Est.** 1 d

**Build**
- An idempotent seed as described in Appendix E: the structure, the users (with the administrator's MFA pre-enrolled for tests), the topic trees and the notices.
- A `--scenario` flag that later phases extend: `core-loop` in P3/P4 and `practice` in P5.

**Acceptance criteria**
- [ ] Running the seed twice creates no duplicates.
- [ ] The E2E tests use only seed fixtures.

**Phase 2 exit criteria (M2)**
- [ ] The E2E test "admin sets up Greenfield from CSV" passes.
- [ ] The notice-targeting and portal personal-data tests pass.
- [ ] Demo to your teacher adviser.
- [ ] `/phase-gate P2` reports GO.

---

### Phase 3. Exams, marks, validation and release (weeks 7–9)

**Objective:** teachers record exams with topics on each question, enter and validate marks, and control exactly what students see.
**Milestone:** M3 (results released to students).

#### P3-T01 · Exam and question model and API 🔒
**Owner** 🤖 · **SRS** FR-EXAM-001, FR-EXAM-002, FR-EXAM-003, FR-AIREL-007 · **Depends on** P2-T01 · **Est.** 1.5 d

**Build**
- The `Exam`, `Question` and `QuestionTopic` models in §5.4.
- The exam lifecycle in §4.4, as a pure state machine in `backend/domain/exams`.
- The questions' maximum marks must add up to the exam total.
- Questions can be edited in DRAFT. Once marks exist, structural edits return 409 with guidance.
- Topics must belong to the exam's subject, and only teachers set them. No AI classification happens in R1.

**Acceptance criteria**
- [ ] The transition-table test covers every from→to pair.
- [ ] A teacher of another class subject gets 404.
- [ ] `[FR-AIREL-007]`: topic tags come only from teacher input.

#### P3-T02 · Exam setup UI
**Owner** 🤖 · **SRS** FR-EXAM-001, FR-EXAM-002, FR-TCH-002 · **Depends on** P3-T01 · **Est.** 1.5 d

**Build**
- An exam list with filters.
- A "New exam" form.
- A fast, keyboard-friendly question table:
  - add and duplicate rows;
  - topic multi-select with search;
  - question type;
  - a live check of the total.
- Marking-scheme text or file, and a publish button.

**Acceptance criteria**
- [ ] An E2E test creates *Term 1 Mathematics* with the 7 questions from Appendix E.
- [ ] No axe violations.
- [ ] A mismatched total blocks publishing and explains why.

#### P3-T03 · Results domain (mark sheet) 🔒
**Owner** 🤖 · **SRS** FR-EXAM-010, FR-EXAM-012, FR-ACAD-007, FR-AIREL-009, NFR-REL-003 · **Depends on** P3-T01 · **Est.** 2 d

**Build**
- `AssessmentResult` and `QuestionMark`, with the result lifecycle in §4.4.
- Pure functions `compute_total`, `validate_mark` (0 ≤ m ≤ max, in steps of 0.25 [Proposed]) and the result transitions, in `backend/domain/results`.
- `GET /exams/:id/mark-sheet`.
- `PATCH /exams/:id/mark-sheet`: batched cell updates that send `expectedVersion`, with 409 on conflict. Use a conditional update (`filter(pk=…, version=expected).update(version=F("version") + 1, …)`) and treat 0 rows updated as a conflict. Load the sheet with `select_related` / `prefetch_related` so the query count doesn't grow with class size (assert it with `django_assert_max_num_queries`).
- An exam with no questions works in total-only mode.
- An enrollment check.
- A result can't become EVALUATED until every question has a mark (or `notAttempted`) or the result is marked absent. Marks are never estimated.

**Acceptance criteria**
- [ ] `[FR-EXAM-012]`: 5.5 marks on a 5-mark question is rejected, and so is −1.
- [ ] `[FR-ACAD-007]`: a student who isn't enrolled gets 422, and no row is created.
- [ ] A concurrent edit gets 409.
- [ ] `[FR-AIREL-009]`: a missing mark blocks EVALUATED.
- [ ] Totals with halves and quarters are exact.

#### P3-T04 · Mark-entry grid UI
**Owner** 🤖 · **SRS** FR-EXAM-010, NFR-REL-002, NFR-PERF-003, NFR-ACC-001 · **Depends on** P3-T03 · **Est.** 2.5 d

**Build**
- `/app/teacher/exams/[id]/marks`: a grid with students as rows and questions plus the total as columns.
- Navigation with the arrow keys, Enter and Tab; type to edit; paste a column from a spreadsheet.
- Inline errors and an absent toggle.
- Autosave 1 s after typing stops and when a cell loses focus, retrying with backoff, with a "Saved · 10:42" indicator.
- A "mark complete" action on each row, and a filter for incomplete rows.

**Acceptance criteria**
- [ ] An E2E test enters Sara's marks with the keyboard only, and they persist after a reload.
- [ ] When the network is offline, edits are queued and retried.
- [ ] The grid uses the proper ARIA grid role and labels.
- [ ] A save budget is noted for P7.

#### P3-T05 · Import marks from CSV/XLSX (Should; first item on the cut list)
**Owner** 🤖 · **SRS** FR-EXAM-011 · **Depends on** P3-T03 · **Est.** 1 d

**Build**
- A per-exam template with a username column plus one column per question.
- A dry run with errors, then commit.

**Acceptance criteria**
- [ ] A cell over the maximum is reported with its row and column.
- [ ] A commit updates only NOT_STARTED and IN_PROGRESS results.

#### P3-T06 · Digital answer scripts (Option B) 🔒
**Owner** 🤖 · **SRS** FR-EXAM-013, FR-EXAM-018 · **Depends on** P1-T08, P3-T03 · **Est.** 1 d

**Build**
- `AnswerScript` uploads, either per student from the grid row or in bulk with the filename set to the username.
- A viewer that uses signed URLs.
- Scripts and manual marks coexist on the same exam.

**Acceptance criteria**
- [ ] A teacher of 9B can't get a 9A script URL (404).
- [ ] A student can't open a script before `scriptReleasedAt` is set.

#### P3-T07 · Teacher feedback
**Owner** 🤖 · **SRS** FR-EXAM-027 · **Depends on** P3-T03 · **Est.** 0.5 d

**Build**
- `TeacherFeedback` for the whole result and for each question, editable from a side panel in the grid.
- Edit history is kept through audit events.

**Acceptance criteria**
- [ ] Feedback is saved.
- [ ] Students can't see it before `commentsReleasedAt`.

#### P3-T08 · Validation (official results) 🔒
**Owner** 🤖 · **SRS** FR-EXAM-020, FR-EXAM-021, NFR-SEC-007, NFR-AUD-001 · **Depends on** P3-T03 · **Est.** 1 d

**Build**
- Validate one result, a selection, or all EVALUATED results. Validating more than one needs recent re-authentication.
- In one transaction: set the status to VALIDATED, record who validated and when, and write an audit event for each result.
- The exam closes automatically once every enrolled student is VALIDATED or absent.

**Acceptance criteria**
- [ ] `[FR-EXAM-020]`: unvalidated marks never appear through official endpoints.
- [ ] Bulk validation without re-authentication returns 401 `reauth_required`.

#### P3-T09 · Amend, release and withdraw 🔒
**Owner** 🤖 · **SRS** FR-EXAM-022, FR-EXAM-023, FR-EXAM-025, COM-003 · **Depends on** P3-T08 · **Est.** 1.5 d

**Build**
- **Amend:**
  - requires a reason of at least 10 characters;
  - writes a `ResultRevision` and increments `version`;
  - writes an audit event with the before and after values;
  - notifies the student if the marks were already released.
- **Release dialog:** choose the students (all or selected) and the components (marks, script, comments, AI feedback).
- **Withdraw:** requires a reason.
- In-app notifications when something is released.

**Acceptance criteria**
- [ ] An amendment without a reason gets 422.
- [ ] The audit event shows the old and new values.
- [ ] `[FR-EXAM-025]`: a withdrawal hides the component from the student immediately (E2E).

#### P3-T10 · Student results through the visibility service 🔒
**Owner** 🤖 · **SRS** FR-EXAM-024, FR-EXAM-028, UI-002, FR-STU-002 · **Depends on** P3-T09 · **Est.** 1.5 d

**Build**
- `VisibilityService`: the only route by which students read results, scripts, comments, and (later) findings and recommendations.
- `/app/student/results` and `/results/[id]`, showing `OfficialBadge`, a per-question breakdown, and a topic summary calculated from the released marks.

**Acceptance criteria**
- [ ] `[FR-EXAM-024]`: the visibility-matrix test passes for all 16 combinations of release timestamps.
- [ ] An unreleased result isn't listed at all.
- [ ] `[UI-002]`: official marks show the official badge.

#### P3-T11 · Integrity guards for official results 🔒
**Owner** 🤖 · **SRS** FR-EXAM-026, DR-001, C-03 · **Depends on** P3-T08 · **Est.** 1 d

**Build**
- import-linter contracts: only `modules.results` may import `modules.results.models` and `modules.results.services`. Other apps read results through `modules.results.selectors`, which return frozen dataclasses rather than model instances.
- A runtime write guard: `AssessmentResult`, `QuestionMark` and `ResultRevision` use a model base and queryset that raise `ResultWriteForbidden` on `save()`, `delete()`, `update()`, `bulk_create()` and `bulk_update()` unless the call runs inside `ResultsService`'s `results_write_scope()` context.
- An architecture test.
- Database CHECK constraints (`Meta.constraints`): `marks_centi >= 0` and `total_centi >= 0`.

**Acceptance criteria**
- [ ] `[FR-EXAM-026]`: a deliberate import of `modules.results.models` from `modules.analysis` fails `lint-imports` (a fixture package in the test).
- [ ] `[FR-EXAM-026]`: saving an `AssessmentResult` outside `ResultsService` raises `ResultWriteForbidden`.
- [ ] An integration test shows that official totals are unchanged after an analysis run. Activate this test in P4.

**Phase 3 exit criteria (M3)**
- [ ] The E2E test for Sara steps 1–3 passes (exam recorded, validated and released).
- [ ] Permission and IDOR tests cover every exam and result route.
- [ ] Validate, amend, release and withdraw are all audited.
- [ ] Your teacher adviser has tried the grid and given feedback.
- [ ] `/phase-gate P3` reports GO.

---
### Phase 4. Assessment intelligence (weeks 10–12)

**Objective:** produce traceable, teacher-reviewed findings at student and class level from validated evidence, explained in plain language. AI is optional and safely contained.
**Milestone:** M4 (findings reviewed and released).

#### P4-T01 · Diagnosis engine (pure)
**Owner** 🤖 · **SRS** FR-AI-005, FR-AI-006, FR-AI-007, FR-AI-008, FR-AI-009, FR-AIREL-009 · **Depends on** P3-T03 · **Est.** 3 d

**Build**
- Implement §6.1 in `backend/domain/diagnosis`:
  - per-topic scores;
  - rules A, B, C, S, T and I;
  - evidence levels;
  - configuration with defaults and bounds;
  - an `engineVersion` constant.
- Output findings with their metrics and evidence references.

**Acceptance criteria**
- [ ] `[FR-AI-005]`: the golden fixture `sara-core` produces exactly the two findings in §6.1.
- [ ] `[FR-AI-007]`: `total-only` produces only INSUFFICIENT_DETAIL.
- [ ] `multi-topic` counts a question in full towards each of its topics.
- [ ] Property tests (Hypothesis):
  - findings never cite questions outside the input;
  - there's no WEAKNESS with fewer than 2 questions in the latest assessment, unless the evidence level is HIGH;
  - multiplying every mark and maximum by the same factor leaves the findings unchanged;
  - reordering questions within an assessment leaves the findings unchanged.
- [ ] Every rule branch is covered.

#### P4-T02 · Class-level aggregation (pure)
**Owner** 🤖 · **SRS** FR-AI-010 · **Depends on** P4-T01 · **Est.** 1 d

**Build**
- Implement §6.2: per-topic mean, distribution and share of weak students, with a flag at share ≥ 0.40 and n ≥ 5.
- Student IDs appear only in the teacher view.

**Acceptance criteria**
- [ ] `[FR-AI-010]`: with `class-9a-triangles`, 13 of 30 students gets the flag and 11 of 30 doesn't.
- [ ] A class with fewer than 5 students with evidence is never flagged.

#### P4-T03 · Analysis runs, jobs and persistence 🔒
**Owner** 🤖 · **SRS** FR-AI-001, FR-AI-004, FR-AI-014, FR-AI-017, NFR-REL-001, NFR-REL-004, NFR-SCAL-003, DR-003 · **Depends on** P4-T01, P4-T02, P3-T08 · **Est.** 2 d

**Build**
- `POST /analysis-runs {examId}` runs for each student and then for the class.
- Before queuing, check the associations and that the results are VALIDATED.
- Build an immutable snapshot with its hash, then queue a Celery task with `transaction.on_commit`: `max_retries=3`, `retry_backoff=True`, `time_limit=60`, `acks_late=True`. The task takes the run ID and the school ID only, and enters `tenant_context` itself.
- The worker runs the engine, optionally asks the AI for wording (P4-T05), and stores the run, findings and evidence in one `transaction.atomic()` block. It locks the run row (`select_for_update`) so a duplicate delivery does nothing.
- A new run supersedes the earlier GENERATED findings for the same student and topic.
- Statuses follow §4.5. On failure the run becomes FAILED and the teacher is notified.

**Acceptance criteria**
- [ ] `[FR-AI-001]`: requesting analysis on an exam with unvalidated results returns 409.
- [ ] `[NFR-REL-001]`: fault injection at the AI step and in the middle of the database write leaves no partial findings, and official results stay byte-identical.
- [ ] Re-running the same snapshot is idempotent.
- [ ] `[FR-EXAM-026]`: the P3-T11 integration test is now active and passes.

#### P4-T04 · AI gateway 🔒
**Owner** 🤖 · **SRS** SW-001, SW-002, FR-AI-013, FR-AI-020, FR-AI-021, FR-AI-023, NFR-SEC-014, NFR-PRIV-005 · **Depends on** P4-T03 · **Est.** 2.5 d

**Build** the `backend/ai` package:
- An `AiProvider` protocol with two implementations:
  - `FakeAiProvider`, which has bad-output modes (§9.5);
  - `AnthropicProvider`, using the `anthropic` Python SDK with the model from `AI_MODEL`, a timeout and a token cap. It requests JSON output, using the SDK's tool or structured-output feature where available, and **always** validates with pydantic.
- Allow-list payload mappers for each task, with pseudonymisation.
- The validators in §6.4.
- An `AiCall` log row.
- The per-school `aiEnabled` setting, a monthly token budget, and the `AI_KILL_SWITCH` variable.

**Acceptance criteria**
- [ ] `[FR-AI-020]`: the property test shows that random names, emails and usernames never appear in a payload.
- [ ] `[FR-AI-013]`: malformed or unfaithful output is rejected, and the template text is used.
- [ ] `[NFR-PRIV-005]`: with `aiEnabled=false`, the provider receives zero calls and findings are still produced.
- [ ] `[SW-002]`: every call records the provider, model and prompt version.

#### P4-T05 · Explanations (template and AI wording)
**Owner** 🤖 · **SRS** FR-AI-006, FR-AI-009, UI-004 · **Depends on** P4-T04 · **Est.** 1 d

**Build**
- Localised templates for every finding type, in student-facing and teacher-facing versions (§6.3).
- The prompt `backend/ai/prompts/explain_findings/v1.md`. Its rules:
  - use only the topics and numbers it is given;
  - hedge the wording;
  - suit the student's grade;
  - at most 80 words per finding;
  - suggest next steps only from the list provided.
- Store the text, its source and the prompt version.

**Acceptance criteria**
- [ ] Snapshot tests for every template in English.
- [ ] Text from the fake AI is stored with `textSource=AI`.
- [ ] Unfaithful text, such as "45%" when the metric is 27%, falls back to the template.

#### P4-T06 · Teacher review workflow 🔒
**Owner** 🤖 · **SRS** FR-AI-014, FR-AI-015, FR-AI-016, FR-AI-018, FR-AIREL-002, FR-AIREL-014, FR-TCH-004 · **Depends on** P4-T05 · **Est.** 2 d

**Build**
- A review queue at `/app/teacher/review`, filterable by exam, class, status, type and evidence level.
- Finding cards show the evidence and metrics. The teacher can:
  - accept;
  - edit, with the original kept;
  - reject, with a reason from a picklist plus free text;
  - rate usefulness from 1 to 5;
  - release in bulk.
- The school's release policy is `REVIEW_REQUIRED` by default, or `AUTO_RELEASE_AFTER_HOURS(n)` (Should, on the cut list). Auto-released items are labelled.
- Every decision is audited and stored for later evaluation.

**Acceptance criteria**
- [ ] State-machine tests cover §4.5.
- [ ] A rejected finding is never visible to the student.
- [ ] An edited finding shows the teacher's text with a "Reviewed by teacher" label, and the original is kept.
- [ ] `[FR-AIREL-002]`: decisions can be exported.

#### P4-T07 · Traceability view
**Owner** 🤖 · **SRS** FR-AI-019, NFR-AUD-004, DR-003 · **Depends on** P4-T06 · **Est.** 1 d

**Build** a finding detail panel showing:
- the evidence items (exam, question numbers, marks out of maximum, date);
- the rules that fired and the metrics;
- the engine version, the AI model and the prompt version;
- the review history.

It must be reachable from the review queue and from the student's profile.

**Acceptance criteria**
- [ ] `[NFR-AUD-004]`: the E2E test reaches the panel in 3 clicks or fewer.
- [ ] If marks were amended after the analysis, the panel shows the snapshot values and flags "evidence changed since analysis".

#### P4-T08 · Student learning-gap report
**Owner** 🤖 · **SRS** FR-STU-003, FR-EXAM-028, UI-002, UI-004 · **Depends on** P4-T06 · **Est.** 1 d

**Build**
- `/app/student/gaps` lists the released weaknesses (sorted as in §6.1) and strengths.
- Each card shows the plain-language text, `AiBadge` or "Reviewed by teacher", a "Why am I seeing this?" evidence list, and a link to the next step. The link is a placeholder until P5.

**Acceptance criteria**
- [ ] Only RELEASED findings are shown (`[FR-EXAM-028]`).
- [ ] INSUFFICIENT_DETAIL appears as a neutral note.
- [ ] No axe violations, and the layout works at 360 px.

#### P4-T09 · Class insights for teachers
**Owner** 🤖 · **SRS** FR-AI-010, FR-TCH-006 · **Depends on** P4-T03 · **Est.** 1.5 d

**Build**
- `/app/teacher/classes/[id]/insights`: a topic table with the mean, percentage flagged and distribution.
- Flagged topics are marked with an icon and text, not just colour.
- Drill down to the questions and students.
- An "Assign class practice" button, connected in P5-T04.

**Acceptance criteria**
- [ ] The fixture shows Triangles as flagged.
- [ ] The table works with a keyboard and a screen reader.
- [ ] Only the teacher's assigned class is shown.

**Phase 4 exit criteria (M4)**
- [ ] The golden fixtures pass.
- [ ] The E2E test for Sara step 4 passes: analysis, review, release, and the student seeing the gap.
- [ ] The AI-disabled path and the personal-data payload test pass.
- [ ] The security-reviewer reports PASS on `analysis` and `ai`.
- [ ] `/phase-gate P4` reports GO.

---

### Phase 5. Learning resources, practice and progress (weeks 13–15)

**Objective:** turn findings into a learning path, targeted practice and a measured reassessment, which closes the loop.
**Milestone:** M5 (core loop).

#### P5-T01 · Learning resources
**Owner** 🤖 · **SRS** FR-RES-001, FR-RES-002 · **Depends on** P2-T01, P1-T08 · **Est.** 1 d

**Build**
- The `Resource` model in §5.4, with HTTPS-only links and files through the file service.
- A school library managed by the administrator, and a teacher page at `/app/teacher/resources`.
- A status of DRAFT, APPROVED or ARCHIVED.

**Acceptance criteria**
- [ ] Only APPROVED resources can be recommended.
- [ ] External links use `rel="noopener noreferrer"` and show an external-link indicator.

#### P5-T02 · Question bank
**Owner** 🤖 · **SRS** FR-RES-008 · **Depends on** P2-T01 · **Est.** 1.5 d

**Build**
- The `QuestionBankItem` model in §5.4, with an answer key validated by type.
- The stem is markdown. The server renders it to HTML and sanitises it with `nh3` on save, and the web shows only that sanitised HTML.
- An editor with preview.
- CSV import (Should, on the cut list).
- Retired items are kept for history.

**Acceptance criteria**
- [ ] An invalid key for a given type is rejected.
- [ ] Retired items are excluded from new tests.
- [ ] An XSS payload in the stem is neutralised.

#### P5-T03 · Recommendation engine (pure) and persistence
**Owner** 🤖 · **SRS** FR-RES-003, FR-RES-004 · **Depends on** P5-T01, P5-T02, P4-T06 · **Est.** 1.5 d

**Build**
- Implement §6.5: for each released weakness, a 6-step path with PROPOSED `Recommendation` rows.
- Reserve the reassessment items.
- When content is missing, create a task for the teacher.

**Acceptance criteria**
- [ ] `[FR-RES-004]`: the Sara fixture produces the six steps in order.
- [ ] Nothing from another grade or subject is recommended.
- [ ] The order is deterministic.
- [ ] Missing content produces the exact shortfall message.

#### P5-T04 · Teacher control and assignment
**Owner** 🤖 · **SRS** FR-RES-005, FR-PRAC-002, FR-PRAC-003, FR-TCH-005 · **Depends on** P5-T03 · **Est.** 1.5 d

**Build**
- Recommendations by student and by class. The teacher can approve, reorder, replace or remove each one.
- Practice rules: number of items, difficulty mix, time limit, attempts and due date.
- Assign to a student, a group or a whole class.
- Notify the students.

**Acceptance criteria**
- [ ] `[FR-RES-005]`: students see only APPROVED recommendations, or auto-approved ones that are labelled.
- [ ] Assignments are audited.

#### P5-T05 · Practice assembly (pure)
**Owner** 🤖 · **SRS** FR-PRAC-001, FR-PRAC-002, FR-PRAC-009 · **Depends on** P5-T02 · **Est.** 1.5 d

**Build**
- Implement §6.6 selection: blueprints, seeded shuffle, quotas, exclusions, disjoint reassessments, and the `INSUFFICIENT_ITEMS` error.

**Acceptance criteria**
- [ ] Property tests show that:
  - quotas are respected;
  - the baseline and reassessment share no items;
  - the same seed gives the same test;
  - a shortfall is reported exactly.
- [ ] With the `practice-bank-forming-eq` fixture (25 items), both the baseline and the reassessment can be built.

#### P5-T06 · Taking practice tests (student)
**Owner** 🤖 · **SRS** FR-PRAC-004, NFR-ACC-006, NFR-REL-002 · **Depends on** P5-T05, P5-T04 · **Est.** 2 d

**Build**
- `/app/student/practice` lists assigned and recommended tests.
- Students can start, read instructions, answer one item per screen or all at once, autosave, resume, and submit after confirming.
- A timer that respects each student's time extension.
- Accessible inputs.

**Acceptance criteria**
- [ ] An E2E test completes an attempt using only the keyboard.
- [ ] A reload in the middle resumes the attempt.
- [ ] `[NFR-ACC-006]`: a time extension is applied.

#### P5-T07 · Automatic scoring and feedback
**Owner** 🤖 · **SRS** FR-PRAC-005, FR-PRAC-007, NFR-PERF-005 · **Depends on** P5-T06 · **Est.** 1 d

**Build**
- Pure scorers for each type (§6.6).
- Feedback on each item: correct or not, the key, and the explanation.
- The attempt score.
- Subjective item types are not offered in R1.

**Acceptance criteria**
- [ ] Scorer unit tests cover empty answers, NaN, Unicode and whitespace.
- [ ] A submitted attempt is scored in under 5 s in the test environment.

#### P5-T08 · Progress records and next step
**Owner** 🤖 · **SRS** FR-PRAC-010, FR-PRAC-011, FR-PRAC-012, UI-005 · **Depends on** P5-T07 · **Est.** 1.5 d

**Build**
- Implement the §6.6 progress labels, next steps and teacher-support flag.
- Use the exam score as the baseline, with LOW comparability, when no quick check was taken.
- Write the student copy that states the comparison basis.

**Acceptance criteria**
- [ ] `[FR-PRAC-010]` `[FR-PRAC-011]`: going from 4/10 to 8/10 gives "Improved on practice, 40% → 80%", and never "mastered".
- [ ] Two later comparable scores at or above baseline + 15 give `CONSISTENT_IMPROVEMENT`.
- [ ] Two reassessments in a row without improvement raise the teacher-support flag.

#### P5-T09 · Close the loop: practice evidence and engagement
**Owner** 🤖 · **SRS** FR-AI-002, FR-RES-006 · **Depends on** P5-T08 · **Est.** 1 d

**Build**
- Scored attempts become PRACTICE evidence for later analysis runs, whether a teacher triggers them or a nightly job runs for students with new evidence [Proposed].
- Record `ResourceEngagement` when a resource is opened and when it's completed, and show it to the teacher.

**Acceptance criteria**
- [ ] A re-run after a reassessment reflects the new evidence (trend or updated finding).
- [ ] Engagement appears in the teacher's view of the student.

#### P5-T10 · Core-loop E2E (Sara)
**Owner** 🤖 · **SRS** SRS §7 end-to-end scenario · **Depends on** P5-T01..T09 · **Est.** 1.5 d

**Build**
- `tests/e2e/core-loop/sara.spec.ts` runs SRS steps 1–7 with teacher and student sessions, using the `core-loop` and `practice` seed scenarios. It answers 4/10 correctly on the baseline and 8/10 on the reassessment.
- It runs in CI on every PR to `main`.

**Acceptance criteria**
- [ ] It passes 10 CI runs in a row, with no flakiness.
- [ ] Runtime is under 4 minutes.

**Phase 5 exit criteria (M5, core loop)**
- [ ] The Sara E2E test passes.
- [ ] `pnpm req:trace --module FR-RES` and `--module FR-PRAC` show every Must/R1 requirement as tested.
- [ ] Your teacher adviser has done a walkthrough.
- [ ] `/phase-gate P5` reports GO.

---

### Phase 6. Dashboards, notifications and reporting (weeks 16–17)

**Objective:** make the loop easy to use every day, with role dashboards that connect a result to its explanation and the next action, plus oversight for administrators.
**Milestone:** M6 (feature complete).

#### P6-T01 · Student dashboard
**Owner** 🤖 · **SRS** FR-STU-001, FR-STU-002, FR-STU-003, FR-STU-004, FR-STU-005, FR-STU-006, FR-STU-007, UI-003, UI-005, NFR-ACC-005 · **Depends on** P5-T10 · **Est.** 2.5 d

**Build**
- The `/app/student` overview shows:
  - subjects;
  - recent released results;
  - upcoming exams (PUBLISHED, in the future, with `announce` on);
  - notices;
  - a "Next step" card.
- `/plan` (learning plan) and `/progress`: trend charts by subject and topic, each with a table alternative.

**Acceptance criteria**
- [ ] `[UI-003]`: an E2E test gets from a result to its gap and then to practice in no more than 2 navigation steps.
- [ ] Every chart can be switched to a table.
- [ ] `[FR-STU-006]`: students see only their own data.
- [ ] Works at 360 px.

#### P6-T02 · Teacher dashboard
**Owner** 🤖 · **SRS** FR-TCH-001, FR-TCH-002, FR-TCH-003, FR-TCH-004, FR-TCH-005, FR-TCH-006, FR-TCH-009 · **Depends on** P5-T10 · **Est.** 2 d

**Build**
- `/app/teacher` shows:
  - the teacher's class subjects;
  - queues for marks to validate, findings to review, unreleased results and practice awaiting attention;
  - students flagged for support;
  - release status for each exam.
- A student progress page.

**Acceptance criteria**
- [ ] `[FR-TCH-001]`: only assigned data is shown (integration test).
- [ ] Queue counts match the queues.

#### P6-T03 · Admin dashboard, reports and audit viewer 🔒
**Owner** 🤖 · **SRS** FR-ADM-001..008 · **Depends on** P5-T10 · **Est.** 2 d

**Build**
- A `/app/admin` overview with:
  - a setup checklist;
  - usage figures: active users over 7 and 30 days, exams created, validated and released, findings reviewed, and practice attempts;
  - academic activity by class subject, without student identities unless `adminCanViewStudentResults` is on.
- An audit viewer with filters and CSV export. Exporting requires re-authentication and is itself audited.
- A "My activity" page where teachers see their own audit events.

**Acceptance criteria**
- [ ] `[FR-ADM-007]`: with the setting off, no admin endpoint returns marks for an individual student (test).
- [ ] Exports are audited.

#### P6-T04 · Notifications
**Owner** 🤖 · **SRS** COM-003, SW-006 · **Depends on** P3-T09, P4-T06, P5-T04 · **Est.** 1 d

**Build**
- A notification centre with a bell, a list and mark-as-read.
- Events: results released, findings released, practice assigned or due, and the teacher-support flag.
- Email for invitations and password resets. Release emails depend on a school setting.

**Acceptance criteria**
- [ ] Exactly one notification is created per event (idempotency key).
- [ ] The unread count is correct.

#### P6-T05 · School settings 🔒
**Owner** 🤖 · **SRS** FR-ADM-005, NFR-PRIV-005, FR-AI-016, FR-ADM-007 · **Depends on** P4-T06 · **Est.** 1 d

**Build** `/app/admin/settings` for:
- whether AI is enabled;
- the AI release policy;
- diagnosis and class thresholds, within fixed bounds;
- whether administrators can see individual students' results;
- locale, time zone and labels.

Validate with a pydantic settings model (fixed bounds) behind the DRF serializer, and audit every change.

**Acceptance criteria**
- [ ] Out-of-range values are rejected.
- [ ] Changes apply only from the next analysis run, which records them in `config`.

#### P6-T06 · Portal: signed-in home and resource links
**Owner** 🤖 · **SRS** FR-PORT-005, FR-PORT-007 · **Depends on** P5-T01, P2-T06 · **Est.** 0.5 d

**Build**
- A signed-in portal home for every role that brings together notices and shared resource links (`showOnPortal`).

**Acceptance criteria**
- [ ] Students see resources only for their own classes.
- [ ] The public page is unaffected.

#### P6-T07 · UX polish and copy review
**Owner** 🤝 · **SRS** NFR-USE-004, UI-004, UI-007 · **Depends on** P6-T01..T06 · **Est.** 1 d

**Build**
- Consistent empty, loading and error states.
- Review the copy for plain language at the student's reading level.
- A `scripts/i18n-check.ts` that makes CI fail on missing keys.
- An ESLint rule against hard-coded strings in JSX.
- Add a second locale if one was decided.

**Acceptance criteria**
- [ ] The i18n check passes.
- [ ] No hard-coded user-facing strings remain.

**Phase 6 exit criteria (M6, feature complete)**
- [ ] `pnpm req:trace --release R1 --priority M` shows every FR and UI requirement as tested.
- [ ] A usability dry run with 2 teachers and 2 students has been done, with findings logged.
- [ ] The known-issues list is up to date.
- [ ] `/phase-gate P6` reports GO.

---

### Phase 7. Hardening (weeks 18–20)

**Objective:** prove the system is secure, private, fast, accessible and recoverable before any real student data goes in.
**Milestone:** M7 (release candidate).

#### P7-T01 · Security verification (ASVS L2) 🔒
**Owner** 🤝 · **SRS** NFR-SEC-001, NFR-SEC-015, NFR-SEC-005..011 · **Depends on** P6-T07 (M6) · **Est.** 2.5 d

**Build**
- `docs/security/asvs-l2.md`: the ASVS Level 2 checklist with evidence for each item, and a justification for any N/A.
- Security headers: CSP with nonces, HSTS, `frame-ancestors 'none'`, Referrer-Policy and Permissions-Policy.
- A weekly ZAP baseline scan against staging in CI.
- Clean dependency and secret scans.
- Book an external penetration test before P8-T04.

**Acceptance criteria**
- [ ] No unresolved High or Medium ZAP findings.
- [ ] The ASVS checklist is complete.
- [ ] The security-reviewer sweep reports PASS for every module.

#### P7-T02 · Postgres row-level security (defence in depth) 🔒
**Owner** 🤖 · **SRS** NFR-SEC-002, NFR-SEC-003, DR-002 · **Depends on** P7-T01 · **Est.** 2 d

**Build**
- A migration (run as `as_owner`) that turns on RLS for every `TENANT_MODELS` table with `ENABLE` and `FORCE ROW LEVEL SECURITY`, and the policy `school_id = current_setting('app.school_id', true)::uuid`. Generate it from the registry, and add a test that fails when a tenant table has no policy.
- The `as_app` role must not have BYPASSRLS and must not own the tables.
- Each request runs in a transaction (a middleware wrapping the view in `transaction.atomic()`, or `ATOMIC_REQUESTS = True`) that starts with `SELECT set_config('app.school_id', %s, true)`. `tenant_context()` does the same for Celery tasks and management commands. The setting is transaction-local, so it is safe with the connection pool and PgBouncer.
- `system_scope(reason)` uses a separate database alias with a role that has BYPASSRLS, and every bypass is audited.

**Acceptance criteria**
- [ ] Raw `SELECT * FROM exams` as the app role, without the setting, returns 0 rows.
- [ ] The full test suite passes with RLS on.
- [ ] The 95th-percentile slowdown is under 15% [Proposed].

#### P7-T03 · Exhaustive cross-tenant and cross-role tests 🔒
**Owner** 🤖 · **SRS** NFR-SEC-004 · **Depends on** P7-T02 · **Est.** 1.5 d

**Build**
- Complete the IDOR generator in §9.4 so it covers every route.
- CI publishes a report artifact.

**Acceptance criteria**
- [ ] `[NFR-SEC-004]`: zero unexpected allows.
- [ ] A new route without a fixture factory fails the suite.

#### P7-T04 · Privacy controls 🔒
**Owner** 🤝 · **SRS** NFR-PRIV-001, NFR-PRIV-002, NFR-PRIV-003, NFR-PRIV-004, NFR-PRIV-006, NFR-PRIV-007 · **Depends on** P6-T07 (M6) · **Est.** 2.5 d

**Build**
- `docs/privacy/data-inventory.md`, listing each field with its purpose, retention period and processor.
- Retention settings for each record type, and a nightly purge job with a dry-run mode and an audit summary.
- Deleting a student and offboarding a school: removes database rows, files, derived findings and AI logs, after confirmation, with an audit record.
- A consent or authorisation status for each student.
- `SupportAccessGrant` (school-approved, at most 24 h, scoped and audited).
- A register of data processors.

**Acceptance criteria**
- [ ] `[NFR-PRIV-003]`: after deletion, no rows or files refer to the student, except anonymised audit stubs where policy requires them.
- [ ] `[NFR-PRIV-006]`: an operator without a grant can't read tenant data.

#### P7-T05 · Performance and scale
**Owner** 🤖 · **SRS** NFR-PERF-001..006, NFR-SCAL-001, NFR-SCAL-003 · **Depends on** P6-T07 (M6) · **Est.** 2 d

**Build**
- A large synthetic seed.
- k6 scenarios: login, student dashboard, review queue, saving a 60 × 20 mark sheet, and submitting practice.
- Thresholds from the SRS.
- `EXPLAIN ANALYZE` on the busiest queries (`QuerySet.explain(analyze=True)`), then add indexes and caching as needed. Add query-count assertions to the busiest endpoints to catch N+1 queries.
- Tune gunicorn workers and threads, and the database pool size, for the staging instance size.
- Lighthouse CI on the key pages.
- A bundle budget of 1.5 MB or less for the student dashboard.

**Acceptance criteria**
- [ ] The k6 thresholds pass at the target load, or at a documented proportional load on staging-sized infrastructure.
- [ ] The report is saved in `docs/perf/`.

#### P7-T06 · Accessibility audit
**Owner** 🤝 · **SRS** NFR-ACC-001..007 · **Depends on** P6-T07 (M6) · **Est.** 1.5 d

**Build**
- Run axe on every route with a seeded Playwright crawl.
- Do a manual keyboard pass and a screen-reader pass (NVDA or VoiceOver) on the core flows.
- Check WCAG 2.2 success criteria 2.4.11, 2.5.8 and 3.3.8.
- Write `docs/a11y/report.md`.

**Acceptance criteria**
- [ ] No serious or critical axe violations.
- [ ] Every item on the manual checklist passes, or has a justification.

#### P7-T07 · Reliability, backups and operations
**Owner** 🤝 · **SRS** NFR-AVL-001..005, NFR-REL-001..004, NFR-MNT-005 · **Depends on** P6-T07 (M6) · **Est.** 1.5 d

**Build**
- Point-in-time recovery plus daily backups.
- A restore drill into a new instance, measuring RPO and RTO.
- Alerts for 5xx rate, 95th-percentile latency, AI failure rate, queue depth and disk.
- Uptime checks.
- Runbooks for incidents, restores, key rotation, AI outages (kill switch) and maintenance mode.
- A degradation test: with the AI provider down, every non-AI flow still works.

**Acceptance criteria**
- [ ] The drill records RPO ≤ 1 h and RTO ≤ 8 h.
- [ ] A test alert fires within 5 minutes.
- [ ] `[NFR-AVL-005]`: the degradation test passes.

#### P7-T08 · AI safety and evaluation readiness 🔒
**Owner** 🤝 · **SRS** FR-AIREL-001, FR-AIREL-002, FR-AIREL-003, FR-AIREL-014, FR-AI-023, NFR-PRIV-010 · **Depends on** P4-T06 · **Est.** 1 d

**Build**
- `pnpm eval:ai` (§9.5).
- A reference-dataset export: pseudonymised validated marks plus teacher decisions, for R2.
- A correction-rate report covering accept, edit and reject rates by finding type (the R1 part of FR-AIREL-003).
- An AI risk assessment covering Govern, Map, Measure and Manage.
- Confirm and record the provider's terms: no training on submitted data, retention, and region.

**Acceptance criteria**
- [ ] The eval report shows no unfaithful text reaching storage.
- [ ] The export contains no direct identifiers (test).
- [ ] The provider's terms are recorded in `docs/verification/manual.md`.

#### P7-T09 · Release candidate
**Owner** 🤖 · **SRS** all R1 · **Depends on** P7-T01..T08 · **Est.** 0.5 d

**Build**
- Tag `v1.0.0-rc.1` and write a changelog.
- Run the full regression: unit, integration, E2E, accessibility and load.
- Run `pnpm req:trace --release R1 --fail-on-missing` and `/phase-gate P7`.

**Acceptance criteria**
- [ ] `docs/gates/P7.md` says **GO**.

**Phase 7 exit criteria (M7)**
- [ ] Every hardening acceptance criterion is met.
- [ ] Requirement trace is at 100% for Must/R1, counting tests and manual records.
- [ ] The release candidate is tagged.

---

### Phase 8. Pilot and launch (weeks 21–24)

**Objective:** run AS safely at a real school, learn from real use, and sign off R1.
**Milestone:** M8 (pilot live).

#### P8-T01 · Legal and compliance gate (G-LEGAL)
**Owner** 🧑 (with legal advice) · **SRS** OI-01, OI-02, OI-03, NFR-PRIV-002, NFR-PRIV-007, NFR-PRIV-010 · **Depends on** P0-T04 (started in week 1) · **Est.** 1 d of your time in this phase

**Build**
- Confirm the jurisdiction and the law that applies.
- Sign a data-processing agreement with the school.
- Settle the consent or authorisation model and configure the retention periods.
- Sign off the DPIA and the AI risk assessment.
- Publish a privacy notice for students and parents.
- Agree incident contacts.

**Acceptance criteria**
- [ ] The signed documents are stored, and the settings match the decisions *(manual)*.
- [ ] ⛔ **No real student data goes in until this passes.**

#### P8-T02 · Production environment
**Owner** 🤝 · **SRS** COM-001, NFR-SEC-012, NFR-SEC-013, NFR-AVL-003 · **Depends on** P7-T09, P8-T01 · **Est.** 2 d

**Build**
- Production infrastructure in the region chosen under OI-10, with its own accounts and secrets.
- Point-in-time recovery, monitoring and alerts, a WAF and rate limits, the domain and TLS.
- Deploy the release candidate and run smoke tests.

**Acceptance criteria**
- [ ] The production checklist (§10.6) is complete.
- [ ] A production backup has been restored into an isolated environment *(manual)*.

#### P8-T03 · UAT with pilot teachers (staging, synthetic data)
**Owner** 🤝 · **SRS** NFR-USE-001, NFR-USE-002 · **Depends on** P7-T09 · **Est.** 4 d

**Build**
- Run the UAT scripts in Appendix F with 2–4 teachers and 4–8 students, and time the tasks.
- Triage what you find. Fix every Severity 1 and 2 issue before go-live.

**Acceptance criteria**
- [ ] Every UAT script passes or has an accepted workaround.
- [ ] The usability targets are met, or improvements are scheduled *(manual)*.

#### P8-T04 · Pilot onboarding
**Owner** 🤝 · **SRS** FR-AUTH-002, SW-003 · **Depends on** P8-T02, P8-T03 · **Est.** 3 d

**Build**
- Provision the school.
- The administrator imports users, with your support.
- Run a 45-minute teacher training session, and write `docs/guides/teacher.md` and `docs/guides/student.md`.
- Hand out credential slips.
- Set up a support channel with agreed response times (§14).

**Acceptance criteria**
- [ ] At least 90% of pilot users are activated [Proposed].
- [ ] A teacher creates the first exam without help *(manual)*.

#### P8-T05 · Hypercare during the first exam cycle
**Owner** 🤝 · **SRS** NFR-AVL-001 · **Depends on** P8-T04 · **Est.** 8 d (spread across the period)

**Build**
- Review system health daily and check in with teachers weekly.
- Fix bugs through the normal task loop; hotfix branches go through CI.
- Fill in the pilot KPI dashboard (§2.3), and monitor AI usage and cost.

**Acceptance criteria**
- [ ] No Severity 1 issues are open.
- [ ] KPIs have been collected for the first cycle.

#### P8-T06 · Sign off R1 and hold a retrospective
**Owner** 🤝 · **SRS** OI-12, OI-13 · **Depends on** P8-T05 · **Est.** 2 d

**Build**
- Compare the KPI snapshot with the targets.
- Collect AI review statistics: acceptance, edit and rejection rates, and usefulness ratings.
- Update the SRS open issues and the thresholds.
- Prioritise R2 and tag `v1.0.0`.

**Acceptance criteria**
- [ ] `docs/releases/R1-signoff.md` is approved *(manual)*.

**Phase 8 exit criteria (M8)**
- [ ] The pilot is live.
- [ ] The first real exam cycle has gone through AS.
- [ ] No Severity 1 issues are open.
- [ ] R1 is signed off.

---

## 14. Pilot plan

| Item | Plan |
|---|---|
| Scope | 1 school, 2–4 teachers, 1–2 classes, starting with Mathematics (Science is optional). Run at least one full exam cycle, then continue through the term in parallel with R2 |
| Roles | **You:** product owner and on-call. **School coordinator:** the administrator and the school's single point of contact. **Teachers:** run exams in AS and give weekly feedback |
| Data | Real data only after G-LEGAL (P8-T01). Staging always holds synthetic data |
| Training | A 45-minute teacher session (create exam → grid → validate → release → review findings → assign practice), plus a 10-minute student walkthrough. Guides go in `docs/guides/` |
| Support | Severity 1 (data exposure, login down, wrong official marks): respond within 2 h and fix immediately. Severity 2 (blocked workflow): respond within 1 working day. Severity 3: next sprint [Proposed] |
| Feedback | Weekly 20-minute teacher check-in, usefulness ratings on findings, an in-app feedback link, and anonymised usage metrics |
| Exit or continue | Continue into R2 if the KPIs in §2.3 are mostly met, there are no open Severity 1 issues, and teachers want to keep going |

---

## 15. Release 2 and Release 3 roadmap

R2 runs from week 25 to week 40 and is outlined here. Expand each phase into full tasks before it starts, using the same format as §13.

| Phase | Weeks | Key tasks | SRS |
|---|---|---|---|
| **P9 Scanned scripts (Option C)** | 25–28 | Bulk PDF/image upload with resumable transfers. Page splitting. **Printable cover sheets with a QR code per student and exam**, used for page-to-student matching, with human confirmation for low-confidence matches. Legibility checks that send scripts to manual review. Larger file limits | FR-EXAM-014, FR-EXAM-015, FR-EXAM-016, HW-001, NFR-PERF-007, FR-AIREL-010 |
| **P10 AI evaluation harness** | 29–31 | Tools for the reference dataset. Metrics: exact and adjacent agreement, QWK, MAE, SMD and maximum error, reported per question type and subject. A monthly quality report. A CI gate when the prompt or model changes | FR-AIREL-003, FR-AIREL-004, FR-AIREL-005, FR-AIREL-012, FR-AIREL-013, NFR-PRIV-009 |
| **P11 AI-assisted marking pilot (gated)** | 32–35 | OCR/handwriting recognition through the provider, with redacted crops. AI-suggested marks per question with confidence, stored as `AiMarkSuggestion` and **never** in official tables. A side-by-side verification UI. Switched on only per subject and question type once the gates pass | FR-EXAM-017, FR-AIREL-004, FR-AIREL-008, FR-AI-003, FR-AI-022 |
| **P12 Content and analytics expansion** | 36–40 | AI-drafted explanations and questions, reviewed by teachers. Teacher-marked subjective practice. Before/after class comparisons. Richer analytics. Mock exams. Exports. Portal extensions. Optional teacher MFA. Data residency | FR-RES-007, FR-PRAC-006, FR-PRAC-008, FR-PRAC-013, FR-AI-011, FR-TCH-007, FR-TCH-008, SW-004, NFR-PRIV-008, FR-PORT-006, FR-PORT-008, FR-PORT-011, FR-AUTH-008, FR-EXAM-004, FR-ADM-009, NFR-LOC-003, NFR-SCAL-002, NFR-MNT-003, NFR-USE-003 |

**AI-marking gate** (from SRS FR-AIREL-004, still [Proposed]). It is checked separately for each subject and question type against teacher-validated reference data:

- QWK ≥ 0.70;
- |SMD| ≤ 0.15;
- AI–human QWK is no more than 0.10 below human–human QWK;
- at most 2% of items differ from the teacher's mark by more than 20% of the item's maximum.

The metric code in `backend/domain/metrics` must reproduce these values (tests may cross-check against `sklearn.metrics.cohen_kappa_score(weights="quadratic")` as a dev-only dependency):

| Human marks | AI marks | QWK |
|---|---|---|
| `[0,1,2,3,4,4,2,1]` | `[0,2,2,3,3,4,1,1]` | 0.888889 (8/9), with MAE 0.375, exact agreement 62.5%, adjacent agreement 100% and SMD (AI − human, pooled SD) −0.0902 |
| `[1,2,3,4,5]` | `[1,2,3,4,4]` | 0.941176 (16/17) |
| `[0,1,2,3]` | `[0,1,2,3]` | 1.0 (identical) |
| `[0,0,1,1,2,2]` | `[2,2,1,1,0,0]` | −1.0 (reversed) |

**Release 3** (late 2027 onwards):

- Advanced handwritten-answer evaluation, wherever the gates are met.
- Longitudinal mastery models (FR-AI-012).
- SSO (FR-AUTH-010) and roster integrations (SW-005).
- A parent portal (FR-AUTH-011, OI-05).
- Multi-pass consistency checks (FR-AIREL-011) and subgroup fairness checks (FR-AIREL-006).
- Pluggable resource formats (FR-RES-009) and custom roles.

---

## 16. Risks and mitigations

| # | Risk | Likelihood / impact | Mitigation | Owner |
|---|---|---|---|---|
| R1 | Scope creep into general school management | M / H | The SRS sets the boundary, the cut list (§12.5) applies, and every new idea goes to the R2/R3 backlog first | You |
| R2 | Legal requirements unclear | M / H | Start the legal track in week 1. The G-LEGAL gate comes before real data. The design allows configurable retention and consent | You |
| R3 | AI produces unfaithful or harmful text | M / H | Deterministic diagnosis, validators, template fallback, teacher review by default, labels, evals | Claude + you |
| R4 | Teachers don't tag questions with topics, so there's little diagnosis | H / H | Make tagging fast (P3-T02), show the "insufficient detail" note, track the ≥ 80% KPI, and train teachers | You |
| R5 | Extra workload for teachers | M / H | Keyboard-first grid, CSV import, bulk actions, timed UAT, and measuring the time to validate | You |
| R6 | Data leaking between schools or roles | L / Critical | `TenantModel` scoped managers, RLS, deny-by-default `PolicyPermission`, Django admin off in production, IDOR generator, security-reviewer, penetration test | Claude + you |
| R7 | One developer's limited capacity, or poor generated code | M / M | Small tasks, tests first, reviewers, phase gates, maintaining `CLAUDE.md`, and the cut list | You |
| R8 | Not enough question-bank content | H / M | Seed items, teacher authoring, AI drafts with review in R2, and shortfall alerts | You + teachers |
| R9 | Low bandwidth or old devices at schools | M / M | Bundle budget, mobile-first student UI, autosave and resume | Claude |
| R10 | AI provider outage, cost or terms change | M / M | Gateway abstraction, fake and disabled modes, budgets, kill switch, and templates that always work | You |
| R11 | Bad data imported | M / M | Dry runs, row-level errors, all-or-nothing commits, audited imports | Claude |
| R12 | An infrastructure component is abandoned (for example, MinIO's community edition was archived) | L / M | Code against standard S3 APIs, pin versions, and record choices in ADRs | You |
| R13 | The Python API and the TypeScript web app drift apart | M / M | OpenAPI schema generated from the serializers, a generated web client, a CI drift check, contract checks in integration tests, and E2E tests | Claude |
| R14 | Django ORM shortcuts bypass tenancy (raw SQL, unscoped managers, Django admin) | M / H | Scoped default and base managers, Ruff banned-API rules, admin disabled outside local development, RLS in P7, security-reviewer | Claude + you |

---
## Appendix A. Claude Code kit

P0-T03 creates these files exactly as written. Each heading gives the file's path. They follow the official Claude Code documentation: project memory in `CLAUDE.md`, path-scoped rules in `.claude/rules/`, skills in `.claude/skills/<name>/SKILL.md`, subagents in `.claude/agents/<name>.md`, and permissions and hooks in `.claude/settings.json`. Hook scripts are written in Node.js so they also work on Windows (through Git Bash or WSL).

### A.1 `CLAUDE.md`

```markdown
# AS — AI-Powered Academic Assessment and School Platform

Multi-tenant school platform. Loop: teacher records exam → validates marks (official) → deterministic diagnosis finds likely weak topics → teacher reviews → student gets resources, targeted practice and a measured reassessment.

## Read on demand (never `@import` these — they are large)
- Task specs: `docs/BUILD_PLAN.md`. Find a task with `grep -n "^#### P3-T04" docs/BUILD_PLAN.md` and read only that section. Algorithms §6, conventions §8, testing §9.
- Requirements: `docs/SRS.md` (IDs like FR-EXAM-026). Status: `docs/PROGRESS.md`. Decisions: `docs/adr/`.

## Stack
Back end: `backend/` Django 5.2 + DRF, REST `/api/v1`, PostgreSQL (psycopg 3), Celery + beat on Redis, managed with uv. One Django app per module in `backend/modules/<name>/` (models, selectors = reads, services = writes, serializers, views, urls, permissions, tasks). `backend/core` = tenancy, policy, errors, clock, logging. `backend/domain` = pure Python logic (no Django, no I/O). `backend/ai` = AI gateway. `backend/openapi.yaml` is generated by drf-spectacular.
Web: `apps/web` Next.js App Router + Tailwind + shadcn/ui + TanStack Query + next-intl; API client generated by orval into `apps/web/src/api/generated` (never edit by hand). pnpm. S3-compatible storage (SeaweedFS locally), ClamAV, Mailpit via docker compose.

## Commands
- `docker compose up -d` then `pnpm dev` (web :3000, Django :8000 behind `/api`, Celery worker)
- `pnpm verify` — Ruff + mypy + import-linter + migrations check + OpenAPI drift + pytest + web lint/typecheck/Vitest. Must pass before a task is done.
- Unit test: `uv run --directory backend pytest domain -k "<name>"`
- Integration: `uv run --directory backend pytest modules/<app>/tests/<file>.py`
- E2E: `pnpm --filter @as/e2e exec playwright test <spec>`
- DB: `pnpm db:makemigrations <app> --name <change>` · `pnpm db:migrate` · `pnpm db:seed` · `pnpm db:reset` (ask first)
- After changing a serializer or URL: `pnpm api:schema`
- Requirement coverage: `pnpm req:trace --release R1`

## Non-negotiable rules
1. IMPORTANT: official marks change ONLY via `ResultsService` (`modules/results/services.py`) through a teacher action. Analysis/AI code never imports `results.models` or `results.services` (FR-EXAM-026).
2. Tenant = `ctx().school_id` from the session, never from request input. Tenant models inherit `TenantModel` and are queried through `objects` (scoped). `all_schools` only inside `system_scope(reason)`. No raw SQL.
3. Every view action has `@require_permission(...)` or `@public`. Out-of-scope records return 404.
4. Validate/amend/release/withdraw, finding review/release, role/setting changes, exports and deletions call `audit.record(...)` inside the same `transaction.atomic()`.
5. Student-facing reads go through `VisibilityService`; nothing unreleased reaches a student.
6. Weak/strong topics are decided by deterministic code in `backend/domain/diagnosis`. The LLM only words existing findings, via the `backend/ai` gateway, with allow-listed, pseudonymised payloads.
7. Tests never call a real AI API. Use `FakeAiProvider`.
8. AI-generated text is always shown with `<AiBadge>`; official marks with `<OfficialBadge>`.
9. Marks are integers in hundredths (`marks_centi`; 2.5 marks = 250). No float maths on marks.
10. Never put real student data in code, fixtures, prompts, screenshots or logs. Use the Greenfield seed.

## Workflow
- One task per session (`/task <ID>`); `/clear` between tasks.
- Failing tests first; tag them with the requirement or task ID: `@pytest.mark.req("FR-EXAM-026")` in Python, `test('[FR-EXAM-026] …')` in TypeScript.
- Fix root causes. Never skip, weaken or delete a test to get green.
- Never edit a committed migration; create a new one.
- Commit per task: `P3-T04: <title>`. Don't push unless asked.
- If CLAUDE.md, the plan, the SRS and the code disagree: stop and ask.

## Compaction
When compacting, keep: current task ID, files changed, failing tests with their errors, decisions taken, next steps.
```

### A.2 `.claude/settings.json`

Rules are checked deny first, then ask, then allow. Adjust them later with `/permissions`.

```json
{
  "permissions": {
    "allow": [
      "Bash(pnpm verify*)",
      "Bash(pnpm lint*)",
      "Bash(pnpm typecheck*)",
      "Bash(pnpm test*)",
      "Bash(pnpm build*)",
      "Bash(pnpm db:makemigrations*)",
      "Bash(pnpm db:migrate*)",
      "Bash(pnpm db:seed*)",
      "Bash(pnpm api:schema*)",
      "Bash(pnpm req*)",
      "Bash(pnpm format*)",
      "Bash(pnpm --filter * exec vitest *)",
      "Bash(pnpm --filter * exec playwright *)",
      "Bash(pnpm --filter * exec tsc *)",
      "Bash(uv run --directory backend pytest*)",
      "Bash(uv run --directory backend ruff *)",
      "Bash(uv run --directory backend mypy*)",
      "Bash(uv run --directory backend lint-imports*)",
      "Bash(uv run --directory backend python manage.py check*)",
      "Bash(uv run --directory backend python manage.py makemigrations*)",
      "Bash(uv run --directory backend python manage.py showmigrations*)",
      "Bash(uv run --directory backend python manage.py sqlmigrate*)",
      "Bash(uv run --directory backend python manage.py spectacular*)",
      "Bash(uv sync*)",
      "Bash(docker compose *)",
      "Bash(git status*)",
      "Bash(git diff*)",
      "Bash(git log*)",
      "Bash(git show*)",
      "Bash(git add *)",
      "Bash(git commit *)",
      "Bash(git switch *)",
      "Bash(git branch*)"
    ],
    "ask": [
      "Bash(uv add *)",
      "Bash(uv remove *)",
      "Bash(uv lock --upgrade*)",
      "Bash(pnpm add *)",
      "Bash(pnpm remove *)",
      "Bash(pnpm dlx *)",
      "Bash(pnpm --filter * add *)",
      "Bash(pnpm --filter * remove *)",
      "Bash(pnpm db:reset*)",
      "Bash(uv run --directory backend python manage.py flush*)",
      "Bash(uv run --directory backend python manage.py shell*)",
      "Bash(uv run --directory backend python manage.py dbshell*)",
      "Bash(docker compose down -v*)",
      "Bash(git push *)",
      "Bash(git reset *)",
      "Bash(git rebase *)"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./.env.local)",
      "Read(./.env.test)",
      "Read(./.env.staging)",
      "Read(./.env.production)",
      "Read(./backend/.env)",
      "Bash(git push --force*)",
      "Bash(git push -f*)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "node \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect-files.mjs" }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "node \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/format-file.mjs" }
        ]
      }
    ]
  }
}
```

### A.3 Hook scripts

The hooks are written in Node.js, which is installed for the web app anyway, so they work the same on Windows, macOS and Linux.

`.claude/hooks/protect-files.mjs`. It blocks edits by exiting with code 2; Claude receives the message as feedback.

```js
#!/usr/bin/env node
// PreToolUse (Edit|Write): block edits to secret env files, the SRS, committed migrations and generated code.
import { execFileSync } from 'node:child_process';
import path from 'node:path';

const chunks = [];
for await (const chunk of process.stdin) chunks.push(chunk);
let input = {};
try { input = JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}'); } catch { process.exit(0); }

const filePath = input?.tool_input?.file_path;
if (!filePath) process.exit(0);

const root = process.env.CLAUDE_PROJECT_DIR || process.cwd();
const rel = path.relative(root, path.resolve(root, filePath)).split(path.sep).join('/');
const base = path.posix.basename(rel);

function block(reason) {
  console.error(`Blocked: ${rel} — ${reason}`);
  process.exit(2);
}

if (base === '.env' || (base.startsWith('.env.') && base !== '.env.example')) {
  block('secret env files are never edited by Claude. Update .env.example and tell the human which variable to set.');
}
if (rel === 'docs/SRS.md') {
  block('the SRS changes only through the human. Add a change request to docs/PROGRESS.md instead.');
}
if (rel.startsWith('apps/web/src/api/generated/')) {
  block('this client is generated from backend/openapi.yaml. Change the serializer or view, then run pnpm api:schema.');
}
if (/^backend\/(modules\/[^/]+|core)\/migrations\/\d{4}_[^/]+\.py$/.test(rel)) {
  let tracked = false;
  try {
    execFileSync('git', ['ls-files', '--error-unmatch', rel], { cwd: root, stdio: 'ignore' });
    tracked = true;
  } catch { /* untracked: a new migration, allowed */ }
  if (tracked) block('committed migrations are immutable. Create a new one with pnpm db:makemigrations <app> --name <change>.');
}
process.exit(0);
```

`.claude/hooks/format-file.mjs`. It never blocks.

```js
#!/usr/bin/env node
// PostToolUse (Edit|Write): format the edited file — Ruff for Python, Prettier for everything else it supports.
import { spawnSync } from 'node:child_process';
import path from 'node:path';

const chunks = [];
for await (const chunk of process.stdin) chunks.push(chunk);
let filePath;
try { filePath = JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}')?.tool_input?.file_path; } catch { process.exit(0); }
if (!filePath) process.exit(0);

const root = process.env.CLAUDE_PROJECT_DIR || process.cwd();
const ext = path.extname(filePath);
const shell = process.platform === 'win32';
const run = (cmd, args) => spawnSync(cmd, args, { cwd: root, stdio: ['ignore', 'ignore', 'pipe'], shell });

let result;
if (ext === '.py') {
  // Format only. Don't run `ruff check --fix` here: it would delete an import Claude added for its next edit.
  result = run('uv', ['run', '--directory', 'backend', 'ruff', 'format', '--quiet', path.resolve(root, filePath)]);
} else if (new Set(['.ts', '.tsx', '.js', '.mjs', '.cjs', '.json', '.css', '.md', '.yml', '.yaml']).has(ext)) {
  result = run('pnpm', ['exec', 'prettier', '--write', '--ignore-unknown', filePath]);
} else {
  process.exit(0);
}
if (result.status !== 0) {
  console.error(`could not format ${filePath}: ${String(result.stderr || '').slice(0, 300)}`);
}
process.exit(0);
```

### A.4 Path-scoped rules

`.claude/rules/backend.md`

```markdown
---
paths:
  - "backend/modules/**"
  - "backend/core/**"
  - "backend/config/**"
---
# Back-end rules (Django + DRF)
- App layout: `backend/modules/<name>/` with `models.py`, `selectors.py` (reads), `services.py` (writes: transactions + audit), `serializers.py`, `views.py`, `urls.py`, `permissions.py` (scope resolvers), `tasks.py` (Celery), `tests/`. Views stay thin and call selectors and services. Business rules go in `backend/domain`.
- Import other apps only through their `selectors` and `services`. Never import another app's `models`, `views`, `serializers` or `tasks`. FKs to other apps use string references (`"academic.ClassSubject"`).
- Every view action: `@require_permission("<key>", scope=<resolver>)` or `@public`. Querysets come from the scope resolver, so out-of-scope or missing records → 404 (`NotFound`); role lacks permission → 403; validation → 422 problem+json with a stable `code`.
- Actor and tenant come from `ctx()`. Request serializers never contain `schoolId`, `userId` or the actor's role.
- Separate input and output serializers. Annotate views with `@extend_schema` so `openapi.yaml` is accurate, then run `pnpm api:schema`.
- State changes to results, findings, releases, roles, settings, exports and deletions: one `transaction.atomic()` in a service function, with `audit.record(...)` inside it.
- Bulk validate/release, amend, role changes and exports need `@require_recent_auth()`.
- Lists: DRF cursor pagination `?cursor=&limit=` (default 25, max 100) with a stable ordering. Use `select_related` / `prefetch_related`; add a query-count assertion for list endpoints.
- Long work goes to a Celery task in `tasks.py`: idempotent, takes IDs (never model instances), passes `school_id` and enters `tenant_context`, `max_retries=3` with `retry_backoff`, queued via `transaction.on_commit`. The view returns 202 with the resource id.
- Time from `core.clock.now()`, never `timezone.now()`. No raw SQL, `.raw()` or `.extra()`.
- For every new route add: permission tests per role, a foreign-school and other-class IDOR test, a contract check (`expect_contract`), and a factory in `backend/tests/security/route_fixtures.py`.
```

`.claude/rules/web.md`

```markdown
---
paths:
  - "apps/web/**"
---
# Web rules (Next.js)
- Public portal lives in `app/s/[school]/…`; the signed-in app in `app/app/(admin|teacher|student)/…`. Inside `/app` the tenant comes from the session, never the URL.
- Data: only the orval-generated hooks and types in `src/api/generated` (never edit them; change the Django serializer and run `pnpm api:schema`). Wrap them in `src/api/<area>.ts` when a page needs composition. Forms: react-hook-form + zodResolver with the generated zod schemas.
- Requests that change data send the `X-CSRFToken` header (the shared fetch wrapper does this). Map problem+json `code`s to translated messages.
- Components: shadcn/ui primitives in `src/components/ui`; feature components in `src/components/<area>`. Reuse `OfficialBadge`, `AiBadge`, `EvidenceList`, `DataTable`, `EmptyState`, `ErrorState`.
- AI-generated or AI-assisted text always renders with `<AiBadge status=…>`; official marks with `<OfficialBadge>`. Never use `dangerouslySetInnerHTML` for AI or user text. The only HTML rendered is the server-sanitised question stem.
- Every user-facing string goes through next-intl `t('…')`; add the key to every locale file.
- Accessibility: label every control; visible focus that is never hidden by sticky bars; targets at least 24×24 px; never colour alone (add icon or text); charts need a table alternative; dialogs trap and restore focus.
- Layout works from 360 px wide with no horizontal scrolling.
- Each page has a Playwright spec in `tests/e2e/<area>/` that calls `expectNoA11yViolations(page)`.
- Visual references: `docs/design/reference/` (inspiration only; no third-party names, logos or assets).
```

`.claude/rules/db.md`

```markdown
---
paths:
  - "backend/**/models.py"
  - "backend/**/models/**"
  - "backend/**/migrations/**"
  - "backend/core/tenancy/**"
---
# Database rules (Django ORM + PostgreSQL)
- Tenant-owned models inherit `TenantModel` (UUID `id`, `school` FK, `created_at`, `updated_at`), which puts them in `TENANT_MODELS` automatically. Composite indexes and unique constraints start with `school`.
- Use `Meta.constraints` (`UniqueConstraint`, `CheckConstraint`) for invariants, not only Python checks. Timestamps are `DateTimeField` (UTC, `USE_TZ = True`).
- Marks are `IntegerField` hundredths with a `_centi` suffix (`max_marks_centi`, `marks_centi`, `total_centi`). Never `FloatField` or `DecimalField` for marks.
- Enums are `TextChoices`. JSON columns are `JSONField`, validated by a pydantic model in the service before saving.
- Keep raw evidence, official results, AI interpretations, release state and practice outcomes in separate models (DR-001).
- `AuditEvent` is append-only: no update or delete code paths; the app role has no UPDATE/DELETE grant.
- Schema change: `pnpm db:makemigrations <app> --name <change>`, then read the generated file. Never edit a committed migration. Data changes go expand → backfill (`RunPython` with a reverse) → contract, in separate migrations. `RunPython` uses `apps.get_model()`, never direct model imports.
- Raw SQL (`RunSQL`) only in migrations: grants, RLS policies, CHECKs Django can't express.
- Keep the seed (`manage.py seed`) idempotent and update it when models change.
```

`.claude/rules/ai.md`

```markdown
---
paths:
  - "backend/ai/**"
  - "backend/domain/diagnosis/**"
  - "backend/modules/analysis/**"
---
# AI and diagnosis rules
- Deterministic code in `backend/domain/diagnosis` decides which topics are weak or strong (BUILD_PLAN §6). The LLM only words findings that already exist.
- Call providers only through `AiGateway`. Build payloads with the task's allow-list mapper from the analysis snapshot (plain dataclasses); never pass model instances or whole objects.
- Pseudonymise students as `S1…Sn`. R1 payloads contain no names, usernames, emails, teacher comments or other free text.
- Validate every output in order: pydantic schema → references exist in the input → banned phrases → numbers match metrics (±1) → length. On any failure use the template text, log the `AiCall` as REJECTED, and never block the teacher workflow.
- Student-facing wording is hedged ("may", "suggests") and grade-appropriate. No diagnoses or ability labels.
- Prompts live in `backend/ai/prompts/<task>/v<N>.md`. A change means a new version file, a CHANGELOG line and a `pnpm eval:ai` run.
- Tests use `FakeAiProvider` and fixtures only. Real provider calls happen only in `pnpm eval:ai`.
- Analysis code reads results only through `modules.results.selectors` and must not import `results.models` or `results.services` (FR-EXAM-026).
```

`.claude/rules/testing.md`

```markdown
---
paths:
  - "backend/**/tests/**"
  - "backend/**/test_*.py"
  - "backend/conftest.py"
  - "**/*.spec.ts"
  - "**/*.spec.tsx"
  - "**/*.test.ts"
  - "**/*.test.tsx"
  - "tests/**"
---
# Testing rules
- Tag the requirement or task ID: `@pytest.mark.req("FR-EXAM-026")` (or `"P3-T04-AC2"`) in Python; `test('[FR-EXAM-026] AI suggestion never changes official marks', …)` in TypeScript. `pnpm req:trace` reads these tags.
- Unit tests (`backend/domain`, `backend/ai`) are pure: no database (`django_db` is not allowed there), network or real clock. Inject a fake clock and a seeded random generator. Use Hypothesis for properties.
- Integration tests use `@pytest.mark.django_db`, DRF's `APIClient`, and the real Postgres and Redis from docker compose. Create data with factory_boy inside `tenant_context`. Run Celery tasks eagerly. Don't mock our own services; mock only external providers (AI, SMTP via `mail.outbox`, ClamAV unless testing the scanner, S3 unless testing files).
- For behaviour that depends on commit (`on_commit`, audit, RLS), use `django_db(transaction=True)` or `django_capture_on_commit_callbacks`.
- E2E tests use the Greenfield seed and its users. Every page spec calls `expectNoA11yViolations(page)`.
- Fictional data only. Never copy real student data into fixtures.
- A bug fix starts with a failing test. Never skip, weaken or delete a test to get green; if a test is wrong, say why in the commit message.
- No sleeps. Use polling helpers and fixed dates.
```

### A.5 Skills

`.claude/skills/task/SKILL.md`

```markdown
---
name: task
description: Implement one task from docs/BUILD_PLAN.md end to end (plan, failing tests, code, verify, review, progress, commit). Usage /task P3-T04
disable-model-invocation: true
argument-hint: "[task-id, e.g. P3-T04]"
---
Implement build-plan task $ARGUMENTS.

1. Find it: run `grep -n "^#### $ARGUMENTS" docs/BUILD_PLAN.md` and read only that section (it ends at the next `####` heading). For each SRS ID it cites, read that requirement in docs/SRS.md (grep the ID).
2. Check docs/PROGRESS.md: every task under "Depends on" must be ✅. If not, stop and tell me which are missing. Mark $ARGUMENTS as 🔄.
3. Explore only the code this task touches. Then present a short plan: files to add or change, the test that will prove each acceptance criterion, risks, and open questions. If the task conflicts with CLAUDE.md, the SRS or existing code, stop and ask. In plan mode, wait for my approval.
4. Write the tests for every acceptance criterion first. Tag each test with its SRS ID or `$ARGUMENTS-ACn` (`@pytest.mark.req(...)` in Python, `[ID]` in the test name in TypeScript). Run them and confirm they fail for the right reason.
5. Implement until they pass. Pure business logic goes in backend/domain; API shapes in DRF serializers. If a serializer or URL changed, run `pnpm api:schema` and commit the regenerated schema and client.
6. Run `pnpm verify`. For UI work also run the page's Playwright spec (with axe). Fix root causes; never skip, weaken or delete a test.
7. If the task is marked 🔒 or touches auth, tenancy, results, findings, files or AI: use the security-reviewer subagent on the diff and fix every FAIL.
8. Use the requirements-auditor subagent for $ARGUMENTS and fix every NOT MET or NO TEST item.
9. Update docs/PROGRESS.md: mark $ARGUMENTS ✅ with today's date; add follow-ups, deviations and SRS change requests.
10. Commit as `$ARGUMENTS: <task title>` with a body that maps each acceptance criterion to its test. Do not push.

Finish by showing the evidence: each command you ran and its pass/fail summary.
```

`.claude/skills/phase-gate/SKILL.md`

```markdown
---
name: phase-gate
description: Check a phase's exit criteria in docs/BUILD_PLAN.md and write a GO / NO-GO report. Usage /phase-gate P3
disable-model-invocation: true
argument-hint: "[phase, e.g. P3]"
---
Check the exit criteria for phase $ARGUMENTS. Report only; do not fix anything in this run.

1. The phase number is the digit in $ARGUMENTS (P3 means Phase 3). In docs/BUILD_PLAN.md read the "### Phase <n>." header and its "**Phase <n> exit criteria" list.
2. Confirm every task P<n>-Txx is ✅ in docs/PROGRESS.md.
3. Run `pnpm verify`, `pnpm test:e2e` and `pnpm req:trace --release R1`, and collect the results.
4. For each exit criterion record the status (MET, NOT MET or MANUAL), the evidence (command and result, test names, report paths) and any blockers.
5. Write docs/gates/$ARGUMENTS.md with a table (criterion | status | evidence), then GO or NO-GO and the list of blockers. Commit it as "$ARGUMENTS: phase gate report".
```

### A.6 Subagents

`.claude/agents/security-reviewer.md`

```markdown
---
name: security-reviewer
description: Reviews the current diff against AS security and privacy rules (tenant isolation, authorisation, IDOR, official results, student visibility, audit, AI payloads, files, secrets). Use after any change to auth, tenancy, results, findings, files or AI.
tools: Read, Grep, Glob, Bash
model: inherit
---
You are a senior application security engineer reviewing a change to AS, a multi-tenant school platform that holds student records.

Review only the current change: `git diff main...HEAD` plus uncommitted changes. For each finding give file:line, the rule broken, a concrete failure or exploit scenario, and the fix.

Check:
1. Tenant isolation: school_id never comes from client input; tenant models inherit TenantModel and are read through the scoped `objects` manager; `all_schools` appears only inside `system_scope(reason)`; no raw SQL, `.raw()` or `.extra()`; Celery tasks enter `tenant_context`; Django admin is not exposed outside local development.
2. Authorisation: every new view action has `@require_permission` or `@public`; scope resolvers filter querysets by assignment or ownership; out-of-scope records return 404.
3. Official results: only ResultsService writes AssessmentResult, QuestionMark or ResultRevision; analysis and AI code never import `results.models` or `results.services`.
4. Visibility: student-facing endpoints go through VisibilityService; nothing unreleased leaks through includes, counts, sorting or error messages.
5. Audit: validate, amend, release, withdraw, finding review and release, role and setting changes, exports and deletions write an AuditEvent in the same transaction.
6. AI payloads: built only by allow-list mappers; no names, usernames, emails or free text; outputs schema-validated and rendered as plain text.
7. Files: no public URLs; signed URLs at most 5 minutes, issued after an authorisation check, never logged; uploads type- and size-checked and scanned.
8. Secrets and logs: no secrets in code; logs contain IDs, never names, emails, marks, tokens or URLs.
9. Web: no dangerouslySetInnerHTML with user or AI content; Django CSRF and Origin checks, cookie flags and CSP intact; no `csrf_exempt` on session-authenticated views.

Report only real issues that affect security, privacy or these rules; skip style. End with "VERDICT: PASS" or "VERDICT: FAIL".
```

`.claude/agents/requirements-auditor.md`

```markdown
---
name: requirements-auditor
description: Audits one build-plan task (the ID is given in the request) against its acceptance criteria and cited SRS requirements, checking that each has a passing test. Use before marking a task done.
tools: Read, Grep, Glob, Bash
model: inherit
---
You audit one task from docs/BUILD_PLAN.md.

1. Read only that task's section (`grep -n "^#### <ID>" docs/BUILD_PLAN.md`) and the SRS requirements it cites (grep each ID in docs/SRS.md).
2. Inspect the change: `git diff main...HEAD` plus uncommitted changes.
3. For every acceptance criterion, find the test that proves it (file and test name) and run it with the narrowest command from CLAUDE.md. Mark it MET, NOT MET or NO TEST. Criteria marked (manual) need a line in docs/verification/manual.md or in the task notes.
4. Flag changes outside the task's scope and requirements claimed but not implemented.

Report only gaps that affect correctness or the stated requirements, not style. Output a table (criterion | status | evidence), then "VERDICT: PASS" or "VERDICT: FAIL".
```

### A.7 `docs/adr/template.md`

```markdown
# ADR-NNNN: <title>

- Status: Proposed | Accepted | Superseded by ADR-XXXX
- Date: YYYY-MM-DD
- SRS: <requirement IDs>

## Context

## Decision

## Consequences

## Alternatives considered
```

### A.8 `.github/pull_request_template.md`

```markdown
## Task
P?-T??: <title>

## Acceptance criteria → tests
| AC | Test |
|---|---|

## Checks
- [ ] `pnpm verify` green
- [ ] New migrations read and reversible; `openapi.yaml` and the generated client regenerated if the API changed
- [ ] E2E + axe for UI changes
- [ ] Permission and IDOR tests for new routes
- [ ] Audit events for state changes
- [ ] security-reviewer PASS (auth, tenancy, results, findings, files, AI)
- [ ] requirements-auditor PASS
- [ ] docs/PROGRESS.md updated
```

### A.9 `docs/PROGRESS.md` format

```markdown
# Build progress

Legend: ⬜ todo · 🔄 in progress · ✅ done · ⏸ blocked

| Task | Title | Status | Date | Notes |
|---|---|---|---|---|
| P0-T01 | Prepare your machine and accounts | ⬜ | | |
| … one row per "#### Px-Tyy" heading in docs/BUILD_PLAN.md … | | | | |

## Decisions log

## SRS change requests

## Follow-ups and known issues
```

---
## Appendix B. API surface (R1)

Every path is under `/api/v1`. Request and response serializers live in `backend/modules/<module>/serializers.py`, and the published contract is `backend/openapi.yaml`. Path parameters such as `:id` are UUIDs (`<uuid:id>` in Django URL patterns). In the permission column, ⟲ means recent re-authentication is needed for that call or for bulk use (NFR-SEC-007).

**Auth and account (P1)**

| Method and path | Permission | SRS |
|---|---|---|
| `POST /auth/login` | Public | FR-AUTH-003 |
| `POST /auth/logout` | Any session | — |
| `POST /auth/mfa/verify` | Session waiting for MFA | FR-AUTH-007 |
| `POST /auth/reauth` | Any session | NFR-SEC-007 |
| `POST /auth/password/forgot` · `POST /auth/password/reset` | Public | FR-AUTH-006 |
| `POST /auth/invitations/accept` | Public (token) | FR-AUTH-001 |
| `GET /me` · `POST /me/active-role` | Any session | FR-AUTH-004 |
| `POST /me/mfa/setup` · `POST /me/mfa/enable` · `POST /me/password` | Any session | FR-AUTH-007 |
| `GET /me/activity` | `audit.read` (own) | FR-ADM-008 |
| `POST /files` · `GET /files/:id/url` | Policy of the record that owns the file | NFR-SEC-009..011 |

**School, portal and notices (P2, P6)**

| Method and path | Permission | SRS |
|---|---|---|
| `GET /public/schools/:slug` | Public | FR-PORT-001, FR-PORT-002, FR-PORT-010 |
| `GET /school` · `PATCH /school` | `school.update` | FR-ADM-001 |
| `GET /school/settings` · `PATCH /school/settings` ⟲ | `settings.manage` | FR-ADM-005 |
| `GET /notices/feed` | `notice.read` | FR-PORT-005 |
| `GET /notices` · `POST /notices` · `PATCH /notices/:id` · `DELETE /notices/:id` | `notice.manage.school` / `notice.manage.class` | FR-PORT-003, FR-PORT-004 |
| `GET /portal/home` | Any session | FR-PORT-005, FR-PORT-007 |

**Academic structure and people (P2)**

| Method and path | Permission | SRS |
|---|---|---|
| `GET /academic-years` · `POST /academic-years` · `PATCH /academic-years/:id` · `POST /academic-years/:id/close` | `academic.manage` | FR-ACAD-003 |
| `/class-groups`, `/subjects`, `/class-subjects`, `/teacher-assignments`, `/enrollments` (CRUD) | `academic.manage` | FR-ACAD-001, 002, 004, 005, 006 |
| `GET /topics` · `POST /topics` · `PATCH /topics/:id` | `topic.manage` | FR-ACAD-008 |
| `GET /users` · `POST /users/invitations` · `PATCH /users/:id` ⟲ | `user.manage` | FR-AUTH-001, FR-AUTH-009 |
| `POST /imports` (dry run or commit) · `GET /imports/:id` | `user.import` | FR-AUTH-002, SW-003 |
| `GET /teaching/class-subjects` | Teacher (own assignments) | FR-TCH-001 |

**Exams and results (P3)**

| Method and path | Permission | SRS |
|---|---|---|
| `GET /exams` · `POST /exams` · `GET /exams/:id` · `PATCH /exams/:id` | `exam.manage` | FR-EXAM-001 |
| `POST /exams/:id/publish` · `POST /exams/:id/close` · `POST /exams/:id/cancel` | `exam.manage` | FR-EXAM-003 |
| `PUT /exams/:id/questions` | `exam.manage` | FR-EXAM-002 |
| `GET /exams/:id/mark-sheet` · `PATCH /exams/:id/mark-sheet` | `marks.enter` | FR-EXAM-010, FR-EXAM-012 |
| `POST /exams/:id/mark-sheet/import` | `marks.enter` | FR-EXAM-011 |
| `POST /exams/:id/results/evaluate` | `marks.enter` | FR-EXAM-003 |
| `POST /exams/:id/results/validate` ⟲ (bulk) | `result.validate` | FR-EXAM-020, FR-EXAM-021 |
| `POST /results/:id/amend` ⟲ | `result.amend` | FR-EXAM-022 |
| `POST /exams/:id/release` ⟲ (bulk) · `POST /exams/:id/withdraw` | `result.release` | FR-EXAM-023, FR-EXAM-025 |
| `PUT /results/:id/feedback` | `feedback.write` | FR-EXAM-027 |
| `POST /exams/:id/scripts` · `GET /scripts/:id/url` | `script.upload` / `script.read` | FR-EXAM-013, FR-EXAM-024 |

**Analysis and review (P4)**

| Method and path | Permission | SRS |
|---|---|---|
| `POST /analysis-runs` · `GET /analysis-runs/:id` | `analysis.request` | FR-AI-001, FR-AI-004, FR-AI-017 |
| `GET /findings` · `GET /findings/:id` | `finding.review` | FR-AI-014, FR-AI-019 |
| `PATCH /findings/:id` (accept, edit, reject or rate) | `finding.review` | FR-AI-015, FR-AI-018, FR-AIREL-014 |
| `POST /findings/release` | `finding.release` | FR-AI-016 |
| `GET /class-subjects/:id/insights` | `classInsight.read` | FR-AI-010, FR-TCH-006 |
| `GET /reports/ai-review-decisions` (pseudonymised) ⟲ | `report.read` | FR-AIREL-002 |

**Learning and practice (P5)**

| Method and path | Permission | SRS |
|---|---|---|
| `GET /resources` · `POST /resources` · `PATCH /resources/:id` | `resource.manage` | FR-RES-001, FR-RES-002 |
| `GET /question-bank/items` · `POST /question-bank/items` · `PATCH /question-bank/items/:id` | `questionBank.manage` | FR-RES-008 |
| `GET /recommendations` · `PATCH /recommendations/:id` · `POST /recommendations/approve` | `recommendation.manage` | FR-RES-003, FR-RES-004, FR-RES-005 |
| `POST /practice-tests` · `GET /practice-tests/:id` · `POST /practice-tests/:id/assign` | `practice.manage` | FR-PRAC-001, FR-PRAC-002, FR-PRAC-003 |
| `GET /students/:id/progress` | `progress.read` | FR-STU-005, FR-TCH-006 |

**Student (P3–P6)**

All of these go through `VisibilityService`.

| Method and path | Permission | SRS |
|---|---|---|
| `GET /student/overview` | `student.self.read` | FR-STU-001 |
| `GET /student/results` · `GET /student/results/:id` | `student.self.read` | FR-STU-002, FR-EXAM-024, FR-EXAM-028 |
| `GET /student/learning-gaps` | `student.self.read` | FR-STU-003 |
| `GET /student/learning-plan` | `student.self.read` | FR-STU-004 |
| `POST /student/resources/:id/opened` · `POST /student/resources/:id/completed` | `student.self.read` | FR-RES-006 |
| `GET /student/practice` · `POST /student/practice-tests/:id/attempts` | `practice.take` | FR-PRAC-004 |
| `PATCH /student/attempts/:id` · `POST /student/attempts/:id/submit` · `GET /student/attempts/:id` | `practice.take` | FR-PRAC-004, FR-PRAC-005, FR-PRAC-007 |
| `GET /student/progress` | `progress.read` (own) | FR-STU-005, FR-PRAC-010 |

**Reports, audit, notifications and operator (P6, P7)**

| Method and path | Permission | SRS |
|---|---|---|
| `GET /reports/usage` · `GET /reports/academic-activity` | `report.read` | FR-ADM-006, FR-ADM-007 |
| `GET /audit-events` · `GET /audit-events/export` ⟲ | `audit.read` | FR-ADM-008 |
| `GET /notifications` · `POST /notifications/:id/read` · `POST /notifications/read-all` | Any session | COM-003 |
| `POST /operator/schools` | `operator.tenant.provision` | — |
| `POST /operator/support-grants` · `POST /school/support-grants/:id/approve` ⟲ | Operator / `settings.manage` | NFR-PRIV-006 |

---

## Appendix C. UI routes (R1)

| Route | Who | What | Phase |
|---|---|---|---|
| `/s/[school]` | Public | School portal: profile, public notices, sign-in | P2 |
| `/s/[school]/login` · `/mfa` · `/invite/[token]` · `/reset/[token]` | Public | Authentication | P1 |
| `/app` | Signed in | Redirects to the role's home | P1 |
| `/app/home` | All roles | Signed-in portal: notices and shared resources | P6 |
| `/app/notifications` · `/app/account` | All roles | Notifications; password, MFA and my activity | P1, P6 |
| `/app/admin` | Admin | Overview, setup checklist, reports | P6 |
| `/app/admin/school` | Admin | Profile and portal content | P2 |
| `/app/admin/structure` | Admin | Years, classes and sections, subjects, topics | P2 |
| `/app/admin/people` | Admin | Users, imports, assignments, enrollments | P2 |
| `/app/admin/notices` · `/app/admin/settings` · `/app/admin/audit` | Admin | Notices, settings, audit viewer | P2, P6 |
| `/app/teacher` | Teacher | Dashboard and queues | P6 |
| `/app/teacher/classes/[id]` · `/insights` | Teacher | Students and class topic insights | P4, P6 |
| `/app/teacher/exams` · `/new` · `/[id]` · `/[id]/marks` · `/[id]/release` | Teacher | Exam setup, mark grid, release | P3 |
| `/app/teacher/review` · `/app/teacher/findings/[id]` | Teacher | Review queue and traceability view | P4 |
| `/app/teacher/resources` · `/question-bank` · `/practice` | Teacher | Content and practice assignment | P5 |
| `/app/teacher/students/[id]` | Teacher | A student's progress and engagement | P5, P6 |
| `/app/student` | Student | Overview with a next-step card | P6 |
| `/app/student/results` · `/results/[id]` | Student | Released results | P3 |
| `/app/student/gaps` | Student | Learning-gap report | P4 |
| `/app/student/plan` | Student | Learning plan | P5, P6 |
| `/app/student/practice` · `/practice/[attemptId]` | Student | Practice tests | P5 |
| `/app/student/progress` | Student | Progress history (charts with tables) | P6 |

**Dashboard design references:** `docs/design/reference/01–05` are the five screenshots from the original description. They map to the student dashboard's five areas: academic overview, exam records, learning-gap report, learning plan and progress history. Use them for layout ideas only. Don't copy names, logos, characters or other assets.

---

## Appendix D. Permission catalog

Scopes:
- **school**: any record in the user's school.
- **assigned**: the teacher has a `TeacherAssignment` for the record's class subject.
- **own**: the student's own records.
- ⚙️: allowed only if a school setting enables it.
- —: denied (403).

Records outside the scope always return 404.

| Key | School admin | Teacher | Student | SRS / notes |
|---|---|---|---|---|
| `school.update` | ✅ school | — | — | FR-ADM-001 |
| `settings.manage` | ✅ school ⟲ | — | — | FR-ADM-005 |
| `user.manage` | ✅ school ⟲ | — | — | FR-AUTH-001, FR-AUTH-009 |
| `user.import` | ✅ school | — | — | FR-AUTH-002 |
| `academic.manage` | ✅ school | — | — | FR-ACAD-001..006 |
| `topic.manage` | ✅ school | ✅ assigned subjects (add, rename) | — | FR-ACAD-008 |
| `notice.manage.school` | ✅ | — | — | FR-PORT-003 |
| `notice.manage.class` | ✅ | ✅ assigned | — | FR-PORT-004 |
| `notice.read` | ✅ | ✅ targeted | ✅ targeted | FR-PORT-005 |
| `exam.manage` | ⚙️ (R2: FR-EXAM-004) | ✅ assigned | — | FR-EXAM-001..003 |
| `marks.enter` | — | ✅ assigned | — | FR-EXAM-010, FR-EXAM-011 |
| `result.validate` | — | ✅ assigned (bulk ⟲) | — | FR-EXAM-020, FR-EXAM-021 |
| `result.amend` | — | ✅ assigned ⟲ | — | FR-EXAM-022 |
| `result.release` | ⚙️ | ✅ assigned (bulk ⟲) | — | FR-EXAM-023, FR-EXAM-025 |
| `script.upload` | — | ✅ assigned | — | FR-EXAM-013 |
| `script.read` | ⚙️ | ✅ assigned | ✅ own, released | FR-EXAM-024 |
| `feedback.write` | — | ✅ assigned | — | FR-EXAM-027 |
| `analysis.request` | — | ✅ assigned | — | FR-AI-001 |
| `finding.review` | — | ✅ assigned | — | FR-AI-014, FR-AI-015 |
| `finding.release` | — | ✅ assigned | — | FR-AI-016 |
| `classInsight.read` | ⚙️ aggregate only | ✅ assigned | — | FR-AI-010 |
| `resource.manage` | ✅ school library | ✅ own and assigned subjects | — | FR-RES-001, FR-RES-002 |
| `questionBank.manage` | — | ✅ assigned subjects | — | FR-RES-008 |
| `recommendation.manage` | — | ✅ assigned | — | FR-RES-005 |
| `practice.manage` | — | ✅ assigned | — | FR-PRAC-002, FR-PRAC-003 |
| `practice.take` | — | — | ✅ own | FR-PRAC-004 |
| `progress.read` | ⚙️ | ✅ assigned | ✅ own | FR-STU-005 |
| `student.self.read` | — | — | ✅ own | FR-STU-001..004 |
| `report.read` | ✅ aggregate | — | — | FR-ADM-006, FR-ADM-007 |
| `audit.read` | ✅ school (export ⟲) | ✅ own actions | — | FR-ADM-008 |
| `operator.tenant.provision` | Operator only | | | — |
| `operator.support.access` | Operator with an active, school-approved grant | | | NFR-PRIV-006 |

---

## Appendix E. Seed data and golden fixtures

All of this data is **fictional**.

### E.1 Greenfield School (slug `greenfield`)

| Item | Seed |
|---|---|
| Academic year | 2026–27 (ACTIVE) |
| Classes | Class 9 – A (30 students, including Sara) and Class 9 – B (25 students) |
| Subjects | Mathematics and Science, taught in both classes |
| Mathematics topics | Algebra (Algebraic simplification, Solving linear equations, Forming equations from word problems) and Geometry (Triangles, Circles) |
| Science topics | Chemistry (Balancing chemical equations, Acids and bases) |
| Users (password = `SEED_PASSWORD`) | `admin` (MFA enrolled with a fixed test secret from `.env.test`); `t.rivera` (Mathematics, 9A and 9B); `t.okafor` (Science, 9A and 9B); `sara` (9A); `s9a-01`…`s9a-29`; `s9b-01`…`s9b-25` |
| Notices | School-wide, public: "Term 1 exams start 7 December". 9A Mathematics, signed-in: "Bring a calculator" |

### E.2 `core-loop` scenario (Mathematics, 9A)

**Class Test 2** (20 marks; all results VALIDATED and marks released):

| Question | Topic | Max | Sara |
|---|---|---|---|
| Q1 | Forming equations from word problems | 5 | 2 |
| Q2 | Forming equations from word problems | 5 | 2.5 |
| Q3 | Algebraic simplification | 10 | 9 |

**Term 1 Mathematics** (40 marks):
- The exam is PUBLISHED. The 29 other students' results are VALIDATED, and 13 of them score below 50% on Triangles.
- Sara's result is NOT_STARTED, so the E2E test enters her marks:

| Question | Topic | Max | Sara |
|---|---|---|---|
| Q1 | Algebraic simplification | 4 | 4 |
| Q2 | Algebraic simplification | 4 | 3.5 |
| Q3 | Solving linear equations | 5 | 4 |
| Q4 | Forming equations from word problems | 5 | 1 |
| Q5 | Forming equations from word problems | 6 | 2 |
| Q6 | Triangles | 8 | 6 |
| Q7 | Triangles | 8 | 6.5 |
| **Total** | | **40** | **27 (67.5%)** |

### E.3 `practice` scenario

- **Question bank** for "Forming equations from word problems": **25 APPROVED items**, made up of 10 at difficulty 1, 10 at difficulty 2 and 5 at difficulty 3. They are a mix of MCQ_SINGLE and NUMERIC.
- **Resources:** one `WORKED_EXAMPLE`, one teacher `NOTE`, and one `VIDEO_LINK` to `https://example.org/forming-equations`.
- In the E2E test, Sara answers **4 of 10** correctly on the baseline and **8 of 10** on the reassessment.

### E.4 Golden fixtures (`backend/domain/tests/fixtures/`)

| File | What it encodes | Expected result |
|---|---|---|
| `sara-core.json` | Sara's two exams (E.2) | WEAKNESS on forming equations (HIGH; rules A, B and C) and STRENGTH on algebraic simplification (MEDIUM). Nothing else (§6.1) |
| `total-only.json` | One exam with only total marks | One INSUFFICIENT_DETAIL note and no topic findings |
| `multi-topic.json` | One question tagged with two topics (6/10), plus one question per topic | The shared question counts in full towards both topics' scores |
| `class-9a-triangles.json` | 30 students' Term 1 marks, with 13 below 50% on Triangles | CLASS_TOPIC_FLAG on Triangles (43%). A variant with 11 students gives no flag |
| `practice-bank-forming-eq.json` | The 25 items (10/10/5) | A baseline and a disjoint reassessment both assemble from blueprint 4/4/2. A third disjoint set returns `INSUFFICIENT_ITEMS {1: 2, 2: 2, 3: 1}` |
| `progress-sara.json` | Baseline 4/10, reassessment 8/10 | `IMPROVED_ON_PRACTICE`, 40 → 80, `deltaPp` +40, `nextStep` ADVANCE |
| `metrics-qwk.json` | The vectors in §15 | The values in the §15 table |

---

## Appendix F. UAT scripts

Run these on staging with synthetic data in P8-T03. Record the results in `docs/uat/<date>.md`.

| ID | Role | Steps | Expected result | SRS |
|---|---|---|---|---|
| UAT-01 | Admin | Import Greenfield from CSV files containing 3 bad rows | The dry run lists the 3 errors by row; nothing is committed until they're fixed; the import then succeeds | FR-AUTH-002, SW-003 |
| UAT-02 | Teacher | Create "Term 1 Mathematics" with 7 questions and their topics, then publish | The exam is published, and a mismatched total is blocked with a message | FR-EXAM-001, FR-EXAM-002 |
| UAT-03 | Teacher | Enter marks for the whole class using only the keyboard, and time it | Marks are saved and totals are correct; record the time against the NFR-USE-001 target | FR-EXAM-010, NFR-USE-001 |
| UAT-04 | Teacher | Validate everyone and release marks only | Re-authentication is requested and the results are released | FR-EXAM-020, FR-EXAM-023 |
| UAT-05 | Student | Open the result | Marks are visible; the script and comments are not | FR-EXAM-024 |
| UAT-06 | Teacher, then admin | Amend one mark with a reason; the admin then opens the audit log | The student sees the new mark; the audit log shows the old and new values and the reason | FR-EXAM-022, NFR-AUD-001 |
| UAT-07 | Teacher | Request analysis; accept one finding, edit one, reject one; release | Only the accepted and edited findings reach the student, labelled correctly | FR-AI-015, FR-AI-016 |
| UAT-08 | Student | Open the gap report and then "Why am I seeing this?" | The text is plain language and the evidence shows the questions and marks | FR-STU-003, UI-004 |
| UAT-09 | Student | Do the quick check, the resources, the practice and the reassessment | The improvement is shown with its comparison basis, and never as "mastered" | FR-PRAC-010, FR-PRAC-011, UI-005 |
| UAT-10 | Teacher | Open class insights, select the flagged topic and assign class practice | Students receive the assignment | FR-AI-010, FR-TCH-005 |
| UAT-11 | Negative | A student opens a teacher URL; a 9B teacher opens a 9A exam URL | Both get "not found" | FR-AUTH-005 |
| UAT-12 | Admin | Turn AI off and re-run the analysis | Findings use the template text and no AI calls are logged | NFR-PRIV-005 |
| UAT-13 | Accessibility | Do a practice attempt with the keyboard only, and read a gap card with a screen reader | Everything can be completed and the content is announced correctly | NFR-ACC-001 |
| UAT-14 | Mobile | Run the student flow on a 360 px phone | No horizontal scrolling, and all actions are reachable | UI-006 |
| UAT-15 | Resilience | Drop the network during mark entry, then reconnect | No marks are lost | NFR-REL-002 |

---

## Appendix G. Definition of Ready and Done

**A task is ready when:**
- It has an ID, a title, SRS IDs and a clear owner.
- Its dependencies are ✅ in `docs/PROGRESS.md`.
- Its acceptance criteria are testable.
- The test approach is known.
- UI references are noted, where relevant.
- Any questions that block it have been answered.

**A task is done when:**
1. Every acceptance criterion has an automated test tagged with its ID (§9.2), or a recorded manual check.
2. `pnpm verify` passes. For UI work, the page's E2E and axe checks also pass.
3. There are no new lint or type errors, no unexplained `any`, and no TODO without an issue link.
4. Migrations are new files, not edits to old ones, and the seed has been updated if needed.
5. New routes declare a permission and have IDOR tests and fixture factories. State changes write audit events.
6. Strings are localised, accessibility is checked, and AI content is labelled.
7. The security-reviewer reports PASS (🔒 tasks) and the requirements-auditor reports PASS.
8. `docs/PROGRESS.md` is updated, and the commit is named `Px-Tyy: <title>`, with ACs mapped to tests.
9. Docs, runbooks and ADRs are updated if behaviour or operations changed.

---

## Appendix H. SRS coverage by phase

This is a summary; each task lists its exact IDs. R2 and R3 requirements are covered in §15.

| Phase | Release 1 requirements implemented |
|---|---|
| P0 | NFR-MNT-001, NFR-MNT-004, plus decisions on OI-04..OI-11 |
| P1 | FR-AUTH-001, FR-AUTH-003..007; COM-001, COM-002; UI-001, UI-002, UI-006, UI-007; NFR-SEC-002, NFR-SEC-003, NFR-SEC-005..013; NFR-AUD-001..003; NFR-ACC-001..004; NFR-LOC-001, NFR-LOC-002; NFR-USE-004; NFR-MNT-005; DR-002, DR-005; SW-006 |
| P2 | FR-ACAD-001..006, FR-ACAD-008; DR-004; FR-AUTH-002, FR-AUTH-009; FR-PORT-001..005, FR-PORT-009, FR-PORT-010; FR-ADM-001..004; SW-003 |
| P3 | FR-EXAM-001..003, FR-EXAM-010..013, FR-EXAM-018, FR-EXAM-020..028; FR-ACAD-007; FR-STU-002; FR-AIREL-007, FR-AIREL-009; DR-001; NFR-REL-002, NFR-REL-003; COM-003 |
| P4 | FR-AI-001, FR-AI-002, FR-AI-004..010, FR-AI-013..021, FR-AI-023; FR-AIREL-002, FR-AIREL-014; FR-STU-003; FR-TCH-004, FR-TCH-006; UI-004; SW-001, SW-002; NFR-SEC-014; NFR-PRIV-005; NFR-REL-001, NFR-REL-004; NFR-SCAL-003; NFR-AUD-004; DR-003 |
| P5 | FR-RES-001..006, FR-RES-008; FR-PRAC-001..005, FR-PRAC-007, FR-PRAC-009..012; FR-STU-004, FR-STU-005; FR-TCH-005; UI-005; NFR-ACC-006; NFR-PERF-005 |
| P6 | FR-STU-001..007; FR-TCH-001..006, FR-TCH-009; FR-ADM-005..008; FR-PORT-007; UI-003; NFR-ACC-005 |
| P7 | NFR-SEC-001, NFR-SEC-004, NFR-SEC-015; NFR-PRIV-001..004, NFR-PRIV-006, NFR-PRIV-007, NFR-PRIV-010; NFR-PERF-001..006; NFR-SCAL-001; NFR-ACC-001..007 (audit); NFR-AVL-001..005; FR-AIREL-001, FR-AIREL-003 (R1 part); FR-AI-023 |
| P8 | NFR-USE-001, NFR-USE-002; HW-002 (manual); OI-01..03 closed |

*End of build plan. Keep this file stable: change it through PRs, and record any deviation in `docs/PROGRESS.md` under "SRS change requests".*
