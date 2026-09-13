/**
 * Minimal typed client helpers for talking to the TIDE backend.
 *
 * Phase 0: only the base-URL resolver and health call exist. Pure functions here
 * are unit-tested without a running backend (see `__tests__/api.test.ts`).
 */

export function apiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
}

/** Join the API base URL with a path, avoiding double slashes. */
export function apiUrl(path: string): string {
  const base = apiBaseUrl().replace(/\/+$/, "");
  const suffix = path.startsWith("/") ? path : `/${path}`;
  return `${base}${suffix}`;
}

export interface HealthResponse {
  status: string;
  env: string;
  version: string;
}

/** Fetch backend liveness. Requires a running backend at runtime. */
export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(apiUrl("/health"), { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`health check failed: ${res.status}`);
  }
  return (await res.json()) as HealthResponse;
}
