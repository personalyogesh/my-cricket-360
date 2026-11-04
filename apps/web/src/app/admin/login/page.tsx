"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { issueDevToken } from "@/lib/api/client";
import { readAccessToken, writeAccessToken } from "@/lib/auth/session";
import { getSupabaseBrowserClient, isSupabaseConfigured } from "@/lib/auth/supabase";

export default function AdminLoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"sign-in" | "sign-up">("sign-in");
  const [email, setEmail] = useState("admin@starks.local");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("Club Admin");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [hasToken, setHasToken] = useState(() =>
    typeof window === "undefined" ? false : Boolean(readAccessToken(window.localStorage)),
  );
  const supabaseReady = isSupabaseConfigured();

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setInfo(null);
    try {
      if (supabaseReady) {
        const supabase = getSupabaseBrowserClient();
        if (!supabase) throw new Error("Supabase client unavailable");
        if (mode === "sign-up") {
          const { data, error: authError } = await supabase.auth.signUp({
            email,
            password,
            options: { data: { display_name: displayName } },
          });
          if (authError) throw authError;
          const token = data.session?.access_token;
          if (!token) {
            setInfo("Account created. Confirm the email, then sign in.");
            return;
          }
          writeAccessToken(window.localStorage, token);
        } else {
          const { data, error: authError } = await supabase.auth.signInWithPassword({
            email,
            password,
          });
          if (authError) throw authError;
          const token = data.session?.access_token;
          if (!token) throw new Error("No session token returned");
          writeAccessToken(window.localStorage, token);
        }
      } else {
        const { access_token } = await issueDevToken(email, displayName);
        writeAccessToken(window.localStorage, access_token);
      }
      setHasToken(true);
      router.push("/admin");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  async function signOut() {
    setBusy(true);
    setError(null);
    try {
      const supabase = getSupabaseBrowserClient();
      if (supabase) await supabase.auth.signOut();
      writeAccessToken(window.localStorage, null);
      setHasToken(false);
      setInfo("Signed out.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign out failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-4">
      <h1 className="font-display text-3xl">
        {mode === "sign-up" ? "Create account" : "Club sign in"}
      </h1>
      <p className="mt-2 text-sm opacity-75">
        {supabaseReady
          ? "Supabase Auth for project mycricket360. The session refreshes in the browser and the API verifies the JWT."
          : "Supabase is not configured — using local dev tokens. Grant org admin in the API before managing sponsors."}
      </p>
      {supabaseReady ? (
        <div className="mt-4 flex gap-2 text-sm">
          <button type="button" className="underline" onClick={() => setMode("sign-in")}>
            Sign in
          </button>
          <button type="button" className="underline" onClick={() => setMode("sign-up")}>
            Sign up
          </button>
        </div>
      ) : null}
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
              minLength={8}
            />
          </label>
        ) : null}
        {!supabaseReady || mode === "sign-up" ? (
          <label className="block text-sm">
            Display name
            <input
              className="mt-1 w-full rounded border border-black/20 px-3 py-2"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
            />
          </label>
        ) : null}
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
        {info ? <p className="text-sm">{info}</p> : null}
        <button
          type="submit"
          disabled={busy}
          className="w-full rounded bg-[#0B3D2E] px-4 py-2.5 text-white disabled:opacity-60"
        >
          {busy ? "Working…" : mode === "sign-up" ? "Create account" : "Continue"}
        </button>
      </form>
      {hasToken ? (
        <button type="button" className="mt-4 text-sm underline" onClick={() => void signOut()} disabled={busy}>
          Sign out
        </button>
      ) : null}
    </main>
  );
}
