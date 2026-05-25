"use client";

import { useState, useRef, useEffect } from "react";
import { streamChat, ChatMessage, Citation } from "@/lib/api";
import MessageBubble from "./MessageBubble";
import LoadingIndicator from "./LoadingIndicator";

interface ChatInterfaceProps {
  sessionId: string;
  hasDocuments: boolean;
  hasSelectedSources: boolean;
  selectedFiles: string[];
}

const CHAT_STORAGE_KEY = "chat_history";

function loadChatHistory(sessionId: string): ChatMessage[] {
  if (typeof window === "undefined") return [];
  try {
    const stored = localStorage.getItem(`${CHAT_STORAGE_KEY}_${sessionId}`);
    if (stored) return JSON.parse(stored);
  } catch {
    // ignore parse errors
  }
  return [];
}

function saveChatHistory(sessionId: string, messages: ChatMessage[]) {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(`${CHAT_STORAGE_KEY}_${sessionId}`, JSON.stringify(messages));
  } catch {
    // ignore quota errors
  }
}

export default function ChatInterface({
  sessionId,
  hasDocuments,
  hasSelectedSources,
  selectedFiles,
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>(() => loadChatHistory(sessionId));
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Reload history when sessionId changes
  useEffect(() => {
    setMessages(loadChatHistory(sessionId));
  }, [sessionId]);

  // Persist messages whenever they change (skip empty assistant messages during streaming)
  useEffect(() => {
    const toSave = messages.filter((m) => m.content !== "");
    if (toSave.length > 0) {
      saveChatHistory(sessionId, toSave);
    }
  }, [messages, sessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const canSend = hasDocuments && hasSelectedSources;

  const getPlaceholder = () => {
    if (!hasDocuments) return "Upload documents first...";
    if (!hasSelectedSources) return "Select sources from the sidebar to ask questions...";
    return "Ask about your documents...";
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading || !canSend) return;

    const question = input.trim();
    setInput("");

    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setIsLoading(true);

    setMessages((prev) => [...prev, { role: "assistant", content: "", citations: [] }]);

    try {
      let citations: Citation[] = [];
      let content = "";

      for await (const event of streamChat(question, sessionId, selectedFiles)) {
        if (event.type === "citations") {
          citations = event.data as Citation[];
        } else if (event.type === "token") {
          content += event.data as string;
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              role: "assistant",
              content,
              citations,
            };
            return updated;
          });
        } else if (event.type === "hide_citations") {
          // LLM couldn't find the answer — hide citations
          citations = [];
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              role: "assistant",
              content,
              citations: [],
            };
            return updated;
          });
        } else if (event.type === "error") {
          content = `Error: ${event.data}`;
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = { role: "assistant", content };
            return updated;
          });
        }
      }

      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = { role: "assistant", content, citations };
        return updated;
      });
    } catch (err) {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: `Error: ${err instanceof Error ? err.message : "Something went wrong"}`,
        };
        return updated;
      });
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900">
      {/* Messages */}
      <div
        className="flex-1 overflow-y-auto p-4 space-y-4"
        role="list"
        aria-label="Chat messages"
      >
        {messages.length === 0 && (
          <div className="text-center text-gray-500 dark:text-gray-400 mt-8">
            <p className="text-lg font-medium">Insurance Document Assistant</p>
            <p className="text-sm mt-2">
              {!hasDocuments
                ? "Upload documents to get started"
                : !hasSelectedSources
                ? "Select sources from the sidebar to start asking questions"
                : "Ask questions about your selected documents"}
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}

        {isLoading && messages[messages.length - 1]?.content === "" && (
          <div className="flex justify-start">
            <div className="bg-gray-100 dark:bg-gray-700 rounded-lg px-4 py-2">
              <LoadingIndicator variant="dots" size="md" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Selected sources indicator */}
      {hasDocuments && (
        <div className="px-4 py-1 border-t border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-800/50">
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {hasSelectedSources
              ? `Searching in ${selectedFiles.length} source${selectedFiles.length > 1 ? "s" : ""}`
              : "No sources selected"}
          </p>
        </div>
      )}

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        className="border-t border-gray-200 dark:border-gray-700 p-4 bg-white dark:bg-gray-800"
        aria-label="Send a message"
      >
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={getPlaceholder()}
            disabled={!canSend || isLoading}
            aria-label="Message input"
            className="flex-1 border border-gray-300 dark:border-gray-600 rounded-lg px-4 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 dark:disabled:bg-gray-800 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={!canSend || isLoading || !input.trim()}
            aria-label="Send message"
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}
