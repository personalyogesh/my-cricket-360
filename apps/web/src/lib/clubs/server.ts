import { headers } from "next/headers";
import { resolveClubFromHost, type ResolvedHost } from "./index";

/**
 * Resolve club for the current request using Next.js request headers.
 * Prefers the validated `x-club-host` set by proxy (copied from Host
 * after allowlist check), falling back to `host` for tests/edge cases.
 */
export async function getResolvedHost(): Promise<ResolvedHost> {
  const h = await headers();
  const clubHost = h.get("x-club-host");
  const host = clubHost ?? h.get("host");
  return resolveClubFromHost(host);
}
