"use client";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { UIMessage } from "ai";
import { ArrowDownIcon, DownloadIcon } from "lucide-react";
import type { ComponentProps } from "react";
import { useCallback, useEffect, useRef, useState } from "react";
import { StickToBottom, useStickToBottomContext } from "use-stick-to-bottom";

/** Instant when reduced-motion is on; spring/"smooth" otherwise. */
function useStickAnimation(): "smooth" | "instant" {
  const [animation, setAnimation] = useState<"smooth" | "instant">("smooth");

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const sync = () => setAnimation(mq.matches ? "instant" : "smooth");
    sync();
    mq.addEventListener("change", sync);
    return () => mq.removeEventListener("change", sync);
  }, []);

  return animation;
}

export type ConversationProps = ComponentProps<typeof StickToBottom>;

/**
 * Scroll shell for chat. Overflow MUST live on StickToBottom.Content's
 * scrollRef (via scrollClassName) — not on this outer wrapper. Putting
 * overflow-y-auto here made the page/window scroll while the library
 * tracked an inner pane that never overflowed.
 */
export const Conversation = ({ className, ...props }: ConversationProps) => {
  const animation = useStickAnimation();

  return (
    <StickToBottom
      className={cn(
        "relative flex min-h-0 flex-1 flex-col overflow-hidden",
        className,
      )}
      initial={animation}
      resize={animation}
      role="log"
      {...props}
    />
  );
};

export type ConversationContentProps = ComponentProps<
  typeof StickToBottom.Content
>;

export const ConversationContent = ({
  className,
  scrollClassName,
  ...props
}: ConversationContentProps) => (
  <StickToBottom.Content
    // Absolute fill so the scrollport always has a bounded height inside
    // the flex chat column (percentage height alone was unreliable).
    scrollClassName={cn(
      "absolute inset-0 overflow-y-auto overscroll-contain",
      scrollClassName,
    )}
    className={cn("flex flex-col gap-8 p-4", className)}
    {...props}
  />
);

/**
 * Stick to bottom when `watch` changes (new messages, loading, approval
 * card, quick replies) — but only if the user was already near the bottom.
 * Uses preserveScrollPosition so a mid-history reader is never yanked down.
 * A short duration keeps following multi-element growth (reply → team panel
 * → citations → approval card) in the same stick session.
 */
export function ConversationAutoScroll({ watch }: { watch: unknown }) {
  const { scrollToBottom } = useStickToBottomContext();
  const animation = useStickAnimation();

  useEffect(() => {
    let cancelled = false;
    let raf2 = 0;
    const raf1 = requestAnimationFrame(() => {
      raf2 = requestAnimationFrame(() => {
        if (cancelled) return;
        void scrollToBottom({
          animation,
          // Critical: do not force isAtBottom=true when the user scrolled away.
          preserveScrollPosition: true,
          // Hold stickiness briefly so sequential layout (cards) stays in view.
          duration: animation === "instant" ? undefined : 480,
        });
      });
    });
    return () => {
      cancelled = true;
      cancelAnimationFrame(raf1);
      cancelAnimationFrame(raf2);
    };
  }, [watch, scrollToBottom, animation]);

  return null;
}

export type ConversationEmptyStateProps = ComponentProps<"div"> & {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
};

export const ConversationEmptyState = ({
  className,
  title = "No messages yet",
  description = "Start a conversation to see messages here",
  icon,
  children,
  ...props
}: ConversationEmptyStateProps) => (
  <div
    className={cn(
      "flex size-full flex-col items-center justify-center gap-3 p-8 text-center",
      className,
    )}
    {...props}
  >
    {children ?? (
      <>
        {icon && <div className="text-muted-foreground">{icon}</div>}
        <div className="space-y-1">
          <h3 className="font-medium text-sm">{title}</h3>
          {description && (
            <p className="text-muted-foreground text-sm">{description}</p>
          )}
        </div>
      </>
    )}
  </div>
);

export type ConversationScrollButtonProps = ComponentProps<typeof Button> & {
  /** When true, label the pill “New message ↓” (content arrived while away). */
  hasNewMessage?: boolean;
};

export const ConversationScrollButton = ({
  className,
  hasNewMessage = false,
  ...props
}: ConversationScrollButtonProps) => {
  const { isAtBottom, scrollToBottom } = useStickToBottomContext();
  const animation = useStickAnimation();

  const handleScrollToBottom = useCallback(() => {
    void scrollToBottom({ animation });
  }, [scrollToBottom, animation]);

  if (isAtBottom) return null;

  return (
    <Button
      className={cn(
        "absolute bottom-4 left-1/2 z-10 -translate-x-1/2 gap-1.5 rounded-full",
        "border-beige-border/30 bg-team-panel px-3.5 text-navy-muted",
        "hover:bg-team-panel hover:text-navy-text",
        "shadow-md",
        className,
      )}
      onClick={handleScrollToBottom}
      size="sm"
      type="button"
      variant="outline"
      {...props}
    >
      {hasNewMessage ? "New message" : "Jump to latest"}
      <ArrowDownIcon className="size-3.5" aria-hidden />
    </Button>
  );
};

/** Tracks whether content changed while the user was scrolled away. */
export function useNewMessageWhileAway(watch: unknown) {
  const { isAtBottom } = useStickToBottomContext();
  const [hasNewMessage, setHasNewMessage] = useState(false);
  const watchRef = useRef(watch);

  useEffect(() => {
    if (watchRef.current !== watch) {
      watchRef.current = watch;
      if (!isAtBottom) {
        setHasNewMessage(true);
      }
    }
  }, [watch, isAtBottom]);

  useEffect(() => {
    if (isAtBottom) setHasNewMessage(false);
  }, [isAtBottom]);

  return hasNewMessage;
}

/** Combines auto-scroll + new-message pill so they share one `watch` signal. */
export function ConversationScrollChrome({ watch }: { watch: unknown }) {
  const hasNewMessage = useNewMessageWhileAway(watch);
  return (
    <>
      <ConversationAutoScroll watch={watch} />
      <ConversationScrollButton hasNewMessage={hasNewMessage} />
    </>
  );
}

const getMessageText = (message: UIMessage): string =>
  message.parts
    .filter((part) => part.type === "text")
    .map((part) => part.text)
    .join("");

export type ConversationDownloadProps = Omit<
  ComponentProps<typeof Button>,
  "onClick"
> & {
  messages: UIMessage[];
  filename?: string;
  formatMessage?: (message: UIMessage, index: number) => string;
};

const defaultFormatMessage = (message: UIMessage): string => {
  const roleLabel =
    message.role.charAt(0).toUpperCase() + message.role.slice(1);
  return `**${roleLabel}:** ${getMessageText(message)}`;
};

export const messagesToMarkdown = (
  messages: UIMessage[],
  formatMessage: (
    message: UIMessage,
    index: number,
  ) => string = defaultFormatMessage,
): string => messages.map((msg, i) => formatMessage(msg, i)).join("\n\n");

export const ConversationDownload = ({
  messages,
  filename = "conversation.md",
  formatMessage = defaultFormatMessage,
  className,
  children,
  ...props
}: ConversationDownloadProps) => {
  const handleDownload = useCallback(() => {
    const markdown = messagesToMarkdown(messages, formatMessage);
    const blob = new Blob([markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.append(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }, [messages, filename, formatMessage]);

  return (
    <Button
      className={cn(
        "absolute top-4 right-4 rounded-full dark:bg-background dark:hover:bg-muted",
        className,
      )}
      onClick={handleDownload}
      size="icon"
      type="button"
      variant="outline"
      {...props}
    >
      {children ?? <DownloadIcon className="size-4" />}
    </Button>
  );
};
