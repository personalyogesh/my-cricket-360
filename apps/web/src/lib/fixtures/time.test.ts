import { describe, expect, it } from "vitest";
import { formatFixtureWhen, localDateTimeToIso } from "./time";

describe("fixture times", () => {
  it("converts an Eastern afternoon to the matching UTC instant", () => {
    expect(localDateTimeToIso("2026-06-14T14:00", "America/New_York")).toBe(
      "2026-06-14T18:00:00.000Z",
    );
  });

  it("formats the kickoff in the fixture timezone", () => {
    const label = formatFixtureWhen("2026-06-14T18:00:00.000Z", "America/New_York");
    expect(label).toContain("2026");
    expect(label).toContain("2:00");
  });
});