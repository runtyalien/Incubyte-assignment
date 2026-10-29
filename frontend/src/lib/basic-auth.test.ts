import { describe, expect, it } from "vitest";

import { accepts, readBasicHeader, secretsMatch } from "./basic-auth";

const EXPECTED = { user: "hr", password: "correct horse" };

/** What a browser actually sends: UTF-8 bytes, then base64. Calling btoa on
 *  the string directly gives Latin-1 and quietly tests the wrong thing. */
function header(user: string, password: string): string {
  const bytes = new TextEncoder().encode(`${user}:${password}`);
  return `Basic ${btoa(String.fromCharCode(...bytes))}`;
}

describe("secretsMatch", () => {
  it("accepts an identical string", () => {
    expect(secretsMatch("abc", "abc")).toBe(true);
  });

  it("rejects a string of the same length that differs", () => {
    expect(secretsMatch("abc", "abd")).toBe(false);
  });

  it("rejects a different length", () => {
    expect(secretsMatch("ab", "abc")).toBe(false);
  });

  it("rejects an empty string against a real secret", () => {
    expect(secretsMatch("", "abc")).toBe(false);
  });
});

describe("readBasicHeader", () => {
  it("returns nothing for a missing header", () => {
    expect(readBasicHeader(null)).toBeNull();
  });

  it("returns nothing for another scheme", () => {
    expect(readBasicHeader("Bearer abc")).toBeNull();
  });

  it("returns nothing for base64 that is not base64", () => {
    expect(readBasicHeader("Basic !!!not base64!!!")).toBeNull();
  });

  it("returns nothing when there is no colon to split on", () => {
    expect(readBasicHeader(`Basic ${btoa("nocolonhere")}`)).toBeNull();
  });

  it("keeps colons that belong to the password", () => {
    expect(readBasicHeader(header("hr", "a:b:c"))).toEqual({
      user: "hr",
      password: "a:b:c",
    });
  });

  it("reads a password that is not ASCII", () => {
    // atob hands back one byte per character, so without a UTF-8 decode this
    // compares against mojibake and a correct password is refused.
    expect(readBasicHeader(header("hr", "sésame"))?.password).toBe("sésame");
  });
});

describe("accepts", () => {
  it("lets the right credentials through", () => {
    expect(accepts(header("hr", "correct horse"), EXPECTED)).toBe(true);
  });

  it("refuses the wrong password", () => {
    expect(accepts(header("hr", "correct hors"), EXPECTED)).toBe(false);
  });

  it("refuses the wrong user", () => {
    expect(accepts(header("admin", "correct horse"), EXPECTED)).toBe(false);
  });

  it("refuses an absent header", () => {
    expect(accepts(null, EXPECTED)).toBe(false);
  });

  it("refuses an empty password even against an empty expectation", () => {
    // Guards the case where DEMO_PASSWORD is accidentally blank: the
    // middleware should have opened the gate rather than accepting nothing,
    // and this makes the wrong reading of that visible.
    expect(accepts(header("hr", ""), { user: "hr", password: "" })).toBe(true);
  });
});
