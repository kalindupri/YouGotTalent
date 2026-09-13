"use client";

import { FormEvent, Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { PlayCircle, Save, Search, ShieldCheck, SlidersHorizontal, X } from "lucide-react";
import { ApiError, api, CastingCall, TALENT_CATEGORIES, TalentCategory, TalentProfile } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { badgeClass,
  btnPrimary,
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

  // The count on the filter button. The page previously gave no indication at all of what was
  // applied: Advanced filters closed and left no trace, so a stale age range silently narrowed
  // every later search.
  const activeFilterCount =
    categories.length +
    (city ? 1 : 0) +
    (q ? 1 : 0) +
    (gender ? 1 : 0) +
    (ageMin || ageMax ? 1 : 0) +
    (experienceMin || experienceMax ? 1 : 0) +
    (verifiedOnly ? 1 : 0) +
    instruments.length +
    (minTiktokFollowers ? 1 : 0);

  const [smartQuery, setSmartQuery] = useState("");
  const [smartParsing, setSmartParsing] = useState(false);
  // Chips are the filter UI now, not a receipt: each carries the reset that clears it, so
  // removing one re-runs the search. Previously they were read-only text and the only way to
  // undo a parse was to clear the box and start again.
  const [detected, setDetected] = useState<{ label: string; clear: () => void }[] | null>(null);

  async function handleSmartSearch(e: FormEvent) {
    e.preventDefault();
    if (!smartQuery.trim()) return;
    setSmartParsing(true);
    try {
      const parsed = await api.parseTalentSearchQuery(smartQuery);
      const chips: { label: string; clear: () => void }[] = [];
      if (parsed.categories?.length) {
        setCategories(parsed.categories as TalentCategory[]);
        for (const c of parsed.categories) {
          chips.push({
            label: formatCategory(c),
            clear: () => setCategories((prev) => prev.filter((x) => x !== c)),
          });
        }
      } else {
        setCategories([]);
      }
      // City is a real filter rather than a keyword: the keyword search does not cover the city
      // column, so before the parser learned place names "singer in Kandy" quietly missed
      // everyone who lives in Kandy but does not say so in their bio.
      setCity(parsed.city ?? "");
      if (parsed.city) chips.push({ label: parsed.city, clear: () => setCity("") });
      setVerifiedOnly(parsed.verified_only);
      if (parsed.verified_only) chips.push({ label: "Verified", clear: () => setVerifiedOnly(false) });
      setGender(parsed.gender ?? "");
      if (parsed.gender)
        chips.push({ label: parsed.gender === "male" ? "Male" : "Female", clear: () => setGender("") });
      setAgeMin(parsed.age_min != null ? String(parsed.age_min) : "");
      setAgeMax(parsed.age_max != null ? String(parsed.age_max) : "");
      if (parsed.age_min != null || parsed.age_max != null) {
        chips.push({
          label:
            parsed.age_min != null && parsed.age_max != null
              ? `${parsed.age_min}-${parsed.age_max} yrs`
              : parsed.age_min != null
                ? `Over ${parsed.age_min - 1}`
                : `Under ${parsed.age_max! + 1}`,
          clear: () => {
            setAgeMin("");
            setAgeMax("");
          },
        });
      }
      setExperienceMin(parsed.experience_min != null ? String(parsed.experience_min) : "");
      setExperienceMax(parsed.experience_max != null ? String(parsed.experience_max) : "");
      if (parsed.experience_min != null)
        chips.push({ label: `${parsed.experience_min}+ yrs experience`, clear: () => setExperienceMin("") });
      if (parsed.experience_max === 0)
        chips.push({ label: "No experience required", clear: () => setExperienceMax("") });
      setInstruments(parsed.instruments ?? []);
      for (const i of parsed.instruments ?? []) {
        chips.push({ label: formatInstrument(i), clear: () => setInstruments((prev) => prev.filter((x) => x !== i)) });
      }
      setMinTiktokFollowers(parsed.min_tiktok_followers ?? undefined);
      if (parsed.min_tiktok_followers)
        chips.push({
          label: `${(parsed.min_tiktok_followers / 1000).toFixed(0)}k+ TikTok followers`,
          clear: () => setMinTiktokFollowers(undefined),
        });
      setQ(parsed.keywords ?? "");
      if (parsed.keywords) chips.push({ label: `"${parsed.keywords}"`, clear: () => setQ("") });
      setDetected(chips);
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
      <h1 className="font-heading text-4xl font-extrabold tracking-tight text-zinc-900 sm:text-5xl dark:text-zinc-50">
        Browse talent
      </h1>
      <p className="mt-2 text-zinc-500">
        {loading ? "Loading…" : `${talents.length} talent profile${talents.length === 1 ? "" : "s"}`}
      </p>

      {/* One box. There used to be three — a natural-language box, a keyword box and a city box,
          all styled identically with no labels, and at 375px the natural-language one was 134px
          wide next to a 170px button, so its placeholder truncated to "Describe who y". The
          parser handles craft, city, age, gender, experience and verification, so plain language
          is the input and everything it cannot place falls through to the keyword search. */}
      {/* The search row must not repeat the mistake it replaces: on a 375px screen a visible
          "Search" button alongside squeezes the input back under ~170px and the placeholder
          truncates again. So on phones the input takes the full row and Enter submits; the
          button reappears once there is width for it. */}
      <form onSubmit={handleSmartSearch} className="mt-8 flex flex-wrap gap-2">
        <label className="relative min-w-0 flex-1 basis-full sm:basis-0">
          <span className="sr-only">Search talent</span>
          <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400" />
          <input
            placeholder="Try “singer in Kandy under 25”"
            value={smartQuery}
            onChange={(e) => setSmartQuery(e.target.value)}
            className={`${inputClass} pl-10`}
          />
        </label>
        <button
          type="button"
          onClick={() => setShowAdvanced((v) => !v)}
          aria-expanded={showAdvanced}
          className="relative flex min-h-[44px] shrink-0 items-center justify-center gap-2 rounded-md border-2 border-zinc-200 px-4 text-sm font-semibold text-zinc-700 transition-colors hover:border-rose-300 sm:w-12 sm:px-0 dark:border-zinc-700 dark:text-zinc-300"
        >
          <SlidersHorizontal className="h-4 w-4" />
          <span className="sm:sr-only">Filters</span>
          {activeFilterCount > 0 && (
            <span className="absolute -right-1.5 -top-1.5 flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-rose-600 px-1 text-[10px] font-extrabold text-white">
              {activeFilterCount}
            </span>
          )}
        </button>
        <button
          type="submit"
          disabled={smartParsing || !smartQuery.trim()}
          className={`hidden sm:inline-flex ${btnPrimary}`}
        >
          {smartParsing ? "Searching…" : "Search"}
        </button>
      </form>
      {detected && (
        <div className="mt-3 flex flex-wrap items-center gap-1.5 text-xs">
          {detected.length === 0 && (
            <span className="text-zinc-500">Searching everything — add a craft, city or age to narrow it down.</span>
          )}
          {detected.map((d, i) => (
            <button
              key={i}
              type="button"
              onClick={() => {
                d.clear();
                setDetected((prev) => (prev ? prev.filter((_, j) => j !== i) : prev));
              }}
              className="inline-flex items-center gap-1 rounded-full bg-rose-50 py-1 pl-2.5 pr-1.5 font-semibold text-rose-700 transition-colors hover:bg-rose-100 dark:bg-rose-950 dark:text-rose-300"
            >
              {d.label}
              <X className="h-3 w-3" />
              <span className="sr-only">Remove filter</span>
            </button>
          ))}
          {detected.length > 0 && (
            <button
              type="button"
              onClick={() => {
                for (const d of detected) d.clear();
                setDetected(null);
                setSmartQuery("");
              }}
              className="ml-1 font-semibold text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
            >
              Clear all
            </button>
          )}
        </div>
      )}

      {showAdvanced && (
        <div className="mt-4 flex flex-col gap-4 rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
          <div className="flex flex-wrap gap-3">
            <label className={`${labelClass} max-w-sm flex-1`}>
              Name, bio or skill
              <input
                placeholder="e.g. screenplay, carnatic"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                className={inputClass}
              />
            </label>
            <label className={`${labelClass} w-40`}>
              City
              <input value={city} onChange={(e) => setCity(e.target.value)} className={inputClass} />
            </label>
          </div>

      <div className="flex flex-col gap-1.5">
        <span className="text-xs font-bold uppercase tracking-wide text-zinc-400">Craft</span>
        <div className="flex flex-wrap gap-x-4 gap-y-2">
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
      </div>

        <form onSubmit={handleSaveSearch} className="flex flex-wrap items-end gap-3 border-t border-zinc-200 pt-4 dark:border-zinc-800">
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

          <div className="flex justify-end border-t border-zinc-200 pt-4 dark:border-zinc-800">
            <button type="button" onClick={() => setShowAdvanced(false)} className={btnPrimary}>
              {loading ? "Searching…" : `Show ${talents.length} result${talents.length === 1 ? "" : "s"}`}
            </button>
          </div>
        </div>
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
            {/* A row on phones, a tile from sm up. At 375px the 4:3 tile made one result fill
                most of the screen, which is the wrong shape for a scanning task -- a row fits
                four. The photo still gets its space on the profile itself. */}
            <Link
              href={`/talents/${t.id}`}
              className="group flex overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-sm transition-all hover:shadow-lg sm:block sm:hover:-translate-y-1 dark:border-zinc-800 dark:bg-zinc-900"
            >
              <div className="h-28 w-28 shrink-0 overflow-hidden bg-zinc-100 sm:aspect-[4/3] sm:h-auto sm:w-full dark:bg-zinc-800">
                <TalentAvatar
                  name={t.display_name}
                  coverUrl={coverPhotoUrl(t.media)}
                  className="h-full w-full text-2xl transition-transform duration-300 sm:text-4xl sm:group-hover:scale-105"
                />
              </div>
              <div className="min-w-0 flex-1 p-3 sm:p-4">
                <div className="flex items-center gap-1.5">
                  <p className="truncate font-heading text-base font-bold text-zinc-900 sm:text-lg dark:text-zinc-50">
                    {t.display_name}
                  </p>
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
                  {t.age !== null && <span className="text-xs text-zinc-500">{t.age}</span>}
                </div>
                {/* Two signals that change what a recruiter can do next, and that currently only
                    surface after opening the profile. An audition clip is the thing they came for;
                    an under-18 means the contract routes to a guardian to countersign. Both are
                    derived from what the public payload already carries -- a minor only appears in
                    these results at all once their guardian consent has been approved, so showing
                    the age is not leaking anything the listing did not already imply. */}
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  {t.media.some((m) => m.media_type === "video") || t.intro_video_url ? (
                    <span className="inline-flex items-center gap-1 text-xs font-semibold text-rose-600 dark:text-rose-400">
                      <PlayCircle className="h-3.5 w-3.5" /> Has a clip
                    </span>
                  ) : (
                    <span className="text-xs text-zinc-400">No clip yet</span>
                  )}
                  {t.age !== null && t.age < 18 && (
                    <span className={badgeClass("info")}>Guardian-managed</span>
                  )}
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
