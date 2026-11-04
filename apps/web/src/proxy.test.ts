import { NextRequest } from "next/server";
import { describe, expect, it } from "vitest";
import { proxy } from "./proxy";

function requestFor(host: string) {
  return new NextRequest(`http://${host}/`, { headers: { host } });
}

function forwarded(response: Response, name: string) {
  return response.headers.get(`x-middleware-request-${name}`);
}

describe("proxy club headers", () => {
  it("maps a Starks host and leaves Steelers data off the request", async () => {
    const response = await proxy(requestFor("starks.localhost:43123"));
    expect(forwarded(response, "x-club-slug")).toBe("starks");
    expect(forwarded(response, "x-club-host")).toBe("starks.localhost");
    expect(forwarded(response, "x-organization-id")).toBeTruthy();
  });

  it("maps a Steelers host to the Steelers organization", async () => {
    const response = await proxy(requestFor("www.cgisteelerscricket.org"));
    expect(forwarded(response, "x-club-slug")).toBe("steelers");
    expect(forwarded(response, "x-club-host")).toBe("www.cgisteelerscricket.org");
  });

  it("does not attach a club on an unknown host", async () => {
    const response = await proxy(requestFor("evil.example"));
    expect(forwarded(response, "x-club-slug")).toBeNull();
    expect(forwarded(response, "x-organization-id")).toBeNull();
    expect(forwarded(response, "x-club-host")).toBe("evil.example");
  });

  it("keeps Starks and Steelers organization ids distinct", async () => {
    const starks = await proxy(requestFor("starksgroup.org"));
    const steelers = await proxy(requestFor("cgisteelerscricket.org"));
    expect(forwarded(starks, "x-organization-id")).not.toBe(
      forwarded(steelers, "x-organization-id"),
    );
  });
});
