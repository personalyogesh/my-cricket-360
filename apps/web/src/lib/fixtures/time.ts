/** Interpret a datetime-local value in an IANA timezone and return UTC ISO. */
export function localDateTimeToIso(local: string, timeZone: string): string {
  const [datePart, timePart] = local.split("T");
  const [year, month, day] = datePart.split("-").map(Number);
  const [hour, minute] = timePart.split(":").map(Number);
  const utcGuess = new Date(Date.UTC(year, month - 1, day, hour, minute));
  const utcLabel = new Date(utcGuess.toLocaleString("en-US", { timeZone: "UTC" }));
  const zonedLabel = new Date(utcGuess.toLocaleString("en-US", { timeZone }));
  const offset = utcLabel.getTime() - zonedLabel.getTime();
  return new Date(utcGuess.getTime() + offset).toISOString();
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
