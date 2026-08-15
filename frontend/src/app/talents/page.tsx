"use client";

import { FormEvent, Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Save, ShieldCheck, Sparkles } from "lucide-react";
import { ApiError, api, CastingCall, TALENT_CATEGORIES, TalentCategory, TalentProfile } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import {
  btnSecondary,
  btnSmall,
  cardClass,
  categoryBadgeClass,
  coverPhotoUrl,
  formatCategory,
  formatInstrument,
  INSTRUMENT_GROUPS,
  inputClass,
  labelClass,
  verifiedBadgeClass,
} from "@/lib/ui";
import TalentAvatar from "@/components/TalentAvatar";

export default function TalentsPage() {
  return (
    <Suspense fallback={null}>
      <TalentsPageContent />
    </Suspense>
  );
}

function TalentsPageContent() {
  const searchParams = useSearchParams();
  const { user, token } = useAuth();

  const hasAdvancedParams =
    searchParams.has("experience_min") || searchParams.has("experience_max") || searchParams.has("verified_only");

  const [talents, setTalents] = useState<TalentProfile[]>([]);
  const [categories, setCategories] = useState<TalentCategory[]>(searchParams.getAll("categories") as TalentCategory[]);
  const [city, setCity] = useState(searchParams.get("city") ?? "");
  const [q, setQ] = useState(searchParams.get("q") ?? "");
  const [showAdvanced, setShowAdvanced] = useState(hasAdvancedParams);
  const [experienceMin, setExperienceMin] = useState(searchParams.get("experience_min") ?? "");
  const [experienceMax, setExperienceMax] = useState(searchParams.get("experience_max") ?? "");
  const [verifiedOnly, setVerifiedOnly] = useState(searchParams.get("verified_only") === "true");
  const [instruments, setInstruments] = useState<string[]>(searchParams.getAll("instruments"));
  const [gender, setGender] = useState("");
  const [ageMin, setAgeMin] = useState("");
  const [ageMax, setAgeMax] = useState("");
  const [minTiktokFollowers, setMinTiktokFollowers] = useState<number | undefined>(undefined);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [smartQuery, setSmartQuery] = useState("");
  const [smartParsing, setSmartParsing] = useState(false);
  const [detected, setDetected] = useState<string[] | null>(null);

  async function handleSmartSearch(e: FormEvent) {
    e.preventDefault();
    if (!smartQuery.trim()) return;
    setSmartParsing(true);
    try {
      const parsed = await api.parseTalentSearchQuery(smartQuery);
      const chips: string[] = [];
      if (parsed.categories?.length) {
        setCategories(parsed.categories as TalentCategory[]);
        chips.push(...parsed.categories.map(formatCategory));
      } else {
        setCategories([]);
      }
      setGender(parsed.gender ?? "");
      if (parsed.gender) chips.push(parsed.gender === "male" ? "Male" : "Female");
      setAgeMin(parsed.age_min != null ? String(parsed.age_min) : "");
      setAgeMax(parsed.age_max != null ? String(parsed.age_max) : "");
      if (parsed.age_min != null || parsed.age_max != null) {
        chips.push(
          parsed.age_min != null && parsed.age_max != null
            ? `${parsed.age_min}-${parsed.age_max} yrs`
            : parsed.age_min != null
              ? `Over ${parsed.age_min - 1}`
              : `Under ${parsed.age_max! + 1}`
        );
      }
      setExperienceMin(parsed.experience_min != null ? String(parsed.experience_min) : "");
      setExperienceMax(parsed.experience_max != null ? String(parsed.experience_max) : "");
      if (parsed.experience_min != null) chips.push(`${parsed.experience_min}+ yrs experience`);
      if (parsed.experience_max === 0) chips.push("No experience required");
      setInstruments(parsed.instruments ?? []);
      if (parsed.instruments?.length) chips.push(...parsed.instruments.map(formatInstrument));
      setMinTiktokFollowers(parsed.min_tiktok_followers ?? undefined);
      if (parsed.min_tiktok_followers) chips.push(`${(parsed.min_tiktok_followers / 1000).toFixed(0)}k+ TikTok followers`);
      setQ(parsed.keywords ?? "");
      if (parsed.keywords) chips.push(`"${parsed.keywords}"`);
      setDetected(chips.length > 0 ? chips : ["No specific filters detected — searching keywords only"]);
      setShowAdvanced(true);
    } catch {
      setDetected(null);
    } finally {
      setSmartParsing(false);
    }
  }

  const [savingSearch, setSavingSearch] = useState(false);
  const [saveSearchMessage, setSaveSearchMessage] = useState<string | null>(null);

  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [myOpenCalls, setMyOpenCalls] = useState<CastingCall[]>([]);
  const [inviteCallId, setInviteCallId] = useState("");
  const [inviting, setInviting] = useState(false);
  const [inviteMessage, setInviteMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!token || user?.role !== "recruiter") return;
    api
      .getMyRecruiterProfile(token)
      .then((recruiter) => api.listCastingCalls().then((all) => all.filter((c) => c.recruiter_id === recruiter.id && c.status === "open")))
      .then(setMyOpenCalls)
      .catch(() => {});
  }, [token, user]);

  function toggleInstrument(instrument: string) {
    setInstruments((prev) => (prev.includes(instrument) ? prev.filter((i) => i !== instrument) : [...prev, instrument]));
  }

  function toggleCategory(c: TalentCategory) {
    setCategories((prev) => (prev.includes(c) ? prev.filter((x) => x !== c) : [...prev, c]));
  }

  function toggleSelected(talentId: string) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(talentId)) next.delete(talentId);
      else next.add(talentId);
      return next;
    });
  }

  async function handleBulkInvite() {
    if (!token || !inviteCallId || selectedIds.size === 0) return;
    setInviting(true);
    setInviteMessage(null);
    try {
      const result = await api.bulkInviteTalent(inviteCallId, { talent_ids: Array.from(selectedIds) }, token);
      setInviteMessage(
        `Invited ${result.invited.length} talent${result.invited.length === 1 ? "" : "s"}.` +
          (result.skipped.length > 0 ? ` ${result.skipped.length} already invited or unavailable.` : "")
      );
      setSelectedIds(new Set());
    } catch (err) {
      setInviteMessage(err instanceof ApiError ? err.message : "Could not send these invitations.");
    } finally {
      setInviting(false);
    }
  }

  useEffect(() => {
    const handle = setTimeout(() => {
      async function load() {
        setLoading(true);
        setError(null);
        try {
          setTalents(
            await api.listTalents({
              categories: categories.length > 0 ? categories : undefined,
              city: city || undefined,
              q: q || undefined,
              experience_min: experienceMin ? Number(experienceMin) : undefined,
              experience_max: experienceMax ? Number(experienceMax) : undefined,
              verified_only: verifiedOnly || undefined,
              instruments: instruments.length > 0 ? instruments : undefined,
              gender: gender || undefined,
              age_min: ageMin ? Number(ageMin) : undefined,
              age_max: ageMax ? Number(ageMax) : undefined,
              min_tiktok_followers: minTiktokFollowers,
            })
          );
        } catch {
          setError("Could not load talent right now.");
        } finally {
          setLoading(false);
        }
      }
      load();
    }, 250);
    return () => clearTimeout(handle);
  }, [categories, city, q, experienceMin, experienceMax, verifiedOnly, instruments, gender, ageMin, ageMax, minTiktokFollowers]);

  async function handleSaveSearch(e: FormEvent) {
    e.preventDefault();
    if (!token) return;
    setSavingSearch(true);
    setSaveSearchMessage(null);
    try {
      await api.createSavedSearch(
        {
          name: [categories[0] && formatCategory(categories[0]), city, q].filter(Boolean).join(" · ") || "My search",
          category: categories[0] || undefined,
          city: city || undefined,
          q: q || undefined,
          experience_min: experienceMin ? Number(experienceMin) : undefined,
          experience_max: experienceMax ? Number(experienceMax) : undefined,
          verified_only: verifiedOnly,
        },
        token
      );
      setSaveSearchMessage("Saved! Find it on your dashboard.");
    } catch (err) {
      setSaveSearchMessage(err instanceof ApiError ? err.message : "Could not save this search.");
    } finally {
      setSavingSearch(false);
    }
  }

  return (
    <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-14">
      <h1 className="font-heading text-4xl font-black uppercase tracking-tight text-zinc-900 sm:text-5xl dark:text-zinc-50">
        Browse talent
      </h1>
      <p className="mt-2 text-zinc-500">
        {loading ? "Loading…" : `${talents.length} talent profile${talents.length === 1 ? "" : "s"}`}
      </p>

      <form onSubmit={handleSmartSearch} className="mt-8 flex flex-wrap gap-2">
        <input
          placeholder={`Describe who you're looking for — e.g. "Actor wanted under 35 male with some experience"`}
          value={smartQuery}
          onChange={(e) => setSmartQuery(e.target.value)}
          className={`${inputClass} max-w-lg flex-1`}
        />
        <button type="submit" disabled={smartParsing || !smartQuery.trim()} className={btnSecondary}>
          <Sparkles className="h-4 w-4" /> {smartParsing ? "Thinking…" : "Smart search"}
        </button>
      </form>
      {detected && (
        <div className="mt-2 flex flex-wrap items-center gap-1.5 text-xs">
          <span className="font-semibold text-zinc-500">Detected:</span>
          {detected.map((d, i) => (
            <span
              key={i}
              className="rounded-full bg-rose-50 px-2 py-0.5 font-medium text-rose-700 dark:bg-rose-950 dark:text-rose-300"
            >
              {d}
            </span>
          ))}
        </div>
      )}

      <div className="mt-4 flex flex-wrap gap-3">
        <input
          placeholder="Search by name, bio, or skill (e.g. 'screenplay', 'carnatic')"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className={`${inputClass} max-w-sm`}
        />
        <input
          placeholder="Filter by city"
          value={city}
          onChange={(e) => setCity(e.target.value)}
          className={`${inputClass} w-auto max-w-[10rem]`}
        />
        <button type="button" onClick={() => setShowAdvanced((v) => !v)} className={btnSmall}>
          {showAdvanced ? "Hide" : "Advanced filters"}
        </button>
      </div>

      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-2">
        {TALENT_CATEGORIES.map((c) => (
          <label
            key={c}
            className={`cursor-pointer rounded-full border-2 px-2.5 py-1 text-[11px] font-semibold transition-colors ${
              categories.includes(c)
                ? "border-rose-500 bg-rose-50 text-rose-700 dark:bg-rose-950 dark:text-rose-300"
                : "border-zinc-200 text-zinc-600 dark:border-zinc-700 dark:text-zinc-300"
            }`}
          >
            <input type="checkbox" checked={categories.includes(c)} onChange={() => toggleCategory(c)} className="hidden" />
            {formatCategory(c)}
          </label>
        ))}
      </div>

      {showAdvanced && (
        <form
          onSubmit={handleSaveSearch}
          className="mt-4 flex flex-wrap items-end gap-3 rounded-xl border border-zinc-200 p-4 dark:border-zinc-800"
        >
          <label className={labelClass}>
            Min. experience (years)
            <input
              type="number"
              min={0}
              value={experienceMin}
              onChange={(e) => setExperienceMin(e.target.value)}
              className={`${inputClass} w-32`}
            />
          </label>
          <label className={labelClass}>
            Max. experience (years)
            <input
              type="number"
              min={0}
              value={experienceMax}
              onChange={(e) => setExperienceMax(e.target.value)}
              className={`${inputClass} w-32`}
            />
          </label>
          <label className={labelClass}>
            Gender
            <select value={gender} onChange={(e) => setGender(e.target.value)} className={`${inputClass} w-32`}>
              <option value="">Any</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
            </select>
          </label>
          <label className={labelClass}>
            Min. age
            <input type="number" min={0} value={ageMin} onChange={(e) => setAgeMin(e.target.value)} className={`${inputClass} w-24`} />
          </label>
          <label className={labelClass}>
            Max. age
            <input type="number" min={0} value={ageMax} onChange={(e) => setAgeMax(e.target.value)} className={`${inputClass} w-24`} />
          </label>
          <label className="flex items-center gap-2 pb-2.5 text-sm font-medium text-zinc-700 dark:text-zinc-300">
            <input
              type="checkbox"
              checked={verifiedOnly}
              onChange={(e) => setVerifiedOnly(e.target.checked)}
              className="accent-rose-600"
            />
            Verified talent only
          </label>
          <div className="flex w-full flex-col gap-1.5">
            <span className="text-xs font-bold uppercase tracking-wide text-zinc-400">
              Instruments (music category)
            </span>
            <div className="flex flex-wrap gap-x-4 gap-y-2">
              {INSTRUMENT_GROUPS.map((group) => (
                <div key={group.label} className="flex flex-wrap items-center gap-1.5">
                  {group.instruments.map((i) => (
                    <label
                      key={i}
                      className={`cursor-pointer rounded-full border-2 px-2.5 py-1 text-[11px] font-semibold transition-colors ${
                        instruments.includes(i)
                          ? "border-rose-500 bg-rose-50 text-rose-700 dark:bg-rose-950 dark:text-rose-300"
                          : "border-zinc-200 text-zinc-600 dark:border-zinc-700 dark:text-zinc-300"
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={instruments.includes(i)}
                        onChange={() => toggleInstrument(i)}
                        className="hidden"
                      />
                      {formatInstrument(i)}
                    </label>
                  ))}
                </div>
              ))}
            </div>
          </div>
          {user?.role === "recruiter" && (
            <button type="submit" disabled={savingSearch} className={btnSecondary}>
              {savingSearch ? (
                "Saving…"
              ) : (
                <>
                  <Save className="h-4 w-4" /> Save this search
                </>
              )}
            </button>
          )}
          {saveSearchMessage && <p className="w-full text-sm text-zinc-500">{saveSearchMessage}</p>}
        </form>
      )}

      {error && <p className="mt-8 text-sm text-red-600">{error}</p>}
      {!loading && !error && talents.length === 0 && (
        <p className="mt-8 text-sm text-zinc-500">No talent profiles match your search yet.</p>
      )}

      <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3">
        {talents.map((t) => (
          <div key={t.id} className="relative">
            {user?.role === "recruiter" && myOpenCalls.length > 0 && (
              <label
                className="absolute left-3 top-3 z-10 flex h-6 w-6 items-center justify-center rounded-md bg-white/90 shadow"
                onClick={(e) => e.stopPropagation()}
              >
                <input
                  type="checkbox"
                  checked={selectedIds.has(t.id)}
                  onChange={() => toggleSelected(t.id)}
                  className="h-4 w-4 accent-rose-600"
                />
              </label>
            )}
            <Link
              href={`/talents/${t.id}`}
              className="group block overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-sm transition-all hover:-translate-y-1 hover:shadow-lg dark:border-zinc-800 dark:bg-zinc-900"
            >
              <div className="aspect-[4/3] overflow-hidden bg-zinc-100 dark:bg-zinc-800">
                <TalentAvatar
                  name={t.display_name}
                  coverUrl={coverPhotoUrl(t.media)}
                  className="h-full w-full text-4xl transition-transform duration-300 group-hover:scale-105"
                />
              </div>
              <div className="p-4">
                <div className="flex items-center gap-1.5">
                  <p className="font-heading text-lg font-bold text-zinc-900 dark:text-zinc-50">{t.display_name}</p>
                  {t.is_verified && (
                    <span className={verifiedBadgeClass}>
                      <ShieldCheck className="h-3 w-3" />
                    </span>
                  )}
                </div>
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  {(t.categories?.length ? t.categories : [t.category]).map((c) => (
                    <span key={c} className={categoryBadgeClass(c)}>
                      {formatCategory(c)}
                    </span>
                  ))}
                  {t.city && <span className="text-xs text-zinc-500">{t.city}</span>}
                </div>
                {t.skills && t.skills.length > 0 && (
                  <p className="mt-2 truncate text-xs text-zinc-500">{t.skills.slice(0, 3).join(" · ")}</p>
                )}
              </div>
            </Link>
          </div>
        ))}
        {loading &&
          Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className={`${cardClass} h-64 animate-pulse !p-0`}>
              <div className="aspect-[4/3] rounded-t-xl bg-zinc-100 dark:bg-zinc-800" />
            </div>
          ))}
      </div>

      {(selectedIds.size > 0 || inviteMessage) && (
        <div className="sticky bottom-4 mt-6 flex flex-wrap items-center gap-3 rounded-xl border border-zinc-200 bg-white p-4 shadow-lg dark:border-zinc-800 dark:bg-zinc-900">
          {selectedIds.size > 0 && (
            <>
              <span className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">
                {selectedIds.size} talent selected
              </span>
              <select value={inviteCallId} onChange={(e) => setInviteCallId(e.target.value)} className={`${inputClass} w-auto`}>
                <option value="">Invite to…</option>
                {myOpenCalls.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.title}
                  </option>
                ))}
              </select>
              <button
                type="button"
                disabled={!inviteCallId || inviting}
                onClick={handleBulkInvite}
                className={btnSecondary}
              >
                {inviting ? "Inviting…" : "Send invitations"}
              </button>
              <button type="button" onClick={() => setSelectedIds(new Set())} className={btnSmall}>
                Clear
              </button>
            </>
          )}
          {inviteMessage && (
            <p className="w-full text-sm text-zinc-500">
              {inviteMessage}{" "}
              <button type="button" onClick={() => setInviteMessage(null)} className="font-semibold text-rose-600 hover:underline">
                Dismiss
              </button>
            </p>
          )}
        </div>
      )}
    </main>
  );
}
