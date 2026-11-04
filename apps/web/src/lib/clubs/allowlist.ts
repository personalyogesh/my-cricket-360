import type { ClubConfig, ClubSlug } from "./types";

/**
 * Server-side allowlisted club definitions.
 * Host → club mapping is derived only from this module (plus env overlays later).
 * Never resolve a club from an unvalidated Host string outside this allowlist.
 */
export const CLUBS: Record<ClubSlug, ClubConfig> = {
  starks: {
    slug: "starks",
    organizationId: "00000000-0000-4000-8000-000000000001",
    name: "Starks Cricket",
    shortName: "Starks",
    primaryDomain: "starksgroup.org",
    productionHosts: ["starksgroup.org", "www.starksgroup.org"] as const,
    theme: {
      primary: "#0B3D2E",
      secondary: "#1A5C45",
      background: "#F3F7F4",
      foreground: "#10231C",
      muted: "#D7E5DD",
      accent: "#C4A35A",
    },
    logoText: "Starks Cricket",
    tagline: "Community cricket in the Triangle — fixtures, teams, and partners.",
    initialSponsor: {
      slug: "hashtag-india-cary",
      name: "Hashtag India Cary",
      tagline: "Proud founding sponsor of Starks Cricket",
      websiteUrl: "https://hashtagindiacary.com",
    },
  },
  steelers: {
    slug: "steelers",
    organizationId: "00000000-0000-4000-8000-000000000002",
    name: "CGI Steelers Cricket",
    shortName: "Steelers",
    primaryDomain: "cgisteelerscricket.org",
    productionHosts: [
      "cgisteelerscricket.org",
      "www.cgisteelerscricket.org",
    ] as const,
    theme: {
      primary: "#1B2A4A",
      secondary: "#2E4570",
      background: "#F2F4F8",
      foreground: "#121826",
      muted: "#D8DEEA",
      accent: "#B33A3A",
    },
    logoText: "CGI Steelers",
    tagline: "Steelers cricket — matches, squads, and CGI partnership.",
    initialSponsor: {
      slug: "cgi",
      name: "CGI",
      tagline: "Proud founding sponsor of CGI Steelers Cricket",
      websiteUrl: "https://www.cgi.com",
    },
  },
};

/** Local development hostnames → club slug (port stripped before lookup). */
export const LOCAL_HOST_TO_SLUG: Record<string, ClubSlug> = {
  "starks.localhost": "starks",
  "www.starks.localhost": "starks",
  "steelers.localhost": "steelers",
  "www.steelers.localhost": "steelers",
};

/** Hostnames that intentionally show the platform chooser (not a club). */
export const PLATFORM_HOSTS = new Set([
  "localhost",
  "127.0.0.1",
  "mycricket360.localhost",
  "www.mycricket360.localhost",
]);

/**
 * Build hostname → slug map from production + local allowlists.
 * Exported for tests and middleware.
 */
export function buildHostAllowlist(): ReadonlyMap<string, ClubSlug> {
  const map = new Map<string, ClubSlug>();

  for (const club of Object.values(CLUBS)) {
    for (const host of club.productionHosts) {
      map.set(host.toLowerCase(), club.slug);
    }
  }

  for (const [host, slug] of Object.entries(LOCAL_HOST_TO_SLUG)) {
    map.set(host.toLowerCase(), slug);
  }

  return map;
}

export const HOST_ALLOWLIST = buildHostAllowlist();
