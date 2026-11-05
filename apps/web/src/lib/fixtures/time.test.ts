import { describe, expect, it } from "vitest";
import { buildFixtureWriteBody, type FixtureFormFields } from "./form";
import { isoToLocalDateTime, localDateTimeToIso, LocalTimeError } from "./time";

const form = (overrides: Partial<FixtureFormFields> = {}): FixtureFormFields => ({
  season: "2026",
  competition: "Sunday League",
  home_team_name: "Starks",
  away_team_name: "Visitors",
  venue: "Ground",
  starts_local: "2026-06-14T14:00",
  timezone: "America/New_York",
  format_code: "t20",
  format_name: "T20",
  overs: "",
  status: "scheduled",
  result_summary: "",
  schedule_id: "",
  ...overrides,
});

describe("fixture timezone conversion", () => {
  it("round-trips an Eastern summer afternoon through UTC", () => {
    expect(localDateTimeToIso("2026-06-14T14:00", "America/New_York")).toBe(
      "2026-06-14T18:00:00.000Z",
    );
    expect(isoToLocalDateTime("2026-06-14T18:00:00.000Z", "America/New_York")).toBe(
      "2026-06-14T14:00",
    );
  });

  it("treats an offset-less stored instant as UTC", () => {
    expect(isoToLocalDateTime("2026-11-01T06:30:00", "America/New_York")).toBe(
      "2026-11-01T01:30",
    );
  });

  it("round-trips an Eastern winter afternoon, which is UTC-5", () => {
    expect(localDateTimeToIso("2026-01-14T14:00", "America/New_York")).toBe(
      "2026-01-14T19:00:00.000Z",
    );
    expect(isoToLocalDateTime("2026-01-14T19:00:00+00:00", "America/New_York")).toBe(
      "2026-01-14T14:00",
    );
  });

  it("rejects the spring-forward gap in America/New_York", () => {
    expect(() => localDateTimeToIso("2026-03-08T02:30", "America/New_York")).toThrow(
      /does not exist/,
    );
    expect(() => localDateTimeToIso("2026-03-08T02:30:00", "America/New_York")).toThrow(
      /does not exist/,
    );
  });

  it("keeps the later fall-back instant when that is the stored match time", () => {
    const earlier = localDateTimeToIso("2026-11-01T01:30", "America/New_York");
    const later = "2026-11-01T06:30:00.000Z";
    expect(earlier).toBe("2026-11-01T05:30:00.000Z");
    expect(isoToLocalDateTime(later, "America/New_York")).toBe("2026-11-01T01:30");
    expect(localDateTimeToIso("2026-11-01T01:30", "America/New_York", later)).toBe(later);
  });

  it("rejects a date that is not on the calendar", () => {
    expect(() => localDateTimeToIso("2026-02-31T12:00", "America/New_York")).toThrow(
      LocalTimeError,
    );
  });
});

describe("fixture edit body", () => {
  const baseline = {
    local: "2026-11-01T01:30",
    timezone: "America/New_York",
    startsAt: "2026-11-01T06:30:00.000Z",
    scheduleId: "sched-1",
  };

  it("omits the start time and schedule when only the result changes", () => {
    const body = buildFixtureWriteBody({
      editing: true,
      form: form({
        starts_local: baseline.local,
        timezone: baseline.timezone,
        schedule_id: baseline.scheduleId,
        result_summary: "Starks won by 4 wickets",
      }),
      formats: [{ code: "t20" }],
      baseline,
    });
    expect(body.starts_at).toBeUndefined();
    expect(body.timezone).toBeUndefined();
    expect(body.schedule_id).toBeUndefined();
    expect(body.result_summary).toBe("Starks won by 4 wickets");
  });

  it("sends a new UTC instant when the local start time changes", () => {
    const body = buildFixtureWriteBody({
      editing: true,
      form: form({
        starts_local: "2026-06-14T14:00",
        schedule_id: baseline.scheduleId,
      }),
      formats: [{ code: "t20" }],
      baseline,
    });
    expect(body.starts_at).toBe("2026-06-14T18:00:00.000Z");
    expect(body.timezone).toBe("America/New_York");
    expect(body.schedule_id).toBeUndefined();
  });

  it("includes the schedule link only when the editor changes it", () => {
    const body = buildFixtureWriteBody({
      editing: true,
      form: form({
        starts_local: baseline.local,
        timezone: baseline.timezone,
        schedule_id: "",
      }),
      formats: [{ code: "t20" }],
      baseline,
    });
    expect(body.starts_at).toBeUndefined();
    expect(body.schedule_id).toBeNull();
  });
});
