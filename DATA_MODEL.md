# My Cricket 360 — Data Model

PostgreSQL via Supabase. All multi-tenant tables carry `organization_id` (UUID FK → `organizations.id`) unless platform-global.

Timestamps: `created_at`, `updated_at` (timestamptz). Soft deletes optional via `deleted_at`.

---

## 1. ER Overview

```
users (auth.users / profiles)
    │
    ├── memberships ──────────── organizations
    │                                │
    │                                ├── organization_domains
    │                                ├── themes / branding (JSON or row)
    │                                ├── teams → players
    │                                ├── matches / fixtures
    │                                ├── announcements
    │                                ├── gallery_albums → gallery_items
    │                                ├── sponsors → sponsor_campaigns
    │                                │                 └── sponsor_assets
    │                                ├── analytics_events
    │                                └── entitlements (future)
    │
    └── (global profile fields)
```

---

## 2. Core Tables

### `profiles`

Extends Supabase `auth.users`.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | = `auth.users.id` |
| display_name | text | |
| avatar_url | text | nullable |
| phone | text | nullable |
| created_at / updated_at | timestamptz | |

### `organizations`

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| slug | citext UNIQUE | `starks`, `steelers` |
| name | text | |
| short_name | text | |
| status | text | `active`, `suspended` |
| primary_domain | text | canonical apex host |
| theme | jsonb | colors, fonts, logo URLs |
| settings | jsonb | feature flags |
| subscription_status | text | default `founding`; billing later |
| created_at / updated_at | timestamptz | |

**Seed**

| slug | name | primary_domain |
|------|------|----------------|
| `starks` | Starks Cricket | `starksgroup.org` |
| `steelers` | CGI Steelers Cricket | `cgisteelerscricket.org` |

### `organization_domains`

Allowlist persisted for runtime + ops (web also ships a static allowlist for edge safety).

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| organization_id | uuid FK | |
| hostname | citext UNIQUE | normalized, no port |
| is_primary | boolean | |
| environment | text | `local`, `staging`, `production` |

### `memberships`

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| user_id | uuid FK | profiles |
| organization_id | uuid FK | |
| role | text | `member`, `admin` |
| status | text | `pending`, `approved`, `rejected`, `revoked` |
| requested_at | timestamptz | |
| decided_at | timestamptz | nullable |
| decided_by | uuid | nullable |
| UNIQUE(user_id, organization_id) | | |

iOS membership requests create `pending` rows; club admins approve → `approved`.

---

## 3. Cricket Domain

### `teams`

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| organization_id | uuid FK | indexed |
| name | text | |
| division | text | nullable |
| season | text | nullable |
| is_public | boolean | default true |

### `players`

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| organization_id | uuid FK | |
| team_id | uuid FK | nullable |
| user_id | uuid FK | nullable link to profile |
| display_name | text | |
| role | text | batter/bowler/allrounder/wk |
| jersey_number | int | nullable |
| is_public | boolean | |

### `matches`

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| organization_id | uuid FK | |
| home_team_id / away_team_id | uuid | nullable for external opp |
| opponent_name | text | when external |
| starts_at | timestamptz | |
| venue | text | |
| status | text | `scheduled`, `live`, `completed`, `cancelled` |
| result_summary | text | nullable |
| is_public | boolean | |

### `announcements`

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| organization_id | uuid FK | |
| title | text | |
| body | text | markdown/plain |
| published_at | timestamptz | nullable = draft |
| is_public | boolean | |

### `gallery_albums` / `gallery_items`

Album belongs to org; items have `storage_path`, caption, sort order, public flag.

---

## 4. Sponsors (priority)

### `sponsors`

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| organization_id | uuid FK | indexed |
| slug | citext | unique per org |
| name | text | |
| tagline | text | nullable |
| description | text | |
| website_url | text | nullable |
| logo_path | text | storage path |
| banner_path | text | nullable |
| status | text | `draft`, `pending_approval`, `approved`, `rejected`, `archived` |
| approved_at / approved_by | | |
| sort_order | int | |
| UNIQUE(organization_id, slug) | | |

**Seed**

- Starks: Hashtag India Cary (`hashtag-india-cary`)
- Steelers: CGI (`cgi`)

### `sponsor_campaigns`

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| sponsor_id | uuid FK | |
| organization_id | uuid FK | denormalized for RLS |
| name | text | |
| placement | text | `home_hero`, `home_strip`, `sponsors_page`, `match_day` |
| starts_at / ends_at | timestamptz | |
| is_active | boolean | |

### `sponsor_assets`

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| sponsor_id | uuid FK | |
| organization_id | uuid FK | |
| asset_type | text | `logo`, `banner`, `document` |
| storage_path | text | |
| content_type | text | |
| uploaded_by | uuid | |
| status | text | `pending`, `approved`, `rejected` |

### `analytics_events`

| Column | Type | Notes |
|--------|------|-------|
| id | bigserial / uuid | |
| organization_id | uuid FK | |
| sponsor_id | uuid | nullable |
| event_type | text | `sponsor_impression`, `sponsor_click`, `page_view` |
| source | text | `web`, `ios` |
| path | text | nullable |
| meta | jsonb | |
| occurred_at | timestamptz | |
| session_id | text | nullable anonymous |

Retention/aggregation jobs can roll up later; MVP stores raw events.

---

## 5. Entitlements (inactive billing)

### `organization_entitlements`

| Column | Type | Notes |
|--------|------|-------|
| organization_id | uuid PK/FK | |
| plan_code | text | `founding`, `standard`, … |
| max_admins | int | |
| max_sponsors | int | |
| features | jsonb | |
| valid_until | timestamptz | nullable = unlimited founding |

No payment provider tables in MVP.

---

## 6. Indexes & Isolation

- Index `(organization_id)` on every tenant table.
- Unique hostnames globally on `organization_domains.hostname`.
- Membership lookups: `(user_id, status)`, `(organization_id, role, status)`.
- Sponsor public pages: `(organization_id, slug)` where `status = approved`.

### RLS (sketch)

- Public read: approved sponsors, public matches/announcements/gallery for org.
- Member read: + member-only content for orgs with approved membership.
- Admin write: org_admin membership required.
- Analytics insert: authenticated or signed ingest key; reads admin-only.

API still enforces authz in application code; RLS is defense in depth.

---

## 7. Storage Paths

```
sponsor-assets/{organization_id}/{sponsor_id}/{asset_id}
club-media/{organization_id}/gallery/{album_id}/{item_id}
club-media/{organization_id}/branding/...
```

Never serve another org’s paths via user-controlled IDs without org check.
