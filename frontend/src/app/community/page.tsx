"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, MessageCircle, Star } from "lucide-react";
import { DiscussionThread, Title, api } from "@/lib/api";
import { eyebrowClass } from "@/lib/ui";
import TitlePoster from "@/components/TitlePoster";
import AuthorAvatar from "@/components/AuthorAvatar";

export default function CommunityHubPage() {
  const [titles, setTitles] = useState<Title[]>([]);
  const [threads, setThreads] = useState<DiscussionThread[]>([]);

  useEffect(() => {
    api.listTitles().then(setTitles).catch(() => {});
    api.listDiscussions().then(setThreads).catch(() => {});
  }, []);

  return (
    <main className="flex-1">
      <div className="relative overflow-hidden bg-zinc-950">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(244,63,94,0.25),transparent_60%)]" />
        <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.04)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.04)_1px,transparent_1px)] bg-[size:40px_40px]" />
        <div className="relative mx-auto max-w-4xl px-6 py-16 text-center">
          <span className={eyebrowClass}>Community</span>
          <h1 className="mt-4 font-heading text-4xl font-black uppercase tracking-tight text-white sm:text-5xl">
            Talk shop. Rate the work.
          </h1>
          <p className="mx-auto mt-3 max-w-xl text-zinc-400">
            Sri Lanka's home for honest film, TV, and song critique — plus discussion on everything happening in the
            industry. Open to browse, login required to post.
          </p>
        </div>
      </div>

      <div className="mx-auto grid max-w-4xl grid-cols-1 gap-6 px-6 py-10 sm:grid-cols-2">
        <Link
          href="/community/titles"
          className="group flex flex-col gap-4 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm transition-all hover:-translate-y-1 hover:shadow-xl dark:border-zinc-800 dark:bg-zinc-900"
        >
          <div className="flex items-center justify-between">
            <span className="flex h-11 w-11 items-center justify-center rounded-sm bg-amber-400 text-zinc-900">
              <Star className="h-5 w-5 fill-current" />
            </span>
            <ArrowRight className="h-5 w-5 text-zinc-400 transition-transform group-hover:translate-x-1" />
          </div>
          <div>
            <p className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Rate &amp; critique</p>
            <p className="mt-1 text-sm text-zinc-500">Films, TV series, and songs, rated 1-5 stars with critiques.</p>
          </div>
          {titles.length > 0 ? (
            <div className="flex gap-2">
              {titles.slice(0, 5).map((t) => (
                <div key={t.id} className="aspect-[2/3] w-1/5 overflow-hidden rounded-md">
                  <TitlePoster name={t.name} workType={t.work_type} posterUrl={t.poster_url} className="h-full w-full" iconClassName="h-5 w-5" />
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-zinc-400">No titles yet — be the first to add one.</p>
          )}
        </Link>

        <Link
          href="/community/discussions"
          className="group flex flex-col gap-4 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm transition-all hover:-translate-y-1 hover:shadow-xl dark:border-zinc-800 dark:bg-zinc-900"
        >
          <div className="flex items-center justify-between">
            <span className="flex h-11 w-11 items-center justify-center rounded-sm bg-rose-600 text-white">
              <MessageCircle className="h-5 w-5" />
            </span>
            <ArrowRight className="h-5 w-5 text-zinc-400 transition-transform group-hover:translate-x-1" />
          </div>
          <div>
            <p className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Discussions</p>
            <p className="mt-1 text-sm text-zinc-500">Industry news, films, TV series, and music with talent and recruiters.</p>
          </div>
          {threads.length > 0 ? (
            <div className="flex flex-col gap-2">
              {threads.slice(0, 3).map((t) => (
                <div key={t.id} className="flex items-center gap-2">
                  <AuthorAvatar name={t.author_name} className="h-7 w-7 text-[10px]" />
                  <p className="truncate text-xs text-zinc-600 dark:text-zinc-400">{t.subject}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-zinc-400">No discussions yet — start the first one.</p>
          )}
        </Link>
      </div>
    </main>
  );
}
