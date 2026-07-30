import {
  AtSign,
  Aperture,
  Camera,
  Clapperboard,
  Drama,
  FileText,
  Footprints,
  Globe,
  Image as ImageIcon,
  Laptop,
  Laugh,
  Megaphone,
  Mic,
  Music,
  Music2,
  Paintbrush,
  Palette,
  PartyPopper,
  PenTool,
  PlayCircle,
  Shirt,
  Sparkles,
  ThumbsUp,
  Tv,
  Users,
  Video,
  type LucideIcon,
} from "lucide-react";

import type { CreditProjectType, Media } from "./api";

export function coverPhotoUrl(media: Media[]): string | undefined {
  const photos = media.filter((m) => m.media_type === "photo");
  return photos.find((m) => m.is_cover)?.url ?? photos[0]?.url;
}

export const btnPrimary =
  "inline-flex items-center justify-center gap-1.5 rounded-md bg-rose-600 px-6 py-3 text-sm font-bold uppercase tracking-wide text-white shadow-sm transition-all hover:bg-rose-700 active:translate-y-px disabled:cursor-not-allowed disabled:opacity-50";

export const btnSecondary =
  "inline-flex items-center justify-center gap-1.5 whitespace-nowrap rounded-md border-2 border-zinc-900 bg-transparent px-6 py-3 text-sm font-bold uppercase tracking-wide text-zinc-900 transition-all hover:bg-zinc-900 hover:text-white active:translate-y-px disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-100 dark:text-zinc-100 dark:hover:bg-zinc-100 dark:hover:text-zinc-900";

export const btnSmall =
  "inline-flex items-center justify-center gap-1 whitespace-nowrap rounded-md border border-zinc-300 px-3.5 py-1.5 text-xs font-bold uppercase tracking-wide text-zinc-700 transition-colors hover:border-rose-500 hover:text-rose-600 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:border-rose-500 dark:hover:text-rose-400";

export const btnSmallPrimary =
  "inline-flex items-center justify-center gap-1 whitespace-nowrap rounded-md bg-rose-600 px-3.5 py-1.5 text-xs font-bold uppercase tracking-wide text-white transition-colors hover:bg-rose-700 disabled:cursor-not-allowed disabled:opacity-50";

export const eyebrowClass =
  "inline-flex items-center rounded-sm bg-zinc-900 px-3 py-1 text-xs font-bold uppercase tracking-widest text-white dark:bg-zinc-100 dark:text-zinc-900";

export const inputClass =
  "w-full rounded-md border-2 border-zinc-200 bg-white px-4 py-2.5 text-sm text-zinc-900 placeholder:text-zinc-400 focus:border-rose-500 focus:outline-none focus:ring-2 focus:ring-rose-100 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50 dark:focus:ring-rose-900/40";

export const labelClass = "flex flex-col gap-1.5 text-sm font-medium text-zinc-700 dark:text-zinc-300";

export const cardClass =
  "rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900";

export const sectionClass =
  "rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900";

export function badgeClass(tone: "neutral" | "success" | "warning" | "info" = "neutral") {
  const tones: Record<string, string> = {
    neutral: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
    success: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
    warning: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
    info: "bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300",
  };
  return `inline-flex items-center rounded-sm px-3 py-1 text-xs font-bold uppercase tracking-wide ${tones[tone]}`;
}

export const premiumBadgeClass =
  "inline-flex items-center gap-1 rounded-sm bg-gradient-to-r from-amber-400 to-yellow-500 px-2.5 py-0.5 text-xs font-bold uppercase tracking-wide text-zinc-900";

export const verifiedBadgeClass =
  "inline-flex items-center gap-1 rounded-sm bg-blue-600 px-2.5 py-0.5 text-xs font-bold uppercase tracking-wide text-white";

export const neutralBadgeClass =
  "inline-flex items-center gap-1 rounded-sm bg-zinc-100 px-2.5 py-0.5 text-xs font-bold uppercase tracking-wide text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300";

export function recruiterTypeLabel(recruiterType: string): string {
  return recruiterType === "individual" ? "Individual" : "Agency";
}

export function statusTone(status: string): "neutral" | "success" | "warning" | "info" {
  if (status === "open" || status === "accepted") return "success";
  if (status === "shortlisted") return "info";
  if (status === "rejected" || status === "closed") return "neutral";
  return "warning";
}

export function formatRelativeTime(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} minute${minutes === 1 ? "" : "s"} ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"} ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days} day${days === 1 ? "" : "s"} ago`;
  const months = Math.floor(days / 30);
  return `${months} month${months === 1 ? "" : "s"} ago`;
}

export function invitationStatusTone(status: string): "neutral" | "success" | "warning" | "info" {
  if (status === "accepted") return "success";
  if (status === "declined") return "neutral";
  return "warning";
}

export function bookingStatusTone(status: string): "neutral" | "success" | "warning" | "info" {
  if (status === "accepted") return "success";
  if (status === "declined" || status === "cancelled") return "neutral";
  return "warning";
}

export const DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

// Bookings are stored and compared as a shared, timezone-naive wall clock (matching the
// timezone-naive availability windows they're validated against) — display must force UTC
// so the viewer sees the exact time that was entered, not a shift based on their own timezone.
export function formatBookingRange(startIso: string, endIso: string): string {
  const start = new Date(startIso);
  const end = new Date(endIso);
  const startLabel = start.toLocaleString(undefined, {
    timeZone: "UTC",
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
  const endLabel = end.toLocaleTimeString(undefined, { timeZone: "UTC", hour: "numeric", minute: "2-digit" });
  return `${startLabel} – ${endLabel}`;
}

export function formatTimeOfDay(time: string): string {
  const [h, m] = time.split(":");
  const hour = parseInt(h, 10);
  const period = hour >= 12 ? "PM" : "AM";
  const displayHour = hour % 12 === 0 ? 12 : hour % 12;
  return `${displayHour}:${m} ${period}`;
}

interface CategoryColor {
  solid: string;
  soft: string;
  gradient: string;
}

const CATEGORY_COLORS: Record<string, CategoryColor> = {
  acting: { solid: "bg-rose-500", soft: "bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300", gradient: "from-rose-400 to-rose-600" },
  singing: { solid: "bg-amber-500", soft: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300", gradient: "from-amber-400 to-orange-500" },
  dancing: { solid: "bg-fuchsia-500", soft: "bg-fuchsia-100 text-fuchsia-700 dark:bg-fuchsia-900/40 dark:text-fuchsia-300", gradient: "from-fuchsia-400 to-pink-500" },
  painting: { solid: "bg-orange-500", soft: "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300", gradient: "from-orange-400 to-red-500" },
  script_writing: { solid: "bg-blue-500", soft: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300", gradient: "from-blue-400 to-indigo-500" },
  photography: { solid: "bg-cyan-500", soft: "bg-cyan-100 text-cyan-700 dark:bg-cyan-900/40 dark:text-cyan-300", gradient: "from-cyan-400 to-blue-500" },
  music: { solid: "bg-violet-500", soft: "bg-violet-100 text-violet-700 dark:bg-violet-900/40 dark:text-violet-300", gradient: "from-violet-400 to-purple-600" },
  choreography: { solid: "bg-pink-500", soft: "bg-pink-100 text-pink-700 dark:bg-pink-900/40 dark:text-pink-300", gradient: "from-pink-400 to-rose-500" },
  comedy: { solid: "bg-yellow-500", soft: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300", gradient: "from-yellow-400 to-amber-500" },
  voice_over: { solid: "bg-teal-500", soft: "bg-teal-100 text-teal-700 dark:bg-teal-900/40 dark:text-teal-300", gradient: "from-teal-400 to-emerald-500" },
  direction: { solid: "bg-indigo-500", soft: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300", gradient: "from-indigo-400 to-violet-600" },
  modeling: { solid: "bg-purple-500", soft: "bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300", gradient: "from-purple-400 to-fuchsia-600" },
  design: { solid: "bg-emerald-500", soft: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300", gradient: "from-emerald-400 to-teal-500" },
  other: { solid: "bg-slate-500", soft: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300", gradient: "from-slate-400 to-slate-600" },
};

const DEFAULT_CATEGORY_COLOR: CategoryColor = CATEGORY_COLORS.other;

export function categoryColor(category: string): CategoryColor {
  return CATEGORY_COLORS[category] ?? DEFAULT_CATEGORY_COLOR;
}

export function categoryBadgeClass(category: string): string {
  return `inline-flex items-center rounded-sm px-3 py-1 text-xs font-bold uppercase tracking-wide ${categoryColor(category).soft}`;
}

export function initials(name: string): string {
  const parts = name.trim().split(/\s+/);
  const first = parts[0]?.[0] ?? "";
  const last = parts.length > 1 ? parts[parts.length - 1][0] : "";
  return (first + last).toUpperCase();
}

export function avatarGradient(seed: string): string {
  const keys = Object.keys(CATEGORY_COLORS);
  let hash = 0;
  for (let i = 0; i < seed.length; i++) hash = (hash * 31 + seed.charCodeAt(i)) >>> 0;
  return CATEGORY_COLORS[keys[hash % keys.length]].gradient;
}

export const CATEGORY_ICONS: Record<string, LucideIcon> = {
  acting: Drama,
  singing: Music2,
  dancing: Footprints,
  painting: Palette,
  script_writing: PenTool,
  photography: Camera,
  music: Music,
  choreography: Users,
  comedy: Laugh,
  voice_over: Mic,
  direction: Video,
  modeling: Shirt,
  design: Paintbrush,
  other: Sparkles,
};

export function categoryIcon(category: string): LucideIcon {
  return CATEGORY_ICONS[category] ?? CATEGORY_ICONS.other;
}

export function formatCategory(category: string): string {
  return category
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export const MEDIA_TYPE_ICONS: Record<string, LucideIcon> = {
  photo: ImageIcon,
  video: Video,
  audio: Music,
  document: FileText,
};

export type SocialLinkKey = "instagram_url" | "facebook_url" | "tiktok_url" | "twitter_url" | "youtube_url" | "website_url";

export const SOCIAL_LINK_FIELDS: { key: SocialLinkKey; label: string; icon: LucideIcon }[] = [
  { key: "instagram_url", label: "Instagram", icon: Aperture },
  { key: "facebook_url", label: "Facebook", icon: ThumbsUp },
  { key: "tiktok_url", label: "TikTok", icon: Music2 },
  { key: "twitter_url", label: "X / Twitter", icon: AtSign },
  { key: "youtube_url", label: "YouTube", icon: PlayCircle },
  { key: "website_url", label: "Website", icon: Globe },
];

interface SkillsQuestion {
  label: string;
  placeholder: string;
}

const SKILLS_QUESTIONS: Record<string, SkillsQuestion> = {
  acting: { label: "Genres and styles you act in", placeholder: "e.g. drama, comedy, thriller, Sinhala theatre" },
  singing: { label: "Genres you sing", placeholder: "e.g. pop, classical, playback, Sinhala folk" },
  dancing: { label: "Dance styles", placeholder: "e.g. Kandyan, contemporary, hip-hop, Bharatanatyam" },
  painting: { label: "Mediums and styles", placeholder: "e.g. oil, watercolor, digital, abstract" },
  script_writing: { label: "Languages and formats you write in", placeholder: "e.g. Sinhala, English, screenplay, teleplay" },
  photography: { label: "Photography genres", placeholder: "e.g. portrait, wedding, product, wildlife" },
  music: { label: "Instruments and genres", placeholder: "e.g. guitar, tabla, jazz, classical" },
  choreography: { label: "Choreography styles", placeholder: "e.g. Kandyan, contemporary, Bollywood" },
  comedy: { label: "Comedy formats", placeholder: "e.g. stand-up, sketch, improv" },
  voice_over: { label: "Languages and styles", placeholder: "e.g. Sinhala, English, narration, character voices" },
  direction: { label: "Genres you direct", placeholder: "e.g. drama, documentary, advertising" },
  modeling: { label: "Modeling types", placeholder: "e.g. runway, print, commercial" },
  design: { label: "Design specialties", placeholder: "e.g. graphic design, fashion design, set design" },
  other: { label: "Special skills", placeholder: "Describe your special skills" },
};

export function skillsQuestion(category: string): SkillsQuestion {
  return SKILLS_QUESTIONS[category] ?? SKILLS_QUESTIONS.other;
}

export interface DetectedEmbed {
  type: "youtube" | "spotify";
  embedUrl: string;
}

export function detectEmbed(url: string): DetectedEmbed | null {
  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch {
    return null;
  }

  const host = parsed.hostname.replace(/^www\./, "");

  if (host === "youtube.com" || host === "m.youtube.com" || host === "youtu.be") {
    let videoId = "";
    if (host === "youtu.be") {
      videoId = parsed.pathname.slice(1);
    } else if (parsed.pathname === "/watch") {
      videoId = parsed.searchParams.get("v") ?? "";
    } else if (parsed.pathname.startsWith("/embed/")) {
      videoId = parsed.pathname.slice("/embed/".length);
    } else if (parsed.pathname.startsWith("/shorts/")) {
      videoId = parsed.pathname.slice("/shorts/".length);
    }
    videoId = videoId.split("/")[0]?.split("?")[0] ?? "";
    return videoId ? { type: "youtube", embedUrl: `https://www.youtube.com/embed/${videoId}` } : null;
  }

  if (host === "open.spotify.com") {
    const path = parsed.pathname.replace(/^\/intl-[a-z]+\//, "/");
    return path.length > 1 ? { type: "spotify", embedUrl: `https://open.spotify.com/embed${path}` } : null;
  }

  return null;
}

interface AttributeField {
  key: string;
  label: string;
  placeholder: string;
}

// What "detailed profile" means varies by category — an actor's height/build/eye color has
// no equivalent for a scriptwriter, and vice versa. Each category gets its own small set of
// structured fields, stored in TalentProfile.attributes as a flat key/value map.
export const CATEGORY_ATTRIBUTES: Record<string, AttributeField[]> = {
  acting: [
    { key: "height", label: "Height", placeholder: "e.g. 5'9\" / 175cm" },
    { key: "weight", label: "Weight", placeholder: "e.g. 70kg" },
    { key: "build", label: "Build", placeholder: "e.g. athletic, slim, average" },
    { key: "hair_color", label: "Hair color", placeholder: "e.g. black" },
    { key: "eye_color", label: "Eye color", placeholder: "e.g. brown" },
    { key: "playing_age", label: "Playing age range", placeholder: "e.g. 25-35" },
    { key: "ethnicity", label: "Ethnicity", placeholder: "e.g. South Asian" },
  ],
  modeling: [
    { key: "height", label: "Height", placeholder: "e.g. 5'9\" / 175cm" },
    { key: "weight", label: "Weight", placeholder: "e.g. 55kg" },
    { key: "bust_chest", label: "Bust / chest", placeholder: "e.g. 34\" / 86cm" },
    { key: "waist", label: "Waist", placeholder: "e.g. 26\" / 66cm" },
    { key: "hips", label: "Hips", placeholder: "e.g. 36\" / 91cm" },
    { key: "shoe_size", label: "Shoe size", placeholder: "e.g. UK 6" },
    { key: "hair_color", label: "Hair color", placeholder: "e.g. black" },
    { key: "eye_color", label: "Eye color", placeholder: "e.g. brown" },
  ],
  dancing: [
    { key: "height", label: "Height", placeholder: "e.g. 5'6\" / 168cm" },
    { key: "build", label: "Build", placeholder: "e.g. athletic" },
  ],
  singing: [
    { key: "vocal_range", label: "Vocal range", placeholder: "e.g. mezzo-soprano" },
    { key: "voice_type", label: "Voice type", placeholder: "e.g. belt/pop, classical" },
  ],
  music: [{ key: "primary_instrument", label: "Primary instrument", placeholder: "e.g. guitar" }],
  painting: [{ key: "primary_medium", label: "Primary medium", placeholder: "e.g. oil on canvas" }],
  script_writing: [{ key: "primary_language", label: "Primary writing language", placeholder: "e.g. Sinhala" }],
  photography: [{ key: "camera_gear", label: "Camera gear", placeholder: "e.g. Sony A7IV, 24-70mm f/2.8" }],
  choreography: [{ key: "height", label: "Height", placeholder: "e.g. 5'6\" / 168cm" }],
  comedy: [{ key: "performance_style", label: "Performance style", placeholder: "e.g. observational, improv" }],
  voice_over: [
    { key: "languages_spoken", label: "Languages", placeholder: "e.g. Sinhala, English, Tamil" },
    { key: "accent_specialties", label: "Accent specialties", placeholder: "e.g. British RP, American" },
  ],
  direction: [{ key: "primary_genre", label: "Primary genre", placeholder: "e.g. drama, documentary" }],
  design: [{ key: "software_tools", label: "Software / tools", placeholder: "e.g. Figma, Adobe Illustrator" }],
  other: [],
};

export function categoryAttributeFields(category: string): AttributeField[] {
  return CATEGORY_ATTRIBUTES[category] ?? [];
}

// A pitch/intro video fits performance categories (you show yourself doing the thing) but not
// craft/output categories like painting or design, where the portfolio media speaks for itself.
const INTRO_VIDEO_CATEGORIES = new Set([
  "acting",
  "singing",
  "dancing",
  "choreography",
  "comedy",
  "voice_over",
  "direction",
  "modeling",
  "music",
]);

export function categoryShowsIntroVideo(category: string): boolean {
  return INTRO_VIDEO_CATEGORIES.has(category);
}

export const CREDIT_PROJECT_TYPES: { value: CreditProjectType; label: string; icon: LucideIcon }[] = [
  { value: "film", label: "Film", icon: Clapperboard },
  { value: "television", label: "Television", icon: Tv },
  { value: "commercial", label: "Commercial", icon: Megaphone },
  { value: "theatre", label: "Theatre", icon: Drama },
  { value: "voice", label: "Voice", icon: Mic },
  { value: "music", label: "Music", icon: Music },
  { value: "event", label: "Event", icon: PartyPopper },
  { value: "online", label: "Online / digital", icon: Laptop },
  { value: "other", label: "Other", icon: Sparkles },
];

export function creditProjectTypeLabel(type: string): string {
  return CREDIT_PROJECT_TYPES.find((t) => t.value === type)?.label ?? "Other";
}

export function creditProjectTypeIcon(type: string): LucideIcon {
  return CREDIT_PROJECT_TYPES.find((t) => t.value === type)?.icon ?? Sparkles;
}
