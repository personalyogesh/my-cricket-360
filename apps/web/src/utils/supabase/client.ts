import { createBrowserClient } from "@supabase/ssr";
import { assertPublishableKey, getPublishableKey } from "@/lib/auth/publishable-key";

export const createClient = () => {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey = getPublishableKey();
  if (!supabaseUrl || !supabaseKey) {
    throw new Error(
      "Supabase browser client requires NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY.",
    );
  }
  assertPublishableKey(supabaseKey);
  return createBrowserClient(supabaseUrl, supabaseKey);
};
