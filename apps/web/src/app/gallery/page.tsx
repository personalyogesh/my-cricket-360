import { notFound } from "next/navigation";
import { ClubShell } from "@/components/club-shell";
import { getResolvedHost } from "@/lib/clubs/server";

export default async function GalleryPage() {
  const resolved = await getResolvedHost();
  if (resolved.kind !== "club") notFound();

  return (
    <ClubShell club={resolved.club}>
      <section className="mx-auto max-w-5xl px-4 py-12">
        <h1 className="font-display text-4xl">Gallery</h1>
        <p className="mt-3 opacity-80">
          Media for {resolved.club.name} stored under this organization&apos;s
          prefix only.
        </p>
      </section>
    </ClubShell>
  );
}
