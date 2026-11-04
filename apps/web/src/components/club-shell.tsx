import type { ClubConfig } from "@/lib/clubs";
import Link from "next/link";

type ClubShellProps = {
  club: ClubConfig;
  children: React.ReactNode;
};

export function ClubShell({ club, children }: ClubShellProps) {
  const themeStyle = {
    ["--club-primary" as string]: club.theme.primary,
    ["--club-secondary" as string]: club.theme.secondary,
    ["--club-background" as string]: club.theme.background,
    ["--club-foreground" as string]: club.theme.foreground,
    ["--club-muted" as string]: club.theme.muted,
    ["--club-accent" as string]: club.theme.accent,
  };

  return (
    <div className="club-shell min-h-screen" style={themeStyle}>
      <header className="border-b border-black/10 bg-[var(--club-primary)] text-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-4">
          <Link href="/" className="font-display text-xl tracking-tight sm:text-2xl">
            {club.logoText}
          </Link>
          <nav className="flex flex-wrap items-center gap-3 text-sm text-white/90">
            <Link href="/fixtures" className="hover:text-white">
              Fixtures
            </Link>
            <Link href="/teams" className="hover:text-white">
              Teams
            </Link>
            <Link href="/sponsors" className="hover:text-white">
              Sponsors
            </Link>
            <Link href="/join" className="hover:text-white">
              Join
            </Link>
            <Link href="/admin" className="rounded bg-white/15 px-2 py-1 hover:bg-white/25">
              Admin
            </Link>
          </nav>
        </div>
      </header>
      <main>{children}</main>
      <footer className="mt-16 border-t border-black/10 bg-[var(--club-muted)]">
        <div className="mx-auto flex max-w-5xl flex-col gap-2 px-4 py-8 text-sm text-[var(--club-foreground)]">
          <p className="font-medium">{club.name}</p>
          <p className="opacity-80">
            Powered by My Cricket 360 · {club.primaryDomain}
          </p>
        </div>
      </footer>
    </div>
  );
}
