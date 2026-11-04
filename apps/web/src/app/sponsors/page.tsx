import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ClubShell } from "@/components/club-shell";
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
  const sponsor = club.initialSponsor;

  return (
    <ClubShell club={club}>
      <section className="mx-auto max-w-5xl px-4 py-12">
        <h1 className="font-display text-4xl">Sponsors</h1>
        <p className="mt-3 max-w-2xl opacity-80">
          Partners who make {club.shortName} possible. Public profiles are
          club-scoped to this hostname only.
        </p>
        <ul className="mt-10 space-y-4">
          <li className="border-l-4 border-[var(--club-accent)] bg-white/60 px-5 py-4">
            <h2 className="font-display text-2xl">{sponsor.name}</h2>
            <p className="mt-1 text-sm opacity-80">{sponsor.tagline}</p>
            <Link
              href={`/sponsors/${sponsor.slug}`}
              className="mt-3 inline-block text-[var(--club-primary)] underline"
            >
              View sponsor page
            </Link>
          </li>
        </ul>
      </section>
    </ClubShell>
  );
}
