/** The demo gate's credential check.
 *
 *  Kept out of the middleware so it can be tested without constructing a
 *  request, and because the comparison is the part worth getting right.
 */

export type Credentials = { user: string; password: string };

/** Constant-time comparison.
 *
 *  Neither Node's `timingSafeEqual` nor Web Crypto is available in the edge
 *  runtime the middleware runs in, so this is the loop, written so it cannot
 *  return early. Length is compared first and deliberately: how long the
 *  password is was never the secret.
 */
export function secretsMatch(offered: string, expected: string): boolean {
  const a = new TextEncoder().encode(offered);
  const b = new TextEncoder().encode(expected);
  if (a.length !== b.length) return false;

  let difference = 0;
  for (let i = 0; i < a.length; i += 1) difference |= a[i] ^ b[i];
  return difference === 0;
}

/** Decodes `Authorization: Basic ...`, or null for anything malformed — which
 *  the caller treats exactly as it treats a missing header. */
export function readBasicHeader(header: string | null): Credentials | null {
  if (!header) return null;

  const [scheme, encoded] = header.split(" ");
  if (scheme?.toLowerCase() !== "basic" || !encoded) return null;

  let decoded: string;
  try {
    // atob yields one byte per character, so the bytes go back through a UTF-8
    // decoder; otherwise a non-ASCII password compares against mojibake.
    const bytes = Uint8Array.from(atob(encoded), (char) => char.charCodeAt(0));
    decoded = new TextDecoder().decode(bytes);
  } catch {
    return null;
  }

  // A password may contain colons. A username may not, so the first one wins.
  const separator = decoded.indexOf(":");
  if (separator === -1) return null;

  return {
    user: decoded.slice(0, separator),
    password: decoded.slice(separator + 1),
  };
}

export function accepts(
  header: string | null,
  expected: Credentials,
): boolean {
  const offered = readBasicHeader(header);
  if (!offered) return false;

  // Both run before either is consulted, so a wrong username costs the same
  // as a wrong password.
  const user = secretsMatch(offered.user, expected.user);
  const password = secretsMatch(offered.password, expected.password);

  return user && password;
}
