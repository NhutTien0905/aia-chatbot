"use client";

import { UploadedFile } from "@/lib/api";

interface DocumentListProps {
  files: UploadedFile[];
}

export default function DocumentList({ files }: DocumentListProps) {
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
      <h3 className="text-sm font-medium text-gray-700">Uploaded Documents</h3>
      <div className="space-y-1">
        {files.map((file, i) => (
          <div
            key={i}
            className="flex items-center gap-2 p-2 bg-gray-50 rounded text-sm"
          >
            <span>{getFileIcon(file.file_type)}</span>
            <span className="flex-1 truncate">{file.filename}</span>
            {getStatusIcon(file.status)}
            {file.num_chunks > 0 && (
              <span className="text-xs text-gray-400">{file.num_chunks} chunks</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
