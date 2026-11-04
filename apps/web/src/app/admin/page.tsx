import Link from "next/link";
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
          Club-scoped dashboard for {resolved.club.name}. Authorization is
          enforced by the API using Supabase JWTs (or local dev tokens).
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            href="/admin/login"
            className="rounded bg-[var(--club-primary)] px-4 py-2.5 text-white"
          >
            Admin login
          </Link>
          <Link
            href="/admin/sponsors"
            className="rounded border border-[var(--club-primary)] px-4 py-2.5"
          >
            Manage sponsors
          </Link>
        </div>
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
