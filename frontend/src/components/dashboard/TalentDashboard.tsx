"use client";

import { FormEvent, createElement, useEffect, useState } from "react";
import Link from "next/link";
import {
  Calendar,
  CalendarDays,
  Check,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  CreditCard,
  Crown,
  Eye,
  Image as ImageIcon,
  PlayCircle,
  Plus,
  ShieldCheck,
  Trash2,
  User,
  X,
} from "lucide-react";
import {
  Application,
  ApiError,
  AvailabilityWindow,
  Booking,
  CalendarEntry,
  CalendarEvent,
  ContentVisibility,
  Credit,
  CreditProjectType,
  Follow,
  Invitation,
  LibraryItem,
  Media,
  MediaType,
  ProfileViewSummary,
  Reel,
  TALENT_CATEGORIES,
  TalentCategory,
  TalentProfile,
  api,
} from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import BillingStatusPanel from "@/components/BillingStatusPanel";
import PaymentHistoryList from "@/components/PaymentHistoryList";
import {
  CREDIT_PROJECT_TYPES,
  DAYS_OF_WEEK,
  SOCIAL_LINK_FIELDS,
  SocialLinkKey,
  badgeClass,
  bookingStatusTone,
  formatBookingRange,
  formatRelativeTime,
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
  formatInstrument,
  formatTimeOfDay,
  getVideoDurationSeconds,
  MAX_VIDEO_DURATION_SECONDS,
  INSTRUMENT_GROUPS,
  inputClass,
  invitationStatusTone,
  labelClass,
  libraryLabel,
  premiumBadgeClass,
  PREMIUM_REEL_LIMIT,
  reelPlatformLabel,
  REEL_PLATFORM_ICONS,
  sectionClass,
  VISIBILITY_OPTIONS,
  skillsQuestion,
  statusTone,
  verifiedBadgeClass,
} from "@/lib/ui";
import TalentAvatar from "@/components/TalentAvatar";
import BookingAgreementSection from "@/components/BookingAgreementSection";
import BookingReviewForm from "@/components/BookingReviewForm";
import MediaCard from "@/components/MediaCard";
import LibraryItemCard from "@/components/LibraryItemCard";
import HeadshotUploader from "@/components/HeadshotUploader";
import SubmissionPreview from "@/components/SubmissionPreview";
import DashboardSidebar, { DashboardNavItem } from "@/components/dashboard/DashboardSidebar";

function parseSkills(raw: string): string[] {
  return raw
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

type TalentSection = "profile" | "portfolio" | "activity" | "bookings" | "membership";

const TALENT_NAV_ITEMS: DashboardNavItem[] = [
  { id: "profile", label: "Profile", icon: User },
  { id: "portfolio", label: "Portfolio", icon: ImageIcon },
  { id: "activity", label: "Activity", icon: ClipboardList },
  { id: "bookings", label: "Bookings", icon: CalendarDays },
  { id: "membership", label: "Membership", icon: CreditCard },
];

export default function TalentDashboard() {
  const { token } = useAuth();
  const [activeSection, setActiveSection] = useState<TalentSection>("profile");
  const [profile, setProfile] = useState<TalentProfile | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [applications, setApplications] = useState<Application[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [availability, setAvailability] = useState<AvailabilityWindow[]>([]);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [following, setFollowing] = useState<Follow[]>([]);
  const [profileViews, setProfileViews] = useState<ProfileViewSummary | null>(null);
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
    api.getMyProfileViews(token).then(setProfileViews).catch(() => {});
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
    <div className="flex flex-col gap-6 lg:flex-row lg:items-start">
      <DashboardSidebar items={TALENT_NAV_ITEMS} activeId={activeSection} onSelect={(id) => setActiveSection(id as TalentSection)} />
      <div className="flex min-w-0 flex-1 flex-col gap-6">
        {activeSection === "profile" && (
          <>
            <ProfileSummary profile={profile} onUpdated={setProfile} token={token!} />
            <IntroVideoCard profile={profile} onUpdated={setProfile} token={token!} />
            <SocialLinksCard profile={profile} onUpdated={setProfile} token={token!} />
            <AttributesCard profile={profile} onUpdated={setProfile} token={token!} />
            <InstrumentsCard profile={profile} onUpdated={setProfile} token={token!} />
          </>
        )}

        {activeSection === "portfolio" && (
          <>
            <MediaGalleryCard profile={profile} onUpdated={setProfile} token={token!} />
            <AddMediaForm
              token={token!}
              profile={profile}
              onAdded={(m) => setProfile({ ...profile, media: [...profile.media, m] })}
            />
            <CreditsCard profile={profile} onUpdated={setProfile} token={token!} />
            <ReelsCard profile={profile} onUpdated={setProfile} token={token!} />
            <LibraryCard profile={profile} token={token!} />
          </>
        )}

        {activeSection === "activity" && (
          <>
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
                      <div className="flex items-center gap-2">
                        <span className="flex items-center gap-1 text-xs text-zinc-500">
                          <Eye className="h-3.5 w-3.5" />
                          {a.viewed_at
                            ? profile.tier === "premium"
                              ? `Seen ${formatRelativeTime(a.viewed_at)}`
                              : "Seen"
                            : "Not yet seen"}
                        </span>
                        <span className={badgeClass(statusTone(a.status))}>{a.status}</span>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </section>

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
          </>
        )}

        {activeSection === "bookings" && (
          <>
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
                        <BookingResponseButtons
                          booking={b}
                          token={token!}
                          onResponded={(updated) => setBookings((prev) => prev.map((x) => (x.id === updated.id ? updated : x)))}
                        />
                      )}
                      {b.status === "accepted" && (
                        <BookingAgreementSection
                          booking={b}
                          token={token!}
                          viewerRole="talent"
                          otherPartyLabel={b.recruiter_company_name}
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

            <WorkCalendarCard token={token!} />

            <AvailabilityCard availability={availability} onChange={setAvailability} token={token!} />
          </>
        )}

        {activeSection === "membership" && (
          <>
            <MembershipCard profile={profile} onUpdated={setProfile} token={token!} />
            <ProfileViewsCard views={profileViews} isPremium={profile.tier === "premium"} />
            <NotificationPreferencesCard profile={profile} onUpdated={setProfile} token={token!} />
          </>
        )}
      </div>
    </div>
  );
}

function CreateProfileForm({ token, onCreated }: { token: string; onCreated: (p: TalentProfile) => void }) {
  const [displayName, setDisplayName] = useState("");
  const [categories, setCategories] = useState<TalentCategory[]>(["acting"]);
  const [city, setCity] = useState("");
  const [bio, setBio] = useState("");
  const [skillsInput, setSkillsInput] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function toggleCategory(c: TalentCategory) {
    setCategories((prev) => (prev.includes(c) ? prev.filter((x) => x !== c) : [...prev, c]));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (categories.length === 0) {
      setError("Select at least one category.");
      return;
    }
    setSubmitting(true);
    try {
      const profile = await api.createMyTalentProfile(
        {
          display_name: displayName,
          categories,
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
        <fieldset className="flex flex-col gap-1.5">
          <legend className={labelClass}>Categories — pick all that apply</legend>
          <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-3">
            {TALENT_CATEGORIES.map((c) => (
              <label key={c} className="flex items-center gap-1.5 text-sm text-zinc-700 dark:text-zinc-300">
                <input type="checkbox" checked={categories.includes(c)} onChange={() => toggleCategory(c)} />
                {formatCategory(c)}
              </label>
            ))}
          </div>
        </fieldset>
        <label className={labelClass}>
          {skillsQuestion(categories[0] ?? "acting").label} (comma separated)
          <input
            value={skillsInput}
            onChange={(e) => setSkillsInput(e.target.value)}
            placeholder={skillsQuestion(categories[0] ?? "acting").placeholder}
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
  const [categories, setCategories] = useState<TalentCategory[]>(
    profile.categories?.length ? profile.categories : [profile.category]
  );
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const coverUrl = coverPhotoUrl(profile.media);

  return (
    <section className={sectionClass}>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
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
              {(profile.categories?.length ? profile.categories : [profile.category]).map((c) => (
                <span key={c} className={categoryBadgeClass(c)}>
                  {formatCategory(c)}
                </span>
              ))}
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
          categories={categories}
          setBio={setBio}
          setCity={setCity}
          setSkillsInput={setSkillsInput}
          setCategories={setCategories}
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
  categories,
  setBio,
  setCity,
  setSkillsInput,
  setCategories,
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
  categories: TalentCategory[];
  setBio: (v: string) => void;
  setCity: (v: string) => void;
  setSkillsInput: (v: string) => void;
  setCategories: (v: TalentCategory[]) => void;
  onSaved: (p: TalentProfile) => void;
  error: string | null;
  setError: (v: string | null) => void;
  submitting: boolean;
  setSubmitting: (v: boolean) => void;
}) {
  const [dateOfBirth, setDateOfBirth] = useState(profile.date_of_birth ?? "");
  const [gender, setGender] = useState(profile.gender ?? "");
  const [experienceYears, setExperienceYears] = useState(
    profile.experience_years != null ? String(profile.experience_years) : ""
  );
  const [tiktokFollowers, setTiktokFollowers] = useState(
    profile.tiktok_followers != null ? String(profile.tiktok_followers) : ""
  );

  function toggleCategory(c: TalentCategory) {
    setCategories(categories.includes(c) ? categories.filter((x) => x !== c) : [...categories, c]);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (categories.length === 0) {
      setError("Select at least one category.");
      return;
    }
    setSubmitting(true);
    try {
      const updated = await api.updateMyTalentProfile(
        {
          bio: bio || null,
          city: city || null,
          skills: parseSkills(skillsInput),
          categories,
          date_of_birth: dateOfBirth || null,
          gender: gender || null,
          experience_years: experienceYears ? Number(experienceYears) : null,
          tiktok_followers: tiktokFollowers ? Number(tiktokFollowers) : null,
        },
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
      <fieldset className="flex flex-col gap-1.5">
        <legend className={labelClass}>Categories — pick all that apply</legend>
        <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-3">
          {TALENT_CATEGORIES.map((c) => (
            <label key={c} className="flex items-center gap-1.5 text-sm text-zinc-700 dark:text-zinc-300">
              <input type="checkbox" checked={categories.includes(c)} onChange={() => toggleCategory(c)} />
              {formatCategory(c)}
            </label>
          ))}
        </div>
      </fieldset>
      <label className={labelClass}>
        City
        <input value={city} onChange={(e) => setCity(e.target.value)} className={inputClass} />
      </label>
      <label className={labelClass}>
        {skillsQuestion(categories[0] ?? profile.category).label} (comma separated)
        <input
          value={skillsInput}
          onChange={(e) => setSkillsInput(e.target.value)}
          placeholder={skillsQuestion(categories[0] ?? profile.category).placeholder}
          className={inputClass}
        />
      </label>
      <label className={labelClass}>
        Bio
        <textarea rows={3} value={bio} onChange={(e) => setBio(e.target.value)} className={inputClass} />
      </label>
      <div className="flex gap-3">
        <label className={labelClass}>
          Date of birth
          <input
            type="date"
            value={dateOfBirth}
            onChange={(e) => setDateOfBirth(e.target.value)}
            className={inputClass}
          />
          <span className="mt-1 block text-xs font-normal normal-case text-zinc-500">
            Optional — lets recruiters filter by age range.
          </span>
        </label>
        <label className={labelClass}>
          Gender
          <select value={gender} onChange={(e) => setGender(e.target.value)} className={inputClass}>
            <option value="">Prefer not to say</option>
            <option value="male">Male</option>
            <option value="female">Female</option>
          </select>
        </label>
      </div>
      <label className={labelClass}>
        Years of experience
        <input
          type="number"
          min={0}
          value={experienceYears}
          onChange={(e) => setExperienceYears(e.target.value)}
          className={inputClass}
        />
      </label>
      {(categories.includes("content_creator") || profile.category === "content_creator") && (
        <label className={labelClass}>
          TikTok followers
          <input
            type="number"
            min={0}
            value={tiktokFollowers}
            onChange={(e) => setTiktokFollowers(e.target.value)}
            className={inputClass}
          />
          <span className="mt-1 block text-xs font-normal normal-case text-zinc-500">
            Lets recruiters find you by audience size.
          </span>
        </label>
      )}
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
              ? "You're on Premium — unlimited portfolio items, boosted placement, who-viewed-your-profile, and exact read-receipt times."
              : "Free plan: up to 3 portfolio items. Upgrade for unlimited auditions, boosted placement, who-viewed-your-profile, and exact read-receipt times."}
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
        onCanceled={() => api.getMyTalentProfile(token).then(onUpdated)}
      />
      <PaymentHistoryList token={token} />
      <p className="mt-3 text-xs text-zinc-400">Verification is reviewed manually for now.</p>
    </section>
  );
}

function ProfileViewsCard({ views, isPremium }: { views: ProfileViewSummary | null; isPremium: boolean }) {
  if (!views) return null;

  return (
    <section className={sectionClass}>
      <div className="flex items-center gap-2">
        <Eye className="h-5 w-5 text-zinc-400" />
        <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Profile views</h2>
      </div>
      <p className="mt-2 text-2xl font-black text-zinc-900 dark:text-zinc-50">{views.count}</p>
      {isPremium ? (
        views.viewers.length === 0 ? (
          <p className="mt-1 text-sm text-zinc-500">No recruiters have viewed your profile yet.</p>
        ) : (
          <ul className="mt-3 flex flex-col gap-1.5">
            {views.viewers.map((v) => (
              <li key={v.recruiter_id} className="flex items-center justify-between text-sm">
                <span className="font-semibold text-zinc-900 dark:text-zinc-50">{v.company_name}</span>
                <span className="text-xs text-zinc-500">{formatRelativeTime(v.viewed_at)}</span>
              </li>
            ))}
          </ul>
        )
      ) : (
        <p className="mt-1 text-sm text-zinc-500">
          {views.count > 0
            ? "Upgrade to Premium to see which recruiters viewed your profile."
            : "Upgrade to Premium to see who views your profile as views come in."}
        </p>
      )}
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

function currentMonthKey(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

function shiftMonthKey(month: string, delta: number): string {
  const [year, mon] = month.split("-").map(Number);
  const d = new Date(year, mon - 1 + delta, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function monthLabel(month: string): string {
  const [year, mon] = month.split("-").map(Number);
  return new Date(year, mon - 1, 1).toLocaleDateString(undefined, { month: "long", year: "numeric" });
}

function buildMonthGrid(month: string): (string | null)[] {
  const [year, mon] = month.split("-").map(Number);
  const firstDay = new Date(year, mon - 1, 1);
  const leading = (firstDay.getDay() + 6) % 7; // Monday-first grid
  const daysInMonth = new Date(year, mon, 0).getDate();
  const cells: (string | null)[] = Array(leading).fill(null);
  for (let d = 1; d <= daysInMonth; d++) {
    cells.push(`${year}-${String(mon).padStart(2, "0")}-${String(d).padStart(2, "0")}`);
  }
  while (cells.length % 7 !== 0) cells.push(null);
  return cells;
}

function WorkCalendarCard({ token }: { token: string }) {
  const [month, setMonth] = useState(currentMonthKey());
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [entries, setEntries] = useState<CalendarEntry[]>([]);
  const [selectedDay, setSelectedDay] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [notes, setNotes] = useState("");
  const [isPublic, setIsPublic] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api.getMyCalendar(month, token).then(setEvents).catch(() => {});
  }, [month, token]);

  useEffect(() => {
    api.listMyCalendarEntries(token).then(setEntries).catch(() => {});
  }, [token]);

  const grid = buildMonthGrid(month);

  function eventsOnDay(day: string): CalendarEvent[] {
    return events.filter((e) => day >= e.start_at.slice(0, 10) && day <= e.end_at.slice(0, 10));
  }

  function openFormForDay(day: string) {
    setSelectedDay(day);
    setTitle("");
    setStartDate(day);
    setEndDate(day);
    setNotes("");
    setIsPublic(true);
    setError(null);
    setShowForm(true);
  }

  async function handleAddEntry(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const entry = await api.addMyCalendarEntry(
        { title, start_date: startDate, end_date: endDate, notes: notes || null, is_public: isPublic },
        token
      );
      setEntries((prev) => [...prev, entry].sort((a, b) => a.start_date.localeCompare(b.start_date)));
      setEvents((prev) =>
        [
          ...prev,
          { id: entry.id, kind: "entry" as const, title: entry.title, start_at: entry.start_date, end_at: entry.end_date, status: "confirmed" },
        ].sort((a, b) => a.start_at.localeCompare(b.start_at))
      );
      setShowForm(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add this calendar entry.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDeleteEntry(entryId: string) {
    await api.deleteMyCalendarEntry(entryId, token);
    setEntries((prev) => prev.filter((e) => e.id !== entryId));
    setEvents((prev) => prev.filter((e) => !(e.kind === "entry" && e.id === entryId)));
  }

  return (
    <section className={sectionClass}>
      <div className="flex items-center justify-between">
        <h2 className="flex items-center gap-2 font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">
          <Calendar className="h-5 w-5" /> Work calendar
        </h2>
        <div className="flex items-center gap-2">
          <button onClick={() => setMonth((m) => shiftMonthKey(m, -1))} className={btnSmall} aria-label="Previous month">
            <ChevronLeft className="h-4 w-4" />
          </button>
          <span className="min-w-[9rem] text-center text-sm font-semibold text-zinc-800 dark:text-zinc-200">
            {monthLabel(month)}
          </span>
          <button onClick={() => setMonth((m) => shiftMonthKey(m, 1))} className={btnSmall} aria-label="Next month">
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>
      <p className="mt-1 text-sm text-zinc-500">
        Bookings made on YouGotTalent and gigs you add yourself, in one place. Click a day to add an entry.
      </p>

      <div className="mt-4 grid grid-cols-7 gap-1 text-center text-xs font-semibold text-zinc-500">
        {DAYS_OF_WEEK.map((d) => (
          <span key={d}>{d.slice(0, 3)}</span>
        ))}
      </div>
      <div className="mt-1 grid grid-cols-7 gap-1">
        {grid.map((day, i) => {
          const dayEvents = day ? eventsOnDay(day) : [];
          const isToday = day === new Date().toISOString().slice(0, 10);
          return (
            <button
              key={i}
              disabled={!day}
              onClick={() => day && openFormForDay(day)}
              className={`flex min-h-[4.5rem] flex-col items-start gap-0.5 rounded-md border p-1 text-left text-xs ${
                day
                  ? "border-zinc-200 hover:border-zinc-400 dark:border-zinc-800 dark:hover:border-zinc-600"
                  : "border-transparent"
              } ${isToday ? "ring-1 ring-rose-500" : ""}`}
            >
              {day && <span className="font-semibold text-zinc-700 dark:text-zinc-300">{parseInt(day.slice(8), 10)}</span>}
              {dayEvents.slice(0, 2).map((ev) => (
                <span
                  key={ev.id}
                  className={`w-full truncate rounded-sm px-1 py-0.5 text-[10px] ${
                    ev.kind === "booking" ? "bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300" : "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
                  }`}
                >
                  {ev.title}
                </span>
              ))}
              {dayEvents.length > 2 && <span className="text-[10px] text-zinc-400">+{dayEvents.length - 2} more</span>}
            </button>
          );
        })}
      </div>

      {showForm && selectedDay && (
        <form onSubmit={handleAddEntry} className="mt-4 flex flex-col gap-3 rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
          <p className="text-sm font-semibold text-zinc-800 dark:text-zinc-200">Add calendar entry</p>
          <label className={labelClass}>
            Title
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Wedding shoot in Kandy"
              required
              className={inputClass}
            />
          </label>
          <div className="flex flex-wrap gap-3">
            <label className={labelClass}>
              Start date
              <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} required className={inputClass} />
            </label>
            <label className={labelClass}>
              End date
              <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} required className={inputClass} />
            </label>
          </div>
          <label className={labelClass}>
            Notes (optional)
            <input value={notes} onChange={(e) => setNotes(e.target.value)} className={inputClass} />
          </label>
          <label className="flex items-center gap-2 text-sm text-zinc-700 dark:text-zinc-300">
            <input type="checkbox" checked={isPublic} onChange={(e) => setIsPublic(e.target.checked)} />
            Show this title to talent hunters checking my availability (otherwise they just see &ldquo;busy&rdquo;)
          </label>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="flex gap-2">
            <button type="submit" disabled={submitting} className={btnPrimary}>
              {submitting ? "Adding…" : "Add entry"}
            </button>
            <button type="button" onClick={() => setShowForm(false)} className={btnSecondary}>
              Cancel
            </button>
          </div>
        </form>
      )}

      {entries.length > 0 && (
        <ul className="mt-4 flex flex-col gap-2">
          {entries.map((e) => (
            <li
              key={e.id}
              className="flex items-center justify-between rounded-lg border border-zinc-200 px-4 py-2 text-sm dark:border-zinc-800"
            >
              <span>
                <span className="font-semibold text-zinc-800 dark:text-zinc-200">{e.title}</span>{" "}
                <span className="text-zinc-500">
                  {e.start_date}
                  {e.end_date !== e.start_date ? ` – ${e.end_date}` : ""}
                </span>
              </span>
              <button onClick={() => handleDeleteEntry(e.id)} className="text-zinc-400 hover:text-red-600" aria-label="Remove">
                <Trash2 className="h-4 w-4" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
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
      onUpdated({ ...updated, media: profile.media, credits: profile.credits, reels: profile.reels });
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

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const input = e.target;
    const picked = input.files?.[0] ?? null;
    if (!picked) return;
    setError(null);
    try {
      const duration = await getVideoDurationSeconds(picked);
      if (duration > MAX_VIDEO_DURATION_SECONDS) {
        setError(`Videos must be ${MAX_VIDEO_DURATION_SECONDS} seconds or shorter (this one is ${Math.round(duration)}s).`);
        setFile(null);
        input.value = "";
        return;
      }
    } catch {
      // If we can't read the duration client-side, let the upload proceed — the server
      // enforces the real limit either way.
    }
    setFile(picked);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (mode === "upload" && file) {
        const updated = await api.uploadMyIntroVideo(file, token);
        onUpdated({ ...updated, media: profile.media, credits: profile.credits, reels: profile.reels });
      } else {
        const updated = await api.updateMyTalentProfile({ intro_video_url: url.trim() || null }, token);
        onUpdated({ ...updated, media: profile.media, credits: profile.credits, reels: profile.reels });
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
              {/* No `capture` attribute — on mobile Safari/Chrome, accept="video/*" alone
                  already opens a picker offering both "record" and "choose from library".
                  Adding `capture` would force straight to the camera and remove the gallery
                  option, the opposite of what we want here. */}
              <input
                type="file"
                accept="video/*"
                onChange={handleFileChange}
                className={inputClass}
              />
              <span className="mt-1 block text-xs font-normal normal-case text-zinc-500">
                We&apos;ll compress it automatically. Max {MAX_VIDEO_DURATION_SECONDS}s.
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
      onUpdated({ ...updated, media: profile.media, credits: profile.credits, reels: profile.reels });
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

function InstrumentsCard({
  profile,
  onUpdated,
  token,
}: {
  profile: TalentProfile;
  onUpdated: (p: TalentProfile) => void;
  token: string;
}) {
  const [selected, setSelected] = useState<string[]>(profile.instruments ?? []);
  const [saving, setSaving] = useState(false);

  if (profile.category !== "music") return null;

  function toggle(instrument: string) {
    setSelected((prev) => (prev.includes(instrument) ? prev.filter((i) => i !== instrument) : [...prev, instrument]));
  }

  async function handleSave() {
    setSaving(true);
    try {
      const updated = await api.updateMyTalentProfile({ instruments: selected }, token);
      onUpdated(updated);
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className={sectionClass}>
      <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Instruments</h2>
      <p className="mt-1 text-sm text-zinc-500">
        Pick everything you play — helps talent hunts searching for a specific instrument find you.
      </p>
      <div className="mt-4 flex flex-col gap-3">
        {INSTRUMENT_GROUPS.map((group) => (
          <div key={group.label}>
            <p className="text-xs font-bold uppercase tracking-wide text-zinc-400">{group.label}</p>
            <div className="mt-1.5 flex flex-wrap gap-2">
              {group.instruments.map((i) => (
                <label
                  key={i}
                  className={`cursor-pointer rounded-full border-2 px-3 py-1 text-xs font-semibold transition-colors ${
                    selected.includes(i)
                      ? "border-rose-500 bg-rose-50 text-rose-700 dark:bg-rose-950 dark:text-rose-300"
                      : "border-zinc-200 text-zinc-600 dark:border-zinc-700 dark:text-zinc-300"
                  }`}
                >
                  <input type="checkbox" checked={selected.includes(i)} onChange={() => toggle(i)} className="hidden" />
                  {formatInstrument(i)}
                </label>
              ))}
            </div>
          </div>
        ))}
      </div>
      <button onClick={handleSave} disabled={saving} className={`mt-4 ${btnSmall}`}>
        {saving ? "Saving…" : "Save instruments"}
      </button>
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
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editRole, setEditRole] = useState("");
  const [editCompanyOrDirector, setEditCompanyOrDirector] = useState("");
  const [editLocation, setEditLocation] = useState("");
  const [editDateLabel, setEditDateLabel] = useState("");
  const [editReferenceUrl, setEditReferenceUrl] = useState("");
  const [editError, setEditError] = useState<string | null>(null);
  const [editSubmitting, setEditSubmitting] = useState(false);

  function startEditing(credit: Credit) {
    setEditingId(credit.id);
    setEditTitle(credit.title);
    setEditRole(credit.role ?? "");
    setEditCompanyOrDirector(credit.company_or_director ?? "");
    setEditLocation(credit.location ?? "");
    setEditDateLabel(credit.date_label ?? "");
    setEditReferenceUrl(credit.reference_url ?? "");
    setEditError(null);
  }

  async function handleEditSave(e: FormEvent) {
    e.preventDefault();
    if (!editingId) return;
    setEditError(null);
    setEditSubmitting(true);
    try {
      const updated = await api.updateMyCredit(
        editingId,
        {
          title: editTitle,
          role: editRole || undefined,
          company_or_director: editCompanyOrDirector || undefined,
          location: editLocation || undefined,
          date_label: editDateLabel || undefined,
          reference_url: editReferenceUrl || undefined,
        },
        token
      );
      onUpdated({ ...profile, credits: profile.credits.map((c) => (c.id === updated.id ? updated : c)) });
      setEditingId(null);
    } catch (err) {
      setEditError(err instanceof ApiError ? err.message : "Could not save these changes.");
    } finally {
      setEditSubmitting(false);
    }
  }

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
          {profile.credits.map((c) =>
            editingId === c.id ? (
              <li key={c.id} className="rounded-2xl border-2 border-zinc-100 p-4 dark:border-zinc-800">
                <form onSubmit={handleEditSave} className="flex flex-col gap-3">
                  <label className={labelClass}>
                    Project title
                    <input required value={editTitle} onChange={(e) => setEditTitle(e.target.value)} className={inputClass} />
                  </label>
                  <label className={labelClass}>
                    Your role
                    <input value={editRole} onChange={(e) => setEditRole(e.target.value)} className={inputClass} />
                  </label>
                  <label className={labelClass}>
                    Company / director
                    <input
                      value={editCompanyOrDirector}
                      onChange={(e) => setEditCompanyOrDirector(e.target.value)}
                      className={inputClass}
                    />
                  </label>
                  <label className={labelClass}>
                    Location
                    <input value={editLocation} onChange={(e) => setEditLocation(e.target.value)} className={inputClass} />
                  </label>
                  <label className={labelClass}>
                    Date
                    <input value={editDateLabel} onChange={(e) => setEditDateLabel(e.target.value)} className={inputClass} />
                  </label>
                  <label className={labelClass}>
                    Reference link
                    <input
                      type="url"
                      value={editReferenceUrl}
                      onChange={(e) => setEditReferenceUrl(e.target.value)}
                      className={inputClass}
                    />
                  </label>
                  {editError && <p className="text-sm text-red-600">{editError}</p>}
                  <div className="flex items-center gap-3">
                    <button type="submit" disabled={editSubmitting} className={`w-fit ${btnPrimary}`}>
                      {editSubmitting ? "Saving…" : "Save"}
                    </button>
                    <button type="button" onClick={() => setEditingId(null)} className={`w-fit ${btnSmall}`}>
                      Cancel
                    </button>
                  </div>
                </form>
              </li>
            ) : (
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
                <div className="flex shrink-0 items-center gap-2">
                  <button onClick={() => startEditing(c)} className={btnSmall}>
                    Edit
                  </button>
                  <button onClick={() => handleDelete(c)} disabled={deletingId === c.id} className={btnSmall}>
                    Delete
                  </button>
                </div>
              </li>
            )
          )}
        </ul>
      )}
    </section>
  );
}

function ReelsCard({
  profile,
  onUpdated,
  token,
}: {
  profile: TalentProfile;
  onUpdated: (p: TalentProfile) => void;
  token: string;
}) {
  const [url, setUrl] = useState("");
  const [caption, setCaption] = useState("");
  const [visibility, setVisibility] = useState<ContentVisibility>("public");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const isPremium = profile.tier === "premium";

  async function handleAdd(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const reel = await api.addMyReel({ url, caption: caption || undefined, visibility }, token);
      onUpdated({ ...profile, reels: [reel, ...profile.reels] });
      setUrl("");
      setCaption("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add this reel.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(reel: Reel) {
    setDeletingId(reel.id);
    try {
      await api.deleteMyReel(reel.id, token);
      onUpdated({ ...profile, reels: profile.reels.filter((r) => r.id !== reel.id) });
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <section className={sectionClass}>
      <div>
        <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Reels</h2>
        <p className="mt-1 text-sm text-zinc-500">
          Showcase your TikTok, Instagram Reels, or Facebook Reels — visible on your public profile.
        </p>
      </div>

      {!isPremium ? (
        <p className="mt-4 text-sm text-zinc-500">
          Reels are a Premium feature. Upgrade to Premium from the Membership tab to showcase your content.
        </p>
      ) : (
        <>
          <form onSubmit={handleAdd} className="mt-4 flex max-w-md flex-col gap-3 border-b border-zinc-200 pb-5 dark:border-zinc-800">
            <label className={labelClass}>
              Reel URL
              <input
                required
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://www.tiktok.com/@you/video/…"
                className={inputClass}
              />
            </label>
            <label className={labelClass}>
              Caption (optional)
              <input value={caption} onChange={(e) => setCaption(e.target.value)} className={inputClass} />
            </label>
            <label className={labelClass}>
              Who can see this
              <select value={visibility} onChange={(e) => setVisibility(e.target.value as ContentVisibility)} className={inputClass}>
                {VISIBILITY_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </label>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button
              type="submit"
              disabled={submitting || profile.reels.length >= PREMIUM_REEL_LIMIT}
              className={`w-fit ${btnPrimary}`}
            >
              {submitting ? "Adding…" : "Add reel"}
            </button>
            <p className="text-xs text-zinc-400">
              {profile.reels.length} of {PREMIUM_REEL_LIMIT} used
            </p>
          </form>

          {profile.reels.length === 0 ? (
            <p className="mt-4 text-sm text-zinc-500">No reels added yet.</p>
          ) : (
            <ul className="mt-4 flex flex-col gap-2">
              {profile.reels.map((r) => {
                const Icon = REEL_PLATFORM_ICONS[r.platform] ?? PlayCircle;
                return (
                  <li
                    key={r.id}
                    className="flex items-center justify-between gap-3 rounded-2xl border-2 border-zinc-100 p-3 dark:border-zinc-800"
                  >
                    <div className="flex min-w-0 items-center gap-2">
                      <Icon className="h-4 w-4 shrink-0 text-zinc-400" />
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-zinc-900 dark:text-zinc-50">
                          {r.caption || reelPlatformLabel(r.platform)}
                        </p>
                        <p className="truncate text-xs text-zinc-500">{r.url}</p>
                      </div>
                    </div>
                    <button
                      onClick={() => handleDelete(r)}
                      disabled={deletingId === r.id}
                      aria-label="Delete reel"
                      className="shrink-0 rounded-full p-1.5 text-zinc-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </>
      )}
    </section>
  );
}

function MediaGalleryCard({
  profile,
  onUpdated,
  token,
}: {
  profile: TalentProfile;
  onUpdated: (p: TalentProfile) => void;
  token: string;
}) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  if (profile.media.length === 0) return null;

  function startEditing(media: Media) {
    setEditingId(media.id);
    setEditTitle(media.title ?? "");
    setError(null);
  }

  async function handleEditSave(e: FormEvent) {
    e.preventDefault();
    if (!editingId) return;
    setBusyId(editingId);
    setError(null);
    try {
      const updated = await api.updateMyMedia(editingId, { title: editTitle || undefined }, token);
      onUpdated({ ...profile, media: profile.media.map((m) => (m.id === updated.id ? updated : m)) });
      setEditingId(null);
    } catch {
      setError("Could not save this title.");
    } finally {
      setBusyId(null);
    }
  }

  async function handleDelete(media: Media) {
    if (!window.confirm("Delete this media item?")) return;
    setBusyId(media.id);
    setError(null);
    try {
      await api.deleteMyMedia(media.id, token);
      onUpdated({ ...profile, media: profile.media.filter((m) => m.id !== media.id) });
    } catch {
      setError("Could not delete this media item.");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section className={sectionClass}>
      <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Your auditions</h2>
      <p className="mt-1 text-sm text-zinc-500">Preview and play back what you&apos;ve added so far.</p>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2">
        {profile.media.map((m) => (
          <div key={m.id} className="flex flex-col gap-2">
            <MediaCard media={m} />
            {editingId === m.id ? (
              <form onSubmit={handleEditSave} className="flex items-center gap-2">
                <input
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  placeholder="Title"
                  className={`${inputClass} flex-1`}
                />
                <button type="submit" disabled={busyId === m.id} className={btnSmall}>
                  Save
                </button>
                <button type="button" onClick={() => setEditingId(null)} className={btnSmall}>
                  Cancel
                </button>
              </form>
            ) : (
              <div className="flex items-center gap-2">
                <button onClick={() => startEditing(m)} className={btnSmall}>
                  Edit title
                </button>
                <button onClick={() => handleDelete(m)} disabled={busyId === m.id} className={btnSmall}>
                  Delete
                </button>
              </div>
            )}
          </div>
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
  onAdded: (m: Media) => void;
}) {
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [mediaType, setMediaType] = useState<MediaType>("photo");
  const [visibility, setVisibility] = useState<ContentVisibility>("public");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const isUpload = UPLOAD_MEDIA_TYPES.includes(mediaType);
  const videoCount = profile.media.filter((m) => m.media_type === "video").length;
  const videoLimit = profile.tier === "premium" ? PREMIUM_TIER_VIDEO_LIMIT : FREE_TIER_VIDEO_LIMIT;
  const videoLimitReached = mediaType === "video" && videoCount >= videoLimit;

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const input = e.target;
    const picked = input.files?.[0] ?? null;
    if (!picked) return;
    setError(null);
    if (mediaType === "video") {
      try {
        const duration = await getVideoDurationSeconds(picked);
        if (duration > MAX_VIDEO_DURATION_SECONDS) {
          setError(`Videos must be ${MAX_VIDEO_DURATION_SECONDS} seconds or shorter (this one is ${Math.round(duration)}s).`);
          setFile(null);
          input.value = "";
          return;
        }
      } catch {
        // If we can't read the duration client-side, let the upload proceed — the server
        // enforces the real limit either way.
      }
    }
    setFile(picked);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const media = isUpload
        ? await api.uploadMyMedia(
            { file: file!, media_type: mediaType as "video" | "audio", title: title || undefined, visibility },
            token
          )
        : await api.addMyMedia({ url, media_type: mediaType, title: title || undefined, visibility }, token);
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
            {" · "}max {MAX_VIDEO_DURATION_SECONDS}s
          </p>
        )}

        {isUpload ? (
          <label key="file-input" className={labelClass}>
            {mediaType === "video" ? "Video file" : "Audio file"}
            <input
              required
              type="file"
              accept={mediaType === "video" ? "video/*" : "audio/*"}
              onChange={handleFileChange}
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

        <label className={labelClass}>
          Who can see this
          <select value={visibility} onChange={(e) => setVisibility(e.target.value as ContentVisibility)} className={inputClass}>
            {VISIBILITY_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>

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

const LIBRARY_UPLOAD_TYPES: { value: "photo" | "video" | "audio"; label: string }[] = [
  { value: "photo", label: "Photo" },
  { value: "video", label: "Video" },
  { value: "audio", label: "Audio" },
];

function LibraryCard({ profile, token }: { profile: TalentProfile; token: string }) {
  const [items, setItems] = useState<LibraryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState<"upload" | "url">("upload");
  const [mediaType, setMediaType] = useState<"photo" | "video" | "audio">("photo");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [visibility, setVisibility] = useState<ContentVisibility>("public");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const isPremium = profile.tier === "premium";
  const label = libraryLabel(profile.category);

  useEffect(() => {
    if (!isPremium) return;
    api.listMyLibrary(token).then(setItems).catch(() => {}).finally(() => setLoading(false));
  }, [token, isPremium]);

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const input = e.target;
    const picked = input.files?.[0] ?? null;
    if (!picked) return;
    setError(null);
    if (mediaType === "video") {
      try {
        const duration = await getVideoDurationSeconds(picked);
        if (duration > MAX_VIDEO_DURATION_SECONDS) {
          setError(`Videos must be ${MAX_VIDEO_DURATION_SECONDS} seconds or shorter (this one is ${Math.round(duration)}s).`);
          setFile(null);
          input.value = "";
          return;
        }
      } catch {
        // If we can't read the duration client-side, let the upload proceed — the server
        // enforces the real limit either way.
      }
    }
    setFile(picked);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const item =
        mode === "upload"
          ? await api.uploadMyLibraryItem(
              { file: file!, media_type: mediaType, title, description: description || undefined, visibility },
              token
            )
          : await api.addMyLibraryItem(
              { title, description: description || undefined, media_type: mediaType, url, visibility },
              token
            );
      setItems((prev) => [item, ...prev]);
      setTitle("");
      setDescription("");
      setUrl("");
      setFile(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add this item.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(itemId: string) {
    if (!window.confirm("Delete this item from your library?")) return;
    await api.deleteMyLibraryItem(itemId, token);
    setItems((prev) => prev.filter((i) => i.id !== itemId));
  }

  if (!isPremium) {
    return (
      <section className={sectionClass}>
        <h2 className="flex items-center gap-2 font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">
          <Crown className="h-5 w-5" /> {label}
        </h2>
        <p className="mt-2 text-sm text-zinc-500">
          A {label.toLowerCase()} is a Premium feature — upgrade above to build a permanent, public showcase of
          your work that talent hunts can browse anytime, separate from your audition reel.
        </p>
      </section>
    );
  }

  return (
    <section className={sectionClass}>
      <h2 className="flex items-center gap-2 font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">
        <Crown className="h-5 w-5" /> {label}
      </h2>
      <p className="mt-1 text-sm text-zinc-500">
        A permanent showcase of your work, separate from your audition reel — visible on your public profile.
      </p>

      {!loading && items.length > 0 && (
        <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2">
          {items.map((item) => (
            <div key={item.id} className="flex flex-col gap-2">
              <LibraryItemCard item={item} />
              <button onClick={() => handleDelete(item.id)} className={`w-fit ${btnSmall}`}>
                Delete
              </button>
            </div>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit} className="mt-5 flex max-w-md flex-col gap-4">
        <div className="inline-flex w-fit rounded-full border border-zinc-700 p-1 text-xs font-semibold">
          <button
            type="button"
            onClick={() => setMode("upload")}
            className={`rounded-full px-3 py-1 transition-colors ${mode === "upload" ? "bg-rose-600 text-white" : "text-zinc-500"}`}
          >
            Upload file
          </button>
          <button
            type="button"
            onClick={() => setMode("url")}
            className={`rounded-full px-3 py-1 transition-colors ${mode === "url" ? "bg-rose-600 text-white" : "text-zinc-500"}`}
          >
            Paste a link
          </button>
        </div>

        <label className={labelClass}>
          Title
          <input value={title} onChange={(e) => setTitle(e.target.value)} required className={inputClass} />
        </label>

        <fieldset className="grid grid-cols-3 gap-2">
          {LIBRARY_UPLOAD_TYPES.map((t) => (
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

        {mode === "upload" ? (
          <label className={labelClass}>
            File{mediaType === "video" ? ` (max ${MAX_VIDEO_DURATION_SECONDS}s)` : ""}
            <input
              required
              type="file"
              accept={mediaType === "photo" ? "image/*" : mediaType === "video" ? "video/*" : "audio/*"}
              onChange={handleFileChange}
              className={inputClass}
            />
          </label>
        ) : (
          <label className={labelClass}>
            URL
            <input
              required
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://soundcloud.com/…"
              className={inputClass}
            />
          </label>
        )}

        <label className={labelClass}>
          Notes (optional)
          <input value={description} onChange={(e) => setDescription(e.target.value)} className={inputClass} />
        </label>

        <label className={labelClass}>
          Who can see this
          <select value={visibility} onChange={(e) => setVisibility(e.target.value as ContentVisibility)} className={inputClass}>
            {VISIBILITY_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>

        {error && <p className="text-sm text-red-600">{error}</p>}
        <button type="submit" disabled={submitting || (mode === "upload" && !file)} className={`w-fit ${btnSecondary}`}>
          {submitting ? (mode === "upload" ? "Uploading…" : "Adding…") : `Add to ${label.toLowerCase()}`}
        </button>
      </form>
    </section>
  );
}
