"use client";

import { UploadedFile } from "@/lib/api";

interface DocumentListProps {
  files: UploadedFile[];
  onDeleteFile?: (filename: string) => void;
}

export default function DocumentList({ files, onDeleteFile }: DocumentListProps) {
  if (files.length === 0) return null;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "ready":
        return <span className="text-green-500">✓</span>;
      case "processing":
        return <span className="animate-spin">⟳</span>;
      case "error":
        return <span className="text-red-500">✗</span>;
      default:
        return <span className="text-gray-400">○</span>;
    }
  };

  const getFileIcon = (type: string) => {
    if (type.includes("pdf") || type === "pdf") return "📄";
    if (type.includes("docx") || type === "docx") return "📝";
    if (type.includes("image") || type === "image") return "🖼️";
    return "📎";
  };

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
        Uploaded Documents
      </h3>
      <div className="space-y-1">
        {files.map((file, i) => (
          <div
            key={i}
            className="flex items-center gap-2 p-2 bg-gray-50 dark:bg-gray-700/50 rounded text-sm group"
          >
            <span>{getFileIcon(file.file_type)}</span>
            <span className="flex-1 truncate text-gray-900 dark:text-gray-100">
              {file.filename}
            </span>
            {getStatusIcon(file.status)}
            {file.num_chunks > 0 && (
              <span className="text-xs text-gray-400 dark:text-gray-500">
                {file.num_chunks} chunks
              </span>
            )}
            {onDeleteFile && file.status === "ready" && (
              <button
                onClick={() => onDeleteFile(file.filename)}
                className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-600 dark:text-red-500 dark:hover:text-red-400 transition-opacity text-xs"
                aria-label={`Delete ${file.filename}`}
                title="Remove file"
              >
                ✕
              </button>
            )}
            {file.error_message && (
              <span
                className="text-xs text-red-500 dark:text-red-400 truncate max-w-[100px]"
                title={file.error_message}
              >
                {file.error_message}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
