"use client";

import CommunityModeration from "@/components/admin/CommunityModeration";

export default function AdminCommunityPage() {
  return (
    <div>
      <h1 className="font-heading text-3xl font-black text-zinc-900 dark:text-zinc-50">Community</h1>
      <p className="mt-1 text-sm text-zinc-500">Moderate rated titles, critiques, discussions, and replies.</p>
      <div className="mt-6">
        <CommunityModeration />
      </div>
    </div>
  );
}
