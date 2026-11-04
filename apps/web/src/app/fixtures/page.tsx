import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { ClubShell } from "@/components/club-shell";
import { clubPageMetadata } from "@/lib/clubs/metadata";
import { getResolvedHost } from "@/lib/clubs/server";

export async function generateMetadata(): Promise<Metadata> {
  return clubPageMetadata("/fixtures", "Fixtures", "Public match schedule for this club.");
}

export default async function FixturesPage() {
  const resolved = await getResolvedHost();
  if (resolved.kind !== "club") notFound();

  return (
    <ClubShell club={resolved.club}>
      <section className="mx-auto max-w-5xl px-4 py-12">
        <h1 className="font-display text-4xl">Fixtures</h1>
        <p className="mt-3 opacity-80">
          Match schedule for {resolved.club.name}. Live data will load from the
          FastAPI org-scoped fixtures API.
        </p>
        <p className="mt-8 rounded border border-dashed border-black/20 bg-white/50 px-4 py-8 text-sm opacity-70">
          No fixtures seeded in this vertical slice yet.
        </p>
      </section>
    </ClubShell>
  );
}
