import { notFound } from "next/navigation";
import { ClubShell } from "@/components/club-shell";
import { getResolvedHost } from "@/lib/clubs/server";

export default async function AdminPage() {
  const resolved = await getResolvedHost();
  if (resolved.kind !== "club") notFound();

  return (
    <ClubShell club={resolved.club}>
      <section className="mx-auto max-w-5xl px-4 py-12">
        <h1 className="font-display text-4xl">
          {resolved.club.shortName} admin
        </h1>
        <p className="mt-3 max-w-2xl opacity-80">
          Club-scoped dashboard for {resolved.club.name}. Authentication and
          org admin RBAC will gate this route; hostname alone is not sufficient
          authorization.
        </p>
        <ul className="mt-8 list-disc space-y-2 pl-5 text-sm">
          <li>Approve membership requests</li>
          <li>Manage fixtures, teams, announcements, gallery</li>
          <li>Upload and approve sponsor assets (priority)</li>
          <li>Review sponsor analytics</li>
        </ul>
        <p className="mt-6 text-sm opacity-70">
          Organization id:{" "}
          <code className="rounded bg-black/5 px-1">
            {resolved.club.organizationId}
          </code>
        </p>
      </section>
    </ClubShell>
  );
}
