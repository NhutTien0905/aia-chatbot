"use client";

import { useState, useEffect } from "react";
import FileUpload from "@/components/FileUpload";
import ChatInterface from "@/components/ChatInterface";
import DocumentList from "@/components/DocumentList";
import LoadingIndicator from "@/components/LoadingIndicator";
import { createSession, UploadedFile } from "@/lib/api";
import { getSessionId, setSessionId, clearSession } from "@/lib/session";

export default function Home() {
  const [sessionId, setSessionIdState] = useState<string>("");
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [showUpload, setShowUpload] = useState(true);

  useEffect(() => {
    // Get or create session
    const stored = getSessionId();
    if (stored) {
      setSessionIdState(stored);
    } else {
      createSession().then((id) => {
        setSessionIdState(id);
        setSessionId(id);
      }).catch(() => {
        // Fallback: generate local session ID if server is unreachable
        const localId = crypto.randomUUID();
        setSessionIdState(localId);
        setSessionId(localId);
      });
    }
  }, []);

  const handleUploadComplete = (uploadedFiles: UploadedFile[]) => {
    setFiles((prev) => [...prev, ...uploadedFiles]);
  };

  const handleNewSession = () => {
    clearSession();
    window.location.reload();
  };

  const hasDocuments = files.some((f) => f.status === "ready");

  if (!sessionId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingIndicator variant="spinner" text="Initializing session..." />
      </div>
    );
  }

  return (
    <main className="min-h-screen flex flex-col md:flex-row">
      {/* Sidebar - Documents */}
      <aside
        className={`${
          showUpload ? "block" : "hidden md:block"
        } w-full md:w-80 border-b md:border-b-0 md:border-r bg-white p-4 flex flex-col gap-4`}
        aria-label="Document management sidebar"
      >
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-bold text-gray-900">
            Insurance Assistant
          </h1>
          <button
            className="md:hidden text-sm text-blue-600"
            onClick={() => setShowUpload(false)}
            aria-label="Switch to chat view"
          >
            Chat →
          </button>
        </div>

        <FileUpload sessionId={sessionId} onUploadComplete={handleUploadComplete} />
        <DocumentList files={files} />

        <div className="mt-auto pt-4 border-t">
          <p className="text-xs text-gray-400">
            Session: {sessionId.slice(0, 8)}...
          </p>
          <button
            onClick={handleNewSession}
            className="text-xs text-red-500 hover:text-red-700 mt-1"
            aria-label="Start a new session"
          >
            New Session
          </button>
        </div>
      </aside>

      {/* Main - Chat */}
      <section
        className={`${
          !showUpload ? "block" : "hidden md:block"
        } flex-1 flex flex-col h-screen md:h-auto`}
        aria-label="Chat section"
      >
        <div className="md:hidden flex items-center justify-between p-3 border-b">
          <button
            className="text-sm text-blue-600"
            onClick={() => setShowUpload(true)}
            aria-label="Switch to documents view"
          >
            ← Documents
          </button>
          <span className="text-sm font-medium">Chat</span>
          <span className="w-16" />
        </div>
        <div className="flex-1 min-h-0">
          <ChatInterface sessionId={sessionId} hasDocuments={hasDocuments} />
        </div>
      </section>
    </main>
  );
}
