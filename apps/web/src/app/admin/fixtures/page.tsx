import { notFound } from "next/navigation";
import { AdminFixturesPanel } from "@/components/admin-fixtures-panel";
import { ClubShell } from "@/components/club-shell";
import { getResolvedHost } from "@/lib/clubs/server";

export default async function AdminFixturesPage() {
  const resolved = await getResolvedHost();
  if (resolved.kind !== "club") notFound();

  return (
    <ClubShell club={resolved.club}>
      <section className="mx-auto max-w-5xl px-4 py-10 sm:py-12">
        <h1 className="font-display text-4xl">Fixtures</h1>
        <p className="mt-3 max-w-2xl opacity-80">
          Create and edit the {resolved.club.name} schedule. Drafts stay off the public
          site. Leave the result blank unless you are recording one the club already knows.
        </p>
        <div className="mt-8">
          <AdminFixturesPanel
            clubSlug={resolved.club.slug}
            clubName={resolved.club.name}
          />
        </div>
      </section>
    </ClubShell>
  );
}
