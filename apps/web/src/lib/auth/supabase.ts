import { createClient, type SupabaseClient } from "@supabase/supabase-js";

let browserClient: SupabaseClient | null = null;

/**
 * Browser/public Supabase client for project mycricket360 (org: personalyogesh).
 * Only NEXT_PUBLIC_SUPABASE_URL + NEXT_PUBLIC_SUPABASE_ANON_KEY (publishable).
 * Never read service-role or database URLs in the browser.
 */
export function isSupabaseConfigured() {
  return Boolean(
    process.env.NEXT_PUBLIC_SUPABASE_URL &&
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  );
}

function assertPublishableKey(key: string) {
  // Heuristic: service_role JWTs often contain role claim; also reject obvious mislabels.
  const lower = key.toLowerCase();
  if (lower.includes("service_role") || lower.includes("service-role")) {
    throw new Error(
      "Refusing to initialize browser Supabase client with a service-role key. Use the anon/publishable key only.",
    );
  }
}

export function getSupabaseBrowserClient() {
  if (!isSupabaseConfigured()) return null;
  if (browserClient) return browserClient;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL!;
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;
  assertPublishableKey(anonKey);
  browserClient = createClient(url, anonKey, {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
    },
  });
  return browserClient;
}

export function getSupabaseProjectHost(): string | null {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  if (!url) return null;
  try {
    return new URL(url).hostname;
  } catch {
    return null;
  }
}
