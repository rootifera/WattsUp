const TOKEN_KEY = "wattsup_access_token";

export const authToken = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

export async function apiFetch(
  path: string,
  init?: RequestInit,
): Promise<Response> {
  const token = authToken.get();
  const headers = new Headers(init?.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init?.body) headers.set("Content-Type", "application/json");

  const response = await fetch(path, { ...init, headers });
  if (response.status === 401 && token) {
    authToken.clear();
    window.dispatchEvent(new Event("wattsup:unauthorized"));
  }
  return response;
}
