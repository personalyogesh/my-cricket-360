import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ClubShell } from "@/components/club-shell";
import { fetchPublicSponsor } from "@/lib/api/client";
import { canonicalOrigin } from "@/lib/clubs";
import { getResolvedHost } from "@/lib/clubs/server";

type PageProps = { params: Promise<{ slug: string }> };

export async function generateMetadata({
  params,
}: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const resolved = await getResolvedHost();
  if (resolved.kind !== "club") return { title: "Sponsor" };
  try {
    const sponsor = await fetchPublicSponsor(resolved.club.slug, slug);
    const origin = canonicalOrigin(resolved);
    return {
      title: `${sponsor.name} · ${resolved.club.name}`,
      description: sponsor.tagline ?? undefined,
      alternates: origin
        ? { canonical: `${origin}/sponsors/${sponsor.slug}` }
        : undefined,
    };
  } catch {
    return { title: "Sponsor" };
  }
}

export default async function SponsorDetailPage({ params }: PageProps) {
  const { slug } = await params;
  const resolved = await getResolvedHost();
  if (resolved.kind !== "club") notFound();

  let sponsor;
  try {
    sponsor = await fetchPublicSponsor(resolved.club.slug, slug);
  } catch {
    notFound();
  }

  return (
    <ClubShell club={resolved.club}>
      <article className="mx-auto max-w-3xl px-4 py-12">
        <p className="text-xs uppercase tracking-[0.2em] text-[var(--club-secondary)]">
          Official sponsor
        </p>
        <h1 className="font-display mt-2 text-4xl sm:text-5xl">{sponsor.name}</h1>
        {sponsor.tagline ? (
          <p className="mt-4 text-lg opacity-85">{sponsor.tagline}</p>
        ) : null}
        {sponsor.description ? (
          <p className="mt-6 opacity-80">{sponsor.description}</p>
        ) : null}
        {sponsor.logo_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={
              sponsor.logo_url.startsWith("http")
                ? sponsor.logo_url
                : `${process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8400"}${sponsor.logo_url}`
            }
            alt={`${sponsor.name} logo`}
            className="mt-8 max-h-24 object-contain"
          />
        ) : null}
        <div className="mt-8 flex flex-wrap gap-3">
          {sponsor.website_url ? (
            <a
              href={sponsor.website_url}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded bg-[var(--club-primary)] px-4 py-2.5 text-white"
            >
              Visit {sponsor.name}
            </a>
          ) : null}
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
