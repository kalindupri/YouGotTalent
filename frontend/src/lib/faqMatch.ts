import { FAQ_ENTRIES, type FaqEntry } from "./faqData";

const STOPWORDS = new Set([
  "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
  "do", "does", "did", "doing", "can", "could", "would", "should", "will",
  "i", "you", "he", "she", "it", "we", "they", "my", "your", "his", "her", "its", "our", "their",
  "to", "of", "in", "on", "at", "for", "with", "about", "how", "what", "when", "where", "why", "who",
  "and", "or", "but", "if", "so", "as", "than", "then", "this", "that", "these", "those",
  "me", "him", "them", "us", "am", "not", "no", "yes", "up", "out", "get", "got",
]);

// A curated set of common alternate words customers actually type, normalized to the term our
// keyword lists are written against. Deliberately small and hand-checked — a broad/automatic
// synonym system risks silently merging unrelated concepts (e.g. "application" the job
// application vs. "app" the platform) into the same token.
const SYNONYMS: Record<string, string> = {
  job: "hunt", jobs: "hunt", gig: "hunt", gigs: "hunt",
  opportunity: "hunt", opportunities: "hunt", posting: "hunt", postings: "hunt",
  listing: "hunt", listings: "hunt",
  pic: "photo", pics: "photo", picture: "photo", pictures: "photo",
  img: "photo", image: "photo", images: "photo",
  vid: "video", vids: "video", clip: "video", clips: "video",
  website: "platform", site: "platform", app: "platform",
  fee: "price", fees: "price", charge: "price", charges: "price",
  acct: "account",
};

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
    .map(stem)
    .map((tok) => SYNONYMS[tok] ?? tok);
}

function levenshtein(a: string, b: string): number {
  const dp: number[] = Array.from({ length: b.length + 1 }, (_, j) => j);
  for (let i = 1; i <= a.length; i++) {
    let prevDiag = dp[0];
    dp[0] = i;
    for (let j = 1; j <= b.length; j++) {
      const temp = dp[j];
      dp[j] = a[i - 1] === b[j - 1] ? prevDiag : 1 + Math.min(prevDiag, dp[j], dp[j - 1]);
      prevDiag = temp;
    }
  }
  return dp[b.length];
}

// Word pairs that are genuinely close in edit distance (down to 1) but mean unrelated things in
// this app — found by auditing the full FAQ vocabulary for near-collisions before shipping fuzzy
// matching. Without this, a typo-tolerant matcher would treat "contract" (offer/contract) and
// "contact" (contact support) as the same word.
const FUZZY_DENYLIST = new Set<string>([
  ["contract", "contact"].sort().join("|"),
  ["contact", "content"].sort().join("|"),
  ["session", "section"].sort().join("|"),
]);

const FUZZY_MAX_DISTANCE = 2;

function isFuzzyMatch(tok: string, target: string, minLength: number): boolean {
  if (tok === target) return true;
  if (target.length < minLength || Math.abs(tok.length - target.length) > FUZZY_MAX_DISTANCE) return false;
  if (FUZZY_DENYLIST.has([tok, target].sort().join("|"))) return false;
  return levenshtein(tok, target) <= FUZZY_MAX_DISTANCE;
}

// Counts how many keyword tokens have a (possibly fuzzy) match in the query — each query token
// can only satisfy one keyword token. Without that "consumed once" rule, a keyword phrase with
// two morphological variants of the same word (e.g. "view" and "viewers") could both fuzzily
// bridge to a single query token and double-count what is really one overlapping word.
function countMatches(kwTokens: string[], queryTokens: Set<string>, minLength: number): number {
  const available = new Set(queryTokens);
  let count = 0;
  for (const t of kwTokens) {
    let hit: string | null = null;
    for (const tok of available) {
      if (isFuzzyMatch(tok, t, minLength)) {
        hit = tok;
        if (tok === t) break; // prefer an exact match but any match will do
      }
    }
    if (hit) {
      available.delete(hit);
      count++;
    }
  }
  return count;
}

const MATCH_THRESHOLD = 2;
const SUGGESTION_THRESHOLD = 1.5;

export interface FaqMatchResult {
  entry: FaqEntry | null;
  suggestion: FaqEntry | null;
}

function scoreEntry(entry: FaqEntry, queryTokens: Set<string>): number {
  let score = 0;

  // Bag-of-words phrase match (order-independent, stemmed, fuzzy-typo-tolerant) rather than a
  // literal substring — real sentences almost always insert filler words ("upload A video") or
  // small typos, which broke exact substring matching for nearly every multi-word keyword.
  for (const keyword of entry.keywords) {
    const kwTokens = tokenize(keyword);
    if (kwTokens.length === 0) continue;
    const isSingle = kwTokens.length === 1;
    // A single-word keyword fuzzily bridging to an unrelated word is far more likely to flip the
    // winning entry than one word inside a longer phrase, where the other words still have to
    // line up too — so single-word keywords get a stricter (higher minLength) fuzzy tolerance.
    const matchedCount = countMatches(kwTokens, queryTokens, isSingle ? 7 : 6);

    if (isSingle) {
      // A generic single-word "keyword" (e.g. "account") is a weak signal on its own — it must
      // combine with question-token overlap to cross the threshold, so it can't alone hijack an
      // unrelated query the way it used to.
      if (matchedCount === 1) score += 1.5;
    } else if (matchedCount === kwTokens.length) {
      score += 4;
    } else if (kwTokens.length >= 3 && matchedCount >= kwTokens.length - 1) {
      // Near-complete multi-word phrase (missing/substituted one word) still counts for
      // something — covers phrasing we didn't explicitly anticipate without guessing wildly.
      score += 2;
    }
  }

  // De-duplicated on purpose: a question that happens to repeat a word (e.g. "a Talent and a
  // Talent Hunt account") must not score higher just for saying that word twice.
  const questionTokens = new Set(tokenize(entry.question));
  for (const tok of questionTokens) {
    if (queryTokens.has(tok)) score += 1;
  }

  return score;
}

export function matchFaqWithSuggestion(query: string, entries: FaqEntry[] = FAQ_ENTRIES): FaqMatchResult {
  const queryTokens = new Set(tokenize(query));
  if (queryTokens.size === 0) return { entry: null, suggestion: null };

  let best: FaqEntry | null = null;
  let bestScore = 0;

  for (const entry of entries) {
    const score = scoreEntry(entry, queryTokens);
    if (score > bestScore) {
      bestScore = score;
      best = entry;
    }
  }

  if (bestScore >= MATCH_THRESHOLD) return { entry: best, suggestion: null };
  if (bestScore >= SUGGESTION_THRESHOLD) return { entry: null, suggestion: best };
  return { entry: null, suggestion: null };
}

export function matchFaq(query: string, entries: FaqEntry[] = FAQ_ENTRIES): FaqEntry | null {
  return matchFaqWithSuggestion(query, entries).entry;
}

export function suggestedQuestions(entries: FaqEntry[] = FAQ_ENTRIES, count = 4): FaqEntry[] {
  const ids = ["upload-photo-video", "apply-role", "post-casting-call", "pricing"];
  const picked = ids.map((id) => entries.find((e) => e.id === id)).filter((e): e is FaqEntry => !!e);
  if (picked.length >= count) return picked.slice(0, count);
  const rest = entries.filter((e) => !picked.includes(e));
  return [...picked, ...rest.slice(0, count - picked.length)];
}
