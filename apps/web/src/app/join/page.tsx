import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { ClubShell } from "@/components/club-shell";
import { RequestMembership } from "@/components/request-membership";
import { clubPageMetadata } from "@/lib/clubs/metadata";
import { getResolvedHost } from "@/lib/clubs/server";

export async function generateMetadata(): Promise<Metadata> {
  return clubPageMetadata(
    "/join",
    "Join",
    "Request membership in this club. Approval stays with that club's admins.",
  );
}

export default async function JoinPage() {
  const resolved = await getResolvedHost();
  if (resolved.kind !== "club") notFound();

  return (
    <ClubShell club={resolved.club}>
      <section className="mx-auto max-w-3xl px-4 py-12">
        <h1 className="font-display text-4xl">Join {resolved.club.name}</h1>
        <p className="mt-3 max-w-2xl opacity-80">
          One account can request Starks, Steelers, or both. This page only requests{" "}
          {resolved.club.shortName}, because the hostname selects the club.
        </p>
        <RequestMembership clubSlug={resolved.club.slug} clubName={resolved.club.name} />
      </section>
    </ClubShell>
  );
}
