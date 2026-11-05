import { localDateTimeToIso } from "./time";

export type FixtureFormFields = {
  season: string;
  competition: string;
  home_team_name: string;
  away_team_name: string;
  venue: string;
  starts_local: string;
  timezone: string;
  format_code: string;
  format_name: string;
  overs: string;
  status: string;
  result_summary: string;
  schedule_id: string;
};

export type FixtureTimeBaseline = {
  local: string;
  timezone: string;
  startsAt: string;
  scheduleId: string;
};

/** Body for create/update. Unchanged start time and schedule link are omitted. */
export function buildFixtureWriteBody(args: {
  editing: boolean;
  form: FixtureFormFields;
  formats: { code: string }[];
  baseline: FixtureTimeBaseline | null;
}): Record<string, unknown> {
  const { editing, form, formats, baseline } = args;
  const builtin = formats.some((item) => item.code === form.format_code);
  const body: Record<string, unknown> = {
    season: form.season,
    competition: form.competition,
    home_team_name: form.home_team_name,
    away_team_name: form.away_team_name,
    venue: form.venue,
    format_code: form.format_code,
    status: form.status,
    result_summary: form.result_summary.trim() ? form.result_summary.trim() : null,
  };
  if (!builtin) body.format_name = form.format_name;
  if (form.overs.trim()) body.overs = Number(form.overs);

  const timeUnchanged =
    editing &&
    baseline !== null &&
    form.starts_local === baseline.local &&
    form.timezone === baseline.timezone;
  if (!timeUnchanged) {
    if (!form.starts_local) throw new Error("Choose a match date and time.");
    const prefer =
      baseline && form.starts_local === baseline.local ? baseline.startsAt : undefined;
    body.starts_at = localDateTimeToIso(form.starts_local, form.timezone, prefer);
    body.timezone = form.timezone;
  }

  const scheduleUnchanged = editing && baseline !== null && form.schedule_id === baseline.scheduleId;
  if (!scheduleUnchanged) body.schedule_id = form.schedule_id || null;
  return body;
}
