import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ClubShell } from "@/components/club-shell";
import { fetchPublicFixture } from "@/lib/api/client";
import { clubPageMetadata } from "@/lib/clubs/metadata";
import { formatFixtureWhen } from "@/lib/fixtures/time";
import { getResolvedHost } from "@/lib/clubs/server";

type Props = { params: Promise<{ id: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  return clubPageMetadata(`/fixtures/${id}`, "Fixture", "Match details for this club.");
}

export default async function FixtureDetailPage({ params }: Props) {
  const resolved = await getResolvedHost();
  if (resolved.kind !== "club") notFound();
  const { id } = await params;
  const { club } = resolved;

  let fixture: Awaited<ReturnType<typeof fetchPublicFixture>> | null = null;
  let loadError: string | null = null;
  try {
    fixture = await fetchPublicFixture(club.slug, id);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Failed to load fixture";
    if (message.startsWith("404")) notFound();
    loadError = message;
  }

  return (
    <ClubShell club={club}>
      <section className="mx-auto max-w-3xl px-4 py-10 sm:py-12">
        <Link href="/fixtures" className="text-sm underline">
          All fixtures
        </Link>
        {loadError ? (
          <p className="mt-8 rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            Could not reach the API ({loadError}).
          </p>
        ) : null}
        {fixture ? (
          <article className="mt-6 rounded border border-black/10 bg-white/80 p-4 sm:p-6">
            <p className="text-xs uppercase tracking-wide opacity-60">
              {fixture.competition} · {fixture.season}
            </p>
            <h1 className="mt-2 font-display text-3xl sm:text-4xl">
              {fixture.home_team_name} vs {fixture.away_team_name}
            </h1>
            <dl className="mt-6 grid grid-cols-1 gap-4 text-sm sm:grid-cols-2">
              <div>
                <dt className="opacity-60">When</dt>
                <dd>{formatFixtureWhen(fixture.starts_at, fixture.timezone)}</dd>
                <dd className="text-xs opacity-60">{fixture.timezone}</dd>
              </div>
              <div>
                <dt className="opacity-60">Venue</dt>
                <dd>{fixture.venue}</dd>
              </div>
              <div>
                <dt className="opacity-60">Format</dt>
                <dd>
                  {fixture.format_name}
                  {fixture.overs ? ` · ${fixture.overs} overs` : ""}
                </dd>
              </div>
              <div>
                <dt className="opacity-60">Status</dt>
                <dd className="capitalize">{fixture.status}</dd>
              </div>
            </dl>
            <p className="mt-6 text-sm">
              {fixture.result_summary ?? "No result has been entered for this match."}
            </p>
          </article>
        ) : null}
      </section>
    </ClubShell>
  );
}
