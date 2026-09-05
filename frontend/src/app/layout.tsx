import type { Metadata } from "next";
import { headers } from "next/headers";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";
import AppShell from "@/components/AppShell";

// One family for headings and body. Geist was loaded but never referenced -- `body` in
// globals.css set Arial, so every screen actually rendered in Arial while two Geist faces
// downloaded unused.
const jakarta = Plus_Jakarta_Sans({
  variable: "--font-jakarta",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
});

export const metadata: Metadata = {
  title: "YouGotTalent",
  description: "Sri Lanka's talent marketplace for models, actors, and creative professionals",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // Set by proxy.ts on rewrite -- see the comment there for why this can't be read from
  // usePathname() in AppShell instead.
  const siteGate = (await headers()).get("x-site-gate");

  return (
    <html
      lang="en"
      className={`${jakarta.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <AuthProvider>
          <AppShell siteGate={siteGate}>{children}</AppShell>
        </AuthProvider>
      </body>
    </html>
  );
}
