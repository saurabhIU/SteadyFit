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
import {
  PromptInput,
  type PromptInputMessage,
  PromptInputSubmit,
  PromptInputTextarea,
} from "@/components/ai-elements/prompt-input";
import { PlanApprovalCard } from "@/components/chat/PlanApprovalCard";
import { ApiError, fetchChatHistory, sendChat } from "@/lib/api";
import { notifyPlanUpdated } from "@/lib/plan-events";
import type { ChatMessage, PendingApproval } from "@/lib/types";

const THREAD_KEY = "steadyfit_thread_id";

const WELCOME: ChatMessage = {
  id: "welcome",
  role: "assistant",
  content:
    "Tell me your goal, log a meal, or say what got in the way this week — the council will handle the re-planning.",
};

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

  async function handleSubmit(message: PromptInputMessage) {
    const text = message.text.trim();
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

  return (
    <div className="mx-auto flex min-h-0 w-full max-w-3xl flex-1 flex-col px-5">
      <Conversation className="min-h-0 flex-1">
        <ConversationContent className="gap-4 p-0 py-5">
          {messages.map((msg, messageIndex) => {
            const isLastAssistant =
              msg.role === "assistant" && messageIndex === lastAssistantIndex;

            return (
              <Fragment key={msg.id}>
                <Message from={msg.role}>
                  <MessageContent>
                    {msg.role === "assistant" ? (
                      <MessageResponse>{msg.content}</MessageResponse>
                    ) : (
                      <span className="whitespace-pre-wrap">{msg.content}</span>
                    )}
                  </MessageContent>
                </Message>
                {isLastAssistant && !loading ? (
                  <MessageActions>
                    <MessageAction
                      tooltip="Copy"
                      label="Copy"
                      onClick={() => navigator.clipboard.writeText(msg.content)}
                    >
                      <CopyIcon className="size-3" />
                    </MessageAction>
                  </MessageActions>
                ) : null}
              </Fragment>
            );
          })}

          {loading || restoring ? (
            <Message from="assistant">
              <MessageContent>
                <span className="text-steel">
                  {restoring ? "restoring your thread…" : "council convening…"}
                </span>
              </MessageContent>
            </Message>
          ) : null}

          {error ? (
            <div className="rounded border border-lift/40 bg-lift/10 px-3.5 py-2.5 text-sm text-ink">
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
        <ConversationScrollButton />
      </Conversation>

      <PromptInput
        onSubmit={handleSubmit}
        className="relative mb-4 w-full border-t border-line pt-3.5"
      >
        <PromptInputTextarea
          value={input}
          placeholder="e.g. I missed leg day and I'm traveling Wed–Fri"
          onChange={(e) => setInput(e.currentTarget.value)}
          className="min-h-[52px] pr-12"
          disabled={loading || restoring || Boolean(pendingApproval)}
        />
        <PromptInputSubmit
          status={loading ? "submitted" : undefined}
          disabled={!input.trim() || loading || restoring || Boolean(pendingApproval)}
          className="absolute right-2 bottom-2"
        />
      </PromptInput>
    </div>
  );
}
