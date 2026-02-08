"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { Bot, User } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import type { ChatMessage as ChatMessageType } from "@/lib/types/api";

interface ChatMessageProps {
  message: ChatMessageType;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn("flex gap-3 px-4 py-4", isUser ? "bg-transparent" : "bg-gray-900/50")}
    >
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg",
          isUser ? "bg-blue-600" : "bg-gray-700"
        )}
      >
        {isUser ? (
          <User className="h-4 w-4 text-white" />
        ) : (
          <Bot className="h-4 w-4 text-blue-400" />
        )}
      </div>

      <div className="min-w-0 flex-1">
        <div className="mb-1 text-xs font-medium text-gray-500">
          {isUser ? "You" : "EduAGI"}
        </div>
        {isUser ? (
          <p className="text-sm text-gray-200 whitespace-pre-wrap">
            {message.content}
          </p>
        ) : (
          <div className="prose prose-sm prose-invert max-w-none text-gray-200 prose-headings:text-gray-100 prose-p:text-gray-200 prose-a:text-blue-400 prose-strong:text-gray-100 prose-code:text-blue-300 prose-pre:bg-gray-800 prose-pre:border prose-pre:border-gray-700">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeHighlight]}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
