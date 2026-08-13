"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Bookmark, Check, Crown, Share2, ShieldCheck, Star } from "lucide-react";
import { ApiError, Credit, LibraryItem, Reel, TalentProfile, TalentReviewSummary, api } from "@/lib/api";
import {
  CREDIT_PROJECT_TYPES,
  SOCIAL_LINK_FIELDS,
  btnSecondary,
  btnSmall,
  btnSmallPrimary,
  categoryAttributeFields,
  categoryBadgeClass,
  categoryShowsIntroVideo,
  coverPhotoUrl,
  formatCategory,
  libraryLabel,
  premiumBadgeClass,
  reelPlatformLabel,
  REEL_PLATFORM_ICONS,
  verifiedBadgeClass,
} from "@/lib/ui";
import { useAuth } from "@/lib/auth-context";
import TalentAvatar from "@/components/TalentAvatar";
import MessageTalentButton from "@/components/MessageTalentButton";
import InviteToRoleButton from "@/components/InviteToRoleButton";
import BookingRequestButton from "@/components/BookingRequestButton";
import MediaCard from "@/components/MediaCard";
import LibraryItemCard from "@/components/LibraryItemCard";
import SubmissionPreview from "@/components/SubmissionPreview";
import ReportButton from "@/components/ReportButton";
import TikTokEmbed from "@/components/TikTokEmbed";

export default function TalentDetailPage() {
  const params = useParams<{ id: string }>();
  const { user, token } = useAuth();

  const [talent, setTalent] = useState<TalentProfile | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [savedLoaded, setSavedLoaded] = useState(false);
  const [saving, setSaving] = useState(false);
  const [copied, setCopied] = useState(false);
  const [reviewSummary, setReviewSummary] = useState<TalentReviewSummary | null>(null);
  const [library, setLibrary] = useState<LibraryItem[]>([]);

  useEffect(() => {
    api
      .getTalent(params.id, token)
      .then(setTalent)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load this profile."));
    api.getTalentReviews(params.id).then(setReviewSummary).catch(() => {});
    api.listTalentLibrary(params.id, token).then(setLibrary).catch(() => {});
  }, [params.id, token]);

  useEffect(() => {
    if (!token || user?.role !== "recruiter") return;
    api
      .listSavedTalents(token)
      .then((list) => setSaved(list.some((t) => t.id === params.id)))
      .finally(() => setSavedLoaded(true));
  }, [token, user, params.id]);

  async function toggleSave() {
    if (!token) return;
    setSaving(true);
    try {
      if (saved) {
        await api.unsaveTalent(params.id, token);
        setSaved(false);
      } else {
        await api.saveTalent(params.id, token);
        setSaved(true);
      }
    } finally {
      setSaving(false);
    }
  }

  async function handleShare() {
    await navigator.clipboard.writeText(window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  if (error) {
    return (
      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-14">
        <p className="text-sm text-red-600">{error}</p>
      </main>
    );
  }

  if (!talent) {
    return (
      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-14">
        <p className="text-sm text-zinc-500">Loading…</p>
      </main>
    );
  }

  const coverUrl = coverPhotoUrl(talent.media);

  return (
    <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-10">
      <div className="overflow-hidden rounded-xl">
        <div className="h-64 w-full overflow-hidden bg-zinc-100 sm:h-80 dark:bg-zinc-800">
          <TalentAvatar name={talent.display_name} coverUrl={coverUrl} className="h-full w-full text-6xl" />
        </div>
      </div>

      <div className="mt-6 flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="font-heading text-3xl font-bold text-zinc-900 sm:text-4xl dark:text-zinc-50">
              {talent.display_name}
            </h1>
            {talent.is_verified && (
              <span className={verifiedBadgeClass}>
                <ShieldCheck className="h-3 w-3" /> Verified
              </span>
            )}
            {talent.tier === "premium" && (
              <span className={premiumBadgeClass}>
                <Crown className="h-3 w-3" fill="currentColor" strokeWidth={0} /> Premium
              </span>
            )}
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            {(talent.categories?.length ? talent.categories : [talent.category]).map((c) => (
              <span key={c} className={categoryBadgeClass(c)}>
                {formatCategory(c)}
              </span>
            ))}
            {talent.city && <span className="text-sm text-zinc-500">{talent.city}</span>}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button onClick={handleShare} className={btnSmall}>
            {copied ? (
              <>
                <Check className="h-3.5 w-3.5" /> Link copied
              </>
            ) : (
              <>
                <Share2 className="h-3.5 w-3.5" /> Share profile
              </>
            )}
          </button>
          {user?.role === "recruiter" && savedLoaded && (
            <>
              <button onClick={toggleSave} disabled={saving} className={saved ? btnSmallPrimary : btnSecondary}>
                <Bookmark className="h-3.5 w-3.5" fill={saved ? "currentColor" : "none"} />
                {saved ? "Saved" : "Save talent"}
              </button>
              <MessageTalentButton talentId={talent.id} />
              <InviteToRoleButton talentId={talent.id} />
              <BookingRequestButton talentId={talent.id} />
            </>
          )}
          {user && <ReportButton targetType="talent_profile" targetId={talent.id} />}
        </div>
      </div>

      <IntroVideoSection talent={talent} />

      {talent.experience_years !== null && (
        <p className="mt-4 text-sm text-zinc-500">
          <span className="font-semibold text-zinc-700 dark:text-zinc-300">{talent.experience_years}</span> years of
          experience
        </p>
      )}

      <AttributesSection talent={talent} />

      {talent.skills && talent.skills.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {talent.skills.map((s) => (
            <span
              key={s}
              className="rounded-full bg-zinc-100 px-3 py-1 text-xs font-semibold text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
            >
              {s}
            </span>
          ))}
        </div>
      )}

      {talent.bio && <p className="mt-6 whitespace-pre-wrap text-lg text-zinc-700 dark:text-zinc-300">{talent.bio}</p>}

      {SOCIAL_LINK_FIELDS.some((f) => talent[f.key]) && (
        <div className="mt-4 flex flex-wrap gap-2">
          {SOCIAL_LINK_FIELDS.filter((f) => talent[f.key]).map((f) => (
            <a key={f.key} href={talent[f.key]!} target="_blank" rel="noopener noreferrer" className={btnSmall}>
              <f.icon className="h-3.5 w-3.5" /> {f.label}
            </a>
          ))}
        </div>
      )}

      {talent.media.length > 0 && (
        <div className="mt-10">
          <h2 className="font-heading text-2xl font-bold text-zinc-900 dark:text-zinc-50">Auditions & portfolio</h2>
          <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2">
            {talent.media.map((m) => (
              <MediaCard key={m.id} media={m} />
            ))}
          </div>
        </div>
      )}

      {library.length > 0 && (
        <div className="mt-10">
          <h2 className="font-heading text-2xl font-bold text-zinc-900 dark:text-zinc-50">{libraryLabel(talent.category)}</h2>
          <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2">
            {library.map((item) => (
              <LibraryItemCard key={item.id} item={item} />
            ))}
          </div>
        </div>
      )}

      {talent.credits.length > 0 && (
        <div className="mt-10">
          <h2 className="font-heading text-2xl font-bold text-zinc-900 dark:text-zinc-50">Credits & experience</h2>
          <CreditsSection credits={talent.credits} />
        </div>
      )}

      {talent.reels.length > 0 && (
        <div className="mt-10">
          <h2 className="font-heading text-2xl font-bold text-zinc-900 dark:text-zinc-50">Reels</h2>
          <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2">
            {talent.reels.map((r) => (
              <ReelCard key={r.id} reel={r} />
            ))}
          </div>
        </div>
      )}

      {reviewSummary && reviewSummary.review_count > 0 && (
        <div className="mt-10 pb-10">
          <h2 className="flex items-center gap-2 font-heading text-2xl font-bold text-zinc-900 dark:text-zinc-50">
            Reviews
            <span className="flex items-center gap-1 text-base font-semibold text-amber-500">
              <Star className="h-4 w-4" fill="currentColor" strokeWidth={0} /> {reviewSummary.average_rating}
              <span className="text-sm font-normal text-zinc-500">({reviewSummary.review_count})</span>
            </span>
          </h2>
          <ul className="mt-4 flex flex-col gap-3">
            {reviewSummary.reviews.map((r) => (
              <li key={r.id} className="rounded-2xl border-2 border-zinc-100 p-4 text-sm dark:border-zinc-800">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-semibold text-zinc-900 dark:text-zinc-50">{r.reviewer_name}</span>
                  <span className="flex items-center gap-0.5 text-amber-500">
                    {[1, 2, 3, 4, 5].map((n) => (
                      <Star key={n} className="h-3.5 w-3.5" fill={n <= r.rating ? "currentColor" : "none"} />
                    ))}
                  </span>
                </div>
                {r.comment && <p className="mt-1 text-zinc-600 dark:text-zinc-400">&ldquo;{r.comment}&rdquo;</p>}
              </li>
            ))}
          </ul>
        </div>
      )}
    </main>
  );
}

function IntroVideoSection({ talent }: { talent: TalentProfile }) {
  if (!talent.intro_video_url || !categoryShowsIntroVideo(talent.category)) return null;

  return (
    <div className="mt-6">
      <SubmissionPreview url={talent.intro_video_url} />
    </div>
  );
}

function AttributesSection({ talent }: { talent: TalentProfile }) {
  const fields = categoryAttributeFields(talent.category);
  const filled = fields.filter((f) => talent.attributes?.[f.key]);
  if (filled.length === 0) return null;

  return (
    <dl className="mt-4 grid grid-cols-2 gap-x-6 gap-y-3 border-t border-b border-zinc-200 py-4 sm:grid-cols-3 dark:border-zinc-800">
      {filled.map((f) => (
        <div key={f.key}>
          <dt className="text-xs text-zinc-500">{f.label}</dt>
          <dd className="text-sm font-semibold text-zinc-800 dark:text-zinc-200">{talent.attributes?.[f.key]}</dd>
        </div>
      ))}
    </dl>
  );
}

function CreditsSection({ credits }: { credits: Credit[] }) {
  const groups = CREDIT_PROJECT_TYPES.map((t) => ({
    type: t,
    items: credits.filter((c) => c.project_type === t.value),
  })).filter((g) => g.items.length > 0);

  return (
    <div className="mt-5 flex flex-col gap-6">
      {groups.map((group) => (
        <div key={group.type.value}>
          <h3 className="flex items-center gap-2 text-sm font-bold uppercase tracking-wide text-zinc-500">
            <group.type.icon className="h-4 w-4" />
            {group.type.label}
          </h3>
          <ul className="mt-2 flex flex-col gap-2">
            {group.items.map((c) => (
              <li key={c.id} className="rounded-2xl border-2 border-zinc-100 p-4 text-sm dark:border-zinc-800">
                <div className="flex flex-wrap items-baseline justify-between gap-x-3">
                  <p className="font-semibold text-zinc-900 dark:text-zinc-50">
                    {c.title}
                    {c.role && <span className="font-normal text-zinc-500"> — {c.role}</span>}
                  </p>
                  {c.date_label && <span className="text-xs text-zinc-400">{c.date_label}</span>}
                </div>
                {(c.company_or_director || c.location) && (
                  <p className="mt-0.5 text-xs text-zinc-500">
                    {[c.company_or_director, c.location].filter(Boolean).join(" · ")}
                  </p>
                )}
                {c.reference_url && (
                  <a
                    href={c.reference_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-1 inline-block text-xs font-semibold text-rose-600 hover:underline"
                  >
                    View reference →
                  </a>
                )}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

function ReelCard({ reel }: { reel: Reel }) {
  const Icon = REEL_PLATFORM_ICONS[reel.platform];

  if (reel.platform === "tiktok") {
    return (
      <div>
        <TikTokEmbed url={reel.url} />
        {reel.caption && <p className="mt-2 text-sm font-semibold text-zinc-900 dark:text-zinc-50">{reel.caption}</p>}
      </div>
    );
  }

  return (
    <a
      href={reel.url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center justify-between gap-3 rounded-2xl border-2 border-zinc-100 p-4 text-sm transition-colors hover:border-rose-300 dark:border-zinc-800 dark:hover:border-rose-800"
    >
      <div className="min-w-0">
        {reel.caption && <p className="truncate font-semibold text-zinc-900 dark:text-zinc-50">{reel.caption}</p>}
        <p className="truncate text-xs text-zinc-500">{reel.url}</p>
      </div>
      <span className={`shrink-0 ${btnSmall}`}>
        {Icon && <Icon className="h-3.5 w-3.5" />} Watch on {reelPlatformLabel(reel.platform)} ↗
      </span>
    </a>
  );
}

