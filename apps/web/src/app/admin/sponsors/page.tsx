import { notFound } from "next/navigation";
import { ClubShell } from "@/components/club-shell";
import { AdminSponsorsPanel } from "@/components/admin-sponsors-panel";
import { getResolvedHost } from "@/lib/clubs/server";

export default async function AdminSponsorsPage() {
  const resolved = await getResolvedHost();
  if (resolved.kind !== "club") notFound();

  return (
    <ClubShell club={resolved.club}>
      <section className="mx-auto max-w-5xl px-4 py-12">
        <h1 className="font-display text-4xl">Sponsor management</h1>
        <p className="mt-3 max-w-2xl opacity-80">
          Draft → approve → publish for {resolved.club.name}. Cross-club edits
          are rejected by the API.
        </p>
        <div className="mt-8">
          <AdminSponsorsPanel
            clubSlug={resolved.club.slug}
            clubName={resolved.club.name}
          />
        </div>
      </section>
    </ClubShell>
  );
}
