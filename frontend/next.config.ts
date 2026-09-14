import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Required for the multi-stage Docker build (copies only the minimal server bundle)
  output: "standalone",

  // PIN-guarded partner documents (the BDM deck) live in private blob storage behind the backend,
  // not in this public repository -- see backend/app/api/routes/partner_docs.py. Proxying keeps
  // them on the site's own origin, so /docs/walkthrough.html is a real address and the unlock
  // cookie belongs to this domain. NEXT_PUBLIC_API_URL is a build arg, so this is fixed per image.
  async rewrites() {
    const api = process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL;
    return api ? [{ source: "/docs/:path*", destination: `${api}/partner-docs/:path*` }] : [];
  },
};

export default nextConfig;
