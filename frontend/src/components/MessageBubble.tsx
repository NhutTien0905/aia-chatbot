"use client";

import { useState, useRef, useCallback } from "react";
import { createPortal } from "react-dom";
import { ChatMessage, Citation } from "@/lib/api";

interface MessageBubbleProps {
  message: ChatMessage;
}

/** Tooltip rendered via portal to avoid overflow clipping */
function CitationTooltip({
  citation,
  index,
}: {
  citation: Citation;
  index: number;
}) {
  const [show, setShow] = useState(false);
  const [pos, setPos] = useState({ x: 0, y: 0 });
  const ref = useRef<HTMLSpanElement>(null);

  const sourceText = citation.source_text || "No preview available";

  const handleMouseEnter = useCallback(() => {
    if (ref.current) {
      const rect = ref.current.getBoundingClientRect();
      setPos({
        x: rect.left + rect.width / 2,
        y: rect.top,
      });
    }
    setShow(true);
  }, []);

  return (
    <>
      <span
        ref={ref}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={() => setShow(false)}
        className="inline-flex items-center justify-center text-[10px] font-bold bg-blue-200 dark:bg-blue-800 text-blue-800 dark:text-blue-200 rounded-full w-4 h-4 mx-0.5 align-middle cursor-help"
        aria-label={`Source ${index}`}
      >
        {index}
      </span>
      {show &&
        typeof document !== "undefined" &&
        createPortal(
          <div
            className="fixed z-[9999] pointer-events-none"
            style={{
              left: `${pos.x}px`,
              top: `${pos.y}px`,
              transform: "translate(-50%, -100%)",
            }}
          >
            <div className="mb-2 w-72 p-3 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 text-xs rounded-lg shadow-xl">
              <span className="font-semibold block mb-1 text-blue-300 dark:text-blue-700">
                [{index}] {citation.filename}
                {citation.page_number ? `, Page ${citation.page_number}` : ""}
                {citation.section_number ? `, Section ${citation.section_number}` : ""}
              </span>
              <span className="block leading-relaxed opacity-90 whitespace-pre-wrap">
                {sourceText.length > 250 ? sourceText.slice(0, 250) + "..." : sourceText}
              </span>
              {/* Arrow */}
              <span className="absolute -bottom-1 left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900 dark:border-t-gray-100" />
            </div>
          </div>,
          document.body
        )}
    </>
  );
}

/**
 * Parse message content and render:
 * - **text** as bold (uppercase)
 * - [1], [2] etc. as styled citation references with hover tooltip
 */
function renderContent(content: string, citations?: Citation[]) {
  if (!content) return null;

  const parts = content.split(/(\*\*[^*]+\*\*|\[\d+\])/g);

  return parts.map((part, i) => {
    // Bold text: **text** → render uppercase bold
    if (part.startsWith("**") && part.endsWith("**")) {
      const text = part.slice(2, -2);
      return (
        <strong key={i} className="font-bold uppercase">
          {text}
        </strong>
      );
    }

    // Citation reference: [1], [2], etc.
    if (/^\[\d+\]$/.test(part)) {
      const num = parseInt(part.slice(1, -1), 10);
      const citation = citations && citations[num - 1];

      if (citation) {
        return <CitationTooltip key={i} citation={citation} index={num} />;
      }

      return (
        <span
          key={i}
          className="inline-flex items-center justify-center text-[10px] font-bold bg-blue-200 dark:bg-blue-800 text-blue-800 dark:text-blue-200 rounded-full w-4 h-4 mx-0.5 align-middle"
        >
          {num}
        </span>
      );
    }

    return <span key={i}>{part}</span>;
  });
}

/**
 * Deduplicate citations for the Sources list display.
 * Groups citations that share the same file+page+section, showing all reference numbers.
 */
function getUniqueSources(citations: Citation[]) {
  const seen = new Map<string, { citation: Citation; indices: number[] }>();
  citations.forEach((c, j) => {
    const key = `${c.filename}|${c.page_number ?? ""}|${c.section_number ?? ""}`;
    if (seen.has(key)) {
      seen.get(key)!.indices.push(j + 1);
    } else {
      seen.set(key, { citation: c, indices: [j + 1] });
    }
  });
  return Array.from(seen.values());
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const hasCitations = message.citations && message.citations.length > 0;

  return (
    <div
      className={`flex ${isUser ? "justify-end" : "justify-start"}`}
      role="listitem"
      aria-label={`${isUser ? "You" : "Assistant"} said`}
    >
      <div
        className={`max-w-[85%] md:max-w-[70%] rounded-lg px-4 py-2 overflow-hidden ${
          isUser
            ? "bg-blue-600 text-white"
            : "bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100"
        }`}
      >
        <div className="whitespace-pre-wrap text-sm leading-relaxed break-words overflow-wrap-anywhere">
          {isUser ? message.content : renderContent(message.content, message.citations)}
        </div>
        {hasCitations && (
          <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-600">
            <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Sources:</p>
            <div className="flex flex-col gap-1">
              {getUniqueSources(message.citations!).map(({ citation: c, indices }, j) => (
                <div key={j} className="flex items-start gap-1.5 text-xs">
                  <span className="inline-flex items-center justify-center font-bold bg-blue-200 dark:bg-blue-800 text-blue-800 dark:text-blue-200 rounded-full min-w-[18px] h-[18px] text-[10px]">
                    {indices.join(",")}
                  </span>
                  <span className="text-gray-600 dark:text-gray-300 break-all">
                    {c.filename}
                    {c.page_number ? `, Page ${c.page_number}` : ""}
                    {c.section_number ? `, Section ${c.section_number}` : ""}
                    {c.paragraph_range ? `, Paragraphs ${c.paragraph_range}` : ""}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
