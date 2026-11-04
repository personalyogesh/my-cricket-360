import type { SupabaseClient } from "@supabase/supabase-js";
import { getPublishableKey, isSupabaseConfigured } from "@/lib/auth/publishable-key";
import { createClient as createBrowserSupabase } from "@/utils/supabase/client";

let browserClient: SupabaseClient | null = null;

export { getPublishableKey, isSupabaseConfigured };

/**
 * Browser/public Supabase client for project mycricket360 (org: personalyogesh).
 * Cookie session is shared with proxy refresh via @supabase/ssr.
 */
export function getSupabaseBrowserClient() {
  if (!isSupabaseConfigured()) return null;
  if (browserClient) return browserClient;
  browserClient = createBrowserSupabase();
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
