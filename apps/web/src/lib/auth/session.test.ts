import { describe, expect, it } from "vitest";
import { ACCESS_TOKEN_KEY, readAccessToken, writeAccessToken, type TokenStorage } from "./session";

function memoryStorage(): TokenStorage & { dump: () => Record<string, string> } {
  const data = new Map<string, string>();
  return {
    getItem: (key) => data.get(key) ?? null,
    setItem: (key, value) => {
      data.set(key, value);
    },
    removeItem: (key) => {
      data.delete(key);
    },
    dump: () => Object.fromEntries(data),
  };
}

describe("access token storage", () => {
  it("writes and reads a session token", () => {
    const storage = memoryStorage();
    writeAccessToken(storage, "abc.def.ghi");
    expect(readAccessToken(storage)).toBe("abc.def.ghi");
    expect(storage.dump()[ACCESS_TOKEN_KEY]).toBe("abc.def.ghi");
  });

  it("clears the token on logout", () => {
    const storage = memoryStorage();
    writeAccessToken(storage, "abc.def.ghi");
    writeAccessToken(storage, null);
    expect(readAccessToken(storage)).toBeNull();
    writeAccessToken(storage, "   ");
    expect(readAccessToken(storage)).toBeNull();
  });
});
