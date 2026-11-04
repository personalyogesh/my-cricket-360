import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ClubShell } from "@/components/club-shell";
import { fetchPublicSponsors } from "@/lib/api/client";
import { canonicalOrigin } from "@/lib/clubs";
import { getResolvedHost } from "@/lib/clubs/server";

export async function generateMetadata(): Promise<Metadata> {
  const resolved = await getResolvedHost();
  if (resolved.kind !== "club") return { title: "Sponsors" };
  const origin = canonicalOrigin(resolved);
  return {
    title: `Sponsors · ${resolved.club.name}`,
    description: `Partners supporting ${resolved.club.name}`,
    alternates: origin ? { canonical: `${origin}/sponsors` } : undefined,
  };
}

export default async function SponsorsPage() {
  const resolved = await getResolvedHost();
  if (resolved.kind !== "club") notFound();
  const { club } = resolved;

  let sponsors: Awaited<ReturnType<typeof fetchPublicSponsors>> = [];
  let loadError: string | null = null;
  try {
    sponsors = await fetchPublicSponsors(club.slug);
  } catch (err) {
    loadError = err instanceof Error ? err.message : "Failed to load sponsors";
  }

  return (
    <ClubShell club={club}>
      <section className="mx-auto max-w-5xl px-4 py-12">
        <h1 className="font-display text-4xl">Sponsors</h1>
        <p className="mt-3 max-w-2xl opacity-80">
          Published partners for {club.name}. Draft founding profiles stay private
          until club admins verify and publish them.
        </p>
        {loadError ? (
          <p className="mt-8 rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            Could not reach the API ({loadError}). Is it running on{" "}
            {process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8400"}?
          </p>
        ) : null}
        {!loadError && sponsors.length === 0 ? (
          <p className="mt-8 rounded border border-dashed border-black/20 bg-white/50 px-4 py-8 text-sm opacity-70">
            No published sponsors yet for this club.
          </p>
        ) : null}
        <ul className="mt-10 space-y-4">
          {sponsors.map((sponsor) => (
            <li
              key={sponsor.id}
              className="border-l-4 border-[var(--club-accent)] bg-white/60 px-5 py-4"
            >
              <h2 className="font-display text-2xl">{sponsor.name}</h2>
              {sponsor.tagline ? (
                <p className="mt-1 text-sm opacity-80">{sponsor.tagline}</p>
              ) : null}
              <Link
                href={`/sponsors/${sponsor.slug}`}
                className="mt-3 inline-block text-[var(--club-primary)] underline"
              >
                View sponsor page
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </ClubShell>
  );
}
