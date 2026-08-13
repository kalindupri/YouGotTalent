import { NextRequest, NextResponse } from "next/server";

// Site-wide gates, controlled by env vars on the Container App (see .github/workflows/
// toggle-coming-soon.yml and toggle-maintenance.yml) -- flipping either is instant (a new
// revision with the changed env var, no rebuild/redeploy needed) since this reads
// process.env at request time, not at build time like NEXT_PUBLIC_* vars.
// Maintenance takes priority over coming-soon if both are ever left on at once.
export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  if (pathname.startsWith("/maintenance") || pathname.startsWith("/coming-soon")) {
    return NextResponse.next();
  }

  // A rewrite is invisible to the browser's URL bar, so a client component like AppShell
  // can't tell it's rendering the gate page just by reading usePathname() -- it would still
  // see the original route (e.g. /talents) and wrap the gate page in the full site chrome.
  // Passing the gate as a request header lets the (server-rendered) root layout read the
  // real answer via headers() and pass it down as a prop instead.
  if (process.env.MAINTENANCE_MODE === "true") {
    const requestHeaders = new Headers(request.headers);
    requestHeaders.set("x-site-gate", "maintenance");
    return NextResponse.rewrite(new URL("/maintenance", request.url), { request: { headers: requestHeaders } });
  }
  if (process.env.COMING_SOON_MODE === "true") {
    const requestHeaders = new Headers(request.headers);
    requestHeaders.set("x-site-gate", "coming-soon");
    return NextResponse.rewrite(new URL("/coming-soon", request.url), { request: { headers: requestHeaders } });
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
