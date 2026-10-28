import type {
  Distribution,
  EmployeeDetail,
  EmployeeSummary,
  Overview,
  Page,
  PayChangeResult,
  PayReason,
  Reference,
} from "./types";

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
    throw new ApiError(await describe(res), res.status);
  }

  return (await res.json()) as T;
}

/** FastAPI puts a string in `detail` for our own refusals and a list of field
 *  errors there for schema failures. Both are worth showing. */
async function describe(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
    if (Array.isArray(body?.detail)) {
      return body.detail
        .map((item: { loc?: string[]; msg?: string }) => {
          const field = item.loc?.at(-1);
          return field ? `${field}: ${item.msg}` : item.msg;
        })
        .join("; ");
    }
  } catch {
    // Fall through to the status line.
  }
  return `Request failed with ${res.status}`;
}

function query(params: Record<string, unknown>): string {
  const search = new URLSearchParams();

  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    if (Array.isArray(value)) {
      value.forEach((item) => search.append(key, String(item)));
    } else {
      search.set(key, String(value));
    }
  }

  const rendered = search.toString();
  return rendered ? `?${rendered}` : "";
}

export type DirectoryQuery = {
  q?: string;
  country?: string[];
  department?: string[];
  family?: string[];
  level?: string[];
  position?: string;
  status?: string;
  sort?: string;
  order?: string;
  page?: number;
  page_size?: number;
};

export function listEmployees(params: DirectoryQuery) {
  return apiFetch<Page<EmployeeSummary>>(`/api/employees${query(params)}`);
}

export function getReference() {
  return apiFetch<Reference>("/api/reference");
}

export function getEmployee(id: number) {
  return apiFetch<EmployeeDetail>(`/api/employees/${id}`);
}

export function getOverview(params: DirectoryQuery = {}) {
  return apiFetch<Overview>(`/api/analytics/overview${query(params)}`);
}

export function getDistribution(
  by: string,
  params: DirectoryQuery & { local?: boolean } = {},
) {
  return apiFetch<Distribution>(
    `/api/analytics/distribution${query({ by, ...params })}`,
  );
}

export type NewPayChange = {
  effective_from: string;
  amount: string;
  reason: PayReason;
  note?: string;
};

export function recordPayChange(id: number, change: NewPayChange) {
  return apiFetch<PayChangeResult>(`/api/employees/${id}/compensation`, {
    method: "POST",
    body: JSON.stringify(change),
  });
}
