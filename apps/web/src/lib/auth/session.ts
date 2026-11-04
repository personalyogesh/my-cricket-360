export const ACCESS_TOKEN_KEY = "mc360.access_token";

export type TokenStorage = {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
};

export function readAccessToken(storage: TokenStorage): string | null {
  const value = storage.getItem(ACCESS_TOKEN_KEY);
  if (!value) return null;
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

export function writeAccessToken(storage: TokenStorage, token: string | null): void {
  if (token && token.trim()) {
    storage.setItem(ACCESS_TOKEN_KEY, token.trim());
    return;
  }
  storage.removeItem(ACCESS_TOKEN_KEY);
}
