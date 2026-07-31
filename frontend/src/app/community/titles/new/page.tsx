"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ApiError, WorkType, api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { btnPrimary, btnSecondary, inputClass, labelClass, sectionClass } from "@/lib/ui";

export default function NewTitlePage() {
  const { user, token, loading: authLoading } = useAuth();
  const router = useRouter();

  const [name, setName] = useState("");
  const [workType, setWorkType] = useState<WorkType>("film");
  const [releaseYear, setReleaseYear] = useState("");
  const [genre, setGenre] = useState("");
  const [language, setLanguage] = useState("");
  const [synopsis, setSynopsis] = useState("");
  const [posterUrl, setPosterUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login?next=/community/titles/new");
    }
  }, [authLoading, user, router]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!token || !name.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const title = await api.createTitle(
        {
          name: name.trim(),
          work_type: workType,
          release_year: releaseYear ? Number(releaseYear) : undefined,
          genre: genre.trim() || undefined,
          language: language.trim() || undefined,
          synopsis: synopsis.trim() || undefined,
          poster_url: posterUrl.trim() || undefined,
        },
        token
      );
      router.push(`/community/titles/${title.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add this title right now.");
    } finally {
      setSubmitting(false);
    }
  }

  if (authLoading || !user) return null;

  return (
    <main className="mx-auto w-full max-w-2xl flex-1 px-6 py-14">
      <h1 className="font-heading text-3xl font-black uppercase tracking-tight text-zinc-900 sm:text-4xl dark:text-zinc-50">
        Add a title
      </h1>
      <p className="mt-2 text-zinc-500">Add a film, TV series, or song for the community to rate and critique.</p>

      <form onSubmit={handleSubmit} className={`${sectionClass} mt-8 flex flex-col gap-4`}>
        <label className={labelClass}>
          Name
          <input value={name} onChange={(e) => setName(e.target.value)} required className={inputClass} />
        </label>
        <div className="flex flex-wrap gap-4">
          <label className={labelClass}>
            Type
            <select value={workType} onChange={(e) => setWorkType(e.target.value as WorkType)} className={`${inputClass} w-auto`}>
              <option value="film">Film</option>
              <option value="tv_series">TV series</option>
              <option value="song">Song</option>
            </select>
          </label>
          <label className={labelClass}>
            Release year
            <input
              type="number"
              value={releaseYear}
              onChange={(e) => setReleaseYear(e.target.value)}
              className={`${inputClass} w-32`}
            />
          </label>
        </div>
        <div className="flex flex-wrap gap-4">
          <label className={`${labelClass} min-w-[10rem] flex-1`}>
            Genre
            <input value={genre} onChange={(e) => setGenre(e.target.value)} className={inputClass} placeholder="e.g. Drama, Comedy" />
          </label>
          <label className={`${labelClass} min-w-[10rem] flex-1`}>
            Language
            <input value={language} onChange={(e) => setLanguage(e.target.value)} className={inputClass} placeholder="e.g. Sinhala" />
          </label>
        </div>
        <label className={labelClass}>
          Synopsis
          <textarea value={synopsis} onChange={(e) => setSynopsis(e.target.value)} rows={4} className={inputClass} />
        </label>
        <label className={labelClass}>
          Poster / cover image URL (optional)
          <input value={posterUrl} onChange={(e) => setPosterUrl(e.target.value)} className={inputClass} placeholder="https://..." />
        </label>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="flex justify-end gap-3">
          <Link href="/community/titles" className={btnSecondary}>
            Cancel
          </Link>
          <button type="submit" disabled={submitting || !name.trim()} className={btnPrimary}>
            {submitting ? "Adding…" : "Add title"}
          </button>
        </div>
      </form>
    </main>
  );
}
