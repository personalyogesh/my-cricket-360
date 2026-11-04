import { afterEach, describe, expect, it } from "vitest";
import { assertPublishableKey, getPublishableKey, isSupabaseConfigured } from "./publishable-key";

const ENV_KEYS = [
  "NEXT_PUBLIC_SUPABASE_URL",
  "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
  "NEXT_PUBLIC_SUPABASE_ANON_KEY",
] as const;

afterEach(() => {
  for (const key of ENV_KEYS) delete process.env[key];
});

describe("publishable supabase key", () => {
  it("prefers the publishable key over the legacy anon key", () => {
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY = "sb_publishable_test";
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = "anon-legacy";
    expect(getPublishableKey()).toBe("sb_publishable_test");
  });

  it("refuses a secret key", () => {
    expect(() => assertPublishableKey("sb_secret_do_not_use")).toThrow(/secret/);
    expect(() => assertPublishableKey("service_role_key")).toThrow(/secret/);
  });

  it("is configured only when url and a publishable key exist", () => {
    expect(isSupabaseConfigured()).toBe(false);
    process.env.NEXT_PUBLIC_SUPABASE_URL = "https://example.supabase.co";
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY = "sb_publishable_test";
    expect(isSupabaseConfigured()).toBe(true);
  });
});
