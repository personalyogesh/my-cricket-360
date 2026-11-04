/**
 * Publishable browser key for Supabase project mycricket360.
 * Accepts the current sb_publishable_… key or a legacy anon JWT.
 * Secret and service_role keys are refused.
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

export function assertPublishableKey(key: string) {
  const lower = key.toLowerCase();
  if (
    lower.startsWith("sb_secret_") ||
    lower.includes("service_role") ||
    lower.includes("service-role")
  ) {
    throw new Error(
      "Refusing to initialize a Supabase client with a secret/service_role key. Use the publishable or anon key only.",
    );
  }
}
