# Software Requirements Specification (SRS): AS — AI-Powered Academic Assessment and School Platform

This is a complete Software Requirements Specification for AS. It follows ISO/IEC/IEEE 29148, which replaced IEEE 830 in 2011, and every requirement is tagged by release.\[1\]\[2\] Release 1 (MVP) builds the core loop: teacher-validated marks → AI weakness analysis → resources → targeted practice → measured improvement. AI never sets an official grade, and automated handwriting evaluation is deferred to later releases.

## TL;DR
- **What this is:** a finished SRS covering all 9 modules, organised the way ISO/IEC/IEEE 29148 lays out an SRS (Introduction → Overall Description → Specific Requirements → Data → Appendices). It contains about 190 uniquely identified, testable "The system shall…" requirements, each tagged with a MoSCoW priority and a release (R1 = MVP, R2 = Early Expansion, R3 = Long-term).
- **The rule that matters most:** official teacher-approved results, AI-generated interpretations, raw evidence and practice outcomes are kept as separate records with their own status. AI output always carries a review status and can never overwrite an official mark. Low-confidence or unreadable input goes to manual review instead of producing a guessed score. This follows the "humans in the loop" recommendation in the U.S. Department of Education's 2023 AI report.\[3\] It also matches the EU AI Act, which treats AI that evaluates learning outcomes as high-risk.\[4\]
- **What still needs deciding:** the deployment jurisdiction, applicable law (examples include FERPA, COPPA, GDPR and the EU AI Act), retention periods, the AI provider, languages, curriculum mapping and the parent role. These are listed as TBD items in Appendix C. All numeric NFR targets in this document are proposed defaults for the team to confirm.

---

## Document Control

| Item | Value |
|---|---|
| Document | Software Requirements Specification — AS |
| Version | 1.0 (Baseline draft for review) |
| Basis | User's "System Analysis of AS" document (full) |
| Structure standard | ISO/IEC/IEEE 29148:2018 SRS content outline (legacy IEEE 830-1998 sections mapped) |
| Status | Draft — numeric targets marked **[Proposed]** require team confirmation |
| Audience | Product owner, developers, QA/test, UX, AI/ML engineers, pilot-school representatives, security/privacy reviewers |

---

## 1. Introduction

### 1.1 Purpose
This SRS defines the functional and non-functional requirements of AS, a school-connected web platform. AS turns examination results and teacher-validated assessment evidence into actionable feedback, personalised learning resources, targeted practice and measured improvement. It also gives schools, teachers and students one shared academic environment. The SRS is the agreed baseline for design, implementation, testing, acceptance of the pilot release, and later change control.

### 1.2 Scope
**Product name:** AS — AI-Powered Academic Assessment and School Platform.

**The product will:**
1. Give each participating school an institutional portal (profile, notices, resources, access to dashboards).
2. Manage accounts, roles and a configurable academic structure (school → academic year → class/grade → section → subject → teacher assignment → student enrollment).
3. Manage examination records and assessment evidence: manual mark entry, digital upload, scanned upload, and (later) AI-assisted written-script evaluation, always with teacher validation and controlled release.
4. Run AI analysis of validated evidence at student and class level to find likely strengths, weaknesses and recurring gaps, with linked supporting evidence and a review status.
5. Recommend learning resources and build or assign targeted practice tests, then measure change after reassessment.
6. Provide role-specific dashboards for students, teachers and school administrators.

**Out of scope (not confirmed):** fee collection, payroll, HR, attendance, full accounting, and any other general school-management function not named in this SRS. Business, market and financial analysis is also out of scope. The **parent/guardian role is optional/future**. Its requirements are marked R3/Could and depend on open issue OI-05.

**Objectives (used for traceability):**
- **OBJ-1 Academic improvement:** turn results and teacher-validated evidence into actionable feedback and personalised practice.
- **OBJ-2 Academic connectivity:** one shared environment for school information, resources and academic interaction.
- **OBJ-3 Teacher authority and trust:** teachers stay the final authority on official results, and AI output is reviewable and traceable.
- **OBJ-4 Data protection:** student records are reachable only by authorised users, and only the data the educational purpose needs is processed.
- **OBJ-5 Measurable progress:** improvement is measured against a baseline, and short-term practice gains are kept distinct from long-term mastery.

### 1.3 Definitions, Acronyms and Abbreviations

| Term | Definition |
|---|---|
| AI Analysis | A machine-generated, structured interpretation of assessment evidence (e.g., possible weak topic, explanation, recommendation), stored with evidence links and a review status. Never an official result. |
| AI Suggestion | Any AI-produced score, explanation, recommendation or generated question that has not been accepted by an authorised teacher. |
| Answer Script | An uploaded digital file, scanned pages or other digitised record of a student's examination answers. |
| Assessment Evidence | Marks, question-/topic-level marks, scripts, marking schemes, teacher comments and practice results used as inputs. |
| Official Result | A mark/result that a teacher (or authorised role) has validated and that is recorded as the result of record. |
| Released | Made visible to the student (and, if enabled, parent) by an authorised teacher/admin action. |
| Tenant | One participating school; the unit of data isolation. |
| Topic | A syllabus/curriculum unit or learning objective to which questions, resources and practice items are mapped. |
| Baseline | The performance measure on a topic before an intervention, used to compute change after reassessment. |
| HITL | Human-in-the-loop: a required human review step before AI output takes effect. |
| MAE | Mean Absolute Error between AI and teacher marks. |
| QWK | Quadratic Weighted Kappa: chance-corrected agreement for ordinal scores. |
| SMD | Standardised Mean Difference between AI and human score means. |
| OCR / HTR | Optical Character Recognition / Handwritten Text Recognition. |
| RBAC | Role-Based Access Control. |
| MoSCoW | Must / Should / Could / Won't (this release). |
| R1 / R2 / R3 | Release 1 = MVP; Release 2 = Early Expansion; Release 3 = Long-term. |
| TBD | To Be Determined — see Appendix C. |
| WCAG | Web Content Accessibility Guidelines (W3C). |

### 1.4 References
1. User document: "System Analysis of AS — AI-Powered Academic Assessment and School Platform" (source of all functional intent).
2. ISO/IEC/IEEE 29148:2018, *Systems and software engineering — Life cycle processes — Requirements engineering* (SRS content and requirement-quality characteristics). It superseded IEEE Std 830-1998 in 2011.\[5\]
3. IEEE Std 830-1998, *Recommended Practice for Software Requirements Specifications* (legacy structure).\[2\]
4. W3C, *Web Content Accessibility Guidelines (WCAG) 2.2*, W3C Recommendation, 5 October 2023.\[6\]
5. OWASP Application Security Verification Standard (ASVS) 5.0.0; OWASP Multi-Tenant Security, IDOR Prevention and Session Management Cheat Sheets.\[7\]\[8\]\[9\]
6. NIST SP 800-63B-4, *Digital Identity Guidelines: Authentication and Authenticator Management*.\[10\]
7. NIST AI 100-1, *AI Risk Management Framework (AI RMF 1.0)*.
8. Williamson, Xi & Breyer (2012), "A Framework for Evaluation and Use of Automated Scoring," *Educational Measurement: Issues and Practice* 31(1).\[11\]
9. U.S. Department of Education, Office of Educational Technology (2023), *Artificial Intelligence and the Future of Teaching and Learning*.\[12\]
10. UNESCO (2023), *Guidance for Generative AI in Education and Research*.\[13\]
11. Regulation (EU) 2024/1689 (EU AI Act), Annex III point 3; Regulation (EU) 2016/679 (GDPR); U.S. FERPA (34 CFR Part 99); U.S. COPPA Rule (16 CFR Part 312, 2025 amendments). These are cited as **examples only**. Applicable law is TBD (OI-01).
12. Google web.dev, "Web Vitals" (Core Web Vitals thresholds).\[14\]

### 1.5 Overview of this Document
Section 2 covers the product context, users, environment, constraints and assumptions. Section 3 covers external interfaces. Section 4 lists functional requirements by module (M1–M9) plus cross-cutting AI-reliability requirements. Section 5 covers non-functional requirements. Section 6 covers the data requirements and state models. Section 7 covers use cases, including the "Sara" end-to-end scenario. Appendix A is the traceability matrix, Appendix B the logical architecture and data flow, and Appendix C the open issues and TBD list.

**Requirement conventions.** Each requirement has a unique ID (`FR-<MODULE>-nnn`, `NFR-<CATEGORY>-nnn`, `DR-nnn`). It uses "shall" for binding requirements. It aims to meet the 29148 characteristics of an individual requirement: necessary, appropriate, unambiguous, complete, singular, feasible, verifiable, correct and conforming.\[15\]\[16\] Each carries **Priority** (M/S/C/W) and **Release** (R1/R2/R3).

---

## 2. Overall Description

### 2.1 Product Perspective
AS is a new, self-contained, multi-tenant web application. It is not a module of an existing school-management system. Each school is a tenant. All modules share one authentication service, one permission system and one logical data store, and they expose different features through role-specific dashboards. AI processing is a separate service layer called by the backend. It may use external AI APIs, internal models, or both (OI-04). The AI layer never makes access-control decisions. Broader school-system integration (e.g., importing rosters from an external student information system) is R3.

### 2.2 Product Functions (summary)

| # | Module | Summary | First release |
|---|---|---|---|
| M1 | School website & institutional portal | Profile, notices, class/subject/teacher info, resources, exam announcements, sign-in entry point | R1 (basic), R2 (extended) |
| M2 | User accounts, roles & academic structure | Invite/bulk enrol, authentication, roles, configurable hierarchy, assignments, enrollments | R1 |
| M3 | Examination & answer-script management | Exam records, manual marks (A), digital upload (B), scanned upload (C), AI-assisted script evaluation (D), validation, release | A: R1; B: R1; C: R2; D: R3 (pilot R2) |
| M4 | AI assessment intelligence | Student-level and class-level gap analysis with evidence and review status | R1 (student), R1/R2 (class) |
| M5 | Personalised learning resources | Topic-tagged resources, recommendations, learning paths, teacher control | R1 |
| M6 | Targeted practice & mock tests | Assemble/assign practice, take tests, evaluate, reassess, measure improvement | R1 (objective items), R2+ (richer generation) |
| M7 | Student dashboard | Overview, exam records, gap report, learning plan, progress history | R1 |
| M8 | Teacher dashboard | Class overview, exam management, validation, AI review, sharing, monitoring | R1 |
| M9 | School administrator dashboard | Profile/portal, users, structure, notices, settings, institutional reports | R1 |

### 2.3 User Classes and Characteristics

| User class | Description | Technical skill (assumed) | Frequency | Key needs |
|---|---|---|---|---|
| **School Administrator** | Primary institutional user. Manages the portal, academic structure, users, notices and settings | Moderate | Weekly; peaks at term start | Bulk setup, correct relationships, controlled access |
| **Teacher** | Manages assigned exams and assessments, validates marks, reviews AI output, shares resources, monitors progress | Varied; may be low | Several times per week; peaks after exams | Low extra workload, full control over official results, clear evidence |
| **Student** | Primary learner. Sees released results, gap reports, recommendations, practice and progress | Varied; school-age; often mobile | Frequent | Plain-language explanations, a clear next action |
| **Parent/Guardian** *(optional/future, R3)* | May see permitted progress summaries, teacher updates and recommendations | Varied | Occasional | Permissions not yet defined (OI-05) |
| **Platform Operator (Super-admin)** | The AS team: provisions tenants, operates infrastructure, handles support | High | Continuous | Tenant provisioning without routine access to student content |

Platform Operator is an implied role that the user's document does not name. It is needed to provision schools. It is restricted to the minimum access needed (see NFR-PRIV-006).

### 2.4 Permission Matrix (role × action)

Legend: **Y** = allowed. **A** = only for assigned classes/subjects/students. **O** = own records only. **R** = only after release. **P** = only if permitted by school setting/TBD. **—** = not allowed.

| Action | Student | Teacher | School Admin | Parent (R3) | Platform Operator |
|---|---|---|---|---|---|
| View public school portal | Y | Y | Y | Y | Y |
| Edit school profile/portal content | — | — | Y | — | — (support only on request) |
| Publish school-wide notices | — | P | Y | — | — |
| Publish class/subject notices | — | A | Y | — | — |
| Create/invite/deactivate users | — | — | Y | — | Y (tenant's first admin only) |
| Configure academic years, classes, sections, subjects | — | — | Y | — | — |
| Assign teachers to classes/subjects; enrol students | — | — | Y | — | — |
| Create/edit examination record | — | A | P | — | — |
| Upload/view answer scripts | O,R | A | P | — | — |
| Enter/edit marks before validation | — | A | — | — | — |
| Validate official marks | — | A | — | — | — |
| Change an official mark after validation | — | A (with reason; audited) | — | — | — |
| Release results to students | — | A | P | — | — |
| Request AI analysis | — | A | — | — | — |
| Review/accept/edit/reject AI analysis | — | A | — | — | — |
| View released AI feedback / gap report | O,R | A | P (aggregate by default) | P | — |
| View class-level analytics | — | A | P (aggregate) | — | — |
| Create/share learning resources | — | A | Y (school library) | — | — |
| Create/assign practice tests | — | A | — | — | — |
| Take practice tests | O | — | — | — | — |
| View progress history | O | A | P | P | — |
| View institutional usage reports | — | — | Y | — | Y (non-identifying) |
| View audit log | — | O (own actions) | Y (tenant) | — | Y (platform events) |
| Manage school settings (feature toggles) | — | — | Y | — | Y (tenant provisioning) |

### 2.5 Operating Environment
- **Client:** current and previous major versions of Chrome, Edge, Firefox and Safari on desktop, plus Chrome (Android) and Safari (iOS) on mobile. Responsive layouts from 360 px wide. **[Proposed]**
- **Server:** cloud-hosted. Containerised application services, a managed relational database, private object storage for files, a managed queue for AI jobs, and centralised logging and monitoring. Hosting region is TBD (OI-01, OI-10).
- **AI services:** an external AI API and/or internally hosted models reached through an internal AI gateway (OI-04).
- **Network:** public internet over HTTPS only. Pilot schools may have limited bandwidth (see NFR-PERF-006).

### 2.6 Design and Implementation Constraints
- **C-01:** The AI component shall not decide access to records. Authorisation is enforced only by the application's permission system.
- **C-02:** The MVP shall not depend on automated handwriting evaluation (Option D).
- **C-03:** Official results, AI interpretations, raw evidence, released results and practice outcomes shall be separately stored and status-tracked entities.
- **C-04:** Files shall live in private object storage. The database stores identifiers and metadata only.
- **C-05:** The academic hierarchy shall be configurable per school and not hard-coded.
- **C-06:** Legal and regulatory obligations are unknown until jurisdiction is fixed (OI-01). The design must allow region-specific hosting, retention and consent configuration.
- **C-07:** Student data sent to third-party AI services must be minimised and pseudonymised (see FR-AI-020 to FR-AI-023).

### 2.7 Assumptions and Dependencies
- **AS-01:** Pilot schools can supply class lists, subject lists and teacher assignments in a spreadsheet format.
- **AS-02:** Teachers can tag questions with topics, or can choose from a provided topic list (curriculum mapping is OI-08).
- **AS-03:** For MVP AI analysis, at least question-level or topic-level marks are available for an exam. If only a total mark exists, AI analysis is limited (FR-AI-007).
- **AS-04:** Students have access to a web browser (school or personal device).
- **DEP-01:** Availability, terms and data-processing commitments of the chosen AI provider (OI-04).
- **DEP-02:** Cloud provider region availability that meets data-residency needs (OI-10).
- **DEP-03:** A validated question bank or teacher-supplied items are needed for targeted practice in R1.

---

## 3. External Interface Requirements

### 3.1 User Interfaces

| ID | Requirement | Pri | Rel |
|---|---|---|---|
| UI-001 | The system shall provide separate role-specific dashboards for Student, Teacher and School Administrator after sign-in. | M | R1 |
| UI-002 | The system shall visually distinguish official teacher-approved results from AI-generated content using a persistent label (e.g., "Teacher-approved" vs "AI suggestion — reviewed/unreviewed") and a distinct visual style on every screen where both appear. | M | R1 |
| UI-003 | The student dashboard shall link each released result to its explanation and to the next recommended action within no more than two navigation steps. | M | R1 |
| UI-004 | The system shall present AI findings in plain language, with a "Why am I seeing this?" control that lists the supporting questions/assessments. | M | R1 |
| UI-005 | The system shall present any improvement figure with the comparison basis (e.g., "4/10 → 8/10 on comparable linear-equation questions") and a note that one reassessment does not prove long-term mastery. | M | R1 |
| UI-006 | All UIs shall be responsive from 360 px to 1920 px wide without horizontal scrolling of primary content. **[Proposed]** | M | R1 |
| UI-007 | The UI language shall be externalised to resource files to support additional languages (languages TBD, OI-07). | S | R1 |

### 3.2 Hardware Interfaces
| ID | Requirement | Pri | Rel |
|---|---|---|---|
| HW-001 | The system shall accept scanned answer scripts produced by standard document scanners or phone cameras as PDF, JPEG or PNG files. | M | R2 |
| HW-002 | The system shall not require any dedicated hardware at the school beyond a browser-capable device and, for Option C, a scanner or camera. | M | R1 |

### 3.3 Software Interfaces
| ID | Requirement | Pri | Rel |
|---|---|---|---|
| SW-001 | The backend shall reach AI capabilities only through an internal AI gateway interface that accepts structured, pseudonymised inputs and returns structured JSON outputs validated against a versioned schema. | M | R1 |
| SW-002 | The AI gateway shall record the provider, model identifier/version, prompt/template version and timestamp for every AI request. | M | R1 |
| SW-003 | The system shall import users and enrollments from CSV/XLSX files using a published template. | M | R1 |
| SW-004 | The system shall export a school's academic records (per student, per class) in CSV and PDF on authorised request. | S | R2 |
| SW-005 | The system should provide integration interfaces (e.g., roster sync, SSO) for external school systems. | C | R3 |
| SW-006 | The system shall send transactional e-mail (invites, password reset, release notifications) through a configurable e-mail service. | M | R1 |

### 3.4 Communications Interfaces
| ID | Requirement | Pri | Rel |
|---|---|---|---|
| COM-001 | All client–server and server–AI-provider traffic shall use TLS 1.2 or higher (TLS 1.3 preferred). | M | R1 |
| COM-002 | The system shall expose a versioned REST/JSON API to its own frontend, and every endpoint shall require authentication except the public portal pages. | M | R1 |
| COM-003 | In-app notifications shall tell students when a result, feedback or practice assignment is released to them. | S | R1 |

---

## 4. Functional Requirements

Format: **ID — Requirement (Priority, Release)**. Acceptance criteria (AC) are given where useful.

### 4.1 Module 1 — School Website and Institutional Portal (FR-PORT)

| ID | Requirement | Pri | Rel |
|---|---|---|---|
| FR-PORT-001 | The system shall provide each school a portal at a unique school-specific address (subdomain or path). | M | R1 |
| FR-PORT-002 | The system shall let the School Administrator maintain school name, description, logo and basic institutional profile. | M | R1 |
| FR-PORT-003 | The system shall let the School Administrator publish, edit, schedule and archive notices and announcements. | M | R1 |
| FR-PORT-004 | The system shall let notices be targeted at the whole school, a class, a section or a subject audience. | S | R1 |
| FR-PORT-005 | The system shall show an authenticated user only the notices targeted at their school and enrollment/assignment. | M | R1 |
| FR-PORT-006 | The system shall let the School Administrator publish information about classes, subjects and teachers, with per-field visibility (public vs signed-in only). | S | R2 |
| FR-PORT-007 | The system shall let administrators and teachers publish educational resource links on the portal. | S | R1 |
| FR-PORT-008 | The system shall show exam-related announcements and schedules drawn from M3 exam records marked "announce". | S | R2 |
| FR-PORT-009 | The system shall provide a sign-in entry point on the portal that leads to the user's role dashboard. | M | R1 |
| FR-PORT-010 | The public (unauthenticated) portal shall not display any student personal data. | M | R1 |
| FR-PORT-011 | The system should support extended institutional pages (e.g., custom pages, galleries) configurable by the administrator. | C | R2 |

AC (FR-PORT-005): A Class 9A student signed in sees school-wide and 9A notices and does not see 9B-only notices. This is verified by an automated test using two student accounts.

### 4.2 Module 2 — User Accounts, Roles and Academic Structure (FR-AUTH, FR-ACAD)

**Accounts and authentication**

| ID | Requirement | Pri | Rel |
|---|---|---|---|
| FR-AUTH-001 | The system shall let the School Administrator create user accounts individually by e-mail/username invitation. | M | R1 |
| FR-AUTH-002 | The system shall let the School Administrator bulk-create students and staff from an approved CSV/XLSX list. Before committing, it shall validate the file and report row-level errors. | M | R1 |
| FR-AUTH-003 | The system shall authenticate users with credentials and, after verification, resolve the user's school (tenant) and role(s) from server-side records only. | M | R1 |
| FR-AUTH-004 | The system shall load the dashboard that matches the authenticated user's role. If a user holds several roles, it shall let them switch role context. | M | R1 |
| FR-AUTH-005 | The system shall deny access to any record outside the user's permissions and return a non-revealing error. | M | R1 |
| FR-AUTH-006 | The system shall provide self-service password reset through a time-limited, single-use link. | M | R1 |
| FR-AUTH-007 | The system shall support multi-factor authentication (MFA) and shall require it for School Administrator and Platform Operator accounts. | M | R1 |
| FR-AUTH-008 | The system should support MFA for teachers as a school-configurable setting. | S | R2 |
| FR-AUTH-009 | The system shall let administrators deactivate accounts. Deactivation shall end active sessions within 60 seconds. **[Proposed]** | M | R1 |
| FR-AUTH-010 | The system should support single sign-on with school identity providers (e.g., SAML/OIDC). | C | R3 |
| FR-AUTH-011 | The system shall support a Parent/Guardian role linked to one or more students, with permissions defined per OI-05. | C | R3 |

**Academic structure**

| ID | Requirement | Pri | Rel |
|---|---|---|---|
| FR-ACAD-001 | The system shall represent the hierarchy School → Academic Year → Class/Grade → Section → Subject → Teacher Assignment → Student Enrollment. | M | R1 |
| FR-ACAD-002 | The system shall let each school configure hierarchy labels and optional levels (e.g., schools without sections). | S | R1 |
| FR-ACAD-003 | The system shall let the School Administrator create, edit and close academic years. Records shall stay attributed to the year in which they were created. | M | R1 |
| FR-ACAD-004 | The system shall let the School Administrator assign teachers to (class/section, subject, academic year) combinations. | M | R1 |
| FR-ACAD-005 | The system shall let the School Administrator enrol students into class/section and subject offerings for an academic year. | M | R1 |
| FR-ACAD-006 | The system shall support moving students between sections or into a new academic year while keeping historical records linked to the original context. | S | R1 |
| FR-ACAD-007 | The system shall reject creation of an assessment result whose student is not enrolled in the exam's class/subject for that academic year. | M | R1 |
| FR-ACAD-008 | The system shall let administrators maintain a per-subject topic list (syllabus units/learning objectives) that teachers can extend. Curriculum source is TBD (OI-08). | M | R1 |

AC (FR-ACAD-007): An attempt to save a mark for a student who is not enrolled in Class 9A Mathematics 2026–27 is rejected with a validation error, and no result record is created.

### 4.3 Module 3 — Examination and Answer-Script Management (FR-EXAM)

**Examination records**

| ID | Requirement | Pri | Rel |
|---|---|---|---|
| FR-EXAM-001 | The system shall let an assigned teacher create an examination with: name, date, class/section or selected students, subject, topic coverage, total marks, optional section-wise marks, marking scheme/criteria (text or file), assigned teacher and status. | M | R1 |
| FR-EXAM-002 | The system shall let the teacher define questions with max marks, question type (objective, short answer, long answer, numerical, diagram) and one or more topic tags. | M | R1 |
| FR-EXAM-003 | The system shall track each examination through the status model in §6.3. | M | R1 |
| FR-EXAM-004 | The system shall let a School Administrator coordinate school-wide exams (e.g., create term-exam shells for teachers to complete) when the school setting allows it. | C | R2 |

**Evidence capture (Options A–D)**

| ID | Requirement | Pri | Rel |
|---|---|---|---|
| FR-EXAM-010 | **Option A:** The system shall let the teacher enter per-student total marks and, optionally, per-question marks through a grid. Total marks shall be computed automatically from question marks when those are provided. | M | R1 |
| FR-EXAM-011 | The system shall let the teacher import per-question marks from a CSV/XLSX template. | S | R1 |
| FR-EXAM-012 | The system shall reject any mark that is above the question's maximum or negative. | M | R1 |
| FR-EXAM-013 | **Option B:** The system shall let the teacher upload a digital answer script (PDF/DOCX/image) and link it to one student and one examination. | M | R1 |
| FR-EXAM-014 | **Option C:** The system shall let a teacher or authorised staff member upload scanned pages, either in bulk (one PDF for many students) or per student, and associate pages with the right student and examination. | S | R2 |
| FR-EXAM-015 | For bulk scanned uploads, the system shall propose page-to-student matching (e.g., from cover-sheet identifiers) and shall require human confirmation of every match that is unmatched or low-confidence. | S | R2 |
| FR-EXAM-016 | The system shall flag an uploaded file as "Unreadable/needs manual review" when automated quality checks fail (e.g., blank, rotated, low resolution). It shall not discard the file. | S | R2 |
| FR-EXAM-017 | **Option D:** The system shall provide AI-assisted evaluation of written scripts that produces proposed per-question marks and rationales, stored only as AI Suggestions pending teacher verification. | C | R3 (limited pilot R2, per §4.10 gates) |
| FR-EXAM-018 | The system shall let Options A–D coexist within one examination (e.g., manual marks plus uploaded script). | M | R1 |

**Validation and release**

| ID | Requirement | Pri | Rel |
|---|---|---|---|
| FR-EXAM-020 | The system shall require explicit teacher validation before any mark becomes an Official Result. | M | R1 |
| FR-EXAM-021 | The system shall let the teacher validate results per student or in bulk per examination. | M | R1 |
| FR-EXAM-022 | The system shall require a reason, and create an audit record, whenever an Official Result is changed after validation. | M | R1 |
| FR-EXAM-023 | The system shall let the teacher control release separately for: marks, evaluated script, teacher comments and AI feedback. | M | R1 |
| FR-EXAM-024 | The system shall not show students any result, script, comment or AI feedback before it is released. | M | R1 |
| FR-EXAM-025 | The system shall let the teacher withdraw a release (un-release), with an audit record. | S | R1 |
| FR-EXAM-026 | AI Suggestions shall never write to the Official Result entity. Only a teacher action may create or change an Official Result. | M | R1 |
| FR-EXAM-027 | The system shall let the teacher record feedback/comments per student and per question, stored as Teacher Feedback linked to the result. | M | R1 |
| FR-EXAM-028 | After release, the system shall show the student: approved mark and exam details, released evaluated script, teacher comments, released AI feedback (labelled), topic-level strengths and weaknesses, and recommended resources/practice. | M | R1 |

AC (FR-EXAM-026): An automated test injects an AI-suggested mark for a validated student. The official mark is unchanged, and the AI value is visible only in the AI-suggestion view with status "Generated".

### 4.4 Module 4 — AI Assessment Intelligence (FR-AI)

**Inputs and preconditions**

| ID | Requirement | Pri | Rel |
|---|---|---|---|
| FR-AI-001 | The system shall run AI analysis only on assessment data in status Validated or later, never on unvalidated marks. | M | R1 |
| FR-AI-002 | The system shall let analysis use, when available: exam results, question-wise marks, topic tags, question paper and marking scheme, teacher comments, prior exam results, prior practice results, and records of completed recommendations. | M | R1 |
| FR-AI-003 | The system shall let analysis use teacher-validated script text or supported scanned content. | S | R2 |
| FR-AI-004 | Before calling the AI service, the system shall verify that the student, examination, subject, academic year and topic associations are complete and consistent, and shall reject the request with a reason if they are not. | M | R1 |

**Analysis behaviour**

| ID | Requirement | Pri | Rel |
|---|---|---|---|
| FR-AI-005 | The system shall produce student-level analysis that identifies possible weak topics, strengths, changes across assessments, and suggested next steps. | M | R1 |
| FR-AI-006 | Each finding shall include: topic, finding type (weakness/strength/trend), plain-language explanation, list of supporting evidence items (exam, question IDs, marks), evidence-sufficiency level, and generation metadata (model/version, time). | M | R1 |
| FR-AI-007 | The system shall not state a specific misconception when the evidence is only an overall score. In that case it shall produce at most a general "insufficient detail" message and a suggestion to record question- or topic-level marks. | M | R1 |
| FR-AI-008 | The system shall flag a topic as a "possible weakness" only when the evidence meets a configurable rule. Default **[Proposed]**: ≥2 questions on the topic across ≥1 assessment with topic score below 50%, or a recurring low topic score in ≥2 assessments. | M | R1 |
| FR-AI-009 | The system shall word findings as data-supported indications (e.g., "may need help with"), not as certain diagnoses. | M | R1 |
| FR-AI-010 | The system shall produce class-level analysis that aggregates topic performance across the students of an assigned class/subject and highlights topics where a configurable share of students (default 40% **[Proposed]**) are flagged. | M | R1 |
| FR-AI-011 | The system shall show change in class-level topic performance between successive assessments that cover the topic. | S | R2 |
| FR-AI-012 | The system should support improved longitudinal learning models (e.g., mastery estimation across many assessments). | C | R3 |

**Output validation, status and review**

| ID | Requirement | Pri | Rel |
|---|---|---|---|
| FR-AI-013 | The backend shall validate every AI output against the versioned output schema. It shall reject outputs that fail validation, or that reference questions, topics or students absent from the input, and shall mark them "Failed". | M | R1 |
| FR-AI-014 | The system shall store every AI Analysis with a review status following the state model in §6.4. | M | R1 |
| FR-AI-015 | The system shall let the assigned teacher accept, edit or reject each finding and recommendation, and shall preserve the original AI text alongside any edit. | M | R1 |
| FR-AI-016 | The system shall let each school choose a release policy for AI feedback: (a) teacher review required before release (default), or (b) auto-release of low-risk recommendation types after a configurable delay, with teacher override. | S | R1 |
| FR-AI-017 | If an AI request fails or times out, the system shall keep all assessment records unchanged, set the analysis status to "Failed", notify the teacher, and allow retry. | M | R1 |
| FR-AI-018 | The system shall let a teacher record a reason when rejecting or editing a finding, so that correction rates can be measured (see §4.10). | S | R1 |
| FR-AI-019 | The system shall let the teacher see, for each finding, the exact evidence items used and whether a teacher reviewed it (traceability). | M | R1 |

**Data sent to AI services**

| ID | Requirement | Pri | Rel |
|---|---|---|---|
| FR-AI-020 | The system shall replace student names and direct identifiers with internal pseudonymous IDs before sending data to any external AI service. | M | R1 |
| FR-AI-021 | The system shall send to AI services only the fields listed in a documented, versioned data-minimisation allow-list for each AI task. | M | R1 |
| FR-AI-022 | The system shall send to external AI services only scanned content that is cropped or redacted to remove names and identifiers, where technically feasible. | S | R2 |
| FR-AI-023 | The system shall use only AI providers whose contractual terms prohibit using submitted student data to train or improve general models, and set retention limits. Provider choice and terms are tracked in OI-04. | M | R1 |

### 4.5 Module 5 — Personalised Learning Resources (FR-RES)

| ID | Requirement | Pri | Rel |
|---|---|---|---|
| FR-RES-001 | The system shall let teachers upload resources (files) and add external links, each with metadata: subject, class level, topic(s), learning objective, type, difficulty (optional). | M | R1 |
| FR-RES-002 | The system shall let administrators maintain a school-level resource library visible to that school's teachers. | S | R1 |
| FR-RES-003 | The system shall recommend resources to a student by matching flagged topics to resource metadata, limited to resources approved for the student's class level and subject. | M | R1 |
| FR-RES-004 | The system shall order a recommendation as a learning path, for example: (1) principle + worked example, (2) teacher explanation, (3) basic practice, (4) harder practice, (5) targeted reassessment. | S | R1 |
| FR-RES-005 | The system shall let the assigned teacher approve, reorder, replace or remove recommended resources before or after release. | M | R1 |
| FR-RES-006 | The system shall record when a student opens a recommended resource and when they mark it complete. | M | R1 |
| FR-RES-007 | The system shall label AI-generated explanations as AI-generated, and shall show them to students only after teacher approval (or under the school's FR-AI-016 policy). | S | R2 |
| FR-RES-008 | The system shall let teachers manage a question bank with each item tagged by subject, topic, difficulty, question type and answer key/marking guidance. | M | R1 |
| FR-RES-009 | The system shall support new resource formats (e.g., video, interactive) through a pluggable content-type registry. | C | R3 |

### 4.6 Module 6 — Targeted Practice, Demo Exams and Mock Tests (FR-PRAC)

| ID | Requirement | Pri | Rel |
|---|---|---|---|
| FR-PRAC-001 | The system shall build a targeted practice test from: flagged topics, curriculum mapping, the student's prior results, question-bank items with topic/difficulty tags, teacher rules, and desired length and difficulty. | M | R1 |
| FR-PRAC-002 | The system shall let teachers define practice rules (e.g., item count, difficulty mix, time limit, attempts allowed). | M | R1 |
| FR-PRAC-003 | The system shall let teachers assign practice tests to individual students, groups or a whole class. | M | R1 |
| FR-PRAC-004 | The system shall let students open an assigned or recommended test, read instructions, answer, save progress and submit. | M | R1 |
| FR-PRAC-005 | The system shall auto-score objective items with a defined answer key immediately on submission. | M | R1 |
| FR-PRAC-006 | The system shall send subjective/open responses to teacher evaluation, or (when enabled and validated per §4.10) to AI-assisted evaluation followed by the review flow, before showing a score. | S | R2 |
| FR-PRAC-007 | After evaluation, the system shall show the student the result, item-level feedback and the next recommended action. | M | R1 |
| FR-PRAC-008 | The system shall generate AI-produced practice questions only as drafts with status "Generated". They shall be used only after a teacher marks them correct, relevant and of appropriate difficulty. | S | R2 |
| FR-PRAC-009 | The system shall build reassessments from items comparable in topic and difficulty to the baseline items, and shall exclude identical items unless the teacher allows reuse. | S | R1 |
| FR-PRAC-010 | The system shall compute improvement as the change in percentage score on comparable topic items between baseline and reassessment, and shall store both values in a Progress Record. | M | R1 |
| FR-PRAC-011 | The system shall label a single improved reassessment as "Improved on practice"; label it "Consistent improvement" only after improvement is sustained across ≥2 comparable later assessments **[Proposed]**; and never label any result "mastered" automatically. | M | R1 |
| FR-PRAC-012 | After a practice attempt, the system shall recommend the next step: advance (harder items) if the improvement threshold is met; further practice or teacher support if it is not. | M | R1 |
| FR-PRAC-013 | The system should support more sophisticated mock-exam generation (full-length, multi-topic, timed). | C | R2 |

AC (FR-PRAC-010/011): Baseline 4/10 and reassessment 8/10 on comparable linear-equation items produce a Progress Record showing 40% → 80% labelled "Improved on practice", not "mastered".

### 4.7 Module 7 — Student Dashboard (FR-STU)

| ID | Requirement | Pri | Rel |
|---|---|---|---|
| FR-STU-001 | The system shall show an Academic Overview: enrolled subjects, recent released results, upcoming exams and relevant notices. | M | R1 |
| FR-STU-002 | The system shall show Examination Records: released results, exam history and released scripts/feedback. | M | R1 |
| FR-STU-003 | The system shall show a Learning-Gap Report summarising released findings with reasons and links to supporting assessments. | M | R1 |
| FR-STU-004 | The system shall show My Learning Plan: recommended resources, assigned/recommended practice tests and teacher-assigned activities with status. | M | R1 |
| FR-STU-005 | The system shall show Progress History: past assessments and practice results with per-topic trends. | M | R1 |
| FR-STU-006 | The system shall show students only their own records. | M | R1 |
| FR-STU-007 | The system shall let a student go from a released result to the related gap finding and then to the recommended practice in one continuous flow (see UI-003). | M | R1 |

### 4.8 Module 8 — Teacher Dashboard (FR-TCH)

| ID | Requirement | Pri | Rel |
|---|---|---|---|
| FR-TCH-001 | The system shall show the teacher only their assigned classes, subjects and students. | M | R1 |
| FR-TCH-002 | The system shall provide examination management (create, upload/access scripts, enter marks, manage status) for assigned exams. | M | R1 |
| FR-TCH-003 | The system shall provide a validation queue listing results awaiting validation and AI evaluations awaiting verification. | M | R1 |
| FR-TCH-004 | The system shall provide an AI-review queue that lists each finding with its evidence and accept/edit/reject actions. | M | R1 |
| FR-TCH-005 | The system shall let teachers share resources, assign practice and post instructions to classes or students. | M | R1 |
| FR-TCH-006 | The system shall show individual and class-level topic patterns, including students flagged on each topic. | M | R1 |
| FR-TCH-007 | The system shall show change in a class's topic performance after reteaching or assigned practice (before/after comparison). | S | R2 |
| FR-TCH-008 | The system should provide richer analytics (e.g., item difficulty, distractor analysis, cohort comparisons). | C | R2 |
| FR-TCH-009 | The system shall show the teacher which results are released and which are pending, for each examination. | M | R1 |

### 4.9 Module 9 — School Administrator Dashboard (FR-ADM)

| ID | Requirement | Pri | Rel |
|---|---|---|---|
| FR-ADM-001 | The system shall let the administrator maintain the school profile and portal content (M1). | M | R1 |
| FR-ADM-002 | The system shall let the administrator manage user accounts and access (M2). | M | R1 |
| FR-ADM-003 | The system shall let the administrator set up classes, sections, subjects, academic years, teacher assignments and enrollments (M2). | M | R1 |
| FR-ADM-004 | The system shall let the administrator publish notices (M1). | M | R1 |
| FR-ADM-005 | The system shall let the administrator manage school-level settings permitted to them (feature toggles such as Option C/D enablement, AI-release policy, MFA for teachers). | M | R1 |
| FR-ADM-006 | The system shall provide institutional reports on platform usage and academic activity, aggregated by default. | S | R1 |
| FR-ADM-007 | The system shall show identifiable student-level academic data to an administrator only if the school's policy grants that role this access (configurable; default off). | M | R1 |
| FR-ADM-008 | The system shall let the administrator view the tenant audit log with filters (user, action, date, entity). | S | R1 |
| FR-ADM-009 | The system should let the administrator coordinate exam processes school-wide (see FR-EXAM-004). | C | R2 |

### 4.10 Cross-Cutting AI Reliability and Evaluation Requirements (FR-AIREL)

These requirements put into practice the user's §9 and widely used automated-scoring evaluation practice. Williamson, Xi & Breyer (2012) give acceptance guidance: quadratic weighted kappa (QWK) of at least 0.70 between automated and human scores, a standardised mean score difference no greater than 0.15, and no more than 0.10 degradation from human–human agreement.\[17\]\[18\]\[19\] Treat these as **starting thresholds** to confirm with pilot data, not as guarantees.

| ID | Requirement | Pri | Rel |
|---|---|---|---|
| FR-AIREL-001 | The team shall maintain a teacher-validated reference dataset per subject and question type, separate from any data used to tune prompts/models, for evaluating every AI capability before enablement. | M | R1 |
| FR-AIREL-002 | The system shall log, for every AI finding and AI-suggested mark, the teacher's decision (accept/edit/reject) and, for marks, the final official value, to enable continuous evaluation. | M | R1 |
| FR-AIREL-003 | The system shall compute and report the following per subject, per question type and per AI capability: exact agreement %, adjacent (±1 mark) agreement %, QWK, MAE, SMD, maximum absolute error, teacher correction/rejection rate, topic-classification accuracy (precision/recall vs teacher labels), and unreadable/unsupported failure rate. | M | R2 (R1 for topic classification and correction rate) |
| FR-AIREL-004 | AI-assisted marking (Option D, FR-PRAC-006) shall not be enabled for a subject/question type unless, on the reference dataset: QWK ≥ 0.70, \|SMD\| ≤ 0.15, AI–human QWK no more than 0.10 below human–human QWK, and ≤ 2% of items differ from the teacher mark by more than 20% of the item maximum. **[Proposed gates]** | M | R2/R3 |
| FR-AIREL-005 | The system shall report evaluation metrics separately for objective, short-answer, long-answer, numerical and diagram items, and shall not present a single blended accuracy figure as evidence of reliability. | M | R2 |
| FR-AIREL-006 | Where student subgroup data is lawfully available and approved (OI-01), the team should check that \|SMD\| ≤ 0.10 for each subgroup. **[Proposed]** | S | R3 |
| FR-AIREL-007 | Topic-classification of questions by AI shall not be used in student-facing findings unless a teacher has confirmed the topic tag, or classification accuracy on the reference set is ≥ 90% **[Proposed]**. | M | R1 |
| FR-AIREL-008 | The system shall attach a confidence/uncertainty indicator to each AI-suggested mark and each AI-read script region, and shall route items below a configurable threshold to mandatory manual review. | M | R2 |
| FR-AIREL-009 | The system shall never put a guessed score in place of missing, unreadable or unsupported evidence. Such items shall be flagged "Needs manual review" with the reason (e.g., illegible, diagram, out-of-scope). | M | R1 |
| FR-AIREL-010 | When OCR/HTR legibility checks fail for a script, the system shall stop AI evaluation for that script and place it in the teacher's manual queue. | M | R2 |
| FR-AIREL-011 | The system should run each AI-assisted marking request more than once (e.g., 3–5 independent passes) and flag disagreement between passes above a threshold for human review. **[Proposed]** | S | R3 |
| FR-AIREL-012 | The team shall re-run the evaluation suite whenever the AI provider, model version, prompt template or marking scheme format changes, and shall block deployment of the change if gates in FR-AIREL-004 are no longer met. | M | R2 |
| FR-AIREL-013 | The system shall produce a monthly AI quality report per school (aggregate metrics from FR-AIREL-003) visible to the Platform Operator and School Administrator. | S | R2 |
| FR-AIREL-014 | Teachers shall be able to rate the usefulness of each AI finding (e.g., 1–5), and the system shall report mean usefulness per capability. | S | R1 |

**Why these gates matter (context).** Published handwritten-grading studies show the failure modes these requirements guard against. In a UC Irvine study of AI grading of handwritten calculus work (Yu et al., arXiv:2603.00895, 2026), independent reviewers checked 3,851 student–question records, rated 12.36% of scripts' OCR as "Problematic", and judged 10.67% of AI evaluations "incorrect" (79.79% were fully correct). A human-in-the-loop study at Vrije Universiteit Brussel pseudonymised submissions and sent the model only cropped answer-box images. In that study (Vanhoyweghen et al., arXiv:2603.13083, 2026), each response was graded in five independent LLM passes. About 3% of cases still showed larger human-vs-model discrepancies, and the authors concluded that automated inconsistency detection alone is insufficient. Mandatory human verification contained those errors while cutting grading time by about 23%. In K-12 short-answer marking, a University of Oxford/Carousel Learning study (Henkel et al., arXiv:2405.02985) covered 1,710 UK Science and History answers from students aged 5–16. It found that GPT-4 with basic few-shot prompting reached Cohen's kappa 0.70 against the ground truth, versus 0.75 between human raters. That is close to human level, but not equal. Schools also deserve more caution than these university settings, because their students are younger and their handwriting more varied.

---

## 5. Non-Functional Requirements

All numeric values are **[Proposed]** defaults for confirmation by the team (see OI-12).

### 5.1 Performance (NFR-PERF)
| ID | Requirement | Pri | Rel |
|---|---|---|---|
| NFR-PERF-001 | Routine dashboard and record views shall respond (server time) in ≤ 1.0 s at the 95th percentile under expected load. | M | R1 |
| NFR-PERF-002 | Pages shall meet Google's Core Web Vitals "good" thresholds at the 75th percentile: LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1.\[14\] | S | R1 |
| NFR-PERF-003 | Saving a mark grid of 60 students × 20 questions shall complete in ≤ 3 s at the 95th percentile. | M | R1 |
| NFR-PERF-004 | Student-level AI analysis for one examination shall complete within 2 minutes at the 95th percentile, processed asynchronously with visible status. | S | R1 |
| NFR-PERF-005 | Objective practice tests shall be scored and results shown within 5 s of submission. | M | R1 |
| NFR-PERF-006 | The student dashboard initial load shall be ≤ 1.5 MB transferred, to support low-bandwidth schools. | S | R1 |
| NFR-PERF-007 | File uploads up to 50 MB per file shall be supported, with resumable upload for scanned bundles. | S | R2 |

### 5.2 Scalability (NFR-SCAL)
| ID | Requirement | Pri | Rel |
|---|---|---|---|
| NFR-SCAL-001 | R1 shall support at least 10 schools, 10,000 users and 1,000 concurrent sessions without breaching NFR-PERF-001. | M | R1 |
| NFR-SCAL-002 | The architecture shall scale horizontally to at least 200 schools / 200,000 users without redesign of the data model. | S | R2 |
| NFR-SCAL-003 | AI jobs shall be processed through a queue so that peaks (e.g., after term exams) delay AI analysis but never block mark entry, validation or release. | M | R1 |

### 5.3 Security (NFR-SEC)
| ID | Requirement | Pri | Rel |
|---|---|---|---|
| NFR-SEC-001 | The application shall be verified against OWASP ASVS 5.0 Level 2 before pilot go-live.\[20\] | M | R1 |
| NFR-SEC-002 | Every API request touching tenant data shall derive the tenant from the authenticated session/token. It shall never take the tenant from a client-supplied header, parameter or body. | M | R1 |
| NFR-SEC-003 | Every data access shall enforce object-level authorisation (role + tenant + assignment/ownership) on the server to prevent insecure direct object reference. | M | R1 |
| NFR-SEC-004 | Automated tests shall include cross-tenant and cross-role access attempts for every resource type. Zero successful unauthorised accesses is the release criterion. | M | R1 |
| NFR-SEC-005 | Passwords used as the only factor shall be at least 15 characters. Passwords used with MFA shall be at least 8 characters. Maximum length shall be at least 64. The system shall check passwords against a breached-password list, shall not impose composition rules or periodic rotation, and shall allow password managers and paste (aligned with NIST SP 800-63B-4).\[21\]\[22\] | M | R1 |
| NFR-SEC-006 | Login attempts shall be rate-limited (e.g., ≤ 10 failed attempts per account per 15 min, then progressive delay). | M | R1 |
| NFR-SEC-007 | Sessions shall expire after 30 min inactivity for staff and 60 min for students, with an absolute limit of 12 h. Re-authentication shall be required for sensitive actions (changing official marks, bulk release, role changes). | M | R1 |
| NFR-SEC-008 | Session cookies shall be Secure, HttpOnly and SameSite=Lax or stricter. | M | R1 |
| NFR-SEC-009 | Uploaded scripts and files shall be stored in private object storage with no public access. Access shall be granted only through signed URLs issued after an authorisation check, expiring in ≤ 5 minutes.\[23\]\[24\] | M | R1 |
| NFR-SEC-010 | File object keys shall be random and non-guessable, and signed URLs shall not be written to application logs. | M | R1 |
| NFR-SEC-011 | Uploaded files shall be checked for type and size and scanned for malware before they become accessible. | M | R1 |
| NFR-SEC-012 | Data shall be encrypted at rest (AES-256 or provider equivalent) for the database, object storage and backups. | M | R1 |
| NFR-SEC-013 | Secrets (API keys, DB credentials) shall be held in a managed secrets store and rotated at least every 90 days or on suspected compromise. | M | R1 |
| NFR-SEC-014 | Inputs to AI services shall be treated as untrusted, and AI outputs shall be treated as untrusted data (schema-validated, escaped on display). AI outputs shall never be executed as code or used to make authorisation decisions. | M | R1 |
| NFR-SEC-015 | An independent penetration test shall be completed before the first pilot release and annually thereafter. | S | R1 |

### 5.4 Privacy and Data Protection (NFR-PRIV)
| ID | Requirement | Pri | Rel |
|---|---|---|---|
| NFR-PRIV-001 | The system shall collect only the personal data fields listed in a documented data inventory, each linked to an educational purpose (data minimisation). | M | R1 |
| NFR-PRIV-002 | The system shall support configurable retention periods per record type (answer scripts, results, AI analyses, practice attempts, audit logs, accounts). Defaults are TBD per jurisdiction (OI-02). | M | R1 |
| NFR-PRIV-003 | The system shall support authorised deletion of a student's records, and a school's offboarding deletion, including files and derived AI analyses, with deletion confirmation recorded in the audit log. Backups shall be purged within the backup retention window. | M | R1 |
| NFR-PRIV-004 | The system shall maintain a register of every third-party processor (AI, e-mail, hosting) that receives student data, recording the data categories sent and the purpose. | M | R1 |
| NFR-PRIV-005 | The system shall let each school disable external AI processing entirely. Non-AI functions shall keep working. | M | R1 |
| NFR-PRIV-006 | Platform Operator staff shall not have routine access to identifiable student content. Support access shall require a time-limited, school-approved, audited access grant. | M | R1 |
| NFR-PRIV-007 | The system shall support recording consent or authorisation status per student/guardian where the applicable law requires it (OI-01, OI-03). | S | R1 |
| NFR-PRIV-008 | The system shall provide data-subject/record-access export for a student's records on authorised request. | S | R2 |
| NFR-PRIV-009 | Analytics and AI-quality reporting shall use aggregated or pseudonymised data. | M | R2 |
| NFR-PRIV-010 | A privacy/data-protection impact assessment, and an AI risk assessment (e.g., structured on NIST AI RMF's Govern/Map/Measure/Manage functions), shall be completed before pilot go-live.\[25\]\[26\] | M | R1 |

### 5.5 Auditability and Traceability (NFR-AUD)
| ID | Requirement | Pri | Rel |
|---|---|---|---|
| NFR-AUD-001 | The system shall write an append-only audit record for: login success/failure, authorisation failures, account/role changes, mark entry, validation, any change to an Official Result (old value, new value, reason), release/un-release, AI analysis request, AI review decision, file access to answer scripts, data export and deletion. | M | R1 |
| NFR-AUD-002 | Each audit record shall contain: timestamp (UTC), tenant, actor ID, role, action, entity type/ID, before/after values where applicable, source IP and request ID. | M | R1 |
| NFR-AUD-003 | Audit logs shall be tamper-evident (e.g., write-once storage or hash chaining) and retained for a period TBD (default 3 years **[Proposed]**, OI-02). | M | R1 |
| NFR-AUD-004 | For any AI Analysis, an authorised user shall be able to retrieve the input evidence set, model/prompt version, output, review status history and reviewer within 3 clicks. | M | R1 |

### 5.6 Reliability (NFR-REL)
| ID | Requirement | Pri | Rel |
|---|---|---|---|
| NFR-REL-001 | No AI failure, timeout or invalid output shall cause loss or modification of assessment records. | M | R1 |
| NFR-REL-002 | Mark entry shall autosave drafts at least every 30 s and on field blur, so that work is not lost on connection loss. | M | R1 |
| NFR-REL-003 | Database changes shall be transactional. A validation or release action shall either fully succeed or fully roll back. | M | R1 |
| NFR-REL-004 | AI jobs shall retry automatically up to 3 times with back-off, then move to "Failed" with notification. | M | R1 |

### 5.7 Availability, Backup and Recovery (NFR-AVL)
| ID | Requirement | Pri | Rel |
|---|---|---|---|
| NFR-AVL-001 | Monthly availability of core functions (sign-in, dashboards, mark entry, results) shall be ≥ 99.5%, excluding announced maintenance. | M | R1 |
| NFR-AVL-002 | Planned maintenance shall be scheduled outside school hours in the school's time zone and announced ≥ 48 h in advance. | S | R1 |
| NFR-AVL-003 | Backups shall run at least daily with point-in-time recovery. Recovery Point Objective ≤ 1 h and Recovery Time Objective ≤ 8 h. | M | R1 |
| NFR-AVL-004 | Restore procedures shall be tested at least once per term. | S | R1 |
| NFR-AVL-005 | When the AI service is unavailable, all non-AI functions shall remain available (graceful degradation). | M | R1 |

### 5.8 Usability (NFR-USE)
| ID | Requirement | Pri | Rel |
|---|---|---|---|
| NFR-USE-001 | In moderated usability testing, ≥ 80% of first-time teachers shall create an exam and enter marks for a class without assistance within 15 minutes. | S | R1 |
| NFR-USE-002 | In usability testing, ≥ 80% of students shall locate their latest result, its gap finding and the recommended practice within 2 minutes. | S | R1 |
| NFR-USE-003 | Student-facing AI explanations shall be at or below a reading level appropriate to the student's grade (target set per school; OI-07). | S | R2 |
| NFR-USE-004 | Error messages shall state what went wrong and how to fix it, without exposing system internals. | M | R1 |

### 5.9 Accessibility (NFR-ACC)
| ID | Requirement | Pri | Rel |
|---|---|---|---|
| NFR-ACC-001 | All user-facing pages shall conform to WCAG 2.2 Level AA (W3C Recommendation, 5 October 2023). WCAG 2.1 AA is the minimum fallback if a jurisdiction mandates it.\[27\] | M | R1 |
| NFR-ACC-002 | Interactive targets shall be at least 24×24 CSS pixels or have equivalent spacing (WCAG 2.2 SC 2.5.8).\[28\] | M | R1 |
| NFR-ACC-003 | Authentication shall not require a cognitive function test (e.g., transcribing CAPTCHAs). It shall allow password managers and paste (WCAG 2.2 SC 3.3.8).\[29\] | M | R1 |
| NFR-ACC-004 | Keyboard focus shall stay visible and not be obscured by sticky headers or banners (WCAG 2.2 SC 2.4.11).\[6\]\[30\] | M | R1 |
| NFR-ACC-005 | Charts showing progress shall have a text/table alternative, and shall not rely on colour alone to show strong vs weak topics. | M | R1 |
| NFR-ACC-006 | Practice tests shall support time-limit extension configured by the teacher for individual students. | S | R1 |
| NFR-ACC-007 | Accessibility shall be verified by automated scanning on every release plus a manual audit (keyboard and screen reader) before each major release. | M | R1 |

### 5.10 Maintainability and Extensibility (NFR-MNT)
| ID | Requirement | Pri | Rel |
|---|---|---|---|
| NFR-MNT-001 | Assessment, AI, learning/practice and school-management capabilities shall be separately deployable modules or services with versioned internal interfaces, so that one can be updated without redeploying the others. | S | R1 |
| NFR-MNT-002 | AI prompts/templates, output schemas and model selections shall be versioned configuration, changeable without code deployment and subject to FR-AIREL-012. | M | R1 |
| NFR-MNT-003 | New subjects, question types and resource formats shall be addable through configuration/registries without database schema changes to core entities. | S | R2 |
| NFR-MNT-004 | Automated test coverage of backend business rules (permissions, status transitions, mark calculations) shall be ≥ 80% of lines. | S | R1 |
| NFR-MNT-005 | Centralised logs, metrics and alerts shall cover API error rate, latency, AI job failure rate and queue depth. Alerts shall fire within 5 minutes of threshold breach. | M | R1 |

### 5.11 Portability and Localisation (NFR-LOC)
| ID | Requirement | Pri | Rel |
|---|---|---|---|
| NFR-LOC-001 | The system shall store all text in Unicode (UTF-8) and support right-to-left layouts if a supported language requires it (OI-07). | S | R1 |
| NFR-LOC-002 | Dates, times and number formats shall follow the school's configured locale and time zone. | M | R1 |
| NFR-LOC-003 | The system shall support deployment into a specified hosting region per school group to satisfy data-residency requirements (OI-10). | S | R2 |

---

## 6. Data Requirements

### 6.1 Conceptual Data Model — Entities

| Entity | Key attributes (indicative) | Notes |
|---|---|---|
| **School** (tenant) | school_id, name, profile, logo, locale, time zone, settings | Root of isolation |
| **User** | user_id, school_id, name, e-mail/username, status, MFA flag | One person may hold multiple roles |
| **Role / Permission** | role_id, name, permission set; user_role(user_id, role_id, scope) | Scope = school/class/subject |
| **Academic Year** | year_id, school_id, label, start/end, status | Closes; history preserved |
| **Class / Section** | class_id, year_id, grade label, section label | Configurable levels |
| **Subject** | subject_id, school_id, name, class level | |
| **Enrollment / Assignment** | enrollment(student_id, class_id, subject_id, year_id); assignment(teacher_id, class_id, subject_id, year_id) | Context for all records |
| **Topic** | topic_id, subject_id, name, parent_topic, curriculum ref | Curriculum source TBD |
| **Examination** | exam_id, subject_id, class_id, year_id, name, date, total marks, scheme ref, status, owner teacher | §6.3 states |
| **Question** | question_id, exam_id, number, max marks, type, topic_ids | Also used for practice items via Question Bank |
| **Answer Script** | script_id, exam_id, student_id, file refs, source (A/B/C/D), legibility status, release flag | Raw evidence |
| **Assessment Result** (official) | result_id, exam_id, student_id, total, per-question marks, status, validated_by, validated_at, released_at | Only teacher actions write here |
| **Teacher Feedback** | feedback_id, result_id, question_id (optional), text, author, release flag | |
| **AI Analysis** | analysis_id, student_id or class_id, exam_ids, findings[], evidence refs, model/prompt version, review status, reviewer, decision history | Never overwrites results |
| **AI Mark Suggestion** | suggestion_id, script_id, question_id, proposed mark, rationale, confidence, status | R2/R3 |
| **Learning Resource** | resource_id, school_id, type, uri/file ref, subject, class level, topics, objective, difficulty, approval status, origin (teacher/AI/external) | |
| **Recommendation** | rec_id, student_id, analysis_id, resource_ids / practice_id, order, status, teacher-approved flag | Learning path |
| **Practice Examination** | practice_id, creator, topics, rules, item list, assignment targets, purpose (practice/reassessment/mock) | |
| **Practice Attempt** | attempt_id, practice_id, student_id, responses, scores, evaluation status, timestamps | |
| **Progress Record** | progress_id, student_id, topic_id, baseline ref & score, reassessment ref & score, change, label | Supports FR-PRAC-010/011 |
| **Notice** | notice_id, school_id, audience scope, content, schedule, status | M1 |
| **Audit Event** | event_id, tenant, actor, action, entity, before/after, time, request_id | Append-only |
| **Parent Link** *(R3)* | parent_user_id, student_id, permissions | OI-05 |

### 6.2 Key Relationships
- School 1—N User, Academic Year, Subject, Topic, Learning Resource, Notice.
- Academic Year 1—N Class/Section. Class/Section N—M Subject (offering).
- Student User N—M Class/Subject via Enrollment. Teacher User N—M Class/Subject via Assignment.
- Examination N—1 Subject, N—1 Class/Section, N—1 Academic Year. Examination 1—N Question. Question N—M Topic.
- Examination 1—N Answer Script (one or more per student). Examination 1—N Assessment Result (exactly one official result per student per exam).
- Assessment Result 1—N Teacher Feedback.
- AI Analysis N—M Assessment Result / Practice Attempt (evidence links). AI Analysis 1—N Recommendation.
- Recommendation N—M Learning Resource and N—1 Practice Examination. Practice Examination 1—N Practice Attempt.
- Progress Record N—1 Student, N—1 Topic, and references baseline and reassessment evidence.

**DR-001 (M, R1):** The data model shall keep these as distinct entities with distinct status fields: (a) raw/uploaded evidence (Answer Script), (b) teacher-validated results (Assessment Result), (c) AI interpretations (AI Analysis, AI Mark Suggestion), (d) released state (release flags/timestamps), (e) practice outcomes (Practice Attempt, Progress Record).
**DR-002 (M, R1):** Every tenant-owned record shall carry an enforceable school/tenant association.
**DR-003 (M, R1):** Every AI Analysis shall reference the exact evidence records and versions used at generation time, so the analysis can be reproduced and audited even if those records change later.
**DR-004 (M, R1):** Records shall keep their academic-year context when students move between classes or years.
**DR-005 (S, R1):** Files shall be referenced by ID. File binaries shall not be stored in the relational database.

### 6.3 State Model — Examination / Result Status

```
Draft ──► Marks In Progress ──► Evaluated ──► Validated ──► Released
  │              ▲                   │             │            │
  │              └──── Returned ◄────┘             │            ▼
  └──► Cancelled                                   │       Withdrawn (un-released) ──► Released
                                                   └──► Amended (official change w/ reason) ──► Validated
```

| State | Meaning | Who moves it forward | Student visibility |
|---|---|---|---|
| Draft | Exam record created; questions/topics being defined | Assigned teacher | None |
| Marks In Progress | Marks being entered/uploaded (A/B/C) or AI suggestions pending (D) | Assigned teacher | None |
| Evaluated | All marks entered/proposed; awaiting teacher validation | Assigned teacher | None |
| Validated | Teacher has approved; Official Result exists; AI analysis may run | Assigned teacher | None |
| Released | Teacher released selected components (marks/script/comments/AI feedback) | Assigned teacher (or admin if permitted) | Released components only |
| Withdrawn | Release reversed (audited) | Assigned teacher | Hidden |
| Amended | Official mark changed after validation (reason + audit) → returns to Validated | Assigned teacher | Updated value on re-release |
| Cancelled | Exam voided before validation | Assigned teacher / admin | None |

Rules: transitions are enforced server-side (FR-EXAM-003). The transitions Validated→Released and Released→Withdrawn require the actor to be the assigned teacher or a role granted release permission. Each transition writes an audit event.

### 6.4 State Model — AI Analysis Review Status

```
Requested ──► Generated ──► Under Review ──► Accepted ─────┐
    │             │               ├────────► Edited ──────┼──► Released ──► Superseded
    ▼             │               └────────► Rejected     │
  Failed ◄────────┘ (schema/validation failure)           │
                     Auto-release policy (FR-AI-016) ─────┘
```

| State | Meaning |
|---|---|
| Requested | Teacher/system requested analysis; job queued |
| Failed | AI error, timeout or output failed validation; no student impact; retry allowed |
| Generated | Valid structured output stored; not visible to students |
| Under Review | Teacher has opened the analysis |
| Accepted | Teacher accepted unchanged |
| Edited | Teacher modified; original preserved |
| Rejected | Teacher rejected; reason recorded; never shown to students |
| Released | Accepted/Edited findings visible to the student (or auto-released per school policy, labelled as such) |
| Superseded | Replaced by a newer analysis after new evidence; retained for history |

### 6.5 Data Flow — AI Analysis (10 steps, from the user's §8)

| Step | Action | Controls (requirement refs) |
|---|---|---|
| 1 | Frontend sends teacher's "Request analysis" action to backend | COM-002 |
| 2 | Backend authenticates teacher and checks permission and assignment | FR-AUTH-003/005, NFR-SEC-002/003 |
| 3 | Backend verifies student–exam–subject–year–topic associations and Validated status | FR-AI-001, FR-AI-004, FR-ACAD-007 |
| 4 | Approved data are minimised, pseudonymised and queued to the AI workflow | FR-AI-020/021, NFR-SCAL-003 |
| 5 | AI service returns structured analysis (possible weak topics, explanations, next actions) | SW-001/002, FR-AI-005/006 |
| 6 | Backend validates schema and references, stores output with status Generated (or Failed) | FR-AI-013/014/017 |
| 7 | Teacher reviews: accept / edit / reject | FR-AI-015, FR-TCH-004 |
| 8 | Authorised student sees released feedback | FR-EXAM-023/024, FR-STU-003 |
| 9 | If practice is recommended, system creates/assigns exercise | FR-RES-003/004, FR-PRAC-001/003 |
| 10 | Student submits attempt; result stored and available for later analysis | FR-PRAC-005/010, DR-003 |

Every step writes audit events (NFR-AUD-001). Steps 4–6 record model/prompt version (SW-002).

---

## 7. Use Cases and User Stories

### UC-01 Sign in and load dashboard (All users, R1)
**Main flow:** 1) The user enters credentials on the school portal. 2) The system verifies them, plus MFA if required. 3) The system resolves school and role. 4) The system loads the role dashboard. 5) The system restricts data to the user's permissions.
**Alternates:** 2a) Invalid credentials: generic error, attempt counted (NFR-SEC-006). 2b) Account deactivated: access denied. 3a) Multiple roles: role selector shown. 3b) User has no active enrollment/assignment for the current year: limited dashboard with a message to contact the administrator.

### UC-02 Set up academic structure (School Admin, R1)
**Main:** create academic year → classes/sections → subjects → import teachers and students (CSV) → assign teachers → enrol students.
**Alternates:** import file has errors: row-level report, no partial commit unless the admin chooses "import valid rows". Duplicate user detected: the admin chooses whether to merge or skip.

### UC-03 Create exam and enter marks (Teacher, R1)
**Main:** create exam (FR-EXAM-001) → define questions + topics → enter per-question marks (Option A) or import → optionally upload scripts (Option B) → status Evaluated.
**Alternates:** mark exceeds maximum: rejected inline. Student not enrolled: rejected (FR-ACAD-007). Only total marks available: allowed, but AI analysis is limited (FR-AI-007).

### UC-04 Validate and release results (Teacher, R1)
**Main:** open validation queue → review → validate (bulk or individual) → choose components to release → release → students notified.
**Alternates:** teacher releases marks but withholds script. Post-release correction: Amended with reason → re-release. Withdraw release: Withdrawn (audited).

### UC-05 Request and review AI analysis (Teacher, R1)
**Main:** request analysis on a validated exam → job runs → findings appear with evidence → teacher accepts/edits/rejects each → release accepted findings.
**Alternates:** AI fails: status Failed, records untouched, retry offered. Insufficient evidence: "insufficient detail" message only. School has disabled external AI: action hidden, and teacher-authored feedback still possible.

### UC-06 Follow learning plan and take targeted practice (Student, R1)
**Main:** open gap report → open recommended resources in order → start assigned practice → submit → see score and feedback → see next step.
**Alternates:** practice includes open responses: status "Awaiting teacher evaluation". Student abandons: progress saved, resumable until the deadline.

### UC-07 Monitor class weakness and reteach (Teacher, R1/R2)
**Main:** class analytics show a geometry topic flagged for 55% of students → teacher reviews relevant questions → assigns class practice / reteaches → after the next test, compares topic performance before and after (FR-TCH-007, R2).

### UC-08 Scanned-script upload and AI-assisted evaluation (Teacher, R2/R3)
**Main:** bulk upload scans → system proposes page–student matches → teacher confirms → (if enabled and gates met) AI proposes per-question marks with confidence → teacher verifies/corrects every item → validate.
**Alternates:** illegible page: "Needs manual review", no AI mark (FR-AIREL-009/010). Low-confidence item: forced manual review. Matching uncertain: human confirmation required.

### UC-09 Parent views progress summary (Parent, R3, Could — pending OI-05)
**Main:** parent signs in → sees permitted summaries for linked children only.

### End-to-End Scenario — "Sara" (R1 path, with R2 options noted)

| # | Step | System behaviour | Key requirements |
|---|---|---|---|
| 1 | Exam recorded | Sara's Mathematics teacher creates "Term 1 Mathematics" for Class 9A with questions tagged to topics (e.g., "Forming equations from word problems", "Algebraic simplification"). | FR-EXAM-001/002, FR-ACAD-007 |
| 2 | Evaluated & validated | Teacher enters per-question marks (Option A) and optionally uploads Sara's script (B), or scans it (C, R2). Teacher validates. | FR-EXAM-010/013/020 |
| 3 | Released | Teacher releases marks, script and comments. Sara is notified, signs in and sees her approved result labelled "Teacher-approved". | FR-EXAM-023/028, UI-002 |
| 4 | AI analyses evidence | Teacher requests analysis. The system finds lower marks on word-problem equation questions across this and the previous test, links the specific questions, and words it as "may need help with forming equations". Teacher accepts and releases. | FR-AI-001/005–009/015, FR-AI-019 |
| 5 | Personalised practice offered | Sara's learning plan shows a worked example, the teacher's explanation, a basic set, then a harder set and a targeted reassessment. Teacher reviews or adjusts. | FR-RES-003/004/005, FR-PRAC-001/003 |
| 6 | Reassessment | Sara completes a comparable 10-item reassessment. Baseline 4/10 (40%) → 8/10 (80%); the record is labelled "Improved on practice". | FR-PRAC-009/010/011 |
| 7 | Next step | Threshold met, so the system recommends advanced items. Had the difficulty persisted, it would recommend further practice and flag Sara for teacher support. Later assessments confirm or revise the trend. | FR-PRAC-012, FR-STU-005 |

---

## 8. Release Plan Summary

| Release | Scope (requirements tagged) |
|---|---|
| **R1 — MVP** | Accounts/roles/MFA for admins; configurable structure; basic portal & notices; exam records; manual and imported marks (A); digital upload (B); teacher validation & component-level release; student results view; AI student-level weakness analysis + class-level topic flags with HITL review; resource links/uploads & question bank; targeted practice with objective auto-scoring; baseline/reassessment progress; student/teacher/admin dashboards; security, privacy, audit, WCAG 2.2 AA. |
| **R2 — Early Expansion** | Scanned-script workflows (C) with page matching and legibility checks; full AI evaluation metrics suite; limited, gated pilot of AI-assisted marking for validated question types; AI-generated explanations/questions with teacher approval; richer teacher analytics and before/after topic comparisons; extended portal; mock-exam generation; exports; data residency. |
| **R3 — Long-term** | Advanced handwritten-answer evaluation (D) where gates are met; subject-/question-type-specific automated scoring; longitudinal mastery models; SSO and school-system integration; parent/guardian portal; multi-pass AI consistency checks; subgroup fairness checks. |

---

## Appendix A — Requirements Traceability Matrix

| Requirement group | Module | Objective(s) | User-doc source § | Verification method |
|---|---|---|---|---|
| FR-PORT-001–011 | M1 | OBJ-2 | §3, Module 1 | Functional test, demo |
| FR-AUTH-001–011 | M2 | OBJ-2, OBJ-4 | §2, §2.1, §10 | Functional + security test |
| FR-ACAD-001–008 | M2 | OBJ-1, OBJ-2 | Module 2 §2.2–2.3 | Functional test (data-integrity cases) |
| FR-EXAM-001–004 | M3 | OBJ-1 | Module 3 §3.1 | Functional test |
| FR-EXAM-010–018 | M3 | OBJ-1, OBJ-3 | Module 3 §3.2 | Functional test; pilot trial (C/D) |
| FR-EXAM-020–028 | M3 | OBJ-3 | Module 3 §3.3–3.4, §9 | Functional test; audit inspection |
| FR-AI-001–012 | M4 | OBJ-1, OBJ-3 | Module 4 §4.1–4.4 | Test with seeded datasets; teacher review |
| FR-AI-013–019 | M4 | OBJ-3 | §6.5, §8, §9 | Fault-injection test; audit inspection |
| FR-AI-020–023 | M4 | OBJ-4 | §10 (third-party AI) | Payload inspection; contract review |
| FR-RES-001–009 | M5 | OBJ-1, OBJ-2 | Module 5 | Functional test; teacher acceptance |
| FR-PRAC-001–013 | M6 | OBJ-1, OBJ-5 | Module 6 §6.1–6.3 | Functional test; calculation test |
| FR-STU-001–007 | M7 | OBJ-1, OBJ-5 | Module 7 | Usability test (NFR-USE-002) |
| FR-TCH-001–009 | M8 | OBJ-1, OBJ-3 | Module 8 | Usability test (NFR-USE-001) |
| FR-ADM-001–009 | M9 | OBJ-2, OBJ-4 | Module 9 | Functional + permission test |
| FR-AIREL-001–014 | M3, M4, M6 | OBJ-3, OBJ-5 | §9 | Offline evaluation vs reference set; reports |
| NFR-PERF, NFR-SCAL | All | OBJ-1, OBJ-2 | §11 (performance) | Load test |
| NFR-SEC-001–015 | All | OBJ-4 | §6.2, §10, §11 | ASVS L2 verification; pen test |
| NFR-PRIV-001–010 | All | OBJ-4 | §10 | DPIA; data inventory review |
| NFR-AUD-001–004 | All | OBJ-3, OBJ-4 | §8, §10, §11 | Audit-log inspection |
| NFR-REL, NFR-AVL | All | OBJ-3 | §11 (reliability) | Fault injection; DR drill |
| NFR-USE, NFR-ACC | All | OBJ-2 | §11 (ease of use, accessibility) | Usability study; WCAG audit |
| NFR-MNT, NFR-LOC | All | All | §11 (maintainability, extensibility) | Architecture review; code metrics |
| DR-001–005, §6.3–6.5 | All | OBJ-3 | §7, §8 | Schema review; integration test |

**Objective → key requirements (reverse trace):**
- OBJ-1 → FR-AI-005, FR-RES-003, FR-PRAC-001, FR-STU-003/004
- OBJ-2 → FR-PORT-001–009, FR-ADM-001–004
- OBJ-3 → FR-EXAM-020/026, FR-AI-014/015, FR-AIREL-004/009, DR-001
- OBJ-4 → NFR-SEC-002/003/009, NFR-PRIV-001–006, FR-AI-020–023
- OBJ-5 → FR-PRAC-010/011/012, UI-005

---

## Appendix B — Logical Architecture

| Layer | Components | Key requirements |
|---|---|---|
| **Presentation** | School portal (public + authenticated), Student dashboard, Teacher dashboard, Admin dashboard; responsive web UI | UI-001–007, NFR-ACC |
| **Application / API** | Authentication & session; Authorisation (RBAC + tenant + assignment); Academic records; Examinations & results (state machine); Resources & recommendations; Practice engine & scoring; Reporting & analytics; Notifications; Audit service | COM-002, NFR-SEC-002/003, §6.3 |
| **Data** | Relational DB (tenant-scoped); private object storage (scripts, resources); append-only audit store; analytics store (aggregated/pseudonymised) | DR-001–005, NFR-SEC-009/012 |
| **AI services** | AI gateway (schema, pseudonymisation, allow-list, versioning); job queue & workers; capabilities: weakness analysis, recommendations, practice assembly/generation (R2), script OCR/HTR & marking assistance (R2/R3); evaluation harness | SW-001/002, FR-AI, FR-AIREL |
| **Infrastructure & security** | Cloud hosting (region TBD); secrets management; backups & PITR; centralised logging, metrics, alerting; WAF/rate limiting; malware scanning | NFR-AVL, NFR-MNT-005, NFR-SEC |

Design principle: the AI layer is a stateless consumer of minimised, pseudonymised inputs that returns untrusted structured outputs. Every authorisation decision, state transition and write to an Official Result belongs to the application layer.

---

## Appendix C — Open Issues / TBD List

| ID | Open issue | Why it matters | Example references (not assumptions) | Owner / needed by |
|---|---|---|---|---|
| OI-01 | **Deployment jurisdiction(s) and applicable law** | Drives consent, retention, data residency, AI obligations, accessibility mandates | US: FERPA lets schools share records with vendors under the "school official" exception only if the school keeps "direct control" over use and maintenance.\[31\] COPPA's 2025 amendments require a written data-retention policy and separate parental consent for non-integral third-party disclosures.\[32\]\[33\] EU: GDPR Art. 5 (data minimisation, storage limitation); Art. 8 (age 16 for consent to information-society services, which member states may lower to no below 13).\[34\]\[35\]\[36\] EU AI Act Annex III 3(b) lists AI used to evaluate learning outcomes, including steering learning, as high-risk.\[37\] Orrick (29 July 2026) reports that the Digital Omnibus was published in the Official Journal as Regulation (EU) 2026/1744 and moves Annex III high-risk obligations from 2 August 2026 to 2 December 2027. | Product owner + legal, before pilot contract |
| OI-02 | Retention periods per record type (scripts, results, AI analyses, practice, audit logs, accounts) | NFR-PRIV-002, NFR-AUD-003 | COPPA prohibits indefinite retention of children's data\[38\]\[39\] | Schools + legal |
| OI-03 | Consent model (school authorisation vs parental consent; age thresholds) | NFR-PRIV-007; minors' use of generative AI | UNESCO's *Guidance for Generative AI in Education and Research* (launched 7 September 2023) sets an age limit of 13 for the use of AI tools in the classroom | Legal + schools |
| OI-04 | **Choice of AI provider(s)**, hosting model (external API vs internal), contract terms (no training on student data, retention, sub-processors, region) | FR-AI-023, SW-001, cost/latency | — | Tech lead, before R1 build |
| OI-05 | **Parent/guardian role**: whether in scope, permissions, linking/verification | FR-AUTH-011, UC-09 | — | Product owner + pilot schools |
| OI-06 | Whether school administrators may view identifiable student-level results by default | FR-ADM-007 | User doc: sensitive data "should not automatically be visible to every staff member" | Pilot schools |
| OI-07 | **Supported languages** (UI, AI explanations, student answers), RTL needs, reading-level targets | UI-007, NFR-LOC-001, NFR-USE-003; OCR accuracy varies by script/language | — | Product owner |
| OI-08 | **Curriculum / syllabus mapping** source and topic taxonomy per subject and grade | FR-ACAD-008, FR-PRAC-001, AI topic accuracy | — | Pilot schools + subject experts |
| OI-09 | AI-feedback release policy default (teacher review always vs auto-release of low-risk items) | FR-AI-016 | US Dept. of Education (2023): "humans in the loop"\[40\] | Pilot schools |
| OI-10 | Hosting region / data residency | NFR-LOC-003, DEP-02 | — | Tech lead + legal |
| OI-11 | Question-bank sourcing and licensing for practice items | FR-RES-008, FR-PRAC-001 | — | Product owner |
| OI-12 | Confirmation of all **[Proposed]** numeric targets (performance, availability, session timeouts, AI gates, thresholds) | Verifiability of NFRs | Core Web Vitals; Williamson et al. 2012; NIST SP 800-63B-4 | Team, at SRS sign-off |
| OI-13 | Weakness-flagging rule parameters (FR-AI-008) and class threshold (FR-AI-010) | False positives/negatives in gap reports | — | Teachers in pilot |
| OI-14 | Which question types are eligible for the R2 AI-marking pilot | FR-AIREL-004 | — | AI lead + teachers |
| OI-15 | Pilot school list, size and device/bandwidth profile | NFR-SCAL-001, NFR-PERF-006 | — | Product owner |
| OI-16 | Accessibility legal mandate level (WCAG 2.1 vs 2.2 AA) per jurisdiction | NFR-ACC-001 | — | Legal |

---

## Recommendations for Using This SRS
1. **Sign off R1 first, and freeze it.** Treat every "M/R1" row as the pilot acceptance baseline. Resolve OI-01, OI-04, OI-05, OI-08 and OI-12 before build starts, because they change requirements rather than just details.
2. **Make status separation the first thing you build and test.** DR-001, FR-EXAM-026, the §6.3/§6.4 state machines and NFR-SEC-002/003 are the parts that are expensive to retrofit. Write their automated tests before any feature screens.
3. **Start collecting the reference dataset in R1.** Every teacher accept/edit/reject decision and every validated question-level mark (FR-AIREL-002) is the evidence you will need to justify, or refuse, AI marking in R2/R3.
4. **Do not promise automated handwriting grading to pilot schools.** Position R1 as "teacher-validated marks in, diagnosis and practice out". Published studies show OCR and grading errors at levels that require human verification.\[41\]\[42\]

## Caveats
- This SRS covers only what the user's analysis describes. Anything marked "not confirmed" (fees, payroll, HR, attendance, accounting) is excluded on purpose.
- Numeric targets are engineering defaults, not benchmarks from your pilot schools. They must be confirmed (OI-12).
- The AI acceptance thresholds come from automated essay and constructed-response scoring practice in large-scale testing. Their fit for school-level, multi-subject, handwritten work has to be confirmed with your own reference data. Some researchers also argue that QWK alone is not enough, which is why §4.10 requires several metrics broken down by question type.\[43\]
- Legal references are illustrative only. Orrick (29 July 2026) reports that the EU AI Act timeline change was published in the Official Journal as Regulation (EU) 2026/1744 and entered into force on 27 July 2026. Have counsel confirm it against the Official Journal text.

## Sources

1. [Software requirements specification](https://en.wikipedia.org/wiki/Software_requirements_specification)
2. [Superseded Standard](https://standards.ieee.org/standard/830-1998.html)
3. [The Department of Education Shouldn’t Treat Human in the Loop as a Silver Bullet for AI](https://datainnovation.org/2023/07/the-department-of-education-shouldnt-treat-human-in-the-loop-as-a-silver-bullet-for-ai/)
4. [Annex III: High-Risk AI Systems Referred to in Article 6(2)](https://artificialintelligenceact.eu/annex/3/)
5. [Loading \[MathJax\]/extensions/MathMenu.js](https://ieeexplore.ieee.org/document/720574/amendments)
6. [What's New in WCAG 2.2](https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/)
7. [Multi Tenant Security - OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/cheatsheets/Multi_Tenant_Security_Cheat_Sheet.html)
8. [OWASP Application Security Verification Standard (ASVS)](https://owasp.org/www-project-application-security-verification-standard)
9. [Insecure Direct Object Reference Prevention - OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/cheatsheets/Insecure_Direct_Object_Reference_Prevention_Cheat_Sheet.html)
10. [NIST SP 800-63B-4 Second Public Draft, Digital Identity ...](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-63B-4.2pd.pdf)
11. [ERIC - EJ959585 - A Framework for Evaluation and Use of Automated Scoring, Educational Measurement: Issues and Practice, 2012](https://eric.ed.gov/?id=EJ959585)
12. [Education Department Issues Recommendations on AI](https://www.insidehighered.com/news/quick-takes/2023/05/25/education-department-issues-recommendations-ai)
13. [Guidance for Generative AI in Education and Research](https://gcedclearinghouse.org/en/node/129341)
14. [Web Vitals | Articles | web.dev](https://web.dev/articles/vitals)
15. [Un marco conceptual para la generaci\\'on de requerimientos de software de calidad](https://arxiv.org/pdf/2504.10654)
16. [Well-Formed Quality of System Requirements for Verifying to ISO 29148-2018: A Natural Language Processing (NLP) Based Framework and Quantitative Metric](https://asmedigitalcollection.asme.org/IDETC-CIE/proceedings-abstract/IDETC-CIE2024/88353/V02BT02A013/1208775)
17. [Automated Scoring of Constructed-Response Science Items](https://escholarship.org/content/qt2kt675px/qt2kt675px_noSplash_aebf32f309c7fb131c06f750751ddce1.pdf)
18. [A Study of the Use of the e-rater® Scoring Engine for the Analytical Writing](https://files.eric.ed.gov/fulltext/EJ1109327.pdf)
19. [A Framework for Evaluation and Use of Automated Scoring](https://www.researchgate.net/publication/230538214_A_Framework_for_Evaluation_and_Use_of_Automated_Scoring)
20. [asvs-requirements - Skill](https://smithery.ai/skills/Zate/asvs-requirements)
21. [NIST SP 800-63B-4 Password Guidelines for Businesses](https://itecsonline.com/post/nist-password-guidelines)
22. [NIST Password Guidelines (SP 800-63B-4) in Plain English](https://bestpasswordgenerator.io/nist-password-guidelines.html)
23. [Implement single-exchange tokens for short-lived Amazon S3 presigned URLs with Terraform](https://aws.amazon.com/blogs/storage/implement-single-exchange-tokens-for-short-lived-amazon-s3-presigned-urls-with-terraform/)
24. [How to Generate Presigned URLs for Temporary S3 Access](https://oneuptime.com/blog/post/2026-02-12-generate-presigned-urls-temporary-s3-access/view)
25. [NIST AI Risk Management Framework (AI RMF 1.0) Guide - Securiti](https://securiti.ai/nist-ai-risk-management-framework/)
26. [AI RMF Core - AIRC](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/)
27. [WCAG 2.2 - Web Content Accessibility Guidelines](https://quality.arc42.org/standards/wcag-2-2)
28. [What’s New in WCAG 2.2: The 9 New Success Criteria Explained](https://www.audioeye.com/post/whats-new-with-wcag-2-2/)
29. [WCAG 2.2 vs 2.1: 9 New Requirements Your Site Probably Fails](https://adaquickscan.com/blog/wcag-2-2-iso-standard-2025)
30. [WCAG 2.2 AA Testing: How to Test the 6 Criteria Automated Scanners Miss](https://webspecification.com/blog/wcag-22-success-criteria/)
31. [What FERPA actually lets edtech vendors do with student data](https://mamagerah.com/experts/what-ferpa-actually-lets-edtech-vendors-do-with-student-data/)
32. [FTC Updates to the COPPA Rule Impose New Compliance Obligations for Online Services That Collect Data from Children - Gibson Dunn](https://www.gibsondunn.com/ftc-updates-to-coppa-rule-impose-new-compliance-obligations-for-online-services-that-collect-data-from-children/)
33. [COPPA Rule Amendments and Compliance Dates](https://www.privacylawnetwork.com/news/coppa-rule-2025-amendments.html)
34. [Art. 8 GDPR](https://gdpr-info.eu/art-8-gdpr/)
35. [D](https://www.edps.europa.eu/data-protection/data-protection/glossary/d_en)
36. [GDPR Storage Limitation: Set Retention Rules and Verify Deletion](https://www.legiscope.com/blog/storage-limitation.html)
37. [The EU AI Act for education and training](https://www.euaiact.com/guides/education)
38. [Overview: Children's Online Privacy Protection Act (COPPA)](https://usercentrics.com/knowledge-hub/childrens-online-privacy-protection-act-coppa/)
39. [FTC Finalizes Updated COPPA Rules - Outside GC](https://outsidegc.com/blog/ftc-finalizes-updated-coppa-rules/)
40. [Handout: AI and the Future of Teaching and Learning (PDF)](https://www.ed.gov/sites/ed/files/documents/ai-report/ai-report-core-messages.pdf)
41. [Evaluating AI Grading on Real-World Handwritten College Mathematics: A Large-Scale Study Toward a Benchmark](https://arxiv.org/html/2603.00895)
42. [Grading assistance for a handwritten thermodynamics exam using artificial intelligence: An exploratory study](https://journals.aps.org/prper/abstract/10.1103/PhysRevPhysEducRes.20.020144)
43. [Quadratic Weighted Kappa Is Not Enough for Evaluating Automated Essay Scoring Models - ACL Anthology](https://aclanthology.org/2026.lrec-1.348/)
