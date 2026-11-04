import { describe, expect, it } from "vitest";
import {
  HOST_ALLOWLIST,
  canonicalOrigin,
  normalizeHost,
  resolveClubFromHost,
} from "./index";

describe("normalizeHost", () => {
  it("lowercases and strips port", () => {
    expect(normalizeHost("WWW.StarksGroup.org:443")).toBe("www.starksgroup.org");
    expect(normalizeHost("starks.localhost:43123")).toBe("starks.localhost");
  });

  it("rejects empty and unsafe values", () => {
    expect(normalizeHost(null)).toBe("");
    expect(normalizeHost(undefined)).toBe("");
    expect(normalizeHost("")).toBe("");
    expect(normalizeHost("evil.com/path")).toBe("");
    expect(normalizeHost("host name")).toBe("");
  });
});

describe("resolveClubFromHost — founding production hosts", () => {
  it("maps Starks apex and www to the same club", () => {
    const apex = resolveClubFromHost("starksgroup.org");
    const www = resolveClubFromHost("www.starksgroup.org");

    expect(apex.kind).toBe("club");
    expect(www.kind).toBe("club");
    if (apex.kind === "club" && www.kind === "club") {
      expect(apex.club.slug).toBe("starks");
      expect(www.club.slug).toBe("starks");
      expect(apex.club.organizationId).toBe(www.club.organizationId);
      expect(apex.isWww).toBe(false);
      expect(www.isWww).toBe(true);
      expect(apex.club.initialSponsor.name).toBe("Hashtag India Cary");
    }
  });

  it("maps Steelers apex and www to the same club", () => {
    const apex = resolveClubFromHost("cgisteelerscricket.org");
    const www = resolveClubFromHost("WWW.cgisteelerscricket.org:443");

    expect(apex.kind).toBe("club");
    expect(www.kind).toBe("club");
    if (apex.kind === "club" && www.kind === "club") {
      expect(apex.club.slug).toBe("steelers");
      expect(www.club.slug).toBe("steelers");
      expect(apex.club.initialSponsor.name).toBe("CGI");
    }
  });
});

describe("resolveClubFromHost — local hosts", () => {
  it("resolves starks.localhost and steelers.localhost", () => {
    const starks = resolveClubFromHost("starks.localhost:43123");
    const steelers = resolveClubFromHost("steelers.localhost");

    expect(starks.kind).toBe("club");
    expect(steelers.kind).toBe("club");
    if (starks.kind === "club" && steelers.kind === "club") {
      expect(starks.club.slug).toBe("starks");
      expect(steelers.club.slug).toBe("steelers");
      expect(starks.club.organizationId).not.toBe(
        steelers.club.organizationId,
      );
    }
  });
});

describe("resolveClubFromHost — platform and unknown", () => {
  it("treats localhost as platform chooser, not a club", () => {
    const resolved = resolveClubFromHost("localhost:43123");
    expect(resolved.kind).toBe("platform");
    if (resolved.kind === "platform") {
      expect(resolved.platform.name).toBe("My Cricket 360");
    }
  });

  it("never maps unknown hosts to a club (no Host-header trust)", () => {
    const spoofed = [
      "evil.starksgroup.org",
      "starksgroup.org.evil.com",
      "not-a-club.example",
      "cgi.com",
      "",
    ];

    for (const host of spoofed) {
      const resolved = resolveClubFromHost(host);
      expect(resolved.kind).not.toBe("club");
    }
  });

  it("does not allow arbitrary Host to select organizationId", () => {
    // Attacker-controlled Host must not yield Starks or Steelers config.
    const resolved = resolveClubFromHost("00000000-0000-4000-8000-000000000001");
    expect(resolved.kind).toBe("unknown");
  });
});

describe("allowlist integrity", () => {
  it("includes apex and www for both founding clubs", () => {
    expect(HOST_ALLOWLIST.get("starksgroup.org")).toBe("starks");
    expect(HOST_ALLOWLIST.get("www.starksgroup.org")).toBe("starks");
    expect(HOST_ALLOWLIST.get("cgisteelerscricket.org")).toBe("steelers");
    expect(HOST_ALLOWLIST.get("www.cgisteelerscricket.org")).toBe("steelers");
  });
});

describe("canonicalOrigin", () => {
  it("uses https primary domain for production club hosts", () => {
    const www = resolveClubFromHost("www.starksgroup.org");
    expect(canonicalOrigin(www)).toBe("https://starksgroup.org");

    const steelers = resolveClubFromHost("cgisteelerscricket.org");
    expect(canonicalOrigin(steelers)).toBe("https://cgisteelerscricket.org");
  });

  it("keeps local http origin for *.localhost clubs", () => {
    const local = resolveClubFromHost("starks.localhost");
    expect(canonicalOrigin(local)).toBe("http://starks.localhost");
  });
});
