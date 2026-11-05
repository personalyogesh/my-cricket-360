import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { ClubShell } from "@/components/club-shell";
import { fetchPublicTeams } from "@/lib/api/client";
import { clubPageMetadata } from "@/lib/clubs/metadata";
import { getResolvedHost } from "@/lib/clubs/server";

export async function generateMetadata(): Promise<Metadata> {
  return clubPageMetadata("/teams", "Teams", "Public squads for this club only.");
}

export default async function TeamsPage() {
  const resolved = await getResolvedHost();
  if (resolved.kind !== "club") notFound();
  const { club } = resolved;

  let teams: Awaited<ReturnType<typeof fetchPublicTeams>> = [];
  let loadError: string | null = null;
  try {
    teams = await fetchPublicTeams(club.slug);
  } catch (err) {
    loadError = err instanceof Error ? err.message : "Failed to load teams";
  }

  return (
    <ClubShell club={club}>
      <section className="mx-auto max-w-5xl px-4 py-12">
        <h1 className="font-display text-4xl">Teams</h1>
        <p className="mt-3 max-w-2xl opacity-80">
          Public squads for {club.name}. Private teams and other clubs are not loaded on this host.
        </p>
        {loadError ? (
          <p className="mt-8 rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            Could not reach the API ({loadError}).
          </p>
        ) : null}
        {!loadError && teams.length === 0 ? (
          <p className="mt-8 rounded border border-dashed border-black/20 bg-white/50 px-4 py-8 text-sm opacity-70">
            No public teams yet for this club.
          </p>
        ) : null}
        <ul className="mt-8 space-y-3">
          {teams.map((team) => (
            <li key={team.id} className="rounded border border-black/10 bg-white/70 px-4 py-3">
              <h2 className="font-display text-2xl">{team.name}</h2>
              <p className="text-sm opacity-70">
                {[team.division, team.season].filter(Boolean).join(" · ") || "Squad"}
              </p>
            </li>
          ))}
        </ul>
      </section>
    </ClubShell>
  );
}
