import type { Metadata } from "next";
import Link from "next/link";
import { ClubShell } from "@/components/club-shell";
import { SponsorStrip } from "@/components/sponsor-strip";
import { fetchPublicSponsors } from "@/lib/api/client";
import { CLUBS, canonicalOrigin } from "@/lib/clubs";
import { getResolvedHost } from "@/lib/clubs/server";

export async function generateMetadata(): Promise<Metadata> {
  const resolved = await getResolvedHost();

  if (resolved.kind === "club") {
    const origin = canonicalOrigin(resolved);
    return {
      title: resolved.club.name,
      description: resolved.club.tagline,
      alternates: origin ? { canonical: origin } : undefined,
      openGraph: {
        title: resolved.club.name,
        description: resolved.club.tagline,
        url: origin ?? undefined,
        siteName: resolved.club.name,
      },
    };
  }

  if (resolved.kind === "unknown") {
    return {
      title: "Unknown host",
      description: "This hostname is not an allowlisted My Cricket 360 club domain.",
      robots: { index: false, follow: false },
    };
  }

  return {
    title: "My Cricket 360",
    description:
      "One platform for Starks Cricket and CGI Steelers Cricket — fixtures, teams, sponsors, and more.",
  };
}

export default async function HomePage() {
  const resolved = await getResolvedHost();

  if (resolved.kind === "club") {
    const { club } = resolved;
    let publishedSponsors: Awaited<ReturnType<typeof fetchPublicSponsors>> = [];
    try {
      publishedSponsors = await fetchPublicSponsors(club.slug);
    } catch {
      publishedSponsors = [];
    }
    const featured = publishedSponsors[0];

    return (
      <ClubShell club={club}>
        <section className="mx-auto max-w-5xl px-4 pb-10 pt-14">
          <p className="animate-rise text-xs uppercase tracking-[0.25em] text-[var(--club-secondary)]">
            {club.shortName}
          </p>
          <h1 className="animate-rise font-display mt-3 max-w-3xl text-4xl leading-tight text-[var(--club-foreground)] sm:text-6xl">
            {club.name}
          </h1>
          <p className="animate-rise-delay mt-4 max-w-2xl text-lg text-[var(--club-foreground)]/80">
            {club.tagline}
          </p>
          <div className="animate-rise-delay mt-8 flex flex-wrap gap-3">
            <Link
              href="/fixtures"
              className="rounded bg-[var(--club-primary)] px-4 py-2.5 text-white"
            >
              View fixtures
            </Link>
            <Link
              href="/sponsors"
              className="rounded border border-[var(--club-primary)] px-4 py-2.5 text-[var(--club-primary)]"
            >
              Our sponsors
            </Link>
          </div>
        </section>
        {featured ? (
          <SponsorStrip
            sponsor={{
              slug: featured.slug,
              name: featured.name,
              tagline: featured.tagline || "",
              websiteUrl: featured.website_url || "#",
            }}
            clubName={club.name}
          />
        ) : null}
        <section className="mx-auto grid max-w-5xl gap-6 px-4 py-12 sm:grid-cols-3">
          {[
            {
              title: "Teams",
              body: "Squad lists and divisions for the season.",
              href: "/teams",
            },
            {
              title: "Announcements",
              body: "Club news and match-day updates.",
              href: "/announcements",
            },
            {
              title: "Gallery",
              body: "Photos from nets, matches, and events.",
              href: "/gallery",
            },
          ].map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="block border-t-2 border-[var(--club-accent)] pt-4"
            >
              <h2 className="font-display text-xl">{item.title}</h2>
              <p className="mt-2 text-sm opacity-80">{item.body}</p>
            </Link>
          ))}
        </section>
      </ClubShell>
    );
  }

  if (resolved.kind === "unknown") {
    return (
      <main className="mx-auto flex min-h-screen max-w-lg flex-col justify-center px-4 py-16">
        <h1 className="font-display text-3xl">Unknown host</h1>
        <p className="mt-3 text-[var(--foreground)]/80">
          <code className="rounded bg-black/5 px-1">
            {resolved.hostname || "(empty)"}
          </code>{" "}
          is not an allowlisted club domain. My Cricket 360 will not infer a
          club from an unvalidated Host header.
        </p>
        <Link href="http://localhost:43123" className="mt-6 underline">
          Open platform chooser on localhost
        </Link>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(ellipse_at_top,_#e8efe9,_#f7f5f1_55%)]">
      <div className="mx-auto max-w-4xl px-4 py-16">
        <p className="text-xs uppercase tracking-[0.25em] text-[#5a6b60]">
          Platform
        </p>
        <h1 className="font-display mt-3 text-5xl text-[#1a2b22]">
          My Cricket 360
        </h1>
        <p className="mt-4 max-w-2xl text-lg text-[#1a2b22]/80">
          {resolved.platform.tagline}
        </p>
        <div className="mt-10 grid gap-4 sm:grid-cols-2">
          {Object.values(CLUBS).map((club) => (
            <a
              key={club.slug}
              href={`http://${club.slug}.localhost:43123`}
              className="rounded-lg border border-black/10 bg-white/80 p-5 shadow-sm transition hover:-translate-y-0.5"
              style={{ borderTopColor: club.theme.primary, borderTopWidth: 4 }}
            >
              <h2 className="font-display text-2xl">{club.name}</h2>
              <p className="mt-2 text-sm opacity-80">{club.tagline}</p>
              <p className="mt-4 text-xs uppercase tracking-wide opacity-60">
                Local: {club.slug}.localhost:43123
              </p>
              <p className="text-xs opacity-60">
                Sponsor: {club.initialSponsor.name}
              </p>
            </a>
          ))}
        </div>
        <p className="mt-10 text-sm text-[#1a2b22]/70">
          Production hostnames ({Object.values(CLUBS)
            .map((c) => c.primaryDomain)
            .join(", ")}
          ) resolve to the same app after approved DNS cutover. Existing sites
          remain untouched until then.
        </p>
      </div>
    </main>
  );
}
