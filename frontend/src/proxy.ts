/* Next 16 calls this file "proxy"; it is the request gate, and unrelated to
 * the API proxy in app/api/[...path]/route.ts. */
import { NextResponse, type NextRequest } from "next/server";

import { accepts } from "@/lib/basic-auth";

const USER = process.env.DEMO_USER ?? "hr";
const PASSWORD = process.env.DEMO_PASSWORD ?? "";

export const config = {
  // The whole app, minus Next's own assets. A gate written as a list of
  // protected routes is a gate someone forgets to extend.
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};

export function proxy(request: NextRequest) {
  // Unset locally, so `npm run dev` asks for nothing. Set in the deployment,
  // where it is the only thing between a shared link and ten thousand
  // salaries.
  if (!PASSWORD) return NextResponse.next();

  // Whatever is watching the deployment has no credentials, and this tells it
  // only whether the service is up.
  if (request.nextUrl.pathname === "/api/health") return NextResponse.next();

  if (accepts(request.headers.get("authorization"), { user: USER, password: PASSWORD })) {
    return NextResponse.next();
  }

  return new NextResponse("Authentication required.", {
    status: 401,
    headers: {
      "WWW-Authenticate": 'Basic realm="ACME Salary Management", charset="UTF-8"',
      "Cache-Control": "no-store",
    },
  });
}
