import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { AdminMembershipsPanel } from "@/components/admin-memberships-panel";
import { ClubShell } from "@/components/club-shell";
import { clubPageMetadata } from "@/lib/clubs/metadata";
import { getResolvedHost } from "@/lib/clubs/server";

export async function generateMetadata(): Promise<Metadata> {
  return clubPageMetadata(
    "/admin/memberships",
    "Memberships",
    "Club-scoped membership approval. Requests for other clubs are not listed here.",
  );
}

export default async function AdminMembershipsPage() {
  const resolved = await getResolvedHost();
  if (resolved.kind !== "club") notFound();

  return (
    <ClubShell club={resolved.club}>
      <section className="mx-auto max-w-5xl px-4 py-12">
        <h1 className="font-display text-4xl">Memberships</h1>
        <p className="mt-3 max-w-2xl opacity-80">
          Approve, reject, or suspend requests for {resolved.club.name}. You cannot
          decide your own membership, and Steelers decisions are rejected on the Starks site.
        </p>
        <div className="mt-8">
          <AdminMembershipsPanel clubSlug={resolved.club.slug} clubName={resolved.club.name} />
        </div>
      </section>
    </ClubShell>
  );
}
