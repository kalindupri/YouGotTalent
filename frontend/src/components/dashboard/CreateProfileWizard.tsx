"use client";

import { FormEvent, useState } from "react";
import {
  ApiError,
  Media,
  MyTalentProfile,
  TALENT_CATEGORIES,
  TalentCategory,
  api,
} from "@/lib/api";
import {
  btnPrimary,
  btnSecondary,
  formatCategory,
  inputClass,
  labelClass,
  sectionClass,
  skillsQuestion,
} from "@/lib/ui";
import DateOfBirthInput from "@/components/DateOfBirthInput";
import HeadshotUploader from "@/components/HeadshotUploader";
import GuardianConsentCard from "@/components/dashboard/GuardianConsentCard";

/** Talent onboarding, one question per screen.
 *
 * Replaces a single form that asked for craft, date of birth, gender, fourteen category
 * checkboxes, skills, city and bio at once. Three things drive the shape:
 *
 * 1. Craft first. It is the question a performer can answer without thinking, and it decides
 *    what the later steps should even ask about.
 * 2. The under-18 question is asked OUT LOUD, before any date of birth. Previously a minor
 *    discovered that a guardian must hold the account from helper text under the date field --
 *    after they had already filled the form in. Asking plainly routes the two paths cleanly and
 *    puts guardian consent inside onboarding rather than after it.
 * 3. A headshot is required to finish. A profile with no face is the one thing a recruiter
 *    cannot use, and leaving it optional is why empty profiles exist.
 *
 * The profile row has to exist before guardian consent or a headshot can be attached, so it is
 * created at the end of step 3; steps 4 and 5 then act on it. Someone who closes the tab midway
 * keeps the profile and is picked up by the dashboard's own consent card and headshot prompt --
 * the wizard is a better path through the same endpoints, not a separate one.
 */

type Step = "craft" | "basics" | "age" | "guardian" | "headshot";

const ADULT_STEPS: Step[] = ["craft", "basics", "age", "headshot"];
const MINOR_STEPS: Step[] = ["craft", "basics", "age", "guardian", "headshot"];

function parseSkills(raw: string): string[] {
  return raw
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

function StepChrome({
  steps,
  current,
  children,
}: {
  steps: Step[];
  current: Step;
  children: React.ReactNode;
}) {
  const index = steps.indexOf(current);
  return (
    <div className={sectionClass}>
      <div className="flex gap-1" role="progressbar" aria-valuenow={index + 1} aria-valuemin={1} aria-valuemax={steps.length} aria-label="Profile setup progress">
        {steps.map((s, i) => (
          <span
            key={s}
            className={`h-1 flex-1 rounded-full ${i <= index ? "bg-rose-600" : "bg-zinc-200 dark:bg-zinc-800"}`}
          />
        ))}
      </div>
      <p className="mt-3 text-xs font-semibold uppercase tracking-wide text-zinc-500">
        Step {index + 1} of {steps.length}
      </p>
      {children}
    </div>
  );
}

export default function CreateProfileWizard({
  token,
  onCreated,
  onFinished,
}: {
  token: string;
  onCreated: (p: MyTalentProfile) => void;
  onFinished: () => void;
}) {
  const [step, setStep] = useState<Step>("craft");
  const [profile, setProfile] = useState<MyTalentProfile | null>(null);

  const [categories, setCategories] = useState<TalentCategory[]>([]);
  const [displayName, setDisplayName] = useState("");
  const [city, setCity] = useState("");
  const [gender, setGender] = useState("");
  const [skillsInput, setSkillsInput] = useState("");
  const [isMinor, setIsMinor] = useState<boolean | null>(null);
  const [dateOfBirth, setDateOfBirth] = useState("");

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const steps = isMinor ? MINOR_STEPS : ADULT_STEPS;

  function toggleCategory(c: TalentCategory) {
    setCategories((prev) => (prev.includes(c) ? prev.filter((x) => x !== c) : [...prev, c]));
  }

  async function createProfile(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!dateOfBirth) {
      setError("Please give a full date of birth.");
      return;
    }
    setSubmitting(true);
    try {
      const created = await api.createMyTalentProfile(
        {
          display_name: displayName,
          categories,
          city: city || null,
          bio: null,
          date_of_birth: dateOfBirth,
          gender: gender || null,
          experience_years: null,
          skills: parseSkills(skillsInput),
        },
        token
      );
      setProfile(created);
      onCreated(created);
      // The server decides whether consent is actually required -- it knows the real age, and
      // it is the authority whatever the person answered on the previous screen.
      setStep(created.guardian_consent_status === "not_required" ? "headshot" : "guardian");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create your profile.");
    } finally {
      setSubmitting(false);
    }
  }

  function handleHeadshot(media: Media) {
    if (profile) onCreated({ ...profile, media: [...profile.media, media] });
    onFinished();
  }

  // ---- Step 1: craft -------------------------------------------------------------------
  if (step === "craft") {
    return (
      <StepChrome steps={steps} current="craft">
        <h2 className="mt-2 font-heading text-2xl font-extrabold tracking-tight text-zinc-900 dark:text-zinc-50">
          What kind of work?
        </h2>
        <p className="mt-1 text-sm text-zinc-500">Pick your main craft. You can add more any time.</p>
        <div className="mt-5 grid max-w-md grid-cols-2 gap-2 sm:grid-cols-3">
          {TALENT_CATEGORIES.map((c) => {
            const on = categories.includes(c);
            return (
              <button
                key={c}
                type="button"
                aria-pressed={on}
                onClick={() => toggleCategory(c)}
                className={`min-h-[44px] rounded-md border-2 px-3 py-2.5 text-sm font-semibold transition-colors ${
                  on
                    ? "border-rose-600 bg-rose-600 text-white"
                    : "border-zinc-200 text-zinc-700 hover:border-rose-300 hover:bg-rose-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:border-rose-800 dark:hover:bg-rose-950"
                }`}
              >
                {formatCategory(c)}
              </button>
            );
          })}
        </div>
        {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
        <button
          type="button"
          disabled={categories.length === 0}
          onClick={() => {
            setError(null);
            setStep("basics");
          }}
          className={`mt-6 w-full max-w-md ${btnPrimary}`}
        >
          Continue
        </button>
      </StepChrome>
    );
  }

  // ---- Step 2: basics ------------------------------------------------------------------
  if (step === "basics") {
    const skills = skillsQuestion(categories[0] ?? "acting");
    return (
      <StepChrome steps={steps} current="basics">
        <h2 className="mt-2 font-heading text-2xl font-extrabold tracking-tight text-zinc-900 dark:text-zinc-50">
          The basics
        </h2>
        <p className="mt-1 text-sm text-zinc-500">This is what talent hunts see when they search.</p>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            setStep("age");
          }}
          className="mt-5 flex max-w-md flex-col gap-4"
        >
          <label className={labelClass}>
            Stage name
            <input required value={displayName} onChange={(e) => setDisplayName(e.target.value)} className={inputClass} />
          </label>
          <label className={labelClass}>
            City
            <input value={city} onChange={(e) => setCity(e.target.value)} className={inputClass} />
          </label>
          <label className={labelClass}>
            Gender
            <select value={gender} onChange={(e) => setGender(e.target.value)} className={inputClass}>
              <option value="">Prefer not to say</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
            </select>
          </label>
          <label className={labelClass}>
            {skills.label}
            <input
              value={skillsInput}
              onChange={(e) => setSkillsInput(e.target.value)}
              placeholder={skills.placeholder}
              className={inputClass}
            />
          </label>
          <div className="flex gap-2">
            <button type="button" onClick={() => setStep("craft")} className={btnSecondary}>
              Back
            </button>
            <button type="submit" className={`flex-1 ${btnPrimary}`}>
              Continue
            </button>
          </div>
        </form>
      </StepChrome>
    );
  }

  // ---- Step 3: the age question, then the date ------------------------------------------
  if (step === "age") {
    return (
      <StepChrome steps={steps} current="age">
        <h2 className="mt-2 font-heading text-2xl font-extrabold tracking-tight text-zinc-900 dark:text-zinc-50">
          Who is this profile for?
        </h2>
        <p className="mt-1 text-sm text-zinc-500">This decides who holds the account, so we ask it up front.</p>

        <div className="mt-5 flex max-w-md flex-col gap-2.5">
          {[
            {
              minor: false,
              title: "It's for me, I'm 18 or over",
              body: "We'll confirm your date of birth below.",
            },
            {
              minor: true,
              title: "It's for someone under 18",
              body: "A parent or legal guardian must hold the account and give consent.",
            },
          ].map((opt) => (
            <button
              key={String(opt.minor)}
              type="button"
              aria-pressed={isMinor === opt.minor}
              onClick={() => setIsMinor(opt.minor)}
              className={`rounded-xl border-2 p-4 text-left transition-colors ${
                isMinor === opt.minor
                  ? "border-zinc-900 dark:border-zinc-100"
                  : "border-zinc-200 hover:border-zinc-400 dark:border-zinc-800 dark:hover:border-zinc-600"
              }`}
            >
              <span className="block text-sm font-bold text-zinc-900 dark:text-zinc-50">{opt.title}</span>
              <span className="mt-0.5 block text-xs text-zinc-500">{opt.body}</span>
            </button>
          ))}
        </div>

        {isMinor !== null && (
          <form onSubmit={createProfile} className="mt-5 flex max-w-md flex-col gap-4">
            <div className={labelClass}>
              {isMinor ? "The child's date of birth" : "Your date of birth"}
              <DateOfBirthInput required value={dateOfBirth} onChange={setDateOfBirth} />
              <span className="mt-1 block text-xs font-normal text-zinc-500">
                Never shown publicly — talent hunts only see an age.
              </span>
            </div>
            <p className="rounded-md bg-rose-50 p-3 text-xs leading-relaxed text-rose-700 dark:bg-rose-950 dark:text-rose-300">
              Under Sri Lanka&apos;s Personal Data Protection Act, a child&apos;s data needs a parent or
              guardian&apos;s consent. Paid work has a minimum age of 16.
            </p>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <div className="flex gap-2">
              <button type="button" onClick={() => setStep("basics")} className={btnSecondary}>
                Back
              </button>
              <button type="submit" disabled={submitting} className={`flex-1 ${btnPrimary}`}>
                {submitting ? "Creating…" : "Continue"}
              </button>
            </div>
          </form>
        )}
      </StepChrome>
    );
  }

  // ---- Step 4: guardian consent (minors only) -------------------------------------------
  if (step === "guardian" && profile) {
    return (
      <StepChrome steps={steps} current="guardian">
        <h2 className="mt-2 font-heading text-2xl font-extrabold tracking-tight text-zinc-900 dark:text-zinc-50">
          Guardian consent
        </h2>
        <p className="mt-1 max-w-md text-sm text-zinc-500">
          Browsing works right away. Applying to talent hunts unlocks once we approve this — usually
          within a day.
        </p>
        <div className="mt-5">
          <GuardianConsentCard
            profile={profile}
            token={token}
            onSubmitted={() => {
              api
                .getMyTalentProfile(token)
                .then((p) => {
                  setProfile(p);
                  onCreated(p);
                })
                .catch(() => {});
              setStep("headshot");
            }}
          />
        </div>
        <button type="button" onClick={() => setStep("headshot")} className="mt-4 text-sm font-semibold text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100">
          I&apos;ll do this later
        </button>
      </StepChrome>
    );
  }

  // ---- Step 5: headshot, required --------------------------------------------------------
  return (
    <StepChrome steps={steps} current="headshot">
      <h2 className="mt-2 font-heading text-2xl font-extrabold tracking-tight text-zinc-900 dark:text-zinc-50">
        Add a headshot
      </h2>
      <p className="mt-1 max-w-md text-sm text-zinc-500">
        This is the one thing every recruiter looks at. Clear, recent, just you — no sunglasses.
      </p>
      <div className="mt-5 flex max-w-md flex-col gap-3">
        <HeadshotUploader token={token} hasExisting={false} onUploaded={handleHeadshot} />
        <p className="text-xs text-zinc-500">
          A profile without a photo is very rarely opened, so this is the last step rather than an
          optional extra.
        </p>
        {/* The wall is deliberately low. The profile row already exists by this point (guardian
            consent and the photo both need something to attach to), so anyone who closes the tab
            keeps a photo-less profile regardless -- a hard block here would add friction without
            actually preventing the thing it is aimed at. Real enforcement belongs on the apply
            path, server-side: no cover photo, no application. */}
        <button
          type="button"
          onClick={onFinished}
          className="self-start text-sm font-semibold text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
        >
          I&apos;ll add a photo later
        </button>
      </div>
    </StepChrome>
  );
}
