import Link from "next/link";
import ReportBugLink from "@/components/ReportBugLink";

export default function Footer() {
  return (
    <footer className="border-t border-zinc-800 bg-zinc-950">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-6 py-10 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-sm bg-rose-600 text-xs font-black text-white">
            YT
          </span>
          <div>
            <p className="font-heading text-sm font-black uppercase tracking-tight text-white">YouGotTalent</p>
            <p className="text-xs text-zinc-500">Every skill. One stage.</p>
          </div>
        </div>
        <div className="flex flex-col gap-3 sm:items-end">
          <div className="flex gap-6 text-sm font-semibold text-zinc-400">
            <Link href="/talents" className="hover:text-rose-500">
              Browse talent
            </Link>
            <Link href="/casting-calls" className="hover:text-rose-500">
              Talent hunts
            </Link>
            <Link href="/community" className="hover:text-rose-500">
              Community
            </Link>
            <ReportBugLink />
          </div>
          <div className="flex gap-4 text-xs text-zinc-500">
            <Link href="/privacy" className="hover:text-rose-500">
              Privacy Policy
            </Link>
            <Link href="/terms" className="hover:text-rose-500">
              Terms of Service
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
