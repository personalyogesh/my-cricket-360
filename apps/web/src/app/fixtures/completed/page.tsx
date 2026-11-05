import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ClubShell } from "@/components/club-shell";
import { FixtureList } from "@/components/fixture-list";
import { fetchPublicFixtures } from "@/lib/api/client";
import { clubPageMetadata } from "@/lib/clubs/metadata";
import { getResolvedHost } from "@/lib/clubs/server";

export async function generateMetadata(): Promise<Metadata> {
  return clubPageMetadata(
    "/fixtures/completed",
    "Completed fixtures",
    "Completed matches for this club.",
  );
}

export default async function CompletedFixturesPage() {
  const resolved = await getResolvedHost();
  if (resolved.kind !== "club") notFound();
  const { club } = resolved;

  let fixtures: Awaited<ReturnType<typeof fetchPublicFixtures>>["items"] = [];
  let loadError: string | null = null;
  try {
    const page = await fetchPublicFixtures(club.slug, { when: "completed", limit: 50 });
    fixtures = page.items;
  } catch (err) {
    loadError = err instanceof Error ? err.message : "Failed to load fixtures";
  }

  return (
    <ClubShell club={club}>
      <section className="mx-auto max-w-5xl px-4 py-10 sm:py-12">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="font-display text-4xl">Completed fixtures</h1>
            <p className="mt-3 max-w-2xl opacity-80">
              Finished matches for {club.name}. A blank result means the club has not
              entered one yet.
            </p>
          </div>
          <Link href="/fixtures" className="text-sm underline">
            Upcoming fixtures
          </Link>
        </div>
        {loadError ? (
          <p className="mt-8 rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            Could not reach the API ({loadError}).
          </p>
        ) : (
          <FixtureList fixtures={fixtures} empty={`No completed fixtures for ${club.name}.`} />
        )}
      </section>
    </ClubShell>
  );
}
