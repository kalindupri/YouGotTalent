"use client";

import { useState, useRef, useEffect } from "react";
import { MessageCircle, X, Send, Loader2 } from "lucide-react";
import { FAQ_ENTRIES, type FaqEntry } from "@/lib/faqData";
import { matchFaqWithSuggestion, suggestedQuestions } from "@/lib/faqMatch";
import { api, type SupportConversation } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

interface ChatMessage {
  id: number;
  from: "bot" | "user";
  text: string;
  suggestion?: FaqEntry;
  unansweredQuestion?: string;
}

const GREETING =
  "Hi! I'm the YouGotTalent help bot. Ask me how to do something on the site, or tap a question below to get started.";

const FALLBACK =
  "I couldn't find an answer to that in my help topics. Try rephrasing, or use \"Report a problem\" in the footer to reach our team directly.";

const POLL_INTERVAL_MS = 4000;

let nextId = 1;

export default function HelpChatWidget() {
  const { token } = useAuth();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([{ id: 0, from: "bot", text: GREETING }]);
  const [input, setInput] = useState("");
  const [liveChatAvailable, setLiveChatAvailable] = useState(false);
  const [conversation, setConversation] = useState<SupportConversation | null>(null);
  const [startingChat, setStartingChat] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api
      .isSupportChatAvailable()
      .then((r) => setLiveChatAvailable(r.available))
      .catch(() => setLiveChatAvailable(false));
  }, []);

  useEffect(() => {
    if (listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight;
  }, [messages, conversation, open]);

  useEffect(() => {
    if (!conversation || conversation.status !== "open") return;
    const id = setInterval(() => {
      api
        .pollSupportChat(conversation.id)
        .then(setConversation)
        .catch(() => {});
    }, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [conversation?.id, conversation?.status]);

  function ask(question: string) {
    const trimmed = question.trim();
    if (!trimmed) return;
    const { entry, suggestion } = matchFaqWithSuggestion(trimmed, FAQ_ENTRIES);
    setMessages((prev) => [
      ...prev,
      { id: nextId++, from: "user", text: trimmed },
      {
        id: nextId++,
        from: "bot",
        text: entry ? entry.answer : FALLBACK,
        suggestion: !entry && suggestion ? suggestion : undefined,
        unansweredQuestion: !entry && liveChatAvailable ? trimmed : undefined,
      },
    ]);
    setInput("");
  }

  async function startLiveChat(question: string) {
    setStartingChat(true);
    try {
      const convo = await api.startSupportChat(question, token);
      setConversation(convo);
    } catch {
      setMessages((prev) => [
        ...prev,
        { id: nextId++, from: "bot", text: "Couldn't start live chat right now. Please try again in a moment." },
      ]);
    } finally {
      setStartingChat(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed) return;
    setInput("");
    if (conversation && conversation.status === "open") {
      setConversation({
        ...conversation,
        messages: [...conversation.messages, { id: `local-${nextId++}`, sender: "customer", content: trimmed, created_at: new Date().toISOString() }],
      });
      try {
        const updated = await api.sendSupportMessage(conversation.id, trimmed);
        setConversation(updated);
      } catch {
        // next poll will resync; nothing else to do here
      }
      return;
    }
    ask(trimmed);
  }

  const chips = suggestedQuestions();

  return (
    <div className="fixed bottom-5 right-5 z-40 flex flex-col items-end gap-3">
      {open && (
        <div className="flex h-[28rem] w-[22rem] max-w-[90vw] flex-col overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-2xl dark:border-zinc-800 dark:bg-zinc-900">
          <div className="flex shrink-0 items-center justify-between border-b border-zinc-200 bg-zinc-900 px-4 py-3 dark:border-zinc-800">
            <div className="flex items-center gap-2">
              <MessageCircle className="h-5 w-5 text-rose-400" />
              <span className="font-heading text-sm font-bold text-white">
                {conversation ? "Live chat" : "Help & support"}
              </span>
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
            {!conversation &&
              messages.map((m) => (
                <div key={m.id} className={`flex flex-col ${m.from === "user" ? "items-end" : "items-start"}`}>
                  <div
                    className={`max-w-[85%] rounded-xl px-3 py-2 text-sm ${
                      m.from === "user"
                        ? "bg-rose-600 text-white"
                        : "bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-100"
                    }`}
                  >
                    {m.text}
                  </div>
                  {m.suggestion && (
                    <button
                      type="button"
                      onClick={() => ask(m.suggestion!.question)}
                      className="mt-1.5 max-w-[85%] rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-left text-xs font-medium text-rose-700 hover:bg-rose-100 dark:border-rose-900/50 dark:bg-rose-900/20 dark:text-rose-300 dark:hover:bg-rose-900/40"
                    >
                      Did you mean: &ldquo;{m.suggestion.question}&rdquo;
                    </button>
                  )}
                  {m.unansweredQuestion && (
                    <button
                      type="button"
                      disabled={startingChat}
                      onClick={() => startLiveChat(m.unansweredQuestion!)}
                      className="mt-1.5 flex max-w-[85%] items-center gap-1.5 rounded-xl border border-zinc-300 bg-white px-3 py-2 text-left text-xs font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200 dark:hover:bg-zinc-700"
                    >
                      {startingChat && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                      Chat with a person
                    </button>
                  )}
                </div>
              ))}

            {conversation && (
              <>
                <div className="flex justify-start">
                  <div className="max-w-[85%] rounded-xl bg-zinc-100 px-3 py-2 text-xs text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400">
                    You're chatting with a real team member — replies may take a few minutes.
                  </div>
                </div>
                {conversation.messages.map((m) => (
                  <div key={m.id} className={`flex ${m.sender === "customer" ? "justify-end" : "justify-start"}`}>
                    <div
                      className={`max-w-[85%] rounded-xl px-3 py-2 text-sm ${
                        m.sender === "customer"
                          ? "bg-rose-600 text-white"
                          : "bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-100"
                      }`}
                    >
                      {m.content}
                    </div>
                  </div>
                ))}
                {conversation.status === "closed" && (
                  <div className="flex justify-start">
                    <div className="max-w-[85%] rounded-xl bg-zinc-100 px-3 py-2 text-xs text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400">
                      This conversation has ended.
                    </div>
                  </div>
                )}
              </>
            )}

            {!conversation && messages.length === 1 && (
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
              placeholder={conversation ? "Message support…" : "Ask a question…"}
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
