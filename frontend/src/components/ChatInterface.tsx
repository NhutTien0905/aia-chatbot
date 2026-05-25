"use client";

import { useState, useRef, useEffect } from "react";
import { streamChat, ChatMessage, Citation } from "@/lib/api";
import MessageBubble from "./MessageBubble";
import LoadingIndicator from "./LoadingIndicator";

interface ChatInterfaceProps {
  sessionId: string;
  hasDocuments: boolean;
}

export default function ChatInterface({ sessionId, hasDocuments }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const question = input.trim();
    setInput("");

    // Add user message
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setIsLoading(true);

    // Add empty assistant message for streaming
    setMessages((prev) => [...prev, { role: "assistant", content: "", citations: [] }]);

    try {
      let citations: Citation[] = [];
      let content = "";

      for await (const event of streamChat(question, sessionId)) {
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
        } else if (event.type === "error") {
          content = `Error: ${event.data}`;
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = { role: "assistant", content };
            return updated;
          });
        }
      }

      // Final update with citations
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
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div
        className="flex-1 overflow-y-auto p-4 space-y-4"
        role="list"
        aria-label="Chat messages"
      >
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <p className="text-lg font-medium">Insurance Document Assistant</p>
            <p className="text-sm mt-2">
              {hasDocuments
                ? "Ask questions about your uploaded documents"
                : "Upload documents to get started"}
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}

        {isLoading && messages[messages.length - 1]?.content === "" && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-2">
              <LoadingIndicator variant="dots" size="md" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="border-t p-4" aria-label="Send a message">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={hasDocuments ? "Ask about your documents..." : "Upload documents first..."}
            disabled={!hasDocuments || isLoading}
            aria-label="Message input"
            className="flex-1 border rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={!hasDocuments || isLoading || !input.trim()}
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
