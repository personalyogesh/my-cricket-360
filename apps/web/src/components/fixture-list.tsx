import Link from "next/link";
import type { ApiFixture } from "@/lib/api/client";
import { formatFixtureWhen } from "@/lib/fixtures/time";

export function FixtureList({
  fixtures,
  empty,
}: {
  fixtures: ApiFixture[];
  empty: string;
}) {
  if (fixtures.length === 0) {
    return (
      <p className="mt-8 rounded border border-dashed border-black/20 bg-white/50 px-4 py-8 text-sm opacity-70">
        {empty}
      </p>
    );
  }

  return (
    <ul className="mt-8 space-y-3">
      {fixtures.map((fixture) => (
        <li key={fixture.id}>
          <Link
            href={`/fixtures/${fixture.id}`}
            className="block rounded border border-black/10 bg-white/80 p-4 hover:border-[var(--club-primary)]"
          >
            <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="font-display text-xl sm:text-2xl">
                  {fixture.home_team_name} vs {fixture.away_team_name}
                </p>
                <p className="mt-1 text-sm opacity-70">
                  {fixture.competition} · {fixture.season} · {fixture.format_name}
                  {fixture.overs ? ` · ${fixture.overs} overs` : ""}
                </p>
              </div>
              <p className="text-sm sm:text-right">
                {formatFixtureWhen(fixture.starts_at, fixture.timezone)}
                <span className="mt-1 block text-xs uppercase tracking-wide opacity-60">
                  {fixture.status} · {fixture.venue}
                </span>
              </p>
            </div>
            {fixture.result_summary ? (
              <p className="mt-3 text-sm">{fixture.result_summary}</p>
            ) : null}
          </Link>
        </li>
      ))}
    </ul>
  );
}
