export {
  CLUBS,
  HOST_ALLOWLIST,
  LOCAL_HOST_TO_SLUG,
  PLATFORM_HOSTS,
  buildHostAllowlist,
} from "./allowlist";
export {
  canonicalOrigin,
  getClubBySlug,
  isWwwHost,
  normalizeHost,
  resolveClubFromHost,
} from "./resolve";
export type {
  ClubConfig,
  ClubSlug,
  ClubSponsorSeed,
  ClubTheme,
  PlatformConfig,
  ResolvedHost,
} from "./types";
