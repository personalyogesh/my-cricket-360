import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ClubShell } from "@/components/club-shell";
import { canonicalOrigin } from "@/lib/clubs";
import { getResolvedHost } from "@/lib/clubs/server";

type PageProps = { params: Promise<{ slug: string }> };

export async function generateMetadata({
  params,
}: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const resolved = await getResolvedHost();
  if (resolved.kind !== "club") return { title: "Sponsor" };
  if (resolved.club.initialSponsor.slug !== slug) return { title: "Sponsor" };
  const origin = canonicalOrigin(resolved);
  const sponsor = resolved.club.initialSponsor;
  return {
    title: `${sponsor.name} · ${resolved.club.name}`,
    description: sponsor.tagline,
    alternates: origin
      ? { canonical: `${origin}/sponsors/${sponsor.slug}` }
      : undefined,
  };
}

export default async function SponsorDetailPage({ params }: PageProps) {
  const { slug } = await params;
  const resolved = await getResolvedHost();
  if (resolved.kind !== "club") notFound();

  // Only serve sponsors for the allowlisted club on this host — never look up
  // another org's sponsor by slug alone.
  const sponsor = resolved.club.initialSponsor;
  if (sponsor.slug !== slug) notFound();

  return (
    <ClubShell club={resolved.club}>
      <article className="mx-auto max-w-3xl px-4 py-12">
        <p className="text-xs uppercase tracking-[0.2em] text-[var(--club-secondary)]">
          Official sponsor
        </p>
        <h1 className="font-display mt-2 text-4xl sm:text-5xl">
          {sponsor.name}
        </h1>
        <p className="mt-4 text-lg opacity-85">{sponsor.tagline}</p>
        <p className="mt-6 opacity-80">
          {sponsor.name} supports {resolved.club.name} through the My Cricket
          360 sponsor program. Campaign placements and analytics are managed in
          the club admin dashboard.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <a
            href={sponsor.websiteUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded bg-[var(--club-primary)] px-4 py-2.5 text-white"
          >
            Visit {sponsor.name}
          </a>
          <Link
            href="/sponsors"
            className="rounded border border-[var(--club-primary)] px-4 py-2.5"
          >
            All sponsors
          </Link>
        </div>
      </article>
    </ClubShell>
  );
}
