"use client";

import { useEffect, useState } from "react";

const TIKTOK_EMBED_SCRIPT_SRC = "https://www.tiktok.com/embed.js";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

function loadTikTokEmbedScript() {
  if (document.querySelector(`script[src="${TIKTOK_EMBED_SCRIPT_SRC}"]`)) return;
  const script = document.createElement("script");
  script.src = TIKTOK_EMBED_SCRIPT_SRC;
  script.async = true;
  document.body.appendChild(script);
}

export default function TikTokEmbed({ url }: { url: string }) {
  const [html, setHtml] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_URL}/reels/oembed?url=${encodeURIComponent(url)}`)
      .then((res) => {
        if (!res.ok) throw new Error("oEmbed request failed");
        return res.json();
      })
      .then((data: { html?: string }) => {
        if (cancelled) return;
        if (data.html) {
          setHtml(data.html);
          loadTikTokEmbedScript();
        } else {
          setFailed(true);
        }
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, [url]);

  if (failed) {
    return (
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="block rounded-2xl border-2 border-zinc-100 p-4 text-sm font-semibold text-rose-600 hover:underline dark:border-zinc-800"
      >
        Watch on TikTok ↗
      </a>
    );
  }

  if (!html) {
    return <div className="aspect-[9/16] w-full animate-pulse rounded-2xl bg-zinc-100 dark:bg-zinc-800" />;
  }

  return <div className="overflow-hidden rounded-2xl" dangerouslySetInnerHTML={{ __html: html }} />;
}
