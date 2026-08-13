import { Wrench } from "lucide-react";

export const dynamic = "force-dynamic";

export default function MaintenancePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-zinc-950 px-6 text-center">
      <span className="inline-flex items-center gap-1.5 rounded-sm bg-rose-600 px-3 py-1 text-xs font-bold uppercase tracking-widest text-white">
        <Wrench className="h-3.5 w-3.5" /> Under maintenance
      </span>
      <h1 className="font-heading mt-6 text-4xl font-black uppercase tracking-tight text-white sm:text-6xl">
        YouGotTalent
      </h1>
      <p className="mt-4 max-w-md text-balance text-sm text-zinc-400 sm:text-base">
        We&apos;re making some quick improvements. We&apos;ll be back shortly — thanks for your
        patience.
      </p>
    </main>
  );
}
