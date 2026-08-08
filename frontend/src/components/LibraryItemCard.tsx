import { createElement } from "react";
import { FileText } from "lucide-react";
import { LibraryItem } from "@/lib/api";
import { MEDIA_TYPE_ICONS, detectEmbed } from "@/lib/ui";

export default function LibraryItemCard({ item }: { item: LibraryItem }) {
  const embed = detectEmbed(item.url);

  if (item.media_type === "video" && embed?.type === "youtube") {
    return (
      <div className="overflow-hidden rounded-xl border-2 border-zinc-100 dark:border-zinc-800">
        <div className="aspect-video">
          <iframe
            src={embed.embedUrl}
            title={item.title}
            className="h-full w-full"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        </div>
        <div className="p-3">
          <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">{item.title}</p>
          {item.description && <p className="mt-0.5 text-xs text-zinc-500">{item.description}</p>}
        </div>
      </div>
    );
  }

  if (item.media_type === "video") {
    return (
      <div className="overflow-hidden rounded-xl border-2 border-zinc-100 dark:border-zinc-800">
        <div className="aspect-video bg-black">
          {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
          <video controls playsInline preload="metadata" src={item.url} className="h-full w-full">
            Your browser doesn&apos;t support video playback.{" "}
            <a href={item.url} className="underline">
              Download the file
            </a>
            .
          </video>
        </div>
        <div className="p-3">
          <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">{item.title}</p>
          {item.description && <p className="mt-0.5 text-xs text-zinc-500">{item.description}</p>}
        </div>
      </div>
    );
  }

  if (item.media_type === "audio" && embed?.type === "spotify") {
    return (
      <div className="overflow-hidden rounded-xl border-2 border-zinc-100 dark:border-zinc-800">
        <iframe
          src={embed.embedUrl}
          title={item.title}
          className="h-[152px] w-full"
          allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
        />
      </div>
    );
  }

  if (item.media_type === "photo") {
    return (
      <a
        href={item.url}
        target="_blank"
        rel="noopener noreferrer"
        className="group block aspect-square overflow-hidden rounded-xl bg-zinc-100 dark:bg-zinc-800"
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={item.url} alt={item.title} className="h-full w-full object-cover transition-transform group-hover:scale-105" />
        <span className="block truncate bg-black/60 px-3 py-1.5 text-xs text-white">{item.title}</span>
      </a>
    );
  }

  if (item.media_type === "audio") {
    return (
      <div className="rounded-xl border-2 border-zinc-100 p-4 dark:border-zinc-800">
        <p className="flex items-center gap-2 text-sm font-semibold text-zinc-900 dark:text-zinc-50">
          <MEDIA_TYPE_ICONS.audio className="h-4 w-4" />
          {item.title}
        </p>
        {item.description && <p className="mt-1 text-xs text-zinc-500">{item.description}</p>}
        {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
        <audio controls src={item.url} className="mt-3 w-full">
          Your browser doesn&apos;t support audio playback.{" "}
          <a href={item.url} className="underline">
            Download the file
          </a>
          .
        </audio>
      </div>
    );
  }

  return (
    <a
      href={item.url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center gap-3 rounded-xl border-2 border-zinc-100 p-4 hover:border-rose-300 dark:border-zinc-800 dark:hover:border-rose-800"
    >
      {createElement(MEDIA_TYPE_ICONS[item.media_type] ?? FileText, { className: "h-6 w-6 text-zinc-500" })}
      <div>
        <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">{item.title}</p>
        <p className="text-xs capitalize text-zinc-500">{item.media_type}</p>
      </div>
    </a>
  );
}
