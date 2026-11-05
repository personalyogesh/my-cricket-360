"use client";

import { useState } from "react";
import Link from "next/link";
import { readAccessToken } from "@/lib/auth/session";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "http://127.0.0.1:8400";

export function RequestMembership({ clubSlug, clubName }: { clubSlug: string; clubName: string }) {
  const [token] = useState<string | null>(() =>
    typeof window === "undefined" ? null : readAccessToken(window.localStorage),
  );
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function request() {
    if (!token) return;
    setBusy(true);
    setMessage(null);
    try {
      const res = await fetch(`${API_BASE}/v1/me/memberships`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ organization_slug: clubSlug, role: "member" }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = typeof body.detail === "string" ? body.detail : res.statusText;
        throw new Error(detail);
      }
      setMessage(`Request recorded for ${clubName}: ${body.status}.`);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Request failed");
    } finally {
      setBusy(false);
    }
  }

  if (!token) {
    return (
      <p className="mt-6 text-sm">
        <Link href="/admin/login" className="underline">
          Sign in
        </Link>{" "}
        to request membership in {clubName}. The club is taken from this site&apos;s hostname.
      </p>
    );
  }

  return (
    <div className="mt-6">
      <button
        type="button"
        onClick={() => void request()}
        disabled={busy}
        className="rounded bg-[var(--club-primary)] px-4 py-2.5 text-white disabled:opacity-60"
      >
        {busy ? "Sending…" : `Request ${clubName} membership`}
      </button>
      {message ? <p className="mt-3 text-sm">{message}</p> : null}
    </div>
  );
}
