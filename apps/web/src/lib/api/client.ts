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

export function issueDevToken(email: string, displayName: string) {
  return apiFetch<{ access_token: string }>("/v1/auth/dev-token", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, display_name: displayName }),
  });
}
