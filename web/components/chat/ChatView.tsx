"use client";

import { Fragment, useCallback, useEffect, useRef, useState } from "react";
import { CopyIcon, ImagePlusIcon, XIcon } from "lucide-react";
import {
  Conversation,
  ConversationAutoScroll,
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
import { CitationChips } from "@/components/chat/CitationChips";
import { CoachingTeamPanel } from "@/components/chat/CoachingTeamPanel";
import { PlanApprovalCard } from "@/components/chat/PlanApprovalCard";
import { ApiError, fetchChatHistory, sendChat } from "@/lib/api";
import { compressImageForChat } from "@/lib/compress-image";
import { notifyPlanUpdated } from "@/lib/plan-events";
import { threadStorageKey, useProfile } from "@/lib/profile";
import type { ChatMessage, CoachingTeamProposals, PendingApproval } from "@/lib/types";
import { cn } from "@/lib/utils";

const WELCOME: ChatMessage = {
  id: "welcome",
  role: "assistant",
  content:
    "Hi — I'm Steady. If you're new here I'll ask a few quick things about your goals and how you like to train. Or jump straight in: log a meal, or say what got in the way this week.",
};

const USER_BUBBLE =
  "group-[.is-user]:bubble-user group-[.is-user]:max-w-[85%] group-[.is-user]:rounded-[var(--radius-bubble)] group-[.is-user]:border-0 group-[.is-user]:bg-sage group-[.is-user]:px-4 group-[.is-user]:py-3 group-[.is-user]:text-sage-foreground";

const COACH_BUBBLE =
  "group-[.is-assistant]:bubble-coach group-[.is-assistant]:max-w-[92%] group-[.is-assistant]:rounded-[var(--radius-bubble)] group-[.is-assistant]:border group-[.is-assistant]:border-beige-border group-[.is-assistant]:bg-beige group-[.is-assistant]:px-4 group-[.is-assistant]:py-3 group-[.is-assistant]:text-card-text";

function hasCoachingTeam(proposals?: CoachingTeamProposals) {
  if (!proposals) return false;
  if (Array.isArray(proposals)) {
    return proposals.some((e) => e?.text?.trim());
  }
  return Object.values(proposals).some((v) => v?.trim());
}

type PendingImage = {
  base64: string;
  mime: string;
  previewUrl: string;
};

export function ChatView() {
  const { userId, ready } = useProfile();
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME]);
  const [input, setInput] = useState("");
  const [threadId, setThreadId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [lookingAtMeal, setLookingAtMeal] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pendingApproval, setPendingApproval] = useState<PendingApproval | null>(null);
  const [quickReplies, setQuickReplies] = useState<string[]>([]);
  const [restoring, setRestoring] = useState(false);
  const [pendingImage, setPendingImage] = useState<PendingImage | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!ready) return;

    setMessages([WELCOME]);
    setPendingApproval(null);
    setQuickReplies([]);
    setError(null);
    setInput("");
    setPendingImage(null);

    const storedThread = sessionStorage.getItem(threadStorageKey(userId));
    if (!storedThread) {
      setThreadId(null);
      return;
    }

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
              coaching_team: msg.coaching_team,
            })),
          );
        }
        setPendingApproval(data.pending_approval ?? null);
      })
      .catch(() => {
        // Keep welcome state if history cannot be loaded.
      })
      .finally(() => setRestoring(false));
  }, [userId, ready]);

  const submitMessage = useCallback(
    async (text: string, image?: PendingImage | null) => {
      setError(null);
      setLoading(true);
      const hasImage = Boolean(image?.base64);
      setLookingAtMeal(hasImage);

      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: text || (hasImage ? "Meal photo" : ""),
        imagePreviewUrl: image?.previewUrl,
      };
      setMessages((prev) => [...prev, userMsg]);
      setPendingImage(null);

      try {
        const data = await sendChat(
          text,
          threadId,
          hasImage ? { base64: image!.base64, mime: image!.mime } : null,
        );
        setThreadId(data.thread_id);
        sessionStorage.setItem(threadStorageKey(userId), data.thread_id);

        const assistantMsg: ChatMessage = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: data.reply,
          coaching_team: hasCoachingTeam(data.coaching_team) ? data.coaching_team : undefined,
          citations: data.citations?.length ? data.citations : undefined,
        };
        setMessages((prev) => [...prev, assistantMsg]);
        setPendingApproval(data.pending_approval ?? null);
        setQuickReplies(data.quick_replies ?? []);
      } catch (err) {
        const message =
          err instanceof ApiError
            ? `API error (${err.status}): ${err.message}`
            : "Oops something went wrong, Saurabh must be fixing it. Try again in a min";
        setError(message);
      } finally {
        setLoading(false);
        setLookingAtMeal(false);
      }
    },
    [threadId, userId],
  );

  async function handleSubmit(e?: React.FormEvent) {
    e?.preventDefault();
    const text = input.trim();
    if ((!text && !pendingImage) || loading || restoring || pendingApproval) return;
    setInput("");
    await submitMessage(text, pendingImage);
  }

  async function handleFileChange(file: File | null) {
    if (!file) return;
    setError(null);
    try {
      const compressed = await compressImageForChat(file);
      setPendingImage({
        base64: compressed.base64,
        mime: compressed.mime,
        previewUrl: compressed.previewUrl,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not attach image");
    }
  }

  function handleApprovalResolved(reply: string) {
    setPendingApproval(null);
    setQuickReplies([]);
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

  async function handleChip(option: string) {
    if (loading || restoring || pendingApproval) return;
    setQuickReplies([]);
    await submitMessage(option);
  }

  const lastAssistantIndex = messages.findLastIndex((m) => m.role === "assistant");
  const composerDisabled = loading || restoring || Boolean(pendingApproval);
  const canSend = Boolean(input.trim() || pendingImage) && !composerDisabled;

  return (
    <div className="content-width flex min-h-0 flex-1 flex-col">
      <Conversation className="min-h-0 flex-1">
        <ConversationAutoScroll
          watch={`${messages.length}:${loading}:${restoring}:${pendingApproval ? 1 : 0}:${quickReplies.length}`}
        />
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
                        <div className="flex flex-col gap-2">
                          {msg.imagePreviewUrl ? (
                            // eslint-disable-next-line @next/next/no-img-element
                            <img
                              src={msg.imagePreviewUrl}
                              alt="Meal attachment"
                              className="max-h-40 w-auto rounded-lg object-cover"
                            />
                          ) : null}
                          {msg.content ? (
                            <span className="whitespace-pre-wrap">{msg.content}</span>
                          ) : null}
                        </div>
                      )}
                    </MessageContent>
                  </Message>

                  {msg.role === "assistant" && msg.coaching_team && hasCoachingTeam(msg.coaching_team) ? (
                    <CoachingTeamPanel coachingTeam={msg.coaching_team} />
                  ) : null}

                  {msg.role === "assistant" && msg.citations?.length ? (
                    <CitationChips citations={msg.citations} />
                  ) : null}
                </div>

                {isLastAssistant && !loading ? (
                  <MessageActions className="ml-1">
                    <MessageAction
                      tooltip="Copy"
                      label="Copy"
                      variant="ghost"
                      className="text-navy-muted hover:bg-team-panel hover:text-navy-text"
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
                    : lookingAtMeal
                      ? "Looking at your meal…"
                      : "The AI Coaching Team is talking it over…"}
                </span>
              </MessageContent>
            </Message>
          ) : null}

          {error ? (
            <div className="rounded-2xl border border-beige-border/40 bg-team-panel px-4 py-3 text-sm text-navy-muted">
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
          className="border-beige-border/30 bg-team-panel text-navy-muted hover:bg-team-panel hover:text-navy-text"
        />
      </Conversation>

      <form
        onSubmit={handleSubmit}
        className="sticky bottom-0 z-10 -mx-5 border-t border-beige-border/15 bg-navy px-5 py-3"
      >
        {quickReplies.length > 0 && !composerDisabled ? (
          <div className="mb-3 flex flex-wrap gap-2">
            {quickReplies.map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => void handleChip(option)}
                className={cn(
                  "rounded-[var(--radius-pill)] border border-sage/40 bg-sage/90 px-3.5 py-1.5",
                  "text-xs font-medium text-sage-foreground transition-colors",
                  "hover:bg-sage-hover",
                )}
              >
                {option}
              </button>
            ))}
          </div>
        ) : null}

        {pendingImage ? (
          <div className="mb-2 flex items-center gap-2">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={pendingImage.previewUrl}
              alt="Ready to send"
              className="h-14 w-14 rounded-lg object-cover ring-1 ring-beige-border/40"
            />
            <button
              type="button"
              onClick={() => setPendingImage(null)}
              className="inline-flex items-center gap-1 rounded-[var(--radius-pill)] px-2 py-1 text-xs text-navy-muted hover:bg-team-panel hover:text-navy-text"
            >
              <XIcon className="size-3.5" />
              Remove
            </button>
          </div>
        ) : null}

        <div
          className={cn(
            "group flex items-end gap-2 rounded-[var(--radius-pill)] border p-1.5 pl-2 transition-colors duration-150 ease-out",
            "border-beige-border/35 bg-beige-border/20",
            "focus-within:border-beige-border focus-within:bg-beige",
            composerDisabled && "opacity-60",
          )}
        >
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            capture="environment"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0] ?? null;
              void handleFileChange(f);
              e.target.value = "";
            }}
          />
          <button
            type="button"
            disabled={composerDisabled}
            onClick={() => fileRef.current?.click()}
            aria-label="Attach meal photo"
            title="Attach meal photo"
            className={cn(
              "mb-0.5 inline-flex shrink-0 items-center gap-1.5 rounded-[var(--radius-pill)]",
              "border border-sage/50 bg-sage/20 px-2.5 py-1.5",
              "text-xs font-semibold text-navy-text transition-colors",
              "hover:border-sage hover:bg-sage/35",
              "disabled:cursor-not-allowed disabled:opacity-40",
            )}
          >
            <ImagePlusIcon className="size-4 stroke-[2.25]" aria-hidden />
            Photo
          </button>
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
            disabled={!canSend}
            className={cn(
              "mb-0.5 shrink-0 rounded-[var(--radius-pill)] px-5 py-2 text-sm font-medium transition-colors duration-150 ease-out",
              "bg-sage/25 text-sage-foreground/40",
              "group-focus-within:bg-sage/40 group-focus-within:text-sage-foreground/60",
              "disabled:cursor-not-allowed",
              canSend &&
                "group-focus-within:bg-sage group-focus-within:text-sage-foreground group-focus-within:hover:bg-sage-hover bg-sage text-sage-foreground hover:bg-sage-hover",
            )}
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}
