import { createServerClient } from "@supabase/ssr";
import { type NextRequest, NextResponse } from "next/server";
import { assertPublishableKey, getPublishableKey } from "@/lib/auth/publishable-key";

/**
 * Refresh the Supabase auth cookie on the proxied request.
 * getClaims() is what rotates the session; creating the client alone does not.
 * Club headers already on `request` are kept when cookies are rewritten.
 */
export async function updateSession(request: NextRequest) {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey = getPublishableKey();
  if (!supabaseUrl || !supabaseKey) {
    return NextResponse.next({ request });
  }
  assertPublishableKey(supabaseKey);

  let supabaseResponse = NextResponse.next({ request });

  const supabase = createServerClient(supabaseUrl, supabaseKey, {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet) {
        cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value));
        supabaseResponse = NextResponse.next({ request });
        cookiesToSet.forEach(({ name, value, options }) =>
          supabaseResponse.cookies.set(name, value, options),
        );
      },
    },
  });

  try {
    await supabase.auth.getClaims();
  } catch {
    // Public club pages still render if Auth cannot be reached.
  }

  return supabaseResponse;
}
