/**
 * Club configuration types for hostname-based multi-tenancy.
 * Security: only allowlisted hostnames may resolve to a club.
 */

export type ClubSlug = "starks" | "steelers";

export type ClubTheme = {
  /** Primary brand color (CSS hex) */
  primary: string;
  /** Secondary / accent */
  secondary: string;
  /** Page background */
  background: string;
  /** Main text */
  foreground: string;
  /** Muted surface */
  muted: string;
  /** CTA / highlight */
  accent: string;
};

export type ClubSponsorSeed = {
  slug: string;
  name: string;
  tagline: string;
  websiteUrl: string;
};

export type ClubConfig = {
  slug: ClubSlug;
  /** Stable id used in API / DB seed alignment */
  organizationId: string;
  name: string;
  shortName: string;
  /** Canonical production apex hostname (no www) */
  primaryDomain: string;
  /** All production hostnames for this club (apex + www) */
  productionHosts: readonly string[];
  theme: ClubTheme;
  logoText: string;
  tagline: string;
  initialSponsor: ClubSponsorSeed;
};

export type PlatformConfig = {
  kind: "platform";
  name: string;
  tagline: string;
};

export type ResolvedHost =
  | { kind: "club"; club: ClubConfig; hostname: string; isWww: boolean }
  | { kind: "platform"; platform: PlatformConfig; hostname: string }
  | { kind: "unknown"; hostname: string };
