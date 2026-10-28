import { describe, expect, it } from "vitest";

import { toQuery, withParams, type Params } from "./search-params";

describe("URL-backed directory state", () => {
  it("passes the job-family and historical-date filters to the API", () => {
    const params: Params = {
      country: "IN",
      family: "Software",
      as_of: "2025-12-31",
    };

    expect(toQuery(params)).toMatchObject({
      country: ["IN"],
      family: ["Software"],
      as_of: "2025-12-31",
    });
  });

  it("keeps filters when changing the band position and resets the page", () => {
    const params: Params = {
      country: "IN",
      family: "Software",
      as_of: "2025-12-31",
      page: "4",
    };

    expect(withParams(params, { position: "below" })).toBe(
      "?country=IN&family=Software&as_of=2025-12-31&position=below",
    );
  });
});
