"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { issueDevToken } from "@/lib/api/client";
import { getSupabaseBrowserClient, isSupabaseConfigured } from "@/lib/auth/supabase";

const TOKEN_KEY = "mc360.access_token";

export default function AdminLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@starks.local");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("Club Admin");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const supabaseReady = isSupabaseConfigured();

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (supabaseReady) {
        const supabase = getSupabaseBrowserClient();
        if (!supabase) throw new Error("Supabase client unavailable");
        const { data, error: authError } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (authError) throw authError;
        const token = data.session?.access_token;
        if (!token) throw new Error("No session token returned");
        localStorage.setItem(TOKEN_KEY, token);
      } else {
        const { access_token } = await issueDevToken(email, displayName);
        localStorage.setItem(TOKEN_KEY, access_token);
      }
      router.push("/admin/sponsors");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-4">
      <h1 className="font-display text-3xl">Club admin login</h1>
      <p className="mt-2 text-sm opacity-75">
        {supabaseReady
          ? "Sign in with Supabase Auth."
          : "Supabase is not configured — using local dev tokens. Grant org admin in the API DB/tests before managing sponsors."}
      </p>
      <form onSubmit={onSubmit} className="mt-8 space-y-4">
        <label className="block text-sm">
          Email
          <input
            className="mt-1 w-full rounded border border-black/20 px-3 py-2"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        {supabaseReady ? (
          <label className="block text-sm">
            Password
            <input
              className="mt-1 w-full rounded border border-black/20 px-3 py-2"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>
        ) : (
          <label className="block text-sm">
            Display name
            <input
              className="mt-1 w-full rounded border border-black/20 px-3 py-2"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
            />
          </label>
        )}
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
        <button
          type="submit"
          disabled={busy}
          className="w-full rounded bg-[#0B3D2E] px-4 py-2.5 text-white disabled:opacity-60"
        >
          {busy ? "Signing in…" : "Continue"}
        </button>
      </form>
    </main>
  );
}
