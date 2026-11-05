"use client";

import { useState } from "react";
import Link from "next/link";
import {
  createFixture,
  createSchedule,
  fetchAdminFixtures,
  fetchAdminSchedules,
  fetchFixtureFormats,
  updateFixture,
  type ApiFixture,
  type ApiFormat,
  type ApiSchedule,
} from "@/lib/api/client";
import { readAccessToken } from "@/lib/auth/session";
import { buildFixtureWriteBody, type FixtureTimeBaseline } from "@/lib/fixtures/form";
import { isoToLocalDateTime } from "@/lib/fixtures/time";

const STATUSES = ["draft", "scheduled", "postponed", "cancelled", "live", "completed"] as const;

type Props = { clubSlug: string; clubName: string };

function readStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return readAccessToken(window.localStorage);
}

const emptyForm = {
  season: "2026",
  competition: "",
  home_team_name: "",
  away_team_name: "",
  venue: "",
  starts_local: "",
  timezone: "America/New_York",
  format_code: "t20",
  format_name: "",
  overs: "",
  status: "scheduled",
  result_summary: "",
  schedule_id: "",
};

export function AdminFixturesPanel({ clubSlug, clubName }: Props) {
  const [token] = useState<string | null>(() => readStoredToken());
  const [fixtures, setFixtures] = useState<ApiFixture[]>([]);
  const [schedules, setSchedules] = useState<ApiSchedule[]>([]);
  const [formats, setFormats] = useState<ApiFormat[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState<string | null>(null);
  const [baseline, setBaseline] = useState<FixtureTimeBaseline | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [scheduleName, setScheduleName] = useState("");
  const [scheduleSeason, setScheduleSeason] = useState("2026");
  const [scheduleCompetition, setScheduleCompetition] = useState("");

  async function load() {
    if (!token) return;
    setBusy(true);
    setError(null);
    try {
      const [fixturePage, schedulePage, catalog] = await Promise.all([
        fetchAdminFixtures(clubSlug, token),
        fetchAdminSchedules(clubSlug, token),
        fetchFixtureFormats(),
      ]);
      setFixtures(fixturePage.items);
      setSchedules(schedulePage.items);
      setFormats(catalog);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load fixtures");
    } finally {
      setBusy(false);
    }
  }

  function payload() {
    return buildFixtureWriteBody({
      editing: Boolean(editing),
      form,
      formats,
      baseline,
    });
  }

  async function saveFixture(event: React.FormEvent) {
    event.preventDefault();
    if (!token) return;
    if (!form.starts_local && !editing) {
      setError("Choose a match date and time.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      if (editing) {
        await updateFixture(clubSlug, editing, token, payload());
      } else {
        await createFixture(clubSlug, token, payload());
      }
      setEditing(null);
      setBaseline(null);
      setForm(emptyForm);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
      setBusy(false);
    }
  }

  async function saveSchedule(event: React.FormEvent) {
    event.preventDefault();
    if (!token) return;
    setBusy(true);
    setError(null);
    try {
      await createSchedule(clubSlug, token, {
        name: scheduleName,
        season: scheduleSeason,
        competition: scheduleCompetition,
        format_code: form.format_code,
        format_name: form.format_name || undefined,
        timezone: form.timezone,
        status: "published",
        overs: form.overs.trim() ? Number(form.overs) : undefined,
      });
      setScheduleName("");
      setScheduleCompetition("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Schedule save failed");
      setBusy(false);
    }
  }

  if (!token) {
    return (
      <p className="text-sm">
        <Link href="/admin/login" className="underline">
          Sign in
        </Link>{" "}
        to manage {clubName} fixtures.
      </p>
    );
  }

  return (
    <div className="space-y-8">
      <button
        type="button"
        onClick={() => void load()}
        disabled={busy}
        className="rounded bg-[var(--club-primary)] px-3 py-2 text-sm text-white disabled:opacity-60"
      >
        {busy ? "Working…" : "Load fixtures"}
      </button>
      {error ? <p className="text-sm text-red-700">{error}</p> : null}

      <form onSubmit={(event) => void saveSchedule(event)} className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <h2 className="font-display text-2xl sm:col-span-2">Publish a schedule</h2>
        <input
          required
          value={scheduleName}
          onChange={(event) => setScheduleName(event.target.value)}
          placeholder="Schedule name"
          className="rounded border border-black/15 px-3 py-2"
        />
        <input
          required
          value={scheduleCompetition}
          onChange={(event) => setScheduleCompetition(event.target.value)}
          placeholder="Competition"
          className="rounded border border-black/15 px-3 py-2"
        />
        <input
          required
          value={scheduleSeason}
          onChange={(event) => setScheduleSeason(event.target.value)}
          placeholder="Season"
          className="rounded border border-black/15 px-3 py-2"
        />
        <button type="submit" disabled={busy} className="rounded border border-[var(--club-primary)] px-3 py-2 text-sm">
          Save schedule
        </button>
      </form>

      <form onSubmit={(event) => void saveFixture(event)} className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <h2 className="font-display text-2xl sm:col-span-2">
          {editing ? "Edit fixture" : "Add fixture"}
        </h2>
        <input
          required
          value={form.competition}
          onChange={(event) => setForm({ ...form, competition: event.target.value })}
          placeholder="Competition"
          className="rounded border border-black/15 px-3 py-2"
        />
        <input
          required
          value={form.season}
          onChange={(event) => setForm({ ...form, season: event.target.value })}
          placeholder="Season"
          className="rounded border border-black/15 px-3 py-2"
        />
        <input
          required
          value={form.home_team_name}
          onChange={(event) => setForm({ ...form, home_team_name: event.target.value })}
          placeholder="Home side"
          className="rounded border border-black/15 px-3 py-2"
        />
        <input
          required
          value={form.away_team_name}
          onChange={(event) => setForm({ ...form, away_team_name: event.target.value })}
          placeholder="Away side or opponent"
          className="rounded border border-black/15 px-3 py-2"
        />
        <input
          required
          value={form.venue}
          onChange={(event) => setForm({ ...form, venue: event.target.value })}
          placeholder="Venue"
          className="rounded border border-black/15 px-3 py-2"
        />
        <input
          required={!editing}
          type="datetime-local"
          value={form.starts_local}
          onChange={(event) => setForm({ ...form, starts_local: event.target.value })}
          className="rounded border border-black/15 px-3 py-2"
        />
        <label className="text-sm">
          Timezone
          <input
            required
            value={form.timezone}
            onChange={(event) => setForm({ ...form, timezone: event.target.value })}
            className="mt-1 w-full rounded border border-black/15 px-3 py-2"
          />
        </label>
        <label className="text-sm">
          Format
          <select
            value={form.format_code}
            onChange={(event) => setForm({ ...form, format_code: event.target.value })}
            className="mt-1 w-full rounded border border-black/15 px-3 py-2"
          >
            {formats.map((item) => (
              <option key={item.code} value={item.code}>
                {item.name}
                {item.overs ? ` (${item.overs})` : ""}
              </option>
            ))}
            <option value="custom">Custom code…</option>
          </select>
        </label>
        {form.format_code === "custom" || !formats.some((item) => item.code === form.format_code) ? (
          <>
            <input
              required
              value={form.format_code === "custom" ? "" : form.format_code}
              onChange={(event) => setForm({ ...form, format_code: event.target.value.toLowerCase() })}
              placeholder="Format code, e.g. club_cup"
              className="rounded border border-black/15 px-3 py-2"
            />
            <input
              required
              value={form.format_name}
              onChange={(event) => setForm({ ...form, format_name: event.target.value })}
              placeholder="Format name"
              className="rounded border border-black/15 px-3 py-2"
            />
          </>
        ) : null}
        <input
          value={form.overs}
          onChange={(event) => setForm({ ...form, overs: event.target.value })}
          placeholder="Overs (blank uses the format default)"
          inputMode="numeric"
          className="rounded border border-black/15 px-3 py-2"
        />
        <select
          value={form.status}
          onChange={(event) => setForm({ ...form, status: event.target.value })}
          className="rounded border border-black/15 px-3 py-2"
        >
          {STATUSES.map((status) => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </select>
        <select
          value={form.schedule_id}
          onChange={(event) => setForm({ ...form, schedule_id: event.target.value })}
          className="rounded border border-black/15 px-3 py-2"
        >
          <option value="">No schedule</option>
          {schedules.map((schedule) => (
            <option key={schedule.id} value={schedule.id}>
              {schedule.name} ({schedule.status})
            </option>
          ))}
        </select>
        <input
          value={form.result_summary}
          onChange={(event) => setForm({ ...form, result_summary: event.target.value })}
          placeholder="Result, only if you know it"
          className="rounded border border-black/15 px-3 py-2 sm:col-span-2"
        />
        <button
          type="submit"
          disabled={busy}
          className="rounded bg-[var(--club-primary)] px-3 py-2 text-sm text-white disabled:opacity-60"
        >
          {editing ? "Update fixture" : "Create fixture"}
        </button>
      </form>

      <ul className="space-y-3">
        {fixtures.map((fixture) => (
          <li key={fixture.id} className="rounded border border-black/10 bg-white/80 p-4 text-sm">
            <p className="font-medium">
              {fixture.home_team_name} vs {fixture.away_team_name}
            </p>
            <p className="opacity-70">
              {fixture.format_name} · {fixture.status} · {fixture.starts_at}
            </p>
            <p>{fixture.result_summary ?? "No result entered"}</p>
            <button
              type="button"
              className="mt-2 underline"
              onClick={() => {
                let local: string;
                try {
                  local = isoToLocalDateTime(fixture.starts_at, fixture.timezone);
                } catch (err) {
                  setError(err instanceof Error ? err.message : "Could not read this start time");
                  return;
                }
                setEditing(fixture.id);
                setBaseline({
                  local,
                  timezone: fixture.timezone,
                  startsAt: fixture.starts_at,
                  scheduleId: fixture.schedule_id ?? "",
                });
                setForm({
                  ...emptyForm,
                  season: fixture.season,
                  competition: fixture.competition,
                  home_team_name: fixture.home_team_name,
                  away_team_name: fixture.away_team_name,
                  venue: fixture.venue,
                  timezone: fixture.timezone,
                  format_code: fixture.format_code,
                  format_name: fixture.format_name,
                  overs: fixture.overs ? String(fixture.overs) : "",
                  status: fixture.status,
                  result_summary: fixture.result_summary ?? "",
                  schedule_id: fixture.schedule_id ?? "",
                  starts_local: local,
                });
              }}
            >
              Edit
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
