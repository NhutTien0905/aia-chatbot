"use client";

import { UploadedFile } from "@/lib/api";

interface DocumentListProps {
  files: UploadedFile[];
  selectedFiles: string[];
  onToggleFile: (filename: string) => void;
  onSelectAll: () => void;
  onDeselectAll: () => void;
}

export default function DocumentList({
  files,
  selectedFiles,
  onToggleFile,
  onSelectAll,
  onDeselectAll,
}: DocumentListProps) {
  if (files.length === 0) return null;

  const readyFiles = files.filter((f) => f.status === "ready");
  const allSelected = readyFiles.length > 0 && readyFiles.every((f) => selectedFiles.includes(f.filename));

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
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
          Sources
        </h3>
        {readyFiles.length > 1 && (
          <button
            onClick={allSelected ? onDeselectAll : onSelectAll}
            className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
          >
            {allSelected ? "Deselect all" : "Select all"}
          </button>
        )}
      </div>

      {selectedFiles.length === 0 && readyFiles.length > 0 && (
        <p className="text-xs text-amber-600 dark:text-amber-400">
          Select at least one source to ask questions
        </p>
      )}

      <div className="space-y-1">
        {files.map((file, i) => {
          const isReady = file.status === "ready";
          const isSelected = selectedFiles.includes(file.filename);

          return (
            <div
              key={i}
              className={`flex items-center gap-2 p-2 rounded text-sm cursor-pointer transition-colors ${
                isSelected
                  ? "bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700"
                  : "bg-gray-50 dark:bg-gray-700/50 border border-transparent"
              } ${isReady ? "hover:bg-blue-50 dark:hover:bg-blue-900/20" : "opacity-60"}`}
              onClick={() => isReady && onToggleFile(file.filename)}
            >
              {isReady && (
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => onToggleFile(file.filename)}
                  onClick={(e) => e.stopPropagation()}
                  className="h-3.5 w-3.5 rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
                  aria-label={`Select ${file.filename} as source`}
                />
              )}
              <span>{getFileIcon(file.file_type)}</span>
              <span className="flex-1 truncate text-gray-900 dark:text-gray-100">
                {file.filename}
              </span>
              {!isReady && getStatusIcon(file.status)}
              {file.num_chunks > 0 && (
                <span className="text-xs text-gray-400 dark:text-gray-500">
                  {file.num_chunks}
                </span>
              )}
              {file.error_message && (
                <span
                  className="text-xs text-red-500 dark:text-red-400 truncate max-w-[80px]"
                  title={file.error_message}
                >
                  {file.error_message}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
