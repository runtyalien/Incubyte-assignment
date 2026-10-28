export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  let res: Response;

  // fetch only rejects on a network failure, so this is the "API is down" case
  // rather than anything the server said.
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
      cache: "no-store",
    });
  } catch {
    throw new ApiError(`Could not reach the API at ${API_BASE_URL}`);
  }

  if (!res.ok) {
    throw new ApiError(`${path} failed with ${res.status}`, res.status);
  }

  return (await res.json()) as T;
}

export type Health = {
  status: string;
  service: string;
  environment: string;
};

export const getHealth = () => apiFetch<Health>("/api/health");
