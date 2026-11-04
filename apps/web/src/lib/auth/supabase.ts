import { createClient, type SupabaseClient } from "@supabase/supabase-js";

let browserClient: SupabaseClient | null = null;

/**
 * Browser/public Supabase client for project mycricket360 (org: personalyogesh).
 *
 * Publishable only:
 * - NEXT_PUBLIC_SUPABASE_URL
 * - NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY (preferred) or NEXT_PUBLIC_SUPABASE_ANON_KEY (legacy)
 *
 * Never read secret/service_role keys or database URLs in the browser.
 * @supabase/supabase-js accepts both legacy JWT anon keys and sb_publishable_… keys.
 */
export function getPublishableKey(): string | undefined {
  return (
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ||
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
    undefined
  );
}

export function isSupabaseConfigured() {
  return Boolean(process.env.NEXT_PUBLIC_SUPABASE_URL && getPublishableKey());
}

function assertPublishableKey(key: string) {
  const lower = key.toLowerCase();
  if (
    lower.startsWith("sb_secret_") ||
    lower.includes("service_role") ||
    lower.includes("service-role")
  ) {
    throw new Error(
      "Refusing to initialize browser Supabase client with a secret/service_role key. Use the publishable or anon key only.",
    );
  }
}

export function getSupabaseBrowserClient() {
  if (!isSupabaseConfigured()) return null;
  if (browserClient) return browserClient;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL!;
  const publishableKey = getPublishableKey()!;
  assertPublishableKey(publishableKey);
  browserClient = createClient(url, publishableKey, {
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
