import { notFound } from "next/navigation";
import { ClubShell } from "@/components/club-shell";
import { getResolvedHost } from "@/lib/clubs/server";

export default async function TeamsPage() {
  const resolved = await getResolvedHost();
  if (resolved.kind !== "club") notFound();

  return (
    <ClubShell club={resolved.club}>
      <section className="mx-auto max-w-5xl px-4 py-12">
        <h1 className="font-display text-4xl">Teams</h1>
        <p className="mt-3 opacity-80">
          Squads for {resolved.club.shortName}. Organization-scoped; other
          clubs&apos; rosters are never loaded on this host.
        </p>
      </section>
    </ClubShell>
  );
}
