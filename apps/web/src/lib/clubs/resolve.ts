import {
  CLUBS,
  HOST_ALLOWLIST,
  PLATFORM_HOSTS,
} from "./allowlist";
import type { PlatformConfig, ResolvedHost } from "./types";

const PLATFORM: PlatformConfig = {
  kind: "platform",
  name: "My Cricket 360",
  tagline:
    "Multi-club cricket management for Starks, CGI Steelers, and clubs to come.",
};

/**
 * Normalize a Host header value for allowlist lookup.
 * - Lowercase
 * - Strip port
 * - Reject empty / obviously invalid values (return empty string)
 *
 * Does NOT treat the raw Host as a security decision by itself —
 * callers must only act on allowlist hits from resolveClubFromHost.
 */
export function normalizeHost(rawHost: string | null | undefined): string {
  if (!rawHost) return "";

  let host = rawHost.trim().toLowerCase();

  // Strip brackets for IPv6 literals then port — simple cases for local/dev.
  if (host.startsWith("[")) {
    const end = host.indexOf("]");
    if (end !== -1) {
      const ipv6 = host.slice(1, end);
      const rest = host.slice(end + 1);
      if (rest.startsWith(":")) {
        return ipv6;
      }
      return ipv6;
    }
  }

  // Remove port when host is hostname:port (not IPv6).
  const colon = host.lastIndexOf(":");
  if (colon !== -1 && host.indexOf(":") === colon) {
    const maybePort = host.slice(colon + 1);
    if (/^\d+$/.test(maybePort)) {
      host = host.slice(0, colon);
    }
  }

  // Basic sanity: no spaces, no scheme leftovers.
  if (!host || /\s/.test(host) || host.includes("/") || host.includes("?")) {
    return "";
  }

  return host;
}

export function isWwwHost(hostname: string): boolean {
  return hostname.startsWith("www.");
}

/**
 * Resolve club (or platform/unknown) from a Host header value.
 * Only allowlisted hostnames map to clubs — unknown never defaults to a club.
 */
export function resolveClubFromHost(
  rawHost: string | null | undefined,
): ResolvedHost {
  const hostname = normalizeHost(rawHost);

  if (!hostname) {
    return { kind: "unknown", hostname: "" };
  }

  if (PLATFORM_HOSTS.has(hostname)) {
    return { kind: "platform", platform: PLATFORM, hostname };
  }

  const slug = HOST_ALLOWLIST.get(hostname);
  if (!slug) {
    return { kind: "unknown", hostname };
  }

  const club = CLUBS[slug];
  return {
    kind: "club",
    club,
    hostname,
    isWww: isWwwHost(hostname),
  };
}

/**
 * Canonical site origin for SEO (https, primary apex domain).
 * Local hosts keep http and the local hostname.
 */
export function canonicalOrigin(resolved: ResolvedHost): string | null {
  if (resolved.kind === "club") {
    const { hostname, club } = resolved;
    if (hostname.endsWith(".localhost") || hostname === "localhost") {
      return `http://${hostname}`;
    }
    return `https://${club.primaryDomain}`;
  }
  if (resolved.kind === "platform") {
    if (
      resolved.hostname === "localhost" ||
      resolved.hostname.endsWith(".localhost") ||
      resolved.hostname === "127.0.0.1"
    ) {
      return `http://${resolved.hostname}`;
    }
    return null;
  }
  return null;
}

export function getClubBySlug(slug: string) {
  if (slug === "starks" || slug === "steelers") {
    return CLUBS[slug];
  }
  return null;
}
