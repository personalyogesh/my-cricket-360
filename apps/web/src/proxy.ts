import { type NextRequest } from "next/server";
import { resolveClubFromHost } from "@/lib/clubs";
import { updateSession } from "@/utils/supabase/middleware";

/**
 * Attach resolved club context, then refresh the Supabase session cookie.
 * Organization identity still comes only from the hostname allowlist.
 */
export async function proxy(request: NextRequest) {
  const host = request.headers.get("host");
  const resolved = resolveClubFromHost(host);

  const normalized = resolved.hostname || "";
  request.headers.set("x-club-host", normalized);

  if (resolved.kind === "club") {
    request.headers.set("x-club-slug", resolved.club.slug);
    request.headers.set("x-organization-id", resolved.club.organizationId);
  } else {
    request.headers.delete("x-club-slug");
    request.headers.delete("x-organization-id");
  }

  return updateSession(request);
}

export const config = {
  matcher: [
    /*
     * Match all paths except static assets and Next internals.
     */
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
