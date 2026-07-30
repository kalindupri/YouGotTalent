import { Play } from "lucide-react";
import { detectEmbed } from "@/lib/ui";

const VIDEO_EXTENSIONS = [".mp4", ".mov", ".webm", ".m4v", ".avi"];
const AUDIO_EXTENSIONS = [".mp3", ".m4a", ".wav", ".aac", ".ogg"];

function hasExtension(url: string, extensions: string[]): boolean {
  const path = url.split("?")[0].toLowerCase();
  return extensions.some((ext) => path.endsWith(ext));
}

export default function SubmissionPreview({ url }: { url: string }) {
  const embed = detectEmbed(url);

  if (embed?.type === "youtube") {
    return (
      <div className="mt-2 aspect-video w-full max-w-sm overflow-hidden rounded-lg border border-zinc-200 dark:border-zinc-800">
        <iframe
          src={embed.embedUrl}
          title="Submission"
          className="h-full w-full"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        />
      </div>
    );
  }

  if (embed?.type === "spotify") {
    return (
      <div className="mt-2 w-full max-w-sm overflow-hidden rounded-lg border border-zinc-200 dark:border-zinc-800">
        <iframe
          src={embed.embedUrl}
          title="Submission"
          className="h-[152px] w-full"
          allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
        />
      </div>
    );
  }

  if (hasExtension(url, VIDEO_EXTENSIONS)) {
    return (
      <div className="mt-2 aspect-video w-full max-w-sm overflow-hidden rounded-lg border border-zinc-200 bg-black dark:border-zinc-800">
        {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
        <video controls playsInline preload="metadata" src={url} className="h-full w-full" />
      </div>
    );
  }

  if (hasExtension(url, AUDIO_EXTENSIONS)) {
    return (
      // eslint-disable-next-line jsx-a11y/media-has-caption
      <audio controls src={url} className="mt-2 w-full max-w-sm" />
    );
  }

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="mt-1 flex items-center gap-1 text-xs font-semibold text-emerald-700 hover:underline dark:text-emerald-400"
    >
      <Play className="h-3 w-3" fill="currentColor" strokeWidth={0} /> View their submission
    </a>
  );
}
