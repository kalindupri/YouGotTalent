"use client";

import { FormEvent, createElement, useEffect, useState } from "react";
import Link from "next/link";
import { Check, Crown, FileCheck2, Plus, ShieldCheck, Trash2, X } from "lucide-react";
import {
  Application,
  ApiError,
  AvailabilityWindow,
  Booking,
  Credit,
  CreditProjectType,
  Follow,
  Invitation,
  Media,
  MediaType,
  TALENT_CATEGORIES,
  TalentCategory,
  TalentProfile,
  api,
} from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import BillingStatusPanel from "@/components/BillingStatusPanel";
import {
  CREDIT_PROJECT_TYPES,
  DAYS_OF_WEEK,
  SOCIAL_LINK_FIELDS,
  SocialLinkKey,
  badgeClass,
  bookingStatusTone,
  formatBookingRange,
  btnPrimary,
  btnSecondary,
  btnSmall,
  categoryAttributeFields,
  categoryBadgeClass,
  categoryShowsIntroVideo,
  coverPhotoUrl,
  creditProjectTypeIcon,
  creditProjectTypeLabel,
  formatCategory,
  formatTimeOfDay,
  inputClass,
  invitationStatusTone,
  labelClass,
  premiumBadgeClass,
  sectionClass,
  skillsQuestion,
  statusTone,
  verifiedBadgeClass,
} from "@/lib/ui";
import TalentAvatar from "@/components/TalentAvatar";
import BookingReviewForm from "@/components/BookingReviewForm";
import MediaCard from "@/components/MediaCard";
import HeadshotUploader from "@/components/HeadshotUploader";
import SubmissionPreview from "@/components/SubmissionPreview";

function parseSkills(raw: string): string[] {
  return raw
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

export default function TalentDashboard() {
  const { token } = useAuth();
  const [profile, setProfile] = useState<TalentProfile | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [applications, setApplications] = useState<Application[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [availability, setAvailability] = useState<AvailabilityWindow[]>([]);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [following, setFollowing] = useState<Follow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    api
      .getMyTalentProfile(token)
      .then((p) => setProfile(p))
      .catch((err) => {
        if (err instanceof ApiError && err.status === 404) setNotFound(true);
      })
      .finally(() => setLoading(false));
  }, [token]);

  useEffect(() => {
    if (!token || !profile) return;
    api.listMyApplications(token).then(setApplications).catch(() => {});
    api.listMyInvitations(token).then(setInvitations).catch(() => {});
    api.listMyAvailability(token).then(setAvailability).catch(() => {});
    api.listMyBookingsAsTalent(token).then(setBookings).catch(() => {});
    api.listMyFollowing(token).then(setFollowing).catch(() => {});
  }, [token, profile]);

  async function handleUnfollow(recruiterId: string) {
    if (!token) return;
    await api.unfollowRecruiter(recruiterId, token);
    setFollowing((prev) => prev.filter((f) => f.recruiter_id !== recruiterId));
  }

  if (loading) return <p className="text-sm text-zinc-500">Loading…</p>;

  if (notFound || !profile) {
    return (
      <CreateProfileForm
        token={token!}
        onCreated={(p) => {
          setProfile(p);
          setNotFound(false);
        }}
      />
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <ProfileSummary profile={profile} onUpdated={setProfile} token={token!} />
      <MembershipCard profile={profile} onUpdated={setProfile} token={token!} />
      <NotificationPreferencesCard profile={profile} onUpdated={setProfile} token={token!} />
      <IntroVideoCard profile={profile} onUpdated={setProfile} token={token!} />
      <SocialLinksCard profile={profile} onUpdated={setProfile} token={token!} />
      <AttributesCard profile={profile} onUpdated={setProfile} token={token!} />
      <CreditsCard profile={profile} onUpdated={setProfile} token={token!} />
      <MediaGalleryCard profile={profile} />
      <AddMediaForm
        token={token!}
        profile={profile}
        onAdded={(m) => setProfile({ ...profile, media: [...profile.media, m] })}
      />

      <section className={sectionClass}>
        <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Invitations</h2>
        {invitations.length === 0 ? (
          <p className="mt-2 text-sm text-zinc-500">
            No invitations yet — talent hunts can invite you directly to a role from your profile.
          </p>
        ) : (
          <ul className="mt-4 flex flex-col gap-3">
            {invitations.map((inv) => (
              <li key={inv.id} className="rounded-lg border border-zinc-200 p-4 text-sm dark:border-zinc-800">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <Link
                      href={`/casting-calls/${inv.casting_call_id}`}
                      className="font-semibold text-rose-600 hover:underline"
                    >
                      {inv.casting_call.title}
                    </Link>
                    <div className="mt-1 flex flex-wrap items-center gap-2">
                      <span className={categoryBadgeClass(inv.casting_call.category)}>
                        {formatCategory(inv.casting_call.category)}
                      </span>
                      {inv.casting_call.location && (
                        <span className="text-xs text-zinc-500">{inv.casting_call.location}</span>
                      )}
                    </div>
                  </div>
                  <span className={badgeClass(invitationStatusTone(inv.status))}>{inv.status}</span>
                </div>
                {inv.message && <p className="mt-2 text-zinc-600 dark:text-zinc-400">&ldquo;{inv.message}&rdquo;</p>}
                {inv.status === "pending" && (
                  <InvitationResponseButtons
                    invitation={inv}
                    token={token!}
                    onResponded={(updated) =>
                      setInvitations((prev) => prev.map((i) => (i.id === updated.id ? updated : i)))
                    }
                  />
                )}
              </li>
            ))}
          </ul>
        )}
      </section>

      <AvailabilityCard availability={availability} onChange={setAvailability} token={token!} />

      <section className={sectionClass}>
        <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Booking requests</h2>
        {bookings.length === 0 ? (
          <p className="mt-2 text-sm text-zinc-500">
            No booking requests yet — talent hunters can request a time slot from your public profile once
            you&apos;ve set your availability above.
          </p>
        ) : (
          <ul className="mt-4 flex flex-col gap-3">
            {bookings.map((b) => (
              <li key={b.id} className="rounded-lg border border-zinc-200 p-4 text-sm dark:border-zinc-800">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <p className="font-semibold text-zinc-900 dark:text-zinc-50">{b.recruiter_company_name}</p>
                    {b.casting_call_title && <p className="text-xs text-zinc-500">{b.casting_call_title}</p>}
                    <p className="mt-1 text-zinc-600 dark:text-zinc-400">{formatBookingRange(b.start_at, b.end_at)}</p>
                  </div>
                  <span className={badgeClass(bookingStatusTone(b.status))}>{b.status}</span>
                </div>
                {b.message && <p className="mt-2 text-zinc-600 dark:text-zinc-400">&ldquo;{b.message}&rdquo;</p>}
                {b.status === "pending" && (
                  <BookingResponseButtons
                    booking={b}
                    token={token!}
                    onResponded={(updated) => setBookings((prev) => prev.map((x) => (x.id === updated.id ? updated : x)))}
                  />
                )}
                {b.status === "accepted" && (
                  <AgreementSection
                    booking={b}
                    token={token!}
                    onUpdated={(updated) => setBookings((prev) => prev.map((x) => (x.id === updated.id ? updated : x)))}
                  />
                )}
                {b.status === "accepted" && (
                  <BookingReviewForm bookingId={b.id} token={token!} revieweeLabel={b.recruiter_company_name} />
                )}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className={sectionClass}>
        <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Following</h2>
        {following.length === 0 ? (
          <p className="mt-2 text-sm text-zinc-500">
            You&apos;re not following any talent hunters yet — follow one from a talent hunt&apos;s page to hear
            about their new postings.
          </p>
        ) : (
          <ul className="mt-4 flex flex-col gap-2">
            {following.map((f) => (
              <li
                key={f.id}
                className="flex items-center justify-between rounded-lg border border-zinc-200 px-4 py-3 text-sm dark:border-zinc-800"
              >
                <span className="font-semibold text-zinc-900 dark:text-zinc-50">{f.recruiter_company_name}</span>
                <button onClick={() => handleUnfollow(f.recruiter_id)} className={btnSmall}>
                  Unfollow
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className={sectionClass}>
        <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">My applications</h2>
        {applications.length === 0 ? (
          <p className="mt-2 text-sm text-zinc-500">You haven&apos;t applied to any talent hunts yet.</p>
        ) : (
          <ul className="mt-4 flex flex-col gap-2">
            {applications.map((a) => (
              <li
                key={a.id}
                className="flex items-center justify-between rounded-lg border border-zinc-200 px-4 py-3 text-sm dark:border-zinc-800"
              >
                <Link href={`/casting-calls/${a.casting_call_id}`} className="text-rose-600 hover:underline">
                  View opportunity
                </Link>
                <span className={badgeClass(statusTone(a.status))}>{a.status}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

function CreateProfileForm({ token, onCreated }: { token: string; onCreated: (p: TalentProfile) => void }) {
  const [displayName, setDisplayName] = useState("");
  const [category, setCategory] = useState<TalentCategory>("acting");
  const [city, setCity] = useState("");
  const [bio, setBio] = useState("");
  const [skillsInput, setSkillsInput] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const profile = await api.createMyTalentProfile(
        {
          display_name: displayName,
          category,
          city: city || null,
          bio: bio || null,
          date_of_birth: null,
          experience_years: null,
          skills: parseSkills(skillsInput),
        },
        token
      );
      onCreated(profile);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create your profile.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className={sectionClass}>
      <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Create your talent profile</h2>
      <p className="mt-1 text-sm text-zinc-500">
        This is what talent hunts will see when they search for talent like you.
      </p>
      <form onSubmit={handleSubmit} className="mt-5 flex max-w-md flex-col gap-4">
        <label className={labelClass}>
          Display name
          <input required value={displayName} onChange={(e) => setDisplayName(e.target.value)} className={inputClass} />
        </label>
        <label className={labelClass}>
          Category
          <select value={category} onChange={(e) => setCategory(e.target.value as TalentCategory)} className={inputClass}>
            {TALENT_CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {formatCategory(c)}
              </option>
            ))}
          </select>
        </label>
        <label className={labelClass}>
          {skillsQuestion(category).label} (comma separated)
          <input
            value={skillsInput}
            onChange={(e) => setSkillsInput(e.target.value)}
            placeholder={skillsQuestion(category).placeholder}
            className={inputClass}
          />
        </label>
        <label className={labelClass}>
          City
          <input value={city} onChange={(e) => setCity(e.target.value)} className={inputClass} />
        </label>
        <label className={labelClass}>
          Bio
          <textarea rows={3} value={bio} onChange={(e) => setBio(e.target.value)} className={inputClass} />
        </label>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button type="submit" disabled={submitting} className={`w-fit ${btnPrimary}`}>
          {submitting ? "Creating…" : "Create profile"}
        </button>
      </form>
    </div>
  );
}

function ProfileSummary({
  profile,
  onUpdated,
  token,
}: {
  profile: TalentProfile;
  onUpdated: (p: TalentProfile) => void;
  token: string;
}) {
  const [editing, setEditing] = useState(false);
  const [bio, setBio] = useState(profile.bio ?? "");
  const [city, setCity] = useState(profile.city ?? "");
  const [skillsInput, setSkillsInput] = useState((profile.skills ?? []).join(", "));
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const coverUrl = coverPhotoUrl(profile.media);

  return (
    <section className={sectionClass}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="flex flex-col items-center gap-1.5">
            <div className="h-16 w-16 shrink-0 overflow-hidden rounded-xl">
              <TalentAvatar name={profile.display_name} coverUrl={coverUrl} className="h-full w-full text-lg" />
            </div>
            <HeadshotUploader
              token={token}
              hasExisting={!!coverUrl}
              onUploaded={(m) => onUpdated({ ...profile, media: [...profile.media.filter((x) => !x.is_cover), m] })}
            />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">{profile.display_name}</h2>
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
            <div className="mt-1 flex flex-wrap items-center gap-2">
              <span className={categoryBadgeClass(profile.category)}>{formatCategory(profile.category)}</span>
              {profile.city && <span className="text-xs text-zinc-500">{profile.city}</span>}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Link href={`/talents/${profile.id}`} className="text-sm text-rose-600 hover:underline">
            View public page
          </Link>
          <button onClick={() => setEditing((v) => !v)} className={btnSmall}>
            {editing ? "Cancel" : "Edit"}
          </button>
        </div>
      </div>
      {profile.bio && <p className="mt-4 text-sm text-zinc-700 dark:text-zinc-300">{profile.bio}</p>}
      {profile.skills && profile.skills.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {profile.skills.map((s) => (
            <span key={s} className={badgeClass("neutral")}>
              {s}
            </span>
          ))}
        </div>
      )}
      {SOCIAL_LINK_FIELDS.some((f) => profile[f.key]) && (
        <div className="mt-3 flex flex-wrap gap-2">
          {SOCIAL_LINK_FIELDS.filter((f) => profile[f.key]).map((f) => (
            <a
              key={f.key}
              href={profile[f.key]!}
              target="_blank"
              rel="noopener noreferrer"
              className={btnSmall}
            >
              <f.icon className="h-3.5 w-3.5" /> {f.label}
            </a>
          ))}
        </div>
      )}

      {editing && (
        <EditProfileForm
          profile={profile}
          token={token}
          bio={bio}
          city={city}
          skillsInput={skillsInput}
          setBio={setBio}
          setCity={setCity}
          setSkillsInput={setSkillsInput}
          onSaved={(p) => {
            onUpdated(p);
            setEditing(false);
          }}
          error={error}
          setError={setError}
          submitting={submitting}
          setSubmitting={setSubmitting}
        />
      )}
    </section>
  );
}

function EditProfileForm({
  profile,
  token,
  bio,
  city,
  skillsInput,
  setBio,
  setCity,
  setSkillsInput,
  onSaved,
  error,
  setError,
  submitting,
  setSubmitting,
}: {
  profile: TalentProfile;
  token: string;
  bio: string;
  city: string;
  skillsInput: string;
  setBio: (v: string) => void;
  setCity: (v: string) => void;
  setSkillsInput: (v: string) => void;
  onSaved: (p: TalentProfile) => void;
  error: string | null;
  setError: (v: string | null) => void;
  submitting: boolean;
  setSubmitting: (v: boolean) => void;
}) {
  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const updated = await api.updateMyTalentProfile(
        { bio: bio || null, city: city || null, skills: parseSkills(skillsInput) },
        token
      );
      onSaved({ ...updated, media: profile.media });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save changes.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mt-5 flex max-w-md flex-col gap-4 border-t border-zinc-200 pt-5 dark:border-zinc-800">
      <label className={labelClass}>
        City
        <input value={city} onChange={(e) => setCity(e.target.value)} className={inputClass} />
      </label>
      <label className={labelClass}>
        {skillsQuestion(profile.category).label} (comma separated)
        <input
          value={skillsInput}
          onChange={(e) => setSkillsInput(e.target.value)}
          placeholder={skillsQuestion(profile.category).placeholder}
          className={inputClass}
        />
      </label>
      <label className={labelClass}>
        Bio
        <textarea rows={3} value={bio} onChange={(e) => setBio(e.target.value)} className={inputClass} />
      </label>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <button type="submit" disabled={submitting} className={`w-fit ${btnSecondary}`}>
        {submitting ? "Saving…" : "Save"}
      </button>
    </form>
  );
}

function MembershipCard({
  profile,
  onUpdated,
  token,
}: {
  profile: TalentProfile;
  onUpdated: (p: TalentProfile) => void;
  token: string;
}) {
  const [requestingVerification, setRequestingVerification] = useState(false);
  const [upgrading, setUpgrading] = useState(false);

  async function handleRequestVerification() {
    setRequestingVerification(true);
    try {
      onUpdated(await api.requestTalentVerification(token));
    } finally {
      setRequestingVerification(false);
    }
  }

  async function handleUpgrade() {
    setUpgrading(true);
    try {
      onUpdated(await api.upgradeTalentTier(token));
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
              ? "You're on Premium — unlimited portfolio items and priority placement in search."
              : "Free plan: up to 3 portfolio items. Upgrade for unlimited auditions and priority placement."}
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
      <BillingStatusPanel token={token} onCanceled={() => api.getMyTalentProfile(token).then(onUpdated)} />
      <p className="mt-3 text-xs text-zinc-400">Verification is reviewed manually for now.</p>
    </section>
  );
}

function InvitationResponseButtons({
  invitation,
  token,
  onResponded,
}: {
  invitation: Invitation;
  token: string;
  onResponded: (updated: Invitation) => void;
}) {
  const [submitting, setSubmitting] = useState<"accepted" | "declined" | null>(null);

  async function respond(status: "accepted" | "declined") {
    setSubmitting(status);
    try {
      const updated = await api.respondToInvitation(invitation.id, status, token);
      onResponded(updated);
    } finally {
      setSubmitting(null);
    }
  }

  return (
    <div className="mt-3 flex gap-2">
      <button onClick={() => respond("accepted")} disabled={submitting !== null} className={btnSmall}>
        {submitting === "accepted" ? (
          "Accepting…"
        ) : (
          <>
            <Check className="h-3.5 w-3.5" /> Accept
          </>
        )}
      </button>
      <button onClick={() => respond("declined")} disabled={submitting !== null} className={btnSmall}>
        {submitting === "declined" ? (
          "Declining…"
        ) : (
          <>
            <X className="h-3.5 w-3.5" /> Decline
          </>
        )}
      </button>
    </div>
  );
}

function AvailabilityCard({
  availability,
  onChange,
  token,
}: {
  availability: AvailabilityWindow[];
  onChange: (windows: AvailabilityWindow[]) => void;
  token: string;
}) {
  const [dayOfWeek, setDayOfWeek] = useState("0");
  const [startTime, setStartTime] = useState("09:00");
  const [endTime, setEndTime] = useState("17:00");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleAdd(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const window = await api.addMyAvailability(
        { day_of_week: parseInt(dayOfWeek, 10), start_time: `${startTime}:00`, end_time: `${endTime}:00` },
        token
      );
      onChange([...availability, window].sort((a, b) => a.day_of_week - b.day_of_week || a.start_time.localeCompare(b.start_time)));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add this availability window.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRemove(windowId: string) {
    await api.deleteMyAvailability(windowId, token);
    onChange(availability.filter((w) => w.id !== windowId));
  }

  return (
    <section className={sectionClass}>
      <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Availability</h2>
      <p className="mt-1 text-sm text-zinc-500">
        Set the recurring weekly windows when talent hunters can request to book a session with you.
      </p>

      {availability.length > 0 && (
        <ul className="mt-4 flex flex-col gap-2">
          {availability.map((w) => (
            <li
              key={w.id}
              className="flex items-center justify-between rounded-lg border border-zinc-200 px-4 py-2 text-sm dark:border-zinc-800"
            >
              <span>
                <span className="font-semibold text-zinc-800 dark:text-zinc-200">{DAYS_OF_WEEK[w.day_of_week]}</span>{" "}
                {formatTimeOfDay(w.start_time)} &ndash; {formatTimeOfDay(w.end_time)}
              </span>
              <button onClick={() => handleRemove(w.id)} className="text-zinc-400 hover:text-red-600" aria-label="Remove">
                <Trash2 className="h-4 w-4" />
              </button>
            </li>
          ))}
        </ul>
      )}

      <form onSubmit={handleAdd} className="mt-4 flex flex-wrap items-end gap-3">
        <label className={labelClass}>
          Day
          <select value={dayOfWeek} onChange={(e) => setDayOfWeek(e.target.value)} className={inputClass}>
            {DAYS_OF_WEEK.map((d, i) => (
              <option key={d} value={i}>
                {d}
              </option>
            ))}
          </select>
        </label>
        <label className={labelClass}>
          Start time
          <input type="time" value={startTime} onChange={(e) => setStartTime(e.target.value)} className={inputClass} />
        </label>
        <label className={labelClass}>
          End time
          <input type="time" value={endTime} onChange={(e) => setEndTime(e.target.value)} className={inputClass} />
        </label>
        <button type="submit" disabled={submitting} className={btnSecondary}>
          <Plus className="h-4 w-4" /> Add window
        </button>
      </form>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </section>
  );
}

function BookingResponseButtons({
  booking,
  token,
  onResponded,
}: {
  booking: Booking;
  token: string;
  onResponded: (updated: Booking) => void;
}) {
  const [submitting, setSubmitting] = useState<"accepted" | "declined" | null>(null);

  async function respond(status: "accepted" | "declined") {
    setSubmitting(status);
    try {
      const updated = await api.respondToBooking(booking.id, status, token);
      onResponded(updated);
    } finally {
      setSubmitting(null);
    }
  }

  return (
    <div className="mt-3 flex gap-2">
      <button onClick={() => respond("accepted")} disabled={submitting !== null} className={btnSmall}>
        {submitting === "accepted" ? (
          "Accepting…"
        ) : (
          <>
            <Check className="h-3.5 w-3.5" /> Accept
          </>
        )}
      </button>
      <button onClick={() => respond("declined")} disabled={submitting !== null} className={btnSmall}>
        {submitting === "declined" ? (
          "Declining…"
        ) : (
          <>
            <X className="h-3.5 w-3.5" /> Decline
          </>
        )}
      </button>
    </div>
  );
}

function AgreementSection({
  booking,
  token,
  onUpdated,
}: {
  booking: Booking;
  token: string;
  onUpdated: (updated: Booking) => void;
}) {
  const [documentUrl, setDocumentUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (booking.agreement_status === "signed") {
    return (
      <p className="mt-3 flex items-center gap-1.5 text-sm font-semibold text-emerald-700 dark:text-emerald-400">
        <FileCheck2 className="h-4 w-4" /> Agreement signed
        {booking.agreement_document_url && (
          <a
            href={booking.agreement_document_url}
            target="_blank"
            rel="noopener noreferrer"
            className="font-normal text-rose-600 hover:underline"
          >
            View document
          </a>
        )}
      </p>
    );
  }

  async function handleSign(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      const updated = await api.signBookingAgreement(booking.id, documentUrl || undefined, token);
      onUpdated(updated);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSign} className="mt-3 flex flex-wrap items-end gap-2 rounded-lg bg-zinc-50 p-3 dark:bg-zinc-800/60">
      <label className={labelClass}>
        Link to signed agreement (optional)
        <input
          type="url"
          value={documentUrl}
          onChange={(e) => setDocumentUrl(e.target.value)}
          placeholder="https://…"
          className={inputClass}
        />
      </label>
      <button type="submit" disabled={submitting} className={btnSmall}>
        <FileCheck2 className="h-3.5 w-3.5" /> Mark agreement signed
      </button>
      <p className="mt-1 w-full text-xs text-zinc-400">
        No e-signature provider (DocuSign or similar) is wired up yet — mark this once the agreement has been signed
        outside the platform.
      </p>
    </form>
  );
}

function NotificationPreferencesCard({
  profile,
  onUpdated,
  token,
}: {
  profile: TalentProfile;
  onUpdated: (p: TalentProfile) => void;
  token: string;
}) {
  const [saving, setSaving] = useState(false);

  async function toggle() {
    setSaving(true);
    try {
      const updated = await api.updateMyTalentProfile({ job_alert_emails: !profile.job_alert_emails }, token);
      onUpdated({ ...updated, media: profile.media, credits: profile.credits });
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className={sectionClass}>
      <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Notifications</h2>
      <label className="mt-3 flex items-center gap-2 text-sm text-zinc-700 dark:text-zinc-300">
        <input
          type="checkbox"
          checked={profile.job_alert_emails}
          onChange={toggle}
          disabled={saving}
          className="accent-rose-600"
        />
        Email me when a new talent hunt matching my category is posted
      </label>
    </section>
  );
}

function IntroVideoCard({
  profile,
  onUpdated,
  token,
}: {
  profile: TalentProfile;
  onUpdated: (p: TalentProfile) => void;
  token: string;
}) {
  const [editing, setEditing] = useState(false);
  const [mode, setMode] = useState<"upload" | "link">("upload");
  const [url, setUrl] = useState(profile.intro_video_url ?? "");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (!categoryShowsIntroVideo(profile.category)) return null;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (mode === "upload" && file) {
        const updated = await api.uploadMyIntroVideo(file, token);
        onUpdated({ ...updated, media: profile.media, credits: profile.credits });
      } else {
        const updated = await api.updateMyTalentProfile({ intro_video_url: url.trim() || null }, token);
        onUpdated({ ...updated, media: profile.media, credits: profile.credits });
      }
      setEditing(false);
      setFile(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save your intro video.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className={sectionClass}>
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Intro video</h2>
          <p className="mt-1 text-sm text-zinc-500">
            A short pitch video shown at the top of your profile — your one chance to introduce yourself.
          </p>
        </div>
        <button onClick={() => setEditing((v) => !v)} className={btnSmall}>
          {editing ? "Cancel" : profile.intro_video_url ? "Edit" : "Add"}
        </button>
      </div>

      {!editing && profile.intro_video_url && <SubmissionPreview url={profile.intro_video_url} />}

      {editing && (
        <form onSubmit={handleSubmit} className="mt-4 flex max-w-md flex-col gap-4">
          <fieldset className="grid grid-cols-2 gap-2">
            {(["upload", "link"] as const).map((m) => (
              <button
                type="button"
                key={m}
                onClick={() => setMode(m)}
                className={`rounded-md border-2 px-3 py-2 text-sm font-medium transition-colors ${
                  mode === m
                    ? "border-rose-600 bg-rose-600 text-white"
                    : "border-zinc-200 text-zinc-700 hover:border-rose-300 hover:bg-rose-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:border-rose-800 dark:hover:bg-rose-950"
                }`}
              >
                {m === "upload" ? "Upload a file" : "Paste a link"}
              </button>
            ))}
          </fieldset>
          {mode === "upload" ? (
            <label key="intro-file" className={labelClass}>
              Video file
              <input
                type="file"
                accept="video/*"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className={inputClass}
              />
              <span className="mt-1 block text-xs font-normal normal-case text-zinc-500">
                We&apos;ll compress it automatically.
              </span>
            </label>
          ) : (
            <label key="intro-url" className={labelClass}>
              Video URL
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://youtube.com/watch?v=…"
                className={inputClass}
              />
            </label>
          )}
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button type="submit" disabled={submitting} className={`w-fit ${btnSecondary}`}>
            {submitting ? "Saving…" : "Save intro video"}
          </button>
        </form>
      )}
    </section>
  );
}

function SocialLinksCard({
  profile,
  onUpdated,
  token,
}: {
  profile: TalentProfile;
  onUpdated: (p: TalentProfile) => void;
  token: string;
}) {
  const [editing, setEditing] = useState(false);
  const [values, setValues] = useState<Record<SocialLinkKey, string>>(() =>
    Object.fromEntries(SOCIAL_LINK_FIELDS.map((f) => [f.key, profile[f.key] ?? ""])) as Record<SocialLinkKey, string>
  );
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const payload = Object.fromEntries(
        SOCIAL_LINK_FIELDS.map((f) => [f.key, values[f.key].trim() || null])
      );
      const updated = await api.updateMyTalentProfile(payload, token);
      onUpdated({ ...updated, media: profile.media });
      setEditing(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save your links.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className={sectionClass}>
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Social links</h2>
          <p className="mt-1 text-sm text-zinc-500">Let talent hunts find you elsewhere too.</p>
        </div>
        <button onClick={() => setEditing((v) => !v)} className={btnSmall}>
          {editing ? "Cancel" : "Edit"}
        </button>
      </div>

      {editing && (
        <form onSubmit={handleSubmit} className="mt-4 flex max-w-md flex-col gap-4">
          {SOCIAL_LINK_FIELDS.map((f) => (
            <label key={f.key} className={labelClass}>
              <span className="flex items-center gap-1.5">
                <f.icon className="h-3.5 w-3.5" /> {f.label}
              </span>
              <input
                type="url"
                value={values[f.key]}
                onChange={(e) => setValues((prev) => ({ ...prev, [f.key]: e.target.value }))}
                placeholder="https://…"
                className={inputClass}
              />
            </label>
          ))}
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button type="submit" disabled={submitting} className={`w-fit ${btnSecondary}`}>
            {submitting ? "Saving…" : "Save links"}
          </button>
        </form>
      )}
    </section>
  );
}

function AttributesCard({
  profile,
  onUpdated,
  token,
}: {
  profile: TalentProfile;
  onUpdated: (p: TalentProfile) => void;
  token: string;
}) {
  const fields = categoryAttributeFields(profile.category);
  const [editing, setEditing] = useState(false);
  const [values, setValues] = useState<Record<string, string>>(
    () => Object.fromEntries(fields.map((f) => [f.key, profile.attributes?.[f.key] ?? ""]))
  );
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (fields.length === 0) return null;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const attributes = Object.fromEntries(
        Object.entries(values).filter(([, v]) => v.trim() !== "")
      );
      const updated = await api.updateMyTalentProfile({ attributes }, token);
      onUpdated({ ...updated, media: profile.media, credits: profile.credits });
      setEditing(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save your details.");
    } finally {
      setSubmitting(false);
    }
  }

  const filled = fields.filter((f) => profile.attributes?.[f.key]);

  return (
    <section className={sectionClass}>
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Details</h2>
          <p className="mt-1 text-sm text-zinc-500">
            Structured details specific to {formatCategory(profile.category).toLowerCase()} — helps talent hunts
            find the right fit.
          </p>
        </div>
        <button onClick={() => setEditing((v) => !v)} className={btnSmall}>
          {editing ? "Cancel" : "Edit"}
        </button>
      </div>

      {!editing && filled.length > 0 && (
        <dl className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
          {filled.map((f) => (
            <div key={f.key}>
              <dt className="text-xs text-zinc-500">{f.label}</dt>
              <dd className="text-sm font-medium text-zinc-800 dark:text-zinc-200">{profile.attributes?.[f.key]}</dd>
            </div>
          ))}
        </dl>
      )}

      {editing && (
        <form onSubmit={handleSubmit} className="mt-4 grid max-w-md grid-cols-1 gap-4 sm:grid-cols-2">
          {fields.map((f) => (
            <label key={f.key} className={labelClass}>
              {f.label}
              <input
                value={values[f.key] ?? ""}
                onChange={(e) => setValues((prev) => ({ ...prev, [f.key]: e.target.value }))}
                placeholder={f.placeholder}
                className={inputClass}
              />
            </label>
          ))}
          {error && <p className="col-span-full text-sm text-red-600">{error}</p>}
          <button type="submit" disabled={submitting} className={`col-span-full w-fit ${btnSecondary}`}>
            {submitting ? "Saving…" : "Save details"}
          </button>
        </form>
      )}
    </section>
  );
}

function CreditsCard({
  profile,
  onUpdated,
  token,
}: {
  profile: TalentProfile;
  onUpdated: (p: TalentProfile) => void;
  token: string;
}) {
  const [showForm, setShowForm] = useState(false);
  const [projectType, setProjectType] = useState<CreditProjectType>("film");
  const [title, setTitle] = useState("");
  const [role, setRole] = useState("");
  const [companyOrDirector, setCompanyOrDirector] = useState("");
  const [location, setLocation] = useState("");
  const [dateLabel, setDateLabel] = useState("");
  const [referenceUrl, setReferenceUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  async function handleAdd(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const credit = await api.addMyCredit(
        {
          project_type: projectType,
          title,
          role: role || undefined,
          company_or_director: companyOrDirector || undefined,
          location: location || undefined,
          date_label: dateLabel || undefined,
          reference_url: referenceUrl || undefined,
        },
        token
      );
      onUpdated({ ...profile, credits: [credit, ...profile.credits] });
      setTitle("");
      setRole("");
      setCompanyOrDirector("");
      setLocation("");
      setDateLabel("");
      setReferenceUrl("");
      setShowForm(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add this credit.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(credit: Credit) {
    setDeletingId(credit.id);
    try {
      await api.deleteMyCredit(credit.id, token);
      onUpdated({ ...profile, credits: profile.credits.filter((c) => c.id !== credit.id) });
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <section className={sectionClass}>
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Credits & experience</h2>
          <p className="mt-1 text-sm text-zinc-500">Past projects — like a résumé, visible on your public profile.</p>
        </div>
        <button onClick={() => setShowForm((v) => !v)} className={btnSmall}>
          {showForm ? "Cancel" : "+ Add credit"}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleAdd} className="mt-4 flex max-w-md flex-col gap-4 border-b border-zinc-200 pb-5 dark:border-zinc-800">
          <label className={labelClass}>
            Type
            <select
              value={projectType}
              onChange={(e) => setProjectType(e.target.value as CreditProjectType)}
              className={inputClass}
            >
              {CREDIT_PROJECT_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </label>
          <label className={labelClass}>
            Project title
            <input required value={title} onChange={(e) => setTitle(e.target.value)} className={inputClass} />
          </label>
          <label className={labelClass}>
            Your role
            <input value={role} onChange={(e) => setRole(e.target.value)} placeholder="e.g. Lead, Supporting" className={inputClass} />
          </label>
          <label className={labelClass}>
            Company / director
            <input value={companyOrDirector} onChange={(e) => setCompanyOrDirector(e.target.value)} className={inputClass} />
          </label>
          <label className={labelClass}>
            Location
            <input value={location} onChange={(e) => setLocation(e.target.value)} className={inputClass} />
          </label>
          <label className={labelClass}>
            Date
            <input value={dateLabel} onChange={(e) => setDateLabel(e.target.value)} placeholder="e.g. Mar 2026 or 2024" className={inputClass} />
          </label>
          <label className={labelClass}>
            Reference link
            <input
              type="url"
              value={referenceUrl}
              onChange={(e) => setReferenceUrl(e.target.value)}
              placeholder="https://…"
              className={inputClass}
            />
          </label>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button type="submit" disabled={submitting} className={`w-fit ${btnPrimary}`}>
            {submitting ? "Adding…" : "Add credit"}
          </button>
        </form>
      )}

      {profile.credits.length === 0 ? (
        <p className="mt-4 text-sm text-zinc-500">No credits added yet.</p>
      ) : (
        <ul className="mt-4 flex flex-col gap-2">
          {profile.credits.map((c) => (
            <li
              key={c.id}
              className="flex items-center justify-between gap-3 rounded-2xl border-2 border-zinc-100 px-4 py-3 text-sm dark:border-zinc-800"
            >
              <div>
                <p className="flex items-center gap-1.5 font-semibold text-zinc-900 dark:text-zinc-50">
                  {createElement(creditProjectTypeIcon(c.project_type), { className: "h-4 w-4 text-zinc-500" })}
                  {c.title}
                  {c.role && <span className="font-normal text-zinc-500"> — {c.role}</span>}
                </p>
                <p className="mt-0.5 text-xs text-zinc-500">
                  {creditProjectTypeLabel(c.project_type)}
                  {c.date_label ? ` · ${c.date_label}` : ""}
                  {c.company_or_director ? ` · ${c.company_or_director}` : ""}
                </p>
              </div>
              <button onClick={() => handleDelete(c)} disabled={deletingId === c.id} className={btnSmall}>
                Delete
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function MediaGalleryCard({ profile }: { profile: TalentProfile }) {
  if (profile.media.length === 0) return null;

  return (
    <section className={sectionClass}>
      <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Your auditions</h2>
      <p className="mt-1 text-sm text-zinc-500">Preview and play back what you&apos;ve added so far.</p>
      <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2">
        {profile.media.map((m) => (
          <MediaCard key={m.id} media={m} />
        ))}
      </div>
    </section>
  );
}

const MEDIA_TYPES: { value: MediaType; label: string }[] = [
  { value: "photo", label: "Photo" },
  { value: "video", label: "Video" },
  { value: "audio", label: "Audio" },
  { value: "document", label: "Document" },
];

// Mirrors backend/app/core/config.py's FREE_TIER_VIDEO_LIMIT / PREMIUM_TIER_VIDEO_LIMIT — used
// here only to show quota messaging before hitting the server; the server enforces the real limit.
const FREE_TIER_VIDEO_LIMIT = 1;
const PREMIUM_TIER_VIDEO_LIMIT = 5;

const UPLOAD_MEDIA_TYPES: MediaType[] = ["video", "audio"];

function AddMediaForm({
  token,
  profile,
  onAdded,
}: {
  token: string;
  profile: TalentProfile;
  onAdded: (m: { id: string; url: string; media_type: MediaType; title: string | null; is_cover: boolean }) => void;
}) {
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [mediaType, setMediaType] = useState<MediaType>("photo");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const isUpload = UPLOAD_MEDIA_TYPES.includes(mediaType);
  const videoCount = profile.media.filter((m) => m.media_type === "video").length;
  const videoLimit = profile.tier === "premium" ? PREMIUM_TIER_VIDEO_LIMIT : FREE_TIER_VIDEO_LIMIT;
  const videoLimitReached = mediaType === "video" && videoCount >= videoLimit;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const media = isUpload
        ? await api.uploadMyMedia({ file: file!, media_type: mediaType as "video" | "audio", title: title || undefined }, token)
        : await api.addMyMedia({ url, media_type: mediaType, title: title || undefined }, token);
      onAdded(media);
      setUrl("");
      setFile(null);
      setTitle("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add this audition.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className={sectionClass}>
      <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Add an audition</h2>
      <p className="mt-1 text-sm text-zinc-500">
        Upload a video or audio file directly — we&apos;ll compress it automatically. Photos and
        documents are still linked from wherever they&apos;re hosted (YouTube and Spotify links
        also play right on your profile).
      </p>
      <form onSubmit={handleSubmit} className="mt-5 flex max-w-md flex-col gap-4">
        <label className={labelClass}>
          Title
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Cover of Manike Mage Hithe"
            className={inputClass}
          />
        </label>

        <fieldset className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {MEDIA_TYPES.map((t) => (
            <button
              type="button"
              key={t.value}
              onClick={() => setMediaType(t.value)}
              className={`rounded-md border-2 px-3 py-2 text-sm font-medium transition-colors ${
                mediaType === t.value
                  ? "border-rose-600 bg-rose-600 text-white"
                  : "border-zinc-200 text-zinc-700 hover:border-rose-300 hover:bg-rose-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:border-rose-800 dark:hover:bg-rose-950"
              }`}
            >
              {t.label}
            </button>
          ))}
        </fieldset>

        {mediaType === "video" && (
          <p className="text-xs text-zinc-500">
            {videoCount}/{videoLimit} audition video{videoLimit === 1 ? "" : "s"} used
            {profile.tier !== "premium" && " — upgrade to Premium for more"}
          </p>
        )}

        {isUpload ? (
          <label key="file-input" className={labelClass}>
            {mediaType === "video" ? "Video file" : "Audio file"}
            <input
              required
              type="file"
              accept={mediaType === "video" ? "video/*" : "audio/*"}
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className={inputClass}
            />
          </label>
        ) : (
          <label key="url-input" className={labelClass}>
            URL
            <input
              required
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://…"
              className={inputClass}
            />
          </label>
        )}

        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          type="submit"
          disabled={submitting || videoLimitReached || (isUpload && !file)}
          className={`w-fit ${btnSecondary}`}
        >
          {submitting ? (isUpload ? "Uploading & compressing…" : "Adding…") : videoLimitReached ? "Video limit reached" : "Add audition"}
        </button>
      </form>
    </section>
  );
}
