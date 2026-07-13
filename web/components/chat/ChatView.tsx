"use client";

import { Fragment, useCallback, useEffect, useState } from "react";
import { CopyIcon } from "lucide-react";
import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from "@/components/ai-elements/conversation";
import {
  Message,
  MessageAction,
  MessageActions,
  MessageContent,
  MessageResponse,
} from "@/components/ai-elements/message";
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

const USER_BUBBLE =
  "group-[.is-user]:bubble-user group-[.is-user]:max-w-[85%] group-[.is-user]:rounded-[var(--radius-bubble)] group-[.is-user]:border-0 group-[.is-user]:bg-sage group-[.is-user]:px-4 group-[.is-user]:py-3 group-[.is-user]:text-sage-foreground";

const COACH_BUBBLE =
  "group-[.is-assistant]:bubble-coach group-[.is-assistant]:max-w-[92%] group-[.is-assistant]:rounded-[var(--radius-bubble)] group-[.is-assistant]:border group-[.is-assistant]:border-beige-border group-[.is-assistant]:bg-beige group-[.is-assistant]:px-4 group-[.is-assistant]:py-3 group-[.is-assistant]:text-card-text";

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
            : "Oops something went wrong, Saurabh must be fixing it. Try again in a min";
        setError(message);
      } finally {
        setLoading(false);
      }
    },
    [threadId],
  );

  async function handleSubmit(e?: React.FormEvent) {
    e?.preventDefault();
    const text = input.trim();
    if (!text || loading || restoring || pendingApproval) return;
    setInput("");
    await submitMessage(text);
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

  const lastAssistantIndex = messages.findLastIndex((m) => m.role === "assistant");
  const composerDisabled = loading || restoring || Boolean(pendingApproval);

  return (
    <div className="content-width flex min-h-0 flex-1 flex-col">
      <Conversation className="min-h-0 flex-1">
        <ConversationContent className="gap-4 p-0 py-5">
          {messages.map((msg, messageIndex) => {
            const isLastAssistant =
              msg.role === "assistant" && messageIndex === lastAssistantIndex;

            return (
              <Fragment key={msg.id}>
                <div className="animate-enter flex flex-col gap-2">
                  <Message from={msg.role}>
                    <MessageContent
                      className={cn(
                        "text-sm",
                        msg.role === "user" ? USER_BUBBLE : COACH_BUBBLE,
                      )}
                    >
                      {msg.role === "assistant" ? (
                        <MessageResponse className="coach-prose size-full">
                          {msg.content}
                        </MessageResponse>
                      ) : (
                        <span className="whitespace-pre-wrap">{msg.content}</span>
                      )}
                    </MessageContent>
                  </Message>

                  {msg.role === "assistant" && msg.council && hasCouncil(msg.council) ? (
                    <CouncilPanel council={msg.council} />
                  ) : null}
                </div>

                {isLastAssistant && !loading ? (
                  <MessageActions className="ml-1">
                    <MessageAction
                      tooltip="Copy"
                      label="Copy"
                      variant="ghost"
                      className="text-navy-muted hover:bg-council hover:text-navy-text"
                      onClick={() => navigator.clipboard.writeText(msg.content)}
                    >
                      <CopyIcon className="size-3.5" />
                    </MessageAction>
                  </MessageActions>
                ) : null}
              </Fragment>
            );
          })}

          {loading || restoring ? (
            <Message from="assistant" className="animate-enter">
              <MessageContent className={cn("text-sm", COACH_BUBBLE)}>
                <span className="text-card-text/70">
                  {restoring
                    ? "Pulling up your thread…"
                    : "The council is talking it over…"}
                </span>
              </MessageContent>
            </Message>
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
        </ConversationContent>

        <ConversationScrollButton
          className="border-beige-border/30 bg-council text-navy-muted hover:bg-council hover:text-navy-text"
        />
      </Conversation>

      <form
        onSubmit={handleSubmit}
        className="sticky bottom-0 z-10 -mx-5 border-t border-beige-border/15 bg-navy px-5 py-3"
      >
        <div
          className={cn(
            "group flex items-end gap-2 rounded-[var(--radius-pill)] border p-1.5 pl-4 transition-colors duration-150 ease-out",
            "border-beige-border/35 bg-beige-border/20",
            "focus-within:border-beige-border focus-within:bg-beige",
            composerDisabled && "opacity-60",
          )}
        >
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void handleSubmit();
              }
            }}
            placeholder="e.g. Life happened — want me to re-plan?"
            rows={1}
            disabled={composerDisabled}
            className={cn(
              "max-h-32 min-h-[2.25rem] flex-1 resize-none bg-transparent py-2 text-sm shadow-none focus:outline-none",
              "text-card-text/55 placeholder:text-card-text/40",
              "focus:text-card-text focus:placeholder:text-card-text/45",
              "disabled:cursor-not-allowed",
            )}
          />
          <button
            type="submit"
            disabled={!input.trim() || composerDisabled}
            className={cn(
              "mb-0.5 shrink-0 rounded-[var(--radius-pill)] px-5 py-2 text-sm font-medium transition-colors duration-150 ease-out",
              "bg-sage/25 text-sage-foreground/40",
              "group-focus-within:bg-sage/40 group-focus-within:text-sage-foreground/60",
              "disabled:cursor-not-allowed",
              !composerDisabled &&
                input.trim() &&
                "group-focus-within:bg-sage group-focus-within:text-sage-foreground group-focus-within:hover:bg-sage-hover",
            )}
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}
