"use client";

import { useCallback, useState, useTransition } from "react";
import Link from "next/link";
import {
  approveSponsor,
  createSponsor,
  fetchAdminSponsors,
  fetchMe,
  getApiBase,
  publishSponsor,
  unpublishSponsor,
  updateSponsor,
  uploadSponsorAsset,
  type ApiSponsor,
} from "@/lib/api/client";

const TOKEN_KEY = "mc360.access_token";

type Props = { clubSlug: string; clubName: string };

function mediaUrl(url: string | null | undefined) {
  if (!url) return null;
  if (url.startsWith("http")) return url;
  return `${getApiBase()}${url}`;
}

function readStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function AdminSponsorsPanel({ clubSlug, clubName }: Props) {
  const [token] = useState<string | null>(() => readStoredToken());
  const [sponsors, setSponsors] = useState<ApiSponsor[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [roleOk, setRoleOk] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [preview, setPreview] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  const reload = useCallback(
    async (accessToken: string) => {
      const me = await fetchMe(accessToken);
      const membership = me.approved_clubs.find(
        (c) => c.organization_slug === clubSlug && c.role === "admin",
      );
      setRoleOk(Boolean(membership));
      if (!membership) {
        setError(
          `Signed in as ${me.user.email ?? me.user.display_name}, but not an approved admin of ${clubName}.`,
        );
        setSponsors([]);
        setLoaded(true);
        return;
      }
      setError(null);
      setSponsors(await fetchAdminSponsors(clubSlug, accessToken));
      setLoaded(true);
    },
    [clubName, clubSlug],
  );

  function loadSponsors() {
    if (!token) {
      setError("Not signed in");
      return;
    }
    startTransition(() => {
      void reload(token).catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load"),
      );
    });
  }

  async function withToken(fn: (t: string) => Promise<void>) {
    if (!token) {
      setError("Not signed in");
      return;
    }
    try {
      await fn(token);
      await reload(token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed");
    }
  }

  if (!token) {
    return (
      <div className="rounded border border-dashed border-black/20 bg-white/60 px-4 py-6 text-sm">
        <p>Sign in to manage sponsors for {clubName}.</p>
        <Link href="/admin/login" className="mt-3 inline-block underline">
          Go to admin login
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={loadSponsors}
          className="rounded bg-[var(--club-primary)] px-3 py-2 text-sm text-white"
          disabled={pending}
        >
          {pending ? "Loading…" : loaded ? "Refresh sponsors" : "Load sponsors"}
        </button>
        <Link href="/admin/login" className="text-sm underline">
          Switch account
        </Link>
      </div>

      {error ? (
        <p className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
          {error}
        </p>
      ) : null}

      {roleOk ? (
        <form
          className="grid gap-3 rounded border border-black/10 bg-white/70 p-4 sm:grid-cols-3"
          onSubmit={(e) => {
            e.preventDefault();
            withToken(async (t) => {
              await createSponsor(clubSlug, t, { slug, name });
              setName("");
              setSlug("");
            });
          }}
        >
          <input
            className="rounded border px-3 py-2 text-sm"
            placeholder="Sponsor name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <input
            className="rounded border px-3 py-2 text-sm"
            placeholder="slug-like-this"
            value={slug}
            onChange={(e) => setSlug(e.target.value)}
            required
            pattern="^[a-z0-9]+(?:-[a-z0-9]+)*$"
          />
          <button type="submit" className="rounded bg-[var(--club-primary)] px-3 py-2 text-white">
            Create draft
          </button>
        </form>
      ) : null}

      <ul className="space-y-4">
        {sponsors.map((sponsor) => (
          <li key={sponsor.id} className="rounded border border-black/10 bg-white/80 p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="font-display text-xl">{sponsor.name}</h2>
                <p className="text-xs uppercase tracking-wide opacity-60">
                  {sponsor.slug} · {sponsor.status}
                </p>
                {sponsor.tagline ? (
                  <p className="mt-1 text-sm opacity-80">{sponsor.tagline}</p>
                ) : null}
              </div>
              {mediaUrl(sponsor.logo_url) ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={mediaUrl(sponsor.logo_url)!}
                  alt=""
                  className="h-12 object-contain"
                />
              ) : null}
            </div>
            <div className="mt-4 flex flex-wrap gap-2 text-sm">
              <button
                type="button"
                className="rounded border px-2 py-1"
                onClick={() =>
                  withToken((t) =>
                    updateSponsor(clubSlug, sponsor.slug, t, {
                      tagline: sponsor.tagline || `Partner of ${clubName}`,
                    }).then(() => undefined),
                  )
                }
              >
                Save tagline
              </button>
              <button
                type="button"
                className="rounded border px-2 py-1"
                onClick={() =>
                  withToken((t) =>
                    approveSponsor(clubSlug, sponsor.slug, t).then(() => undefined),
                  )
                }
              >
                Approve
              </button>
              <button
                type="button"
                className="rounded border px-2 py-1"
                onClick={() =>
                  withToken((t) =>
                    publishSponsor(clubSlug, sponsor.slug, t).then(() => undefined),
                  )
                }
              >
                Publish
              </button>
              <button
                type="button"
                className="rounded border px-2 py-1"
                onClick={() =>
                  withToken((t) =>
                    unpublishSponsor(clubSlug, sponsor.slug, t).then(() => undefined),
                  )
                }
              >
                Unpublish
              </button>
              <label className="rounded border px-2 py-1">
                Upload logo
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  className="hidden"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (!file) return;
                    setPreview(URL.createObjectURL(file));
                    withToken(async (t) => {
                      await uploadSponsorAsset(
                        clubSlug,
                        sponsor.slug,
                        t,
                        "logo",
                        file,
                      );
                    });
                  }}
                />
              </label>
            </div>
            {preview ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={preview} alt="Upload preview" className="mt-3 h-16 object-contain" />
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
