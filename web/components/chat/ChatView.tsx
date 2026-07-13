"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowDown } from "lucide-react";
import { CouncilPanel } from "@/components/chat/CouncilPanel";
import { PlanApprovalCard } from "@/components/chat/PlanApprovalCard";
import { ApiError, fetchChatHistory, sendChat } from "@/lib/api";
import { notifyPlanUpdated } from "@/lib/plan-events";
import type { ChatMessage, CouncilProposals, PendingApproval } from "@/lib/types";
import { cn } from "@/lib/utils";

const THREAD_KEY = "steadyfit_thread_id";

const WELCOME: ChatMessage = {
  id: "welcome",
  role: "assistant",
  content:
    "Tell me your goal, log a meal, or say what got in the way this week — I'll help you re-plan without the guilt trip.",
};

function hasCouncil(council?: CouncilProposals) {
  return council && Object.values(council).some((v) => v?.trim());
}

export function ChatView() {
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME]);
  const [input, setInput] = useState("");
  const [threadId, setThreadId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pendingApproval, setPendingApproval] = useState<PendingApproval | null>(null);
  const [restoring, setRestoring] = useState(false);
  const [showScrollBtn, setShowScrollBtn] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback((smooth = true) => {
    bottomRef.current?.scrollIntoView({
      behavior: smooth ? "smooth" : "instant",
      block: "end",
    });
  }, []);

  useEffect(() => {
    const storedThread = sessionStorage.getItem(THREAD_KEY);
    if (!storedThread) return;

    setThreadId(storedThread);
    setRestoring(true);
    fetchChatHistory(storedThread)
      .then((data) => {
        if (data.messages.length > 0) {
          setMessages(
            data.messages.map((msg) => ({
              id: crypto.randomUUID(),
              role: msg.role,
              content: msg.content,
              council: msg.council,
            })),
          );
        }
        setPendingApproval(data.pending_approval ?? null);
      })
      .catch(() => {
        // Keep welcome state if history cannot be loaded.
      })
      .finally(() => setRestoring(false));
  }, []);

  useEffect(() => {
    scrollToBottom(false);
  }, [messages, loading, pendingApproval, scrollToBottom]);

  const submitMessage = useCallback(
    async (text: string) => {
      setError(null);
      setLoading(true);

      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: text,
      };
      setMessages((prev) => [...prev, userMsg]);

      try {
        const data = await sendChat(text, threadId);
        setThreadId(data.thread_id);
        sessionStorage.setItem(THREAD_KEY, data.thread_id);

        const assistantMsg: ChatMessage = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: data.reply,
          council: hasCouncil(data.council) ? data.council : undefined,
        };
        setMessages((prev) => [...prev, assistantMsg]);
        setPendingApproval(data.pending_approval ?? null);
      } catch (err) {
        const message =
          err instanceof ApiError
            ? `API error (${err.status}): ${err.message}`
            : "Something went wrong — is the backend running on port 8000?";
        setError(message);
      } finally {
        setLoading(false);
      }
    },
    [threadId],
  );

  function handleSubmit(e?: React.FormEvent) {
    e?.preventDefault();
    const text = input.trim();
    if (!text || loading || restoring || pendingApproval) return;
    setInput("");
    void submitMessage(text);
  }

  function handleApprovalResolved(reply: string) {
    setPendingApproval(null);
    setMessages((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        role: "assistant",
        content: reply,
      },
    ]);
    notifyPlanUpdated();
  }

  function handleScroll() {
    const el = scrollRef.current;
    if (!el) return;
    const distance = el.scrollHeight - el.scrollTop - el.clientHeight;
    setShowScrollBtn(distance > 120);
  }

  const composerDisabled = loading || restoring || Boolean(pendingApproval);

  return (
    <div className="content-width flex min-h-0 flex-1 flex-col">
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="relative min-h-0 flex-1 overflow-y-auto py-5"
        role="log"
        aria-live="polite"
        aria-label="Chat messages"
      >
        <div className="flex flex-col gap-4">
          {messages.map((msg) => (
            <div key={msg.id} className="flex flex-col gap-2">
              {msg.role === "user" ? (
                <div className="flex justify-end">
                  <div
                    className={cn(
                      "bubble-user max-w-[85%] bg-sage px-4 py-3 text-sm text-sage-foreground",
                      "animate-enter",
                    )}
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-start gap-2">
                  <div
                    className={cn(
                      "bubble-coach max-w-[92%] border border-beige-border bg-beige px-4 py-3 text-sm text-card-text",
                      "animate-enter",
                    )}
                  >
                    <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                  </div>
                  {msg.council && hasCouncil(msg.council) ? (
                    <CouncilPanel council={msg.council} />
                  ) : null}
                </div>
              )}
            </div>
          ))}

          {loading || restoring ? (
            <div className="flex justify-start">
              <div className="bubble-coach border border-beige-border bg-beige px-4 py-3 text-sm text-card-text/70">
                {restoring
                  ? "Pulling up your thread…"
                  : "The council is talking it over…"}
              </div>
            </div>
          ) : null}

          {error ? (
            <div className="rounded-2xl border border-beige-border/40 bg-council px-4 py-3 text-sm text-navy-muted">
              {error}
            </div>
          ) : null}

          {pendingApproval && threadId ? (
            <PlanApprovalCard
              approval={pendingApproval}
              threadId={threadId}
              onResolved={handleApprovalResolved}
              onError={setError}
            />
          ) : null}

          <div ref={bottomRef} className="h-1 shrink-0" aria-hidden />
        </div>

        {showScrollBtn ? (
          <button
            type="button"
            onClick={() => scrollToBottom()}
            className="absolute bottom-3 left-1/2 flex size-9 -translate-x-1/2 items-center justify-center rounded-full border border-beige-border/30 bg-council text-navy-muted transition-colors hover:text-navy-text"
            aria-label="Scroll to latest"
          >
            <ArrowDown className="size-4" />
          </button>
        ) : null}
      </div>

      <form
        onSubmit={handleSubmit}
        className="sticky bottom-0 z-10 -mx-5 border-t border-beige-border/15 bg-navy px-5 py-3"
      >
        <div className="flex items-end gap-2 rounded-[var(--radius-pill)] border border-beige-border bg-beige p-1.5 pl-4">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSubmit();
              }
            }}
            placeholder="e.g. Life happened — want me to re-plan?"
            rows={1}
            disabled={composerDisabled}
            className="max-h-32 min-h-[2.25rem] flex-1 resize-none bg-transparent py-2 text-sm text-card-text placeholder:text-card-text/45 focus:outline-none disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || composerDisabled}
            className={cn(
              "shrink-0 rounded-[var(--radius-pill)] bg-sage px-5 py-2 text-sm font-medium text-sage-foreground",
              "transition-colors duration-150 ease-out hover:bg-sage-hover disabled:opacity-40",
            )}
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}
