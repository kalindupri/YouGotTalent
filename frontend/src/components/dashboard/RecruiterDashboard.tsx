"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import {
  BarChart3,
  Building2,
  CalendarDays,
  CreditCard,
  Crown,
  Eye,
  Megaphone,
  Search,
  ShieldCheck,
  Sparkles,
  Star,
} from "lucide-react";
import {
  ApiError,
  Booking,
  CastingCall,
  RecruiterAnalytics,
  RecruiterProfile,
  RecruiterType,
  Review,
  SavedSearch,
  TALENT_CATEGORIES,
  TalentCategory,
  TalentList,
  TalentProfile,
  api,
} from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import BillingStatusPanel from "@/components/BillingStatusPanel";
import PaymentHistoryList from "@/components/PaymentHistoryList";
import {
  badgeClass,
  bookingStatusTone,
  formatBookingRange,
  btnPrimary,
  btnSecondary,
  btnSmall,
  categoryBadgeClass,
  coverPhotoUrl,
  formatCategory,
  inputClass,
  labelClass,
  neutralBadgeClass,
  premiumBadgeClass,
  recruiterTypeLabel,
  sectionClass,
  statusTone,
  verifiedBadgeClass,
} from "@/lib/ui";
import TalentAvatar from "@/components/TalentAvatar";
import BookingAgreementSection from "@/components/BookingAgreementSection";
import BookingReviewForm from "@/components/BookingReviewForm";
import DashboardSidebar, { DashboardNavItem } from "@/components/dashboard/DashboardSidebar";

function parseSkills(raw: string): string[] {
  return raw
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

type RecruiterSection = "overview" | "talent-hunts" | "discover" | "bookings" | "reviews" | "membership";

const RECRUITER_NAV_ITEMS: DashboardNavItem[] = [
  { id: "overview", label: "Overview", icon: Building2 },
  { id: "talent-hunts", label: "Talent hunts", icon: Megaphone },
  { id: "discover", label: "Discover talent", icon: Search },
  { id: "bookings", label: "Bookings", icon: CalendarDays },
  { id: "reviews", label: "Reviews", icon: Star },
  { id: "membership", label: "Membership", icon: CreditCard },
];

export default function RecruiterDashboard() {
  const { token } = useAuth();
  const [activeSection, setActiveSection] = useState<RecruiterSection>("overview");
  const [profile, setProfile] = useState<RecruiterProfile | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [myCalls, setMyCalls] = useState<CastingCall[]>([]);
  const [savedTalents, setSavedTalents] = useState<TalentProfile[]>([]);
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([]);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [analytics, setAnalytics] = useState<RecruiterAnalytics | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [talentLists, setTalentLists] = useState<TalentList[]>([]);
  const [newArrivals, setNewArrivals] = useState<TalentProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [callActionId, setCallActionId] = useState<string | null>(null);
  const [callActionError, setCallActionError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    api
      .getMyRecruiterProfile(token)
      .then(setProfile)
      .catch((err) => {
        if (err instanceof ApiError && err.status === 404) setNotFound(true);
      })
      .finally(() => setLoading(false));
  }, [token]);

  useEffect(() => {
    if (!token || !profile) return;
    api
      .listCastingCalls()
      .then((all) => setMyCalls(all.filter((c) => c.recruiter_id === profile.id)))
      .catch(() => {});
    api.listSavedTalents(token).then(setSavedTalents).catch(() => {});
    api.listSavedSearches(token).then(setSavedSearches).catch(() => {});
    api.listMyBookingsAsRecruiter(token).then(setBookings).catch(() => {});
    api.getMyAnalytics(token).then(setAnalytics).catch(() => {});
    api.listMyReviews(token).then(setReviews).catch(() => {});
    api.listMyTalentLists(token).then(setTalentLists).catch(() => {});
    api.listNewArrivals(token).then(setNewArrivals).catch(() => {});
  }, [token, profile]);

  async function handleDeleteSavedSearch(id: string) {
    if (!token) return;
    await api.deleteSavedSearch(id, token);
    setSavedSearches((prev) => prev.filter((s) => s.id !== id));
  }

  async function handleAddToList(listId: string, talentId: string) {
    if (!token) return;
    const member = await api.addTalentToList(listId, { talent_id: talentId }, token);
    setTalentLists((prev) => prev.map((l) => (l.id === listId ? { ...l, members: [...l.members, member] } : l)));
  }

  async function handleToggleCallStatus(call: CastingCall) {
    if (!token) return;
    setCallActionError(null);
    setCallActionId(call.id);
    try {
      const nextStatus = call.status === "open" ? "closed" : "open";
      const updated = await api.updateCastingCall(call.id, { status: nextStatus }, token);
      setMyCalls((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
    } catch {
      setCallActionError("Could not update that talent hunt's status.");
    } finally {
      setCallActionId(null);
    }
  }

  async function handleDeleteCall(callId: string) {
    if (!token) return;
    if (!window.confirm("Delete this talent hunt? Applications and invitations for it will be removed too.")) return;
    setCallActionError(null);
    setCallActionId(callId);
    try {
      await api.deleteCastingCall(callId, token);
      setMyCalls((prev) => prev.filter((c) => c.id !== callId));
    } catch {
      setCallActionError("Could not delete that talent hunt.");
    } finally {
      setCallActionId(null);
    }
  }

  if (loading) return <p className="text-sm text-zinc-500">Loading…</p>;

  if (notFound || !profile) {
    return (
      <CreateRecruiterProfileForm
        token={token!}
        onCreated={(p) => {
          setProfile(p);
          setNotFound(false);
        }}
      />
    );
  }

  return (
    <div className="flex flex-col gap-6 lg:flex-row lg:items-start">
      <DashboardSidebar
        items={RECRUITER_NAV_ITEMS}
        activeId={activeSection}
        onSelect={(id) => setActiveSection(id as RecruiterSection)}
      />
      <div className="flex min-w-0 flex-1 flex-col gap-6">
        {activeSection === "overview" && (
          <>
            <section className={sectionClass}>
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-center gap-4">
                  <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-sm bg-rose-600 text-lg font-black text-white">
                    {profile.company_name.slice(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">{profile.company_name}</h2>
                      <span className={neutralBadgeClass}>{recruiterTypeLabel(profile.recruiter_type)}</span>
                      {profile.is_verified && (
                        <span className={verifiedBadgeClass}>
                          <ShieldCheck className="h-3 w-3" /> Verified
                        </span>
                      )}
                      {profile.tier === "premium" && (
                        <span className={premiumBadgeClass}>
                          <Crown className="h-3 w-3" fill="currentColor" strokeWidth={0} /> Premium
                        </span>
                      )}
                    </div>
                    {profile.industry && <p className="mt-0.5 text-sm text-zinc-500">{profile.industry}</p>}
                  </div>
                </div>
                <Link href={`/recruiters/${profile.id}`} className={`${btnSmall} self-start sm:self-auto`}>
                  View public page
                </Link>
              </div>
            </section>

            {analytics && (
              <section className={sectionClass}>
                <h2 className="flex items-center gap-2 font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">
                  <BarChart3 className="h-5 w-5" /> Analytics
                </h2>
                <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
                  <div className="rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
                    <p className="font-heading text-2xl font-black text-zinc-900 dark:text-zinc-50">{analytics.total_views}</p>
                    <p className="mt-1 text-xs text-zinc-500">Total views</p>
                  </div>
                  <div className="rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
                    <p className="font-heading text-2xl font-black text-zinc-900 dark:text-zinc-50">
                      {analytics.total_applications}
                    </p>
                    <p className="mt-1 text-xs text-zinc-500">Total applications</p>
                  </div>
                  <div className="rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
                    <p className="font-heading text-2xl font-black text-zinc-900 dark:text-zinc-50">
                      {analytics.response_rate}%
                    </p>
                    <p className="mt-1 text-xs text-zinc-500">Response rate</p>
                  </div>
                </div>

                {analytics.casting_calls.length > 0 && (
                  <ul className="mt-4 flex flex-col gap-2">
                    {analytics.casting_calls.map((c) => (
                      <li key={c.id} className="rounded-lg border border-zinc-200 p-3 text-sm dark:border-zinc-800">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <span className="font-semibold text-zinc-900 dark:text-zinc-50">{c.title}</span>
                          <span className={badgeClass(statusTone(c.status))}>{c.status}</span>
                        </div>
                        <div className="mt-1.5 flex flex-wrap items-center gap-3 text-xs text-zinc-500">
                          <span className="flex items-center gap-1">
                            <Eye className="h-3.5 w-3.5" /> {c.view_count} views
                          </span>
                          <span>{c.application_count} applications</span>
                          <span>{c.pending_count} pending</span>
                          <span>{c.shortlisted_count} shortlisted</span>
                          <span>{c.accepted_count} accepted</span>
                          <span>{c.rejected_count} rejected</span>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            )}
          </>
        )}

        {activeSection === "talent-hunts" && (
          <>
            <PostCastingCallForm token={token!} isPremium={profile.tier === "premium"} onPosted={(c) => setMyCalls((prev) => [c, ...prev])} />

            <section className={sectionClass}>
              <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Your talent hunts</h2>
              {callActionError && <p className="mt-2 text-sm text-red-600">{callActionError}</p>}
              {myCalls.length === 0 ? (
                <p className="mt-2 text-sm text-zinc-500">You haven&apos;t posted any talent hunts yet.</p>
              ) : (
                <ul className="mt-4 flex flex-col gap-2">
                  {myCalls.map((c) => (
                    <li
                      key={c.id}
                      className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border-2 border-zinc-100 px-4 py-3 text-sm dark:border-zinc-800"
                    >
                      <div>
                        <p className="font-semibold text-zinc-900 dark:text-zinc-50">{c.title}</p>
                        <div className="mt-1.5 flex items-center gap-2">
                          <span className={categoryBadgeClass(c.category)}>{formatCategory(c.category)}</span>
                          <span className={badgeClass(statusTone(c.status))}>{c.status}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <Link href={`/dashboard/casting-calls/${c.id}`} className="font-semibold text-rose-600 hover:underline">
                          Manage
                        </Link>
                        <button
                          type="button"
                          disabled={callActionId === c.id}
                          onClick={() => handleToggleCallStatus(c)}
                          className="font-semibold text-zinc-600 hover:underline disabled:opacity-50 dark:text-zinc-300"
                        >
                          {c.status === "open" ? "Close" : "Reopen"}
                        </button>
                        <button
                          type="button"
                          disabled={callActionId === c.id}
                          onClick={() => handleDeleteCall(c.id)}
                          className="font-semibold text-zinc-500 hover:text-red-600 hover:underline disabled:opacity-50"
                        >
                          Delete
                        </button>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </>
        )}

        {activeSection === "discover" && (
          <>
            {profile.tier === "premium" && newArrivals.length > 0 && (
              <section className={sectionClass}>
                <h2 className="flex items-center gap-2 font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">
                  <Sparkles className="h-5 w-5" /> New talent this week
                </h2>
                <p className="mt-1 text-sm text-zinc-500">
                  Fresh sign-ups in your posted categories, from the last 48 hours — a premium early look.
                </p>
                <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
                  {newArrivals.map((t) => (
                    <Link
                      key={t.id}
                      href={`/talents/${t.id}`}
                      className="overflow-hidden rounded-2xl border-2 border-zinc-100 dark:border-zinc-800"
                    >
                      <div className="aspect-square overflow-hidden bg-zinc-100 dark:bg-zinc-900">
                        <TalentAvatar name={t.display_name} coverUrl={coverPhotoUrl(t.media)} className="h-full w-full text-xl" />
                      </div>
                      <div className="p-2">
                        <p className="truncate text-xs font-medium text-zinc-900 dark:text-zinc-50">{t.display_name}</p>
                      </div>
                    </Link>
                  ))}
                </div>
              </section>
            )}

            <section className={sectionClass}>
              <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Saved talent</h2>
              {savedTalents.length === 0 ? (
                <p className="mt-2 text-sm text-zinc-500">
                  No saved talent yet — browse{" "}
                  <Link href="/talents" className="text-rose-600 hover:underline">
                    talent profiles
                  </Link>{" "}
                  and save the ones you like.
                </p>
              ) : (
                <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
                  {savedTalents.map((t) => (
                    <div key={t.id} className="overflow-hidden rounded-2xl border-2 border-zinc-100 dark:border-zinc-800">
                      <Link href={`/talents/${t.id}`} className="block">
                        <div className="aspect-square overflow-hidden bg-zinc-100 dark:bg-zinc-900">
                          <TalentAvatar name={t.display_name} coverUrl={coverPhotoUrl(t.media)} className="h-full w-full text-xl" />
                        </div>
                        <div className="p-2 pb-1">
                          <p className="truncate text-xs font-medium text-zinc-900 dark:text-zinc-50">{t.display_name}</p>
                        </div>
                      </Link>
                      {profile.tier === "premium" && talentLists.length > 0 && (
                        <select
                          defaultValue=""
                          onChange={(e) => {
                            if (e.target.value) handleAddToList(e.target.value, t.id);
                            e.target.value = "";
                          }}
                          className="w-full border-t border-zinc-100 bg-transparent px-2 py-1.5 text-[11px] text-zinc-500 dark:border-zinc-800"
                        >
                          <option value="">Add to list…</option>
                          {talentLists.map((l) => (
                            <option key={l.id} value={l.id} disabled={l.members.some((m) => m.talent_id === t.id)}>
                              {l.name}
                            </option>
                          ))}
                        </select>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </section>

            <TalentListsCard
              profile={profile}
              lists={talentLists}
              onCreated={(l) => setTalentLists((prev) => [l, ...prev])}
              onDeleted={(id) => setTalentLists((prev) => prev.filter((l) => l.id !== id))}
              onUpdated={(updated) => setTalentLists((prev) => prev.map((l) => (l.id === updated.id ? updated : l)))}
              token={token!}
            />

            <section className={sectionClass}>
              <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Saved searches</h2>
              {profile.tier !== "premium" ? (
                <p className="mt-2 text-sm text-zinc-500">
                  Saved searches are a Premium feature — upgrade above to save filters and get back to
                  matching talent instantly.
                </p>
              ) : savedSearches.length === 0 ? (
                <p className="mt-2 text-sm text-zinc-500">
                  No saved searches yet — use the advanced filters on the{" "}
                  <Link href="/talents" className="text-rose-600 hover:underline">
                    browse talent
                  </Link>{" "}
                  page and save one.
                </p>
              ) : (
                <ul className="mt-4 flex flex-col gap-2">
                  {savedSearches.map((s) => {
                    const qs = new URLSearchParams();
                    if (s.category) qs.set("categories", s.category);
                    if (s.city) qs.set("city", s.city);
                    if (s.q) qs.set("q", s.q);
                    if (s.experience_min !== null) qs.set("experience_min", String(s.experience_min));
                    if (s.experience_max !== null) qs.set("experience_max", String(s.experience_max));
                    if (s.verified_only) qs.set("verified_only", "true");
                    return (
                      <li
                        key={s.id}
                        className="flex items-center justify-between rounded-2xl border-2 border-zinc-100 px-4 py-3 text-sm dark:border-zinc-800"
                      >
                        <Link href={`/talents?${qs.toString()}`} className="font-semibold text-rose-600 hover:underline">
                          {s.name}
                        </Link>
                        <button onClick={() => handleDeleteSavedSearch(s.id)} className={btnSmall}>
                          Delete
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )}
            </section>
          </>
        )}

        {activeSection === "bookings" && (
          <section className={sectionClass}>
            <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">My booking requests</h2>
            {bookings.length === 0 ? (
              <p className="mt-2 text-sm text-zinc-500">
                No booking requests yet — request a time slot from a talent&apos;s public profile once they&apos;ve set
                their availability.
              </p>
            ) : (
              <ul className="mt-4 flex flex-col gap-3">
                {bookings.map((b) => (
                  <li key={b.id} className="rounded-lg border border-zinc-200 p-4 text-sm dark:border-zinc-800">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div>
                        <p className="font-semibold text-zinc-900 dark:text-zinc-50">{b.talent_display_name}</p>
                        {b.casting_call_title && <p className="text-xs text-zinc-500">{b.casting_call_title}</p>}
                        {b.start_at && b.end_at ? (
                          <p className="mt-1 text-zinc-600 dark:text-zinc-400">{formatBookingRange(b.start_at, b.end_at)}</p>
                        ) : (
                          b.application_id && (
                            <p className="mt-1 text-[11px] font-bold uppercase tracking-wide text-amber-600 dark:text-amber-400">
                              Contract offer{b.application_role_title ? ` — ${b.application_role_title}` : ""}
                            </p>
                          )
                        )}
                      </div>
                      <span className={badgeClass(bookingStatusTone(b.status))}>{b.status}</span>
                    </div>
                    {b.message && <p className="mt-2 text-zinc-600 dark:text-zinc-400">&ldquo;{b.message}&rdquo;</p>}
                    {b.status === "pending" && (
                      <CancelBookingButton
                        booking={b}
                        token={token!}
                        onCancelled={(updated) => setBookings((prev) => prev.map((x) => (x.id === updated.id ? updated : x)))}
                      />
                    )}
                    {b.status === "accepted" && (
                      <BookingAgreementSection
                        booking={b}
                        token={token!}
                        viewerRole="recruiter"
                        otherPartyLabel={b.talent_display_name}
                        onUpdated={(updated) => setBookings((prev) => prev.map((x) => (x.id === updated.id ? updated : x)))}
                      />
                    )}
                    {b.status === "accepted" && (
                      <BookingReviewForm bookingId={b.id} token={token!} revieweeLabel={b.talent_display_name} />
                    )}
                  </li>
                ))}
              </ul>
            )}
          </section>
        )}

        {activeSection === "reviews" && (
          <section className={sectionClass}>
            <h2 className="flex items-center gap-2 font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">
              <Star className="h-5 w-5" /> Reviews received
            </h2>
            {reviews.length === 0 ? (
              <p className="mt-2 text-sm text-zinc-500">
                No reviews yet — talent can rate you once a booking with them is accepted.
              </p>
            ) : (
              <ul className="mt-4 flex flex-col gap-3">
                {reviews.map((r) => (
                  <li key={r.id} className="rounded-lg border border-zinc-200 p-4 text-sm dark:border-zinc-800">
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
            )}
          </section>
        )}

        {activeSection === "membership" && <MembershipCard profile={profile} onUpdated={setProfile} token={token!} />}
      </div>
    </div>
  );
}

function CancelBookingButton({
  booking,
  token,
  onCancelled,
}: {
  booking: Booking;
  token: string;
  onCancelled: (updated: Booking) => void;
}) {
  const [submitting, setSubmitting] = useState(false);

  async function handleCancel() {
    setSubmitting(true);
    try {
      const updated = await api.cancelBooking(booking.id, token);
      onCancelled(updated);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mt-3">
      <button onClick={handleCancel} disabled={submitting} className={btnSmall}>
        {submitting ? "Cancelling…" : "Cancel request"}
      </button>
    </div>
  );
}

function MembershipCard({
  profile,
  onUpdated,
  token,
}: {
  profile: RecruiterProfile;
  onUpdated: (p: RecruiterProfile) => void;
  token: string;
}) {
  const [requestingVerification, setRequestingVerification] = useState(false);
  const [upgrading, setUpgrading] = useState(false);

  async function handleRequestVerification() {
    setRequestingVerification(true);
    try {
      onUpdated(await api.requestRecruiterVerification(token));
    } finally {
      setRequestingVerification(false);
    }
  }

  async function handleUpgrade() {
    setUpgrading(true);
    try {
      onUpdated(await api.upgradeRecruiterTier(token));
    } finally {
      setUpgrading(false);
    }
  }

  return (
    <section className={sectionClass}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Membership</h2>
          <p className="mt-1 text-sm text-zinc-500">
            {profile.tier === "premium"
              ? "You're on Premium — unlimited postings, AI match scoring, talent CRM lists, bulk invite, early access, and exclusive calls."
              : "Free plan: up to 2 open talent hunts at a time. Upgrade for unlimited postings, AI match scoring, talent CRM lists, bulk invite, early access, and exclusive calls."}
          </p>
        </div>
        <span className={profile.tier === "premium" ? premiumBadgeClass : badgeClass("neutral")}>
          {profile.tier === "premium" ? (
            <>
              <Crown className="h-3 w-3" fill="currentColor" strokeWidth={0} /> Premium
            </>
          ) : (
            "Free plan"
          )}
        </span>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        {profile.tier !== "premium" && (
          <>
            <button onClick={handleUpgrade} disabled={upgrading} className={btnPrimary}>
              {upgrading ? (
                "Starting…"
              ) : (
                <>
                  <Crown className="h-4 w-4" /> Start free trial
                </>
              )}
            </button>
            <Link href="/pricing" className="text-xs font-semibold text-rose-600 hover:underline">
              View pricing &amp; subscribe →
            </Link>
          </>
        )}
        {!profile.is_verified &&
          (profile.verification_requested_at ? (
            <span className="self-center text-sm text-zinc-500">
              Verification requested — we&apos;ll review it soon.
            </span>
          ) : (
            <button onClick={handleRequestVerification} disabled={requestingVerification} className={btnSecondary}>
              {requestingVerification ? (
                "Requesting…"
              ) : (
                <>
                  <ShieldCheck className="h-4 w-4" /> Request verification
                </>
              )}
            </button>
          ))}
      </div>
      <BillingStatusPanel
        token={token}
        refreshKey={profile.tier}
        onCanceled={() => api.getMyRecruiterProfile(token).then(onUpdated)}
      />
      <PaymentHistoryList token={token} />
      <p className="mt-3 text-xs text-zinc-400">Verification is reviewed manually for now.</p>
    </section>
  );
}

function TalentListsCard({
  profile,
  lists,
  token,
  onCreated,
  onDeleted,
  onUpdated,
}: {
  profile: RecruiterProfile;
  lists: TalentList[];
  token: string;
  onCreated: (l: TalentList) => void;
  onDeleted: (id: string) => void;
  onUpdated: (l: TalentList) => void;
}) {
  const [name, setName] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setError(null);
    setCreating(true);
    try {
      const list = await api.createTalentList(name.trim(), token);
      onCreated(list);
      setName("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create this list.");
    } finally {
      setCreating(false);
    }
  }

  async function handleRemoveMember(listId: string, member: TalentList["members"][number]) {
    await api.removeTalentFromList(listId, member.id, token);
    const list = lists.find((l) => l.id === listId);
    if (list) onUpdated({ ...list, members: list.members.filter((m) => m.id !== member.id) });
  }

  return (
    <section className={sectionClass}>
      <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Talent lists</h2>
      {profile.tier !== "premium" ? (
        <p className="mt-2 text-sm text-zinc-500">
          Talent lists are a Premium feature — upgrade above to organize candidates into named lists per
          project, with notes on each.
        </p>
      ) : (
        <>
          <form onSubmit={handleCreate} className="mt-4 flex flex-wrap gap-2">
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Monsoon Diaries — Lead"
              className={`${inputClass} max-w-xs`}
            />
            <button type="submit" disabled={creating || !name.trim()} className={btnSmall}>
              {creating ? "Adding…" : "+ New list"}
            </button>
          </form>
          {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
          {lists.length === 0 ? (
            <p className="mt-4 text-sm text-zinc-500">
              No lists yet — create one above, then add saved talent to it from the list above.
            </p>
          ) : (
            <div className="mt-4 flex flex-col gap-3">
              {lists.map((l) => (
                <div key={l.id} className="rounded-2xl border-2 border-zinc-100 p-4 dark:border-zinc-800">
                  <div className="flex items-center justify-between">
                    <p className="font-semibold text-zinc-900 dark:text-zinc-50">
                      {l.name} <span className="text-xs font-normal text-zinc-500">· {l.members.length}</span>
                    </p>
                    <button
                      onClick={async () => {
                        await api.deleteTalentList(l.id, token);
                        onDeleted(l.id);
                      }}
                      className={btnSmall}
                    >
                      Delete list
                    </button>
                  </div>
                  {l.members.length > 0 && (
                    <ul className="mt-3 flex flex-col gap-1.5">
                      {l.members.map((m) => (
                        <li key={m.id} className="flex items-center justify-between gap-2 text-sm">
                          <Link href={`/talents/${m.talent_id}`} className="font-medium text-rose-600 hover:underline">
                            {m.talent_display_name}
                          </Link>
                          <button onClick={() => handleRemoveMember(l.id, m)} className="text-xs text-zinc-400 hover:text-red-600">
                            Remove
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </section>
  );
}

function CreateRecruiterProfileForm({
  token,
  onCreated,
}: {
  token: string;
  onCreated: (p: RecruiterProfile) => void;
}) {
  const [recruiterType, setRecruiterType] = useState<RecruiterType>("agency");
  const [companyName, setCompanyName] = useState("");
  const [industry, setIndustry] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const profile = await api.createMyRecruiterProfile(
        { company_name: companyName, recruiter_type: recruiterType, industry: industry || undefined },
        token
      );
      onCreated(profile);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create your organizer profile.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className={sectionClass}>
      <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Set up your organizer profile</h2>
      <p className="mt-1 text-sm text-zinc-500">This is required before you can post talent hunts.</p>
      <form onSubmit={handleSubmit} className="mt-5 flex max-w-md flex-col gap-4">
        <fieldset className="grid grid-cols-2 gap-2">
          {(["individual", "agency"] as const).map((t) => (
            <button
              type="button"
              key={t}
              onClick={() => setRecruiterType(t)}
              className={`rounded-md border-2 px-3 py-2 text-sm font-medium capitalize transition-colors ${
                recruiterType === t
                  ? "border-rose-600 bg-rose-600 text-white"
                  : "border-zinc-200 text-zinc-700 hover:border-rose-300 hover:bg-rose-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:border-rose-800 dark:hover:bg-rose-950"
              }`}
            >
              {t}
            </button>
          ))}
        </fieldset>
        <label className={labelClass}>
          {recruiterType === "individual" ? "Your name" : "Company / agency name"}
          <input required value={companyName} onChange={(e) => setCompanyName(e.target.value)} className={inputClass} />
        </label>
        <label className={labelClass}>
          Industry
          <input
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
            placeholder="e.g. Film, Music, Publishing, Theatre"
            className={inputClass}
          />
        </label>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button type="submit" disabled={submitting} className={`w-fit ${btnPrimary}`}>
          {submitting ? "Creating…" : "Create profile"}
        </button>
      </form>
    </div>
  );
}

interface RoleDraft {
  title: string;
  criteria: string;
  category: TalentCategory | "";
  compensation: string;
  guideTrackUrl: string;
  uploadingGuide: boolean;
}

function emptyRole(): RoleDraft {
  return {
    title: "",
    criteria: "",
    category: "",
    compensation: "",
    guideTrackUrl: "",
    uploadingGuide: false,
  };
}

function PostCastingCallForm({
  token,
  isPremium,
  onPosted,
}: {
  token: string;
  isPremium: boolean;
  onPosted: (c: CastingCall) => void;
}) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState<TalentCategory>("acting");
  const [location, setLocation] = useState("");
  const [compensation, setCompensation] = useState("");
  const [auditionBrief, setAuditionBrief] = useState("");
  const [auditionReferenceUrl, setAuditionReferenceUrl] = useState("");
  const [tagsInput, setTagsInput] = useState("");
  const [shootDetails, setShootDetails] = useState("");
  const [premiumTalentOnly, setPremiumTalentOnly] = useState(false);
  const [roles, setRoles] = useState<RoleDraft[]>([emptyRole()]);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function updateRole(index: number, patch: Partial<RoleDraft>) {
    setRoles((prev) => prev.map((r, i) => (i === index ? { ...r, ...patch } : r)));
  }

  async function handleTrackUpload(index: number, file: File) {
    updateRole(index, { uploadingGuide: true });
    setError(null);
    try {
      const { url } = await api.uploadAuditionTrack(file, token);
      updateRole(index, { guideTrackUrl: url, uploadingGuide: false });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not upload this track.");
      updateRole(index, { uploadingGuide: false });
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const call = await api.createCastingCall(
        {
          title,
          description,
          category,
          location: location || undefined,
          compensation: compensation || undefined,
          audition_brief: auditionBrief || undefined,
          audition_reference_url: auditionReferenceUrl || undefined,
          tags: parseSkills(tagsInput).length > 0 ? parseSkills(tagsInput) : undefined,
          shoot_details: shootDetails || undefined,
          premium_talent_only: premiumTalentOnly,
          roles: roles.map((r) => ({
            title: r.title.trim() || title,
            criteria: r.criteria.trim() || undefined,
            category: r.category || category,
            compensation: r.compensation.trim() || undefined,
            guide_track_url: r.guideTrackUrl || undefined,
          })),
        },
        token
      );
      onPosted(call);
      setTitle("");
      setDescription("");
      setLocation("");
      setCompensation("");
      setAuditionBrief("");
      setAuditionReferenceUrl("");
      setTagsInput("");
      setShootDetails("");
      setPremiumTalentOnly(false);
      setRoles([emptyRole()]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not post this talent hunt.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className={sectionClass}>
      <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Post a talent hunt</h2>
      <form onSubmit={handleSubmit} className="mt-5 flex max-w-md flex-col gap-4">
        <label className={labelClass}>
          Title
          <input required value={title} onChange={(e) => setTitle(e.target.value)} className={inputClass} />
        </label>
        <label className={labelClass}>
          Category
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value as TalentCategory)}
            className={inputClass}
          >
            {TALENT_CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {formatCategory(c)}
              </option>
            ))}
          </select>
        </label>
        <label className={labelClass}>
          Description
          <textarea
            required
            rows={4}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className={inputClass}
          />
        </label>
        <label className={labelClass}>
          Location
          <input value={location} onChange={(e) => setLocation(e.target.value)} className={inputClass} />
        </label>
        <label className={labelClass}>
          Compensation
          <input
            value={compensation}
            onChange={(e) => setCompensation(e.target.value)}
            placeholder="e.g. LKR 15,000/day"
            className={inputClass}
          />
        </label>
        <label className={labelClass}>
          What should they perform? (optional)
          <textarea
            rows={3}
            value={auditionBrief}
            onChange={(e) => setAuditionBrief(e.target.value)}
            placeholder="e.g. Record yourself performing this monologue, 60 seconds max"
            className={inputClass}
          />
        </label>
        <label className={labelClass}>
          Reference material link (optional)
          <input
            type="url"
            value={auditionReferenceUrl}
            onChange={(e) => setAuditionReferenceUrl(e.target.value)}
            placeholder="https://… (script, sheet music, reference video)"
            className={inputClass}
          />
        </label>
        <label className={labelClass}>
          Tags (comma separated, optional)
          <input
            value={tagsInput}
            onChange={(e) => setTagsInput(e.target.value)}
            placeholder="e.g. Product Demo / Explainer Video"
            className={inputClass}
          />
        </label>
        <label className={labelClass}>
          Dates & locations (optional)
          <input
            value={shootDetails}
            onChange={(e) => setShootDetails(e.target.value)}
            placeholder="e.g. Shoots remotely at home."
            className={inputClass}
          />
        </label>
        {isPremium ? (
          <label className="flex items-center gap-2 text-sm font-medium text-zinc-700 dark:text-zinc-300">
            <input
              type="checkbox"
              checked={premiumTalentOnly}
              onChange={(e) => setPremiumTalentOnly(e.target.checked)}
              className="accent-rose-600"
            />
            Premium talent only
          </label>
        ) : (
          <p className="text-xs text-zinc-400">
            Upgrade to Premium to restrict this posting to Premium talent only.
          </p>
        )}

        <div className="flex flex-col gap-3 rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
          <div>
            <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">Roles in this project</p>
            <p className="mt-0.5 text-xs text-zinc-500">
              Add one role for a single-position job, or several roles talent can apply to independently.
            </p>
          </div>
          {roles.map((role, i) => (
            <div key={i} className="flex flex-col gap-2 rounded-lg border border-zinc-200 p-3 dark:border-zinc-800">
              <div className="flex items-center justify-between gap-2">
                <input
                  value={role.title}
                  onChange={(e) => updateRole(i, { title: e.target.value })}
                  placeholder={`Role title (defaults to "${title || "job title"}")`}
                  className={inputClass}
                />
                {roles.length > 1 && (
                  <button
                    type="button"
                    onClick={() => setRoles((prev) => prev.filter((_, idx) => idx !== i))}
                    className={btnSmall}
                  >
                    Remove
                  </button>
                )}
              </div>
              <input
                value={role.criteria}
                onChange={(e) => updateRole(i, { criteria: e.target.value })}
                placeholder="Criteria, e.g. Content Creators, Female, 18+"
                className={inputClass}
              />
              <div className="flex gap-2">
                <select
                  value={role.category}
                  onChange={(e) => updateRole(i, { category: e.target.value as TalentCategory })}
                  className={inputClass}
                >
                  <option value="">Same as job category</option>
                  {TALENT_CATEGORIES.map((c) => (
                    <option key={c} value={c}>
                      {formatCategory(c)}
                    </option>
                  ))}
                </select>
                <input
                  value={role.compensation}
                  onChange={(e) => updateRole(i, { compensation: e.target.value })}
                  placeholder="Pay for this role (optional)"
                  className={inputClass}
                />
              </div>
              {(role.category || category) === "singing" && (
                <div className="flex flex-col gap-2 rounded-md border border-dashed border-zinc-300 p-3 dark:border-zinc-700">
                  <p className="text-xs font-semibold text-zinc-700 dark:text-zinc-300">
                    Guided audition (optional) — up to 30 seconds
                  </p>
                  <label className={labelClass}>
                    Guide track (a sample for talent to learn from before recording their own take)
                    <input
                      type="file"
                      accept="audio/*"
                      disabled={role.uploadingGuide}
                      onChange={(e) => e.target.files?.[0] && handleTrackUpload(i, e.target.files[0])}
                      className={inputClass}
                    />
                    {role.uploadingGuide && <span className="text-xs text-zinc-500">Uploading…</span>}
                    {role.guideTrackUrl && !role.uploadingGuide && <span className="text-xs text-emerald-600">Uploaded ✓</span>}
                  </label>
                </div>
              )}
            </div>
          ))}
          {isPremium ? (
            <button
              type="button"
              onClick={() => setRoles((prev) => [...prev, emptyRole()])}
              className={`w-fit ${btnSmall}`}
            >
              + Add another role
            </button>
          ) : (
            <p className="text-xs text-zinc-400">
              Posting multiple roles in one talent hunt is a Premium feature — upgrade above to add more.
            </p>
          )}
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}
        <button type="submit" disabled={submitting} className={`w-fit ${btnPrimary}`}>
          {submitting ? "Posting…" : "Post talent hunt"}
        </button>
      </form>
    </section>
  );
}
