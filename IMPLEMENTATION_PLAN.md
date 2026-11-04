# My Cricket 360 — Implementation Plan

Phased delivery. **Do not mark a feature complete without verification** (automated test and/or recorded manual check).

Sponsor readiness and founding clubs (Starks, CGI Steelers) are prioritized in every phase.

---

## Phase 0 — Foundation (this task) ✅

| Deliverable | Verification |
|-------------|--------------|
| Product / architecture / data / plan docs | Review against product brief |
| Cursor project rules | Present under `.cursor/rules` |
| Monorepo scaffold (`apps/web`, `apps/api`, `apps/ios`) | Install + boot locally |
| Hostname allowlist club config | Unit tests for apex/www/local/unknown |
| SwiftUI app shell | Compiles on macOS Xcode (structure + README) |
| Local run instructions | README paths work |

---

## Phase 1 — API + schema bootstrap

1. Alembic migrations for `organizations`, `organization_domains`, `profiles`, `memberships`, sponsor tables.
2. Seed Starks + Steelers + Hashtag India Cary + CGI.
3. FastAPI health + `/v1/orgs/{slug}` public read.
4. OpenAPI export to `packages/openapi`.
5. Pytest against local Postgres / SQLite test harness.

**Exit:** API returns org theme for both founding slugs; migrations clean.

---

## Phase 2 — Web club sites (public)

1. Middleware / layout resolves club from allowlist; injects theme CSS variables.
2. Shared layouts: home, fixtures, teams, sponsors, gallery, announcements.
3. Canonical + metadata per club.
4. Public sponsor page `/sponsors/[slug]` with analytics beacon.
5. Playwright or component tests for host → branding.

**Exit:** `starks.localhost` vs `steelers.localhost` show distinct logos/themes; unknown host safe.

---

## Phase 3 — Auth + memberships + admin

1. Supabase Auth on web admin + iOS.
2. Membership request / approve flows.
3. Club-scoped `/admin` dashboard (sponsors first).
4. Secure Storage uploads with approval states.
5. RBAC tests (Starks admin cannot mutate Steelers).

**Exit:** Cross-org write attempts return 403; approval works for both clubs.

---

## Phase 4 — iOS vertical slice

1. Auth session + membership list.
2. Club switcher + persisted last club.
3. Home feed: announcements, next match, sponsor strip.
4. Sponsors list + detail.
5. Server-side authz regression tests via API.

**Exit:** User with only Starks membership cannot load Steelers private endpoints.

---

## Phase 5 — Matches, teams, content, finances (read)

1. Fixtures CRUD (admin) + public calendar.
2. Teams / players public views.
3. Gallery + announcements.
4. Finances: member-visible summaries only (no payment processor).

**Exit:** Content CRUD scoped by org; public sites updated.

---

## Phase 6 — Staging hardening & cutover prep

1. Staging Supabase + multi-domain staging hosts.
2. GitHub Actions deploy to staging (gated).
3. Analytics rollups for sponsors.
4. Go-live checklist (DNS, redirects, Firebase freeze).
5. **No production DNS** until explicit approval.

---

## Deferred (designed, not built)

- Paid billing / Stripe.
- Third-party club self-onboarding.
- Android.
- Sponsor self-serve portal.
- Live scoring advanced features.

---

## Near-term engineering order (after Phase 0)

1. Hostname config tests green (done in Phase 0).
2. API org + sponsor seed + tests.
3. Web themed public home + sponsor strip for both clubs.
4. Admin sponsor approval slice.
5. iOS auth + club switcher wired to API.

---

## Risk Register

| Risk | Mitigation |
|------|------------|
| Accidental DNS cutover | Document freeze; no prod deploy secrets in default CI |
| Cross-club data leak | Allowlist + org_id filters + RBAC tests |
| Firebase confusion | New Supabase only; docs forbid Firebase edits |
| iOS build on Linux CI | Shell + SPM structure; macOS for compile verification |
| Scope creep | Vertical slices; sponsors + two clubs first |
