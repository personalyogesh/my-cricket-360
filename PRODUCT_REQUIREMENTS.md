# My Cricket 360 — Product Requirements

**Status:** Founding clubs MVP (Starks + CGI Steelers)  
**Repository:** `my-cricket-360`  
**Priority:** Sponsor readiness and dual-club hostname branding

---

## 1. Product Vision

My Cricket 360 is a **native iOS and web multi-club cricket management platform**. One product serves many clubs from a shared codebase and database, with strict organization (club) isolation, hostname-based web branding, and a single global user identity on mobile.

### Founding Clubs

| Club | Public domains | Initial sponsor |
|------|----------------|-----------------|
| Starks Cricket | `starksgroup.org`, `www.starksgroup.org` | Hashtag India Cary |
| CGI Steelers Cricket | `cgisteelerscricket.org`, `www.cgisteelerscricket.org` | CGI |

Existing Starks and Steelers production websites must keep running. DNS changes and production cutover require explicit approval. Existing Firebase projects must not be deleted or modified.

---

## 2. Goals (MVP)

1. **One monorepo** with web, API, and iOS apps sharing contracts and club identity.
2. **Hostname-resolved club sites** — same Next.js deployment, club-specific branding, content, SEO, and admin.
3. **One My Cricket 360 iOS app** — global account, membership requests, club switcher, server-enforced authz.
4. **Sponsor vertical** — profiles, assets, campaigns, approval workflow, public pages, analytics hooks.
5. **Organization-scoped RBAC** so club private data never leaks across clubs.
6. **Local / staging / production** configs without activating paid billing or third-party club onboarding yet.

### Non-Goals (this phase)

- Paid subscription billing or Stripe (design entitlements only).
- Self-serve onboarding of arbitrary third-party clubs.
- DNS cutover or production deploy without approval.
- Migrating or deleting Firebase projects.
- Android client.

---

## 3. Personas & Roles

| Role | Scope | Capabilities |
|------|-------|--------------|
| Public visitor | Club hostname | View public fixtures, teams, gallery, announcements, sponsors |
| Member | Club membership | View member content; club switcher when multi-member |
| Club admin | Organization | Manage teams, fixtures, announcements, galleries, sponsors, membership approvals |
| Platform operator | Platform | Future multi-club ops; not exposed in founding MVP UI |
| Sponsor contact | Club (read-ish) | Future portal; MVP is admin-managed sponsor records |

RBAC is **organization-scoped**. A Starks admin cannot administer Steelers (and vice versa) unless separately granted.

---

## 4. Web Requirements

### 4.1 Club resolution

- Resolve club from a **server-side allowlisted hostname → organization** mapping.
- Support **apex and `www`** for each founding domain.
- Local/dev hostnames (e.g. `starks.localhost`, `steelers.localhost`) map to the same clubs.
- **Never** use an unvalidated `Host` header for security decisions; only allowlisted hosts resolve; unknown hosts get a safe fallback (platform landing or 404), never another club’s data.
- Canonical URLs and SEO metadata must reflect the **resolved club’s** primary domain.

### 4.2 Public surfaces (per club)

- Home / branding (logo, theme, hero, sponsor strip)
- Fixtures / matches
- Teams & squads (public subset)
- Gallery
- Announcements
- Sponsors directory + public shareable sponsor pages
- Contact / about (club-specific)

### 4.3 Admin (club-scoped)

- Separate admin dashboard paths under the same hostname (e.g. `/admin`).
- Auth via Supabase; session must include org membership with admin role.
- Manage content, fixtures, teams, galleries, announcements, sponsors (upload + approval).
- Reuse the same components and layouts across clubs; only theme/config and data change.

### 4.4 Isolation & SEO

- All data queries filter by `organization_id` derived from hostname (or authenticated membership), never from client-supplied club IDs alone for public pages.
- No cross-club private data in HTML, API responses, or sitemap/canonical tags.
- Per-domain sitemap, Open Graph, and `robots` as appropriate.

---

## 5. iOS Requirements

- **One app:** My Cricket 360 (SwiftUI).
- **One global user account** (Supabase Auth).
- User may **request membership** for Starks, Steelers, or both.
- Each club’s admins **approve independently**.
- **Club switcher** lists only approved memberships.
- Persist **last selected club** securely (Keychain / App Storage with server revalidation).
- Surfaces: teams, sponsors, matches, content, finances (club-scoped).
- **All authorization enforced server-side**; client UI is advisory.

---

## 6. Sponsor Requirements (priority)

| Capability | MVP |
|------------|-----|
| Sponsor profile (name, logo, banner, website, blurb) | Required |
| Campaigns (date range, placement tags) | Required |
| Secure admin upload + approval workflow | Required |
| Visibility on mobile + matching club website | Required |
| Public shareable sponsor page (`/sponsors/[slug]`) | Required |
| Analytics (impressions / clicks events) | Required (store events; simple admin charts later) |
| Sponsor self-serve portal | Deferred |

Initial seed sponsors:

- Starks → **Hashtag India Cary**
- Steelers → **CGI**

---

## 7. Platform & Ops Requirements

| Area | Requirement |
|------|-------------|
| Apps | `apps/web` (Next.js), `apps/api` (FastAPI), `apps/ios` (SwiftUI) |
| Data | Single Supabase PostgreSQL + Auth + Storage |
| Contracts | OpenAPI as source of truth between web/iOS and API |
| CI/CD | GitHub Actions (lint, test, typecheck; deploy gated) |
| Environments | `local`, `staging`, `production` configs |
| Future clubs | Schema and entitlements allow more orgs; UI/billing off |

---

## 8. Success Criteria (First Task)

- [x] Product, architecture, data model, and implementation plan documents
- [x] Cursor project rules
- [x] Monorepo scaffold
- [x] Hostname-based club configuration with automated tests
- [x] SwiftUI app shell
- [x] Local run documentation

Features are **not** marked complete without verification (tests or manual proof).

---

## 9. Constraints & Safety

1. Keep existing Starks/Steelers production sites live.
2. No DNS or production deploy without approval.
3. Do not delete or modify existing Firebase projects.
4. Prefer additive, reversible changes for cutover planning.
5. Secrets never committed; use env examples only.
