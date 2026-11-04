import type { ClubSponsorSeed } from "@/lib/clubs";
import Link from "next/link";

type SponsorStripProps = {
  sponsor: ClubSponsorSeed;
  clubName: string;
};

export function SponsorStrip({ sponsor, clubName }: SponsorStripProps) {
  return (
    <section
      aria-label="Founding sponsor"
      className="border-y border-black/10 bg-white/70"
    >
      <div className="mx-auto flex max-w-5xl flex-col gap-2 px-4 py-6 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-[var(--club-secondary)]">
            Founding sponsor
          </p>
          <p className="font-display text-xl text-[var(--club-foreground)]">
            {sponsor.name}
          </p>
          <p className="text-sm text-[var(--club-foreground)]/80">
            {sponsor.tagline} · supporting {clubName}
          </p>
        </div>
        <div className="flex gap-3 text-sm">
          <Link
            href={`/sponsors/${sponsor.slug}`}
            className="rounded bg-[var(--club-primary)] px-3 py-2 text-white"
          >
            Sponsor page
          </Link>
          <a
            href={sponsor.websiteUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded border border-[var(--club-primary)] px-3 py-2 text-[var(--club-primary)]"
          >
            Visit website
          </a>
        </div>
      </div>
    </section>
  );
}
