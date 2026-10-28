/** Filter state lives in the URL, not in React.
 *
 *  It makes a filtered view shareable, the back button work, and every page a
 *  server render with no client-side store to keep in sync.
 */

import type { DirectoryQuery } from "./api";

export type Params = Record<string, string | string[] | undefined>;

export function one(params: Params, key: string): string | undefined {
  const value = params[key];
  return Array.isArray(value) ? value[0] : value;
}

export function many(params: Params, key: string): string[] {
  const value = params[key];
  if (value === undefined) return [];
  return Array.isArray(value) ? value : [value];
}

export function pageNumber(params: Params): number {
  const raw = Number(one(params, "page"));
  return Number.isInteger(raw) && raw > 0 ? raw : 1;
}

export function toQuery(params: Params): DirectoryQuery {
  return {
    q: one(params, "q"),
    country: many(params, "country"),
    department: many(params, "department"),
    family: many(params, "family"),
    level: many(params, "level"),
    position: one(params, "position"),
    status: one(params, "status"),
    as_of: one(params, "as_of"),
  };
}

/** A new querystring with some keys replaced. Anything set to undefined is
 *  dropped, and changing a filter sends you back to page one — staying on
 *  page 12 of a result set that now has three pages shows nothing. */
export function withParams(params: Params, changes: Params): string {
  const search = new URLSearchParams();

  for (const [key, value] of Object.entries({ ...params, ...changes })) {
    if (value === undefined || value === "") continue;
    if (Array.isArray(value)) value.forEach((v) => search.append(key, v));
    else search.set(key, value);
  }

  if (!("page" in changes)) search.delete("page");

  const rendered = search.toString();
  return rendered ? `?${rendered}` : "";
}
