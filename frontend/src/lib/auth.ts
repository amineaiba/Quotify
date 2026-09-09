import { api } from "./api";

export type Business = {
  id: string;
  email: string;
  name: string;
};

export type TokenPair = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export const authApi = {
  register: (fields: { email: string; password: string; name: string }) =>
    api.post<Business>("/api/v1/auth/register", fields),
  login: (email: string, password: string) =>
    api.postForm<TokenPair>("/api/v1/auth/jwt/login", { username: email, password }),
  refresh: (refreshToken: string) =>
    api.post<TokenPair>("/api/v1/auth/jwt/refresh", { refresh_token: refreshToken }),
  logout: (refreshToken: string) =>
    api.post<void>("/api/v1/auth/jwt/logout", { refresh_token: refreshToken }),
};

/** Backend error `detail` codes we show a specific message for. */
export const AUTH_ERROR_MESSAGES: Record<string, string> = {
  LOGIN_BAD_CREDENTIALS: "Wrong email or password.",
  REGISTER_USER_ALREADY_EXISTS: "An account already exists for this email.",
};
