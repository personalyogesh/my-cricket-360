"use client";

import { useEffect } from "react";
import { getSupabaseBrowserClient } from "@/lib/auth/supabase";
import { writeAccessToken } from "@/lib/auth/session";

/** Keep the API bearer token aligned with the Supabase session, including refresh. */
export function AuthSessionSync() {
  useEffect(() => {
    const supabase = getSupabaseBrowserClient();
    if (!supabase) return;
    const { data } = supabase.auth.onAuthStateChange((_event, session) => {
      writeAccessToken(window.localStorage, session?.access_token ?? null);
    });
    return () => data.subscription.unsubscribe();
  }, []);
  return null;
}
