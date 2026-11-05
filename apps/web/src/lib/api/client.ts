import type { ClubSlug } from "@/lib/clubs";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ||
  "http://127.0.0.1:8400";

export type ApiSponsor = {
  id: string;
  slug: string;
  name: string;
  tagline: string | null;
  description: string | null;
  website_url: string | null;
  logo_url: string | null;
  banner_url: string | null;
  status: string;
  sort_order: number;
  organization_id?: string;
  logo_path?: string | null;
  banner_path?: string | null;
  approved_at?: string | null;
  published_at?: string | null;
};

export type ApiOrganization = {
  id: string;
  slug: ClubSlug | string;
  name: string;
  short_name: string;
  primary_domain: string;
  theme: Record<string, string>;
  initial_sponsor: ApiSponsor | null;
};

export type MeResponse = {
  user: {
    id: string;
    email: string | null;
    display_name: string;
    avatar_url: string | null;
  };
  memberships: Array<{
    id: string;
    organization_id: string;
    organization_slug: string;
    organization_name: string;
    role: string;
    status: string;
  }>;
  approved_clubs: Array<{
    id: string;
    organization_slug: string;
    role: string;
    status: string;
  }>;
};

async function apiFetch<T>(
  path: string,
  init: RequestInit & { token?: string } = {},
): Promise<T> {
  const { token, headers, ...rest } = init;
  const res = await fetch(`${API_BASE}${path}`, {
    ...rest,
    headers: {
      ...(headers || {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? JSON.stringify(body);
    } catch {
      /* ignore */
    }
    throw new Error(`${res.status}: ${detail}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export function getApiBase() {
  return API_BASE;
}

export function fetchOrganization(slug: string) {
  return apiFetch<ApiOrganization>(`/v1/orgs/${slug}`);
}

export function fetchPublicSponsors(slug: string) {
  return apiFetch<ApiSponsor[]>(`/v1/orgs/${slug}/sponsors`);
}

export type ApiTeam = {
  id: string;
  name: string;
  division: string | null;
  season: string | null;
};

export function fetchPublicTeams(slug: string) {
  return apiFetch<ApiTeam[]>(`/v1/orgs/${slug}/teams`);
}

export function fetchPublicSponsor(slug: string, sponsorSlug: string) {
  return apiFetch<ApiSponsor>(`/v1/orgs/${slug}/sponsors/${sponsorSlug}`);
}

export function fetchMe(token: string) {
  return apiFetch<MeResponse>("/v1/me", { token });
}

export function fetchAdminSponsors(slug: string, token: string) {
  return apiFetch<ApiSponsor[]>(`/v1/orgs/${slug}/admin/sponsors`, { token });
}

export function createSponsor(
  slug: string,
  token: string,
  body: {
    slug: string;
    name: string;
    tagline?: string;
    description?: string;
    website_url?: string;
  },
) {
  return apiFetch<ApiSponsor>(`/v1/orgs/${slug}/admin/sponsors`, {
    method: "POST",
    token,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function updateSponsor(
  slug: string,
  sponsorSlug: string,
  token: string,
  body: Record<string, unknown>,
) {
  return apiFetch<ApiSponsor>(`/v1/orgs/${slug}/admin/sponsors/${sponsorSlug}`, {
    method: "PATCH",
    token,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function approveSponsor(slug: string, sponsorSlug: string, token: string) {
  return apiFetch<ApiSponsor>(
    `/v1/orgs/${slug}/admin/sponsors/${sponsorSlug}/approve`,
    { method: "POST", token },
  );
}

export function publishSponsor(slug: string, sponsorSlug: string, token: string) {
  return apiFetch<ApiSponsor>(
    `/v1/orgs/${slug}/admin/sponsors/${sponsorSlug}/publish`,
    { method: "POST", token },
  );
}

export function unpublishSponsor(
  slug: string,
  sponsorSlug: string,
  token: string,
) {
  return apiFetch<ApiSponsor>(
    `/v1/orgs/${slug}/admin/sponsors/${sponsorSlug}/unpublish`,
    { method: "POST", token },
  );
}

export async function uploadSponsorAsset(
  slug: string,
  sponsorSlug: string,
  token: string,
  assetType: "logo" | "banner",
  file: File,
) {
  const form = new FormData();
  form.set("asset_type", assetType);
  form.set("file", file);
  return apiFetch<{ url: string | null; storage_path: string }>(
    `/v1/orgs/${slug}/admin/sponsors/${sponsorSlug}/assets`,
    { method: "POST", token, body: form },
  );
}

export type ApiFixture = {
  id: string;
  schedule_id: string | null;
  season: string;
  competition: string;
  home_team_id: string | null;
  away_team_id: string | null;
  home_team_name: string;
  away_team_name: string;
  venue: string;
  starts_at: string;
  timezone: string;
  format_code: string;
  format_name: string;
  overs: number | null;
  status: string;
  result_summary: string | null;
  organization_id?: string;
};

export type ApiFixturePage = {
  items: ApiFixture[];
  total: number;
  limit: number;
  offset: number;
};

export type ApiSchedule = {
  id: string;
  name: string;
  season: string;
  competition: string;
  format_code: string;
  format_name: string;
  overs: number | null;
  timezone: string;
  status: string;
  organization_id?: string;
};

export type ApiSchedulePage = {
  items: ApiSchedule[];
  total: number;
  limit: number;
  offset: number;
};

export type ApiFormat = { code: string; name: string; overs: number | null };

export function fetchFixtureFormats() {
  return apiFetch<ApiFormat[]>("/v1/fixture-formats");
}

export function fetchPublicFixtures(
  slug: string,
  params: Record<string, string | number | undefined> = {},
) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") query.set(key, String(value));
  }
  const suffix = query.size ? `?${query.toString()}` : "";
  return apiFetch<ApiFixturePage>(`/v1/orgs/${slug}/fixtures${suffix}`);
}

export function fetchPublicFixture(slug: string, fixtureId: string) {
  return apiFetch<ApiFixture>(`/v1/orgs/${slug}/fixtures/${fixtureId}`);
}

export function fetchPublicSchedules(slug: string) {
  return apiFetch<ApiSchedulePage>(`/v1/orgs/${slug}/schedules?limit=50`);
}

export function fetchAdminFixtures(slug: string, token: string) {
  return apiFetch<ApiFixturePage>(`/v1/orgs/${slug}/admin/fixtures?limit=100`, { token });
}

export function fetchAdminSchedules(slug: string, token: string) {
  return apiFetch<ApiSchedulePage>(`/v1/orgs/${slug}/admin/schedules?limit=100`, { token });
}

export function createFixture(slug: string, token: string, body: Record<string, unknown>) {
  return apiFetch<ApiFixture>(`/v1/orgs/${slug}/admin/fixtures`, {
    method: "POST",
    token,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function updateFixture(
  slug: string,
  fixtureId: string,
  token: string,
  body: Record<string, unknown>,
) {
  return apiFetch<ApiFixture>(`/v1/orgs/${slug}/admin/fixtures/${fixtureId}`, {
    method: "PATCH",
    token,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function createSchedule(slug: string, token: string, body: Record<string, unknown>) {
  return apiFetch<ApiSchedule>(`/v1/orgs/${slug}/admin/schedules`, {
    method: "POST",
    token,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function issueDevToken(email: string, displayName: string) {
  return apiFetch<{ access_token: string }>("/v1/auth/dev-token", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, display_name: displayName }),
  });
}
