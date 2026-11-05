import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ClubShell } from "@/components/club-shell";
import { FixtureList } from "@/components/fixture-list";
import { fetchPublicFixtures, fetchPublicSchedules } from "@/lib/api/client";
import { clubPageMetadata } from "@/lib/clubs/metadata";
import { getResolvedHost } from "@/lib/clubs/server";

export async function generateMetadata(): Promise<Metadata> {
  return clubPageMetadata("/fixtures", "Fixtures", "Upcoming matches for this club.");
}

export default async function FixturesPage() {
  const resolved = await getResolvedHost();
  if (resolved.kind !== "club") notFound();
  const { club } = resolved;

  let fixtures: Awaited<ReturnType<typeof fetchPublicFixtures>>["items"] = [];
  let schedules: Awaited<ReturnType<typeof fetchPublicSchedules>>["items"] = [];
  let loadError: string | null = null;
  try {
    const [fixturePage, schedulePage] = await Promise.all([
      fetchPublicFixtures(club.slug, { when: "upcoming", limit: 50 }),
      fetchPublicSchedules(club.slug),
    ]);
    fixtures = fixturePage.items;
    schedules = schedulePage.items;
  } catch (err) {
    loadError = err instanceof Error ? err.message : "Failed to load fixtures";
  }

  return (
    <ClubShell club={club}>
      <section className="mx-auto max-w-5xl px-4 py-10 sm:py-12">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="font-display text-4xl">Upcoming fixtures</h1>
            <p className="mt-3 max-w-2xl opacity-80">
              Scheduled, postponed, and live matches for {club.name}. Results appear only
              after a club admin records them.
            </p>
          </div>
          <Link href="/fixtures/completed" className="text-sm underline">
            Completed matches
          </Link>
        </div>
        {loadError ? (
          <p className="mt-8 rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            Could not reach the API ({loadError}).
          </p>
        ) : (
          <>
            {schedules.length > 0 ? (
              <ul className="mt-6 flex flex-col gap-2 sm:flex-row sm:flex-wrap">
                {schedules.map((schedule) => (
                  <li
                    key={schedule.id}
                    className="rounded border border-black/10 bg-white/70 px-3 py-2 text-sm"
                  >
                    {schedule.name} · {schedule.competition} · {schedule.format_name}
                  </li>
                ))}
              </ul>
            ) : null}
            <FixtureList
              fixtures={fixtures}
              empty={`No upcoming fixtures published for ${club.name}.`}
            />
          </>
        )}
      </section>
    </ClubShell>
  );
}
