import { createElement } from "react";
import { FileText } from "lucide-react";
import { Media } from "@/lib/api";
import { MEDIA_TYPE_ICONS, detectEmbed } from "@/lib/ui";

export default function MediaCard({ media }: { media: Media }) {
  const embed = detectEmbed(media.url);

  if (media.media_type === "video" && embed?.type === "youtube") {
    return (
      <div className="overflow-hidden rounded-xl border-2 border-zinc-100 dark:border-zinc-800">
        <div className="aspect-video">
          <iframe
            src={embed.embedUrl}
            title={media.title ?? "YouTube video"}
            className="h-full w-full"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        </div>
        {media.title && <p className="p-3 text-sm font-semibold text-zinc-900 dark:text-zinc-50">{media.title}</p>}
      </div>
    );
  }

  if (media.media_type === "video") {
    return (
      <div className="overflow-hidden rounded-xl border-2 border-zinc-100 dark:border-zinc-800">
        <div className="aspect-video bg-black">
          {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
          <video controls playsInline preload="metadata" src={media.url} className="h-full w-full">
            Your browser doesn&apos;t support video playback.{" "}
            <a href={media.url} className="underline">
              Download the file
            </a>
            .
          </video>
        </div>
        {media.title && <p className="p-3 text-sm font-semibold text-zinc-900 dark:text-zinc-50">{media.title}</p>}
      </div>
    );
  }

  if (media.media_type === "audio" && embed?.type === "spotify") {
    return (
      <div className="overflow-hidden rounded-xl border-2 border-zinc-100 dark:border-zinc-800">
        <iframe
          src={embed.embedUrl}
          title={media.title ?? "Spotify track"}
          className="h-[152px] w-full"
          allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
        />
      </div>
    );
  }

  if (media.media_type === "photo") {
    return (
      <a
        href={media.url}
        target="_blank"
        rel="noopener noreferrer"
        className="group block aspect-square overflow-hidden rounded-xl bg-zinc-100 dark:bg-zinc-800"
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={media.url}
          alt={media.title ?? ""}
          className="h-full w-full object-cover transition-transform group-hover:scale-105"
        />
        {media.title && (
          <span className="block truncate bg-black/60 px-3 py-1.5 text-xs text-white">{media.title}</span>
        )}
      </a>
    );
  }

  if (media.media_type === "audio") {
    return (
      <div className="rounded-xl border-2 border-zinc-100 p-4 dark:border-zinc-800">
        <p className="flex items-center gap-2 text-sm font-semibold text-zinc-900 dark:text-zinc-50">
          <MEDIA_TYPE_ICONS.audio className="h-4 w-4" />
          {media.title ?? "Audio audition"}
        </p>
        {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
        <audio controls src={media.url} className="mt-3 w-full">
          Your browser doesn&apos;t support audio playback.{" "}
          <a href={media.url} className="underline">
            Download the file
          </a>
          .
        </audio>
      </div>
    );
  }

  return (
    <a
      href={media.url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center gap-3 rounded-xl border-2 border-zinc-100 p-4 hover:border-rose-300 dark:border-zinc-800 dark:hover:border-rose-800"
    >
      {createElement(MEDIA_TYPE_ICONS[media.media_type] ?? FileText, { className: "h-6 w-6 text-zinc-500" })}
      <div>
        <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">{media.title ?? "View document"}</p>
        <p className="text-xs capitalize text-zinc-500">{media.media_type}</p>
      </div>
    </a>
  );
}
