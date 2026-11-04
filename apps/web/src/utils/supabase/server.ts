import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import { assertPublishableKey, getPublishableKey } from "@/lib/auth/publishable-key";

export const createClient = async (cookieStore: Awaited<ReturnType<typeof cookies>>) => {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey = getPublishableKey();
  if (!supabaseUrl || !supabaseKey) {
    throw new Error(
      "Supabase server client requires NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY.",
    );
  }
  assertPublishableKey(supabaseKey);

  return createServerClient(supabaseUrl, supabaseKey, {
    cookies: {
      getAll() {
        return cookieStore.getAll();
      },
      setAll(cookiesToSet) {
        try {
          cookiesToSet.forEach(({ name, value, options }) => cookieStore.set(name, value, options));
        } catch {
          // setAll from a Server Component can be ignored when proxy refreshes the session.
        }
      },
    },
  });
};
