import type { Metadata } from "next";
import { headers } from "next/headers";
import { Archivo, Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";
import AppShell from "@/components/AppShell";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const archivo = Archivo({
  variable: "--font-archivo",
  subsets: ["latin"],
  weight: ["700", "800", "900"],
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
      className={`${geistSans.variable} ${geistMono.variable} ${archivo.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <AuthProvider>
          <AppShell siteGate={siteGate}>{children}</AppShell>
        </AuthProvider>
      </body>
    </html>
  );
}
