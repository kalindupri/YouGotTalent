import { FAQ_ENTRIES, type FaqEntry } from "./faqData";

const STOPWORDS = new Set([
  "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
  "do", "does", "did", "doing", "can", "could", "would", "should", "will",
  "i", "you", "he", "she", "it", "we", "they", "my", "your", "his", "her", "its", "our", "their",
  "to", "of", "in", "on", "at", "for", "with", "about", "how", "what", "when", "where", "why", "who",
  "and", "or", "but", "if", "so", "as", "than", "then", "this", "that", "these", "those",
  "me", "him", "them", "us", "am", "not", "no", "yes", "up", "out", "get", "got",
]);

function tokenize(text: string): string[] {
  return text
    .toLowerCase()
    .replace(/[^\w\s]/g, " ")
    .split(/\s+/)
    .filter((tok) => tok.length > 0 && !STOPWORDS.has(tok));
}

const MATCH_THRESHOLD = 2;

export function matchFaq(query: string, entries: FaqEntry[] = FAQ_ENTRIES): FaqEntry | null {
  const queryLower = query.toLowerCase();
  const queryTokens = new Set(tokenize(query));
  if (queryTokens.size === 0) return null;

  let best: FaqEntry | null = null;
  let bestScore = 0;

  for (const entry of entries) {
    let score = 0;

    for (const keyword of entry.keywords) {
      if (queryLower.includes(keyword.toLowerCase())) {
        // A multi-word phrase matched verbatim is a much stronger signal than one shared token.
        score += keyword.includes(" ") ? 4 : 2;
      }
    }

    const questionTokens = tokenize(entry.question);
    for (const tok of questionTokens) {
      if (queryTokens.has(tok)) score += 1;
    }

    if (score > bestScore) {
      bestScore = score;
      best = entry;
    }
  }

  return bestScore >= MATCH_THRESHOLD ? best : null;
}

export function suggestedQuestions(entries: FaqEntry[] = FAQ_ENTRIES, count = 4): FaqEntry[] {
  const ids = ["upload-photo-video", "apply-role", "post-casting-call", "pricing"];
  const picked = ids.map((id) => entries.find((e) => e.id === id)).filter((e): e is FaqEntry => !!e);
  if (picked.length >= count) return picked.slice(0, count);
  const rest = entries.filter((e) => !picked.includes(e));
  return [...picked, ...rest.slice(0, count - picked.length)];
}
