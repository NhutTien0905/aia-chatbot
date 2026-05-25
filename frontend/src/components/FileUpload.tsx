"use client";

import { useCallback, useState } from "react";
import { uploadFiles, UploadedFile } from "@/lib/api";

interface FileUploadProps {
  sessionId: string;
  onUploadComplete: (files: UploadedFile[]) => void;
}

export default function FileUpload({ sessionId, onUploadComplete }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const ALLOWED_TYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/png",
    "image/jpeg",
    "image/jpg",
  ];
  const MAX_SIZE = 5 * 1024 * 1024; // 5MB
  const MAX_FILES = 2;

  const validateFiles = (files: File[]): string | null => {
    if (files.length > MAX_FILES) {
      return `Maximum ${MAX_FILES} files allowed`;
    }
    for (const file of files) {
      if (!ALLOWED_TYPES.includes(file.type)) {
        return `Unsupported file type: ${file.name}. Allowed: PDF, DOCX, PNG, JPG`;
      }
      if (file.size > MAX_SIZE) {
        return `File too large: ${file.name}. Maximum 5MB`;
      }
    }
    return null;
  };

  const handleUpload = useCallback(
    async (files: File[]) => {
      const validationError = validateFiles(files);
      if (validationError) {
        setError(validationError);
        return;
      }

      setError(null);
      setIsUploading(true);

      try {
        const response = await uploadFiles(files, sessionId);
        onUploadComplete(response.files);
        if (!response.success) {
          setError(response.message);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Upload failed");
      } finally {
        setIsUploading(false);
      }
    },
    [sessionId, onUploadComplete]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const files = Array.from(e.dataTransfer.files);
      handleUpload(files);
    },
    [handleUpload]
  );

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) handleUpload(files);
    e.target.value = "";
  };

  return (
    <div className="w-full">
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors cursor-pointer
          ${isDragging ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-gray-400"}
          ${isUploading ? "opacity-50 pointer-events-none" : ""}`}
        onClick={() => document.getElementById("file-input")?.click()}
      >
        {isUploading ? (
          <div className="flex flex-col items-center gap-2">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
            <p className="text-sm text-gray-600">Processing documents...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p className="text-sm text-gray-600">
              <span className="font-medium text-blue-600">Click to upload</span> or drag and drop
            </p>
            <p className="text-xs text-gray-500">PDF, DOCX, PNG, JPG (max 5MB, max 2 files)</p>
          </div>
        )}
      </div>
      <input
        id="file-input"
        type="file"
        multiple
        accept=".pdf,.docx,.png,.jpg,.jpeg"
        onChange={handleFileInput}
        className="hidden"
      />
      {error && (
        <p className="mt-2 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
}
