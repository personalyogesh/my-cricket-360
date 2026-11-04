"use client";

import { useState } from "react";
import Link from "next/link";
import { fetchMe } from "@/lib/api/client";
import { readAccessToken } from "@/lib/auth/session";

type MembershipRow = {
  id: string;
  user_id: string;
  email: string | null;
  display_name: string | null;
  role: string;
  status: string;
};

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "http://127.0.0.1:8400";

async function api<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      ...(init?.headers || {}),
      Authorization: `Bearer ${token}`,
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body);
    } catch {
      /* ignore */
    }
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export function AdminMembershipsPanel({
  clubSlug,
  clubName,
}: {
  clubSlug: string;
  clubName: string;
}) {
  const [token] = useState<string | null>(() =>
    typeof window === "undefined" ? null : readAccessToken(window.localStorage),
  );
  const [rows, setRows] = useState<MembershipRow[]>([]);
  const [selfId, setSelfId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function load() {
    if (!token) return;
    setBusy(true);
    setError(null);
    try {
      const me = await fetchMe(token);
      setSelfId(me.user.id);
      setRows(await api<MembershipRow[]>(`/v1/orgs/${clubSlug}/memberships`, token));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load memberships");
    } finally {
      setBusy(false);
    }
  }

  async function decide(id: string, decision: "approved" | "rejected" | "suspended") {
    if (!token) return;
    setBusy(true);
    setError(null);
    try {
      await api(`/v1/orgs/${clubSlug}/memberships/${id}/decision`, token, {
        method: "POST",
        body: JSON.stringify({ decision }),
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Decision failed");
      setBusy(false);
    }
  }

  if (!token) {
    return (
      <p className="text-sm">
        <Link href="/admin/login" className="underline">
          Sign in
        </Link>{" "}
        to review {clubName} memberships.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <button
        type="button"
        onClick={() => void load()}
        disabled={busy}
        className="rounded bg-[var(--club-primary)] px-3 py-2 text-sm text-white disabled:opacity-60"
      >
        {busy ? "Working…" : "Load memberships"}
      </button>
      {error ? <p className="text-sm text-red-700">{error}</p> : null}
      <ul className="space-y-3">
        {rows.map((row) => {
          const own = selfId === row.user_id;
          return (
            <li key={row.id} className="rounded border border-black/10 bg-white/80 p-4">
              <p className="font-medium">{row.display_name || row.email || row.user_id}</p>
              <p className="text-xs uppercase tracking-wide opacity-60">
                {row.email || "no email"} · {row.role} · {row.status}
              </p>
              {own ? (
                <p className="mt-2 text-sm">You cannot decide your own membership.</p>
              ) : (
                <div className="mt-3 flex flex-wrap gap-2 text-sm">
                  <button
                    type="button"
                    className="rounded border px-2 py-1"
                    disabled={busy}
                    onClick={() => void decide(row.id, "approved")}
                  >
                    Approve
                  </button>
                  <button
                    type="button"
                    className="rounded border px-2 py-1"
                    disabled={busy}
                    onClick={() => void decide(row.id, "rejected")}
                  >
                    Reject
                  </button>
                  <button
                    type="button"
                    className="rounded border px-2 py-1"
                    disabled={busy}
                    onClick={() => void decide(row.id, "suspended")}
                  >
                    Suspend
                  </button>
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
