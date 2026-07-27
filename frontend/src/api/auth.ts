import { apiFetch } from "./client";

interface TokenResponse {
  access_token: string;
  expires_at: string;
}

export async function login(
  username: string,
  password: string,
): Promise<TokenResponse> {
  const response = await apiFetch("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) {
    throw new Error(
      response.status === 401 ? "Invalid username or password" : "Login failed",
    );
  }
  return response.json() as Promise<TokenResponse>;
}
