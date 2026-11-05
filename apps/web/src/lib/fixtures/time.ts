/** Fixture start times: UTC instants shown and edited in an IANA timezone. */

export class LocalTimeError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "LocalTimeError";
  }
}

type Wall = {
  year: number;
  month: number;
  day: number;
  hour: number;
  minute: number;
};

const LOCAL_RE = /^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::\d{2}(?:\.\d+)?)?$/;

function pad(value: number): string {
  return String(value).padStart(2, "0");
}

function wallKey(wall: Wall): string {
  return `${wall.year}-${pad(wall.month)}-${pad(wall.day)}T${pad(wall.hour)}:${pad(wall.minute)}`;
}

function assertTimeZone(timeZone: string): void {
  try {
    new Intl.DateTimeFormat("en-US", { timeZone }).format(0);
  } catch {
    throw new LocalTimeError(`Unknown timezone ${timeZone}`);
  }
}

function wallFromInstant(ms: number, timeZone: string): Wall {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone,
    hourCycle: "h23",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).formatToParts(new Date(ms));
  const bag: Record<string, string> = {};
  for (const part of parts) {
    if (part.type !== "literal") bag[part.type] = part.value;
  }
  let hour = Number(bag.hour);
  if (hour === 24) hour = 0;
  return {
    year: Number(bag.year),
    month: Number(bag.month),
    day: Number(bag.day),
    hour,
    minute: Number(bag.minute),
  };
}

function offsetMs(utcMs: number, timeZone: string): number {
  const wall = wallFromInstant(utcMs, timeZone);
  const asUtc = Date.UTC(wall.year, wall.month - 1, wall.day, wall.hour, wall.minute);
  return asUtc - utcMs;
}

function parseLocal(local: string): Wall {
  const match = LOCAL_RE.exec(local.trim());
  if (!match) throw new LocalTimeError("Enter a date and time");
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const hour = Number(match[4]);
  const minute = Number(match[5]);
  if (hour > 23 || minute > 59) throw new LocalTimeError("Enter a valid date and time");
  const probe = new Date(Date.UTC(year, month - 1, day));
  if (
    probe.getUTCFullYear() !== year ||
    probe.getUTCMonth() !== month - 1 ||
    probe.getUTCDate() !== day
  ) {
    throw new LocalTimeError("Enter a real date and time");
  }
  return { year, month, day, hour, minute };
}

/** Parse a stored instant. A missing offset is UTC (SQLite responses omit it). */
export function parseStoredInstant(iso: string): number {
  const trimmed = iso.trim().replace(" ", "T");
  const match = /^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(\.\d+)?(Z|[+-]\d{2}:?\d{2})?$/i.exec(
    trimmed,
  );
  if (!match) throw new LocalTimeError("Invalid stored start time");
  const fraction = match[2] ? match[2].slice(0, 4) : "";
  const zone = match[3] ?? "Z";
  const ms = Date.parse(`${match[1]}${fraction}${zone}`);
  if (Number.isNaN(ms)) throw new LocalTimeError("Invalid stored start time");
  return ms;
}

/** `datetime-local` value for a stored UTC instant in the fixture timezone. */
export function isoToLocalDateTime(iso: string, timeZone: string): string {
  const ms = parseStoredInstant(iso);
  assertTimeZone(timeZone);
  return wallKey(wallFromInstant(ms, timeZone));
}

/**
 * Convert a `datetime-local` value in `timeZone` to a UTC ISO instant.
 * A spring-forward gap throws. A fall-back hour is ambiguous: the earlier
 * instant is used unless `preferredIso` is one of the real matches, which
 * keeps an existing fixture on its original side of the fold.
 */
export function localDateTimeToIso(
  local: string,
  timeZone: string,
  preferredIso?: string,
): string {
  const wall = parseLocal(local);
  assertTimeZone(timeZone);
  const key = wallKey(wall);
  const guess = Date.UTC(wall.year, wall.month - 1, wall.day, wall.hour, wall.minute);
  let utc = guess - offsetMs(guess, timeZone);
  utc = guess - offsetMs(utc, timeZone);

  const found = new Set<number>();
  for (let delta = -3 * 60; delta <= 3 * 60; delta += 15) {
    const ms = utc + delta * 60_000;
    if (wallKey(wallFromInstant(ms, timeZone)) === key) found.add(ms);
  }
  const matches = [...found].sort((a, b) => a - b);
  if (matches.length === 0) {
    throw new LocalTimeError(
      `${local} does not exist in ${timeZone} because clocks spring forward. Choose another time.`,
    );
  }
  if (preferredIso) {
    try {
      const preferred = parseStoredInstant(preferredIso);
      if (wallKey(wallFromInstant(preferred, timeZone)) === key) {
        return new Date(preferred).toISOString();
      }
    } catch (error) {
      if (!(error instanceof LocalTimeError)) throw error;
    }
  }
  return new Date(matches[0]).toISOString();
}

export function formatFixtureWhen(startsAt: string, timeZone: string): string {
  return new Intl.DateTimeFormat("en-US", {
    timeZone,
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(startsAt));
}
