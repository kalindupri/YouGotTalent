"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Check, Link2, Star } from "lucide-react";
import { CastingCall, TALENT_CATEGORIES, TalentCategory, api } from "@/lib/api";
import CategoryIcon from "@/components/CategoryIcon";
import {
  badgeClass,
  btnPrimary,
  btnSmall,
  cardClass,
  categoryBadgeClass,
  formatCategory,
  formatRelativeTime,
  inputClass,
  statusTone,
} from "@/lib/ui";

export default function CastingCallsPage() {
  return (
    <Suspense fallback={null}>
      <CastingCallsContent />
    </Suspense>
  );
}

function CastingCallsContent() {
  const searchParams = useSearchParams();
  const initialCategory = (searchParams.get("category") as TalentCategory | null) ?? "";

  const [calls, setCalls] = useState<CastingCall[]>([]);
  const [category, setCategory] = useState<TalentCategory | "">(initialCategory);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        setCalls(await api.listCastingCalls({ category: category || undefined }));
      } catch {
        setError("Could not load casting calls right now.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [category]);

  return (
    <main className="mx-auto w-full max-w-5xl flex-1 px-6 py-14">
      <h1 className="font-heading text-4xl font-black uppercase tracking-tight text-zinc-900 sm:text-5xl dark:text-zinc-50">
        Talent hunts
      </h1>
      <p className="mt-2 text-zinc-500">
        {loading ? "Loading…" : `${calls.length} open opportunit${calls.length === 1 ? "y" : "ies"}`}
      </p>

      <div className="mt-8">
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value as TalentCategory | "")}
          className={`${inputClass} w-auto`}
        >
          <option value="">All categories</option>
          {TALENT_CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {formatCategory(c)}
            </option>
          ))}
        </select>
      </div>

      {error && <p className="mt-8 text-sm text-red-600">{error}</p>}
      {!loading && !error && calls.length === 0 && (
        <p className="mt-8 text-sm text-zinc-500">No open opportunities in this category yet.</p>
      )}

      <div className="mt-8 flex flex-col gap-5">
        {calls.map((c) => (
          <CastingCallCard key={c.id} call={c} />
        ))}
      </div>
    </main>
  );
}

function CastingCallCard({ call }: { call: CastingCall }) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);
  const isLong = call.description.length > 220;

  async function handleShare(e: React.MouseEvent) {
    e.preventDefault();
    await navigator.clipboard.writeText(`${window.location.origin}/casting-calls/${call.id}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className={`relative overflow-hidden ${cardClass} ${call.is_featured ? "border-t-4 border-t-amber-400" : ""}`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-wrap items-center gap-2">
          {call.is_featured && (
            <span className="inline-flex items-center gap-1 rounded-sm bg-amber-400 px-2.5 py-0.5 text-xs font-bold uppercase tracking-wide text-zinc-900">
              <Star className="h-3 w-3" fill="currentColor" strokeWidth={0} /> Featured
            </span>
          )}
          <span className={badgeClass(statusTone(call.status))}>{call.status}</span>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={handleShare} className={btnSmall}>
            {copied ? (
              <>
                <Check className="h-3.5 w-3.5" /> Copied
              </>
            ) : (
              <>
                <Link2 className="h-3.5 w-3.5" /> Share
              </>
            )}
          </button>
        </div>
      </div>

      <Link href={`/casting-calls/${call.id}`} className="mt-3 block">
        <p className="font-heading text-xl font-bold text-zinc-900 hover:text-rose-600 dark:text-zinc-50">
          {call.title}
        </p>
      </Link>

      <div className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-zinc-500">
        {call.compensation && (
          <>
            <span className="font-semibold text-emerald-700 dark:text-emerald-400">{call.compensation}</span>
            <span>·</span>
          </>
        )}
        <span>{call.location || "Worldwide"}</span>
        <span>·</span>
        <span>Posted {formatRelativeTime(call.created_at)}</span>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-6 sm:grid-cols-3">
        <div className="sm:col-span-2">
          <p className={`text-sm text-zinc-600 dark:text-zinc-400 ${expanded ? "" : "line-clamp-2"}`}>
            {call.description}
          </p>
          {isLong && (
            <button
              onClick={() => setExpanded((v) => !v)}
              className="mt-1 text-sm font-semibold text-rose-600 hover:underline"
            >
              {expanded ? "view less" : "view more"}
            </button>
          )}

          {call.shoot_details && (
            <p className="mt-3 text-sm text-zinc-500">
              <span className="font-semibold text-zinc-700 dark:text-zinc-300">Dates & Locations:</span>{" "}
              {call.shoot_details}
            </p>
          )}

          {call.tags && call.tags.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {call.tags.map((t) => (
                <span
                  key={t}
                  className="inline-flex items-center gap-1 rounded-full bg-zinc-100 px-3 py-1 text-xs font-semibold text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
                >
                  <Check className="h-3 w-3" /> {t}
                </span>
              ))}
            </div>
          )}

          <Link href={`/casting-calls/${call.id}`} className={`mt-4 inline-flex w-fit ${btnPrimary}`}>
            View Details & Apply
          </Link>
        </div>

        {call.roles.length > 1 && (
          <div className="flex flex-col gap-2">
            {call.roles.map((role) => (
              <Link
                key={role.id}
                href={`/casting-calls/${call.id}?role=${role.id}`}
                className="flex flex-col gap-1.5 rounded-lg bg-zinc-50 p-3 dark:bg-zinc-800/60"
              >
                <div className="flex items-center gap-1.5">
                  <CategoryIcon category={role.category ?? call.category} className="h-4 w-4 text-zinc-500" />
                  <span className="text-sm font-bold text-zinc-900 dark:text-zinc-50">{role.title}</span>
                </div>
                {role.criteria && <p className="text-xs text-zinc-500">{role.criteria}</p>}
                <span className={`w-fit ${btnSmall} !bg-rose-600 !text-white !border-rose-600`}>Apply</span>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
