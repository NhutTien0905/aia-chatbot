"use client";

import { ChatMessage, Citation } from "@/lib/api";

interface MessageBubbleProps {
  message: ChatMessage;
}

function formatCitation(c: Citation): string {
  let s = c.filename;
  if (c.page_number) s += `, Page ${c.page_number}`;
  if (c.section_number) s += `, Section ${c.section_number}`;
  if (c.paragraph_range) s += `, Paragraphs ${c.paragraph_range}`;
  return s;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={`flex ${isUser ? "justify-end" : "justify-start"}`}
      role="listitem"
      aria-label={`${isUser ? "You" : "Assistant"} said`}
    >
      <div
        className={`max-w-[85%] md:max-w-[70%] rounded-lg px-4 py-2 ${
          isUser
            ? "bg-blue-600 text-white"
            : "bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100"
        }`}
      >
        <p className="whitespace-pre-wrap text-sm">{message.content}</p>
        {message.citations && message.citations.length > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-600">
            <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Sources:</p>
            <div className="flex flex-wrap gap-1">
              {message.citations.map((c, j) => (
                <span
                  key={j}
                  className="inline-block text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-0.5 rounded"
                  title={`Relevance: ${(c.relevance_score * 100).toFixed(0)}%`}
                >
                  {formatCitation(c)}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
