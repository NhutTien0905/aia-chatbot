"use client";

import { useState, useEffect } from "react";
import FileUpload from "@/components/FileUpload";
import ChatInterface from "@/components/ChatInterface";
import DocumentList from "@/components/DocumentList";
import LoadingIndicator from "@/components/LoadingIndicator";
import ThemeToggle from "@/components/ThemeToggle";
import { createSession, deleteDocument, UploadedFile } from "@/lib/api";
import { getSessionId, setSessionId, clearSession } from "@/lib/session";

export default function Home() {
  const [sessionId, setSessionIdState] = useState<string>("");
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [showUpload, setShowUpload] = useState(true);

  useEffect(() => {
    const stored = getSessionId();
    if (stored) {
      setSessionIdState(stored);
    } else {
      createSession()
        .then((id) => {
          setSessionIdState(id);
          setSessionId(id);
        })
        .catch(() => {
          const localId = crypto.randomUUID();
          setSessionIdState(localId);
          setSessionId(localId);
        });
    }
  }, []);

  const handleUploadComplete = (uploadedFiles: UploadedFile[]) => {
    setFiles((prev) => [...prev, ...uploadedFiles]);
  };

  const handleDeleteFile = async (filename: string) => {
    try {
      await deleteDocument(sessionId, filename);
      setFiles((prev) => prev.filter((f) => f.filename !== filename));
    } catch {
      // Silently fail — file may already be removed
      setFiles((prev) => prev.filter((f) => f.filename !== filename));
    }
  };

  const handleNewSession = () => {
    clearSession();
    window.location.reload();
  };

  const hasDocuments = files.some((f) => f.status === "ready");

  if (!sessionId) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white dark:bg-gray-900">
        <LoadingIndicator variant="spinner" text="Initializing session..." />
      </div>
    );
  }

  return (
    <main className="min-h-screen flex flex-col md:flex-row bg-white dark:bg-gray-900">
      {/* Sidebar - Documents */}
      <aside
        className={`${
          showUpload ? "block" : "hidden md:block"
        } w-full md:w-80 border-b md:border-b-0 md:border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4 flex flex-col gap-4`}
        aria-label="Document management sidebar"
      >
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-bold text-gray-900 dark:text-white">
            Insurance Assistant
          </h1>
          <div className="flex items-center gap-1">
            <ThemeToggle />
            <button
              className="md:hidden text-sm text-blue-600 dark:text-blue-400"
              onClick={() => setShowUpload(false)}
              aria-label="Switch to chat view"
            >
              Chat →
            </button>
          </div>
        </div>

        <FileUpload sessionId={sessionId} onUploadComplete={handleUploadComplete} />
        <DocumentList files={files} onDeleteFile={handleDeleteFile} />

        <div className="mt-auto pt-4 border-t border-gray-200 dark:border-gray-700">
          <p className="text-xs text-gray-400 dark:text-gray-500">
            Session: {sessionId.slice(0, 8)}...
          </p>
          <button
            onClick={handleNewSession}
            className="text-xs text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 mt-1"
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
        <div className="md:hidden flex items-center justify-between p-3 border-b border-gray-200 dark:border-gray-700">
          <button
            className="text-sm text-blue-600 dark:text-blue-400"
            onClick={() => setShowUpload(true)}
            aria-label="Switch to documents view"
          >
            ← Documents
          </button>
          <span className="text-sm font-medium text-gray-900 dark:text-white">Chat</span>
          <ThemeToggle />
        </div>
        <div className="flex-1 min-h-0">
          <ChatInterface sessionId={sessionId} hasDocuments={hasDocuments} />
        </div>
      </section>
    </main>
  );
}
