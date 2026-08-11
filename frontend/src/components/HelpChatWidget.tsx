"use client";

import { useState, useRef, useEffect } from "react";
import { MessageCircle, X, Send } from "lucide-react";
import { FAQ_ENTRIES } from "@/lib/faqData";
import { matchFaq, suggestedQuestions } from "@/lib/faqMatch";

interface ChatMessage {
  id: number;
  from: "bot" | "user";
  text: string;
}

const GREETING =
  "Hi! I'm the YouGotTalent help bot. Ask me how to do something on the site, or tap a question below to get started.";

const FALLBACK =
  "I couldn't find an answer to that in my help topics. Try rephrasing, or use \"Report a problem\" in the footer to reach our team directly.";

let nextId = 1;

export default function HelpChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([{ id: 0, from: "bot", text: GREETING }]);
  const [input, setInput] = useState("");
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight;
  }, [messages, open]);

  function ask(question: string) {
    const trimmed = question.trim();
    if (!trimmed) return;
    const match = matchFaq(trimmed, FAQ_ENTRIES);
    setMessages((prev) => [
      ...prev,
      { id: nextId++, from: "user", text: trimmed },
      { id: nextId++, from: "bot", text: match ? match.answer : FALLBACK },
    ]);
    setInput("");
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    ask(input);
  }

  const chips = suggestedQuestions();

  return (
    <div className="fixed bottom-5 right-5 z-40 flex flex-col items-end gap-3">
      {open && (
        <div className="flex h-[28rem] w-[22rem] max-w-[90vw] flex-col overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-2xl dark:border-zinc-800 dark:bg-zinc-900">
          <div className="flex shrink-0 items-center justify-between border-b border-zinc-200 bg-zinc-900 px-4 py-3 dark:border-zinc-800">
            <div className="flex items-center gap-2">
              <MessageCircle className="h-5 w-5 text-rose-400" />
              <span className="font-heading text-sm font-bold text-white">Help &amp; support</span>
            </div>
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Minimize help chat"
              className="rounded-full p-1 text-zinc-400 hover:bg-zinc-800 hover:text-white"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div ref={listRef} className="flex-1 space-y-3 overflow-y-auto px-3 py-3">
            {messages.map((m) => (
              <div key={m.id} className={`flex ${m.from === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[85%] rounded-xl px-3 py-2 text-sm ${
                    m.from === "user"
                      ? "bg-rose-600 text-white"
                      : "bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-100"
                  }`}
                >
                  {m.text}
                </div>
              </div>
            ))}

            {messages.length === 1 && (
              <div className="flex flex-wrap gap-1.5 pt-1">
                {chips.map((c) => (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => ask(c.question)}
                    className="rounded-full border border-rose-200 bg-rose-50 px-2.5 py-1 text-xs font-medium text-rose-700 hover:bg-rose-100 dark:border-rose-900/50 dark:bg-rose-900/20 dark:text-rose-300 dark:hover:bg-rose-900/40"
                  >
                    {c.question}
                  </button>
                ))}
              </div>
            )}
          </div>

          <form onSubmit={handleSubmit} className="flex shrink-0 gap-2 border-t border-zinc-200 p-2.5 dark:border-zinc-800">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question…"
              className="flex-1 rounded-full border-2 border-zinc-200 bg-white px-3.5 py-2 text-sm text-zinc-900 placeholder:text-zinc-400 focus:border-rose-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
            />
            <button
              type="submit"
              aria-label="Send"
              disabled={!input.trim()}
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-rose-600 text-white transition-colors hover:bg-rose-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
        </div>
      )}

      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-label={open ? "Close help chat" : "Open help chat"}
        className="flex h-14 w-14 items-center justify-center rounded-full bg-rose-600 text-white shadow-lg transition-all hover:bg-rose-700 active:translate-y-px"
      >
        {open ? <X className="h-6 w-6" /> : <MessageCircle className="h-6 w-6" />}
      </button>
    </div>
  );
}
