import { Clapperboard, Music2, Tv, type LucideIcon } from "lucide-react";
import { avatarGradient } from "@/lib/ui";
import { WorkType } from "@/lib/api";

const WORK_TYPE_ICONS: Record<WorkType, LucideIcon> = {
  film: Clapperboard,
  tv_series: Tv,
  song: Music2,
};

export default function TitlePoster({
  name,
  workType,
  posterUrl,
  className = "h-full w-full",
  iconClassName = "h-10 w-10",
}: {
  name: string;
  workType: WorkType;
  posterUrl?: string | null;
  className?: string;
  iconClassName?: string;
}) {
  if (posterUrl) {
    // eslint-disable-next-line @next/next/no-img-element
    return <img src={posterUrl} alt={name} className={`${className} object-cover`} />;
  }
  const Icon = WORK_TYPE_ICONS[workType];
  return (
    <div className={`${className} flex items-center justify-center bg-gradient-to-br ${avatarGradient(name)}`}>
      <Icon className={`${iconClassName} text-white/60`} strokeWidth={1.5} />
    </div>
  );
}
