import { NextResponse, type NextRequest } from "next/server";

const API_URL = process.env.API_URL ?? "http://localhost:8000";
const API_KEY = process.env.API_KEY ?? "";

/** The browser's only way to the API.
 *
 *  This was a next.config rewrite, which is a pure proxy and cannot add a
 *  header. The API key has to be attached somewhere the browser cannot read
 *  it, and this is that place: it runs on the server, and what it sends
 *  upstream is not what the browser handed it.
 */
async function forward(request: NextRequest, path: string[]) {
  const target = new URL(`/api/${path.join("/")}`, API_URL);
  target.search = request.nextUrl.search;

  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  if (API_KEY) headers.set("x-api-key", API_KEY);
  // The caller's own Authorization header belongs to the demo gate, which the
  // middleware has already checked. It means nothing upstream, so it stops here.

  const carriesBody = request.method !== "GET" && request.method !== "HEAD";

  let upstream: Response;
  try {
    upstream = await fetch(target, {
      method: request.method,
      headers,
      body: carriesBody ? await request.text() : undefined,
      cache: "no-store",
    });
  } catch {
    return NextResponse.json({ detail: "Could not reach the API." }, { status: 502 });
  }

  return new NextResponse(await upstream.text(), {
    status: upstream.status,
    headers: {
      "content-type": upstream.headers.get("content-type") ?? "application/json",
      "cache-control": "no-store",
    },
  });
}

type Context = { params: Promise<{ path: string[] }> };

export async function GET(request: NextRequest, context: Context) {
  return forward(request, (await context.params).path);
}

export async function POST(request: NextRequest, context: Context) {
  return forward(request, (await context.params).path);
}
