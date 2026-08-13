"use client";

import { usePathname } from "next/navigation";
import Header from "./Header";
import Footer from "./Footer";
import HelpChatWidget from "./HelpChatWidget";

export default function AppShell({
  children,
  siteGate,
}: {
  children: React.ReactNode;
  siteGate?: string | null;
}) {
  const pathname = usePathname();
  const isAdmin = pathname?.startsWith("/admin");
  // Coming-soon/maintenance must render standalone -- the proxy rewrites every other route to
  // one of these while the gate is on, so leaving Header/Footer/chat around them would let
  // visitors click straight through via nav links anyway, defeating the point of the gate.
  // This can't be detected via usePathname(): a rewrite is invisible to the browser's URL bar,
  // so on a rewritten request this hook still reports the original route (e.g. /talents), not
  // /coming-soon. siteGate comes from the root layout reading the x-site-gate request header
  // proxy.ts sets on rewrite, which reflects what's actually being rendered. The pathname check
  // still covers someone navigating to /coming-soon or /maintenance directly (no rewrite, so no
  // header, but the URL itself gives it away).
  const isGatePage = Boolean(siteGate) || pathname?.startsWith("/coming-soon") || pathname?.startsWith("/maintenance");

  if (isAdmin || isGatePage) {
    return <>{children}</>;
  }

  return (
    <>
      <Header />
      <div className="flex flex-1 flex-col">{children}</div>
      <Footer />
      <HelpChatWidget />
    </>
  );
}
