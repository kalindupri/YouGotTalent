import { FAQ_ENTRIES, type FaqEntry } from "./faqData";

const STOPWORDS = new Set([
  "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
  "do", "does", "did", "doing", "can", "could", "would", "should", "will",
  "i", "you", "he", "she", "it", "we", "they", "my", "your", "his", "her", "its", "our", "their",
  "to", "of", "in", "on", "at", "for", "with", "about", "how", "what", "when", "where", "why", "who",
  "and", "or", "but", "if", "so", "as", "than", "then", "this", "that", "these", "those",
  "me", "him", "them", "us", "am", "not", "no", "yes", "up", "out", "get", "got",
]);

// Deliberately crude — this is a hand-rolled suffix stripper, not a real stemmer. Good enough
// to fold "videos"->"video", "applied"->"appli"/"applicants"->"applic" close enough to overlap,
// "saved"->"save", without pulling in an NLP dependency (the whole point is "no LLM/ML").
function stem(word: string): string {
  if (word.length > 5 && word.endsWith("ing")) return word.slice(0, -3);
  if (word.length > 5 && word.endsWith("ies")) return word.slice(0, -3) + "y";
  if (word.length > 4 && word.endsWith("ed")) return word.slice(0, -2);
  if (word.length > 4 && word.endsWith("es")) return word.slice(0, -2);
  if (word.length > 4 && word.endsWith("s") && !word.endsWith("ss")) return word.slice(0, -1);
  return word;
}

function tokenize(text: string): string[] {
  return text
    .toLowerCase()
    .replace(/[^\w\s]/g, " ")
    .split(/\s+/)
    .filter((tok) => tok.length > 0 && !STOPWORDS.has(tok))
    .map(stem);
}

const MATCH_THRESHOLD = 2;

export function matchFaq(query: string, entries: FaqEntry[] = FAQ_ENTRIES): FaqEntry | null {
  const queryTokens = new Set(tokenize(query));
  if (queryTokens.size === 0) return null;

  let best: FaqEntry | null = null;
  let bestScore = 0;

  for (const entry of entries) {
    let score = 0;

    // Bag-of-words phrase match (order-independent, stemmed) rather than a literal substring —
    // real sentences almost always insert filler words ("upload A video"), which broke exact
    // substring matching for nearly every multi-word keyword in practice.
    for (const keyword of entry.keywords) {
      const kwTokens = tokenize(keyword);
      if (kwTokens.length === 0) continue;
      if (kwTokens.every((t) => queryTokens.has(t))) {
        // A generic single-word "keyword" (e.g. "account") is a weak signal on its own — it
        // must combine with question-token overlap to cross the threshold, so it can't alone
        // hijack an unrelated query the way it used to.
        score += kwTokens.length > 1 ? 4 : 1.5;
      }
    }

    // De-duplicated on purpose: a question that happens to repeat a word (e.g. "a Talent and a
    // Talent Hunt account") must not score higher just for saying that word twice.
    const questionTokens = new Set(tokenize(entry.question));
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
