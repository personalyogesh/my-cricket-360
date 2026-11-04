import { NextResponse, type NextRequest } from "next/server";
import { resolveClubFromHost } from "@/lib/clubs";

/**
 * Attach resolved club context headers for server components.
 * Security: organization identity for data loading still comes from the
 * allowlist lookup in resolveClubFromHost — never from client-supplied query params.
 */
export function proxy(request: NextRequest) {
  const host = request.headers.get("host");
  const resolved = resolveClubFromHost(host);

  const requestHeaders = new Headers(request.headers);
  const normalized = resolved.hostname || "";
  requestHeaders.set("x-club-host", normalized);

  if (resolved.kind === "club") {
    requestHeaders.set("x-club-slug", resolved.club.slug);
    requestHeaders.set("x-organization-id", resolved.club.organizationId);
  } else {
    requestHeaders.delete("x-club-slug");
    requestHeaders.delete("x-organization-id");
  }

  return NextResponse.next({
    request: { headers: requestHeaders },
  });
}

export const config = {
  matcher: [
    /*
     * Match all paths except static assets and Next internals.
     */
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
