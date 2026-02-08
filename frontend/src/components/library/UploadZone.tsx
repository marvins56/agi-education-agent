"use client";

import { useCallback, useRef, useState } from "react";
import { Upload, FileText, X, CheckCircle, AlertTriangle } from "lucide-react";
import { uploadFileSSE } from "@/lib/api/library";
import type { SSEProgress } from "@/lib/api/client";

const ACCEPTED_EXTENSIONS = [".pdf", ".docx", ".txt", ".md", ".pptx", ".xlsx", ".xls", ".csv", ".epub", ".html", ".htm"];
const MAX_SIZE_MB = 500;

interface UploadZoneProps {
  onSuccess?: () => void;
}

function UploadProgress({ progress }: { progress: SSEProgress }) {
  const isComplete = progress.step === "complete";
  const isError = progress.step === "error";
  if (isComplete || isError) return null;

  const barColor = progress.step === "uploading" ? "bg-cyan-500" : "bg-blue-500";
  return (
    <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4 space-y-3">
      <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ease-out ${barColor}`}
          style={{ width: `${progress.progress}%` }}
        />
      </div>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-4 w-4 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
          <span className="text-sm text-gray-300">{progress.message}</span>
        </div>
        <span className="text-xs font-mono text-gray-500">{progress.progress}%</span>
      </div>
    </div>
  );
}

export function UploadZone({ onSuccess }: UploadZoneProps) {
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [subject, setSubject] = useState("");
  const [gradeLevel, setGradeLevel] = useState("");
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState<SSEProgress | null>(null);
  const [result, setResult] = useState<{ filename: string; chunk_count: number } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): string | null => {
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      return `File too large. Maximum size is ${MAX_SIZE_MB}MB.`;
    }
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!ACCEPTED_EXTENSIONS.includes(ext)) {
      return `Unsupported file type. Accepted: ${ACCEPTED_EXTENSIONS.join(", ")}`;
    }
    return null;
  };

  const handleFile = (file: File) => {
    const err = validateFile(file);
    if (err) {
      setError(err);
      return;
    }
    setError(null);
    setResult(null);
    setSelectedFile(file);
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const handleSubmit = async () => {
    if (!selectedFile) return;
    setError(null);
    setResult(null);
    setUploading(true);
    setProgress(null);

    const opts: { title?: string; subject?: string; grade_level?: string } = {};
    if (title.trim()) opts.title = title.trim();
    if (subject.trim()) opts.subject = subject.trim();
    if (gradeLevel.trim()) opts.grade_level = gradeLevel.trim();

    try {
      await uploadFileSSE(selectedFile, opts, (event) => {
        setProgress(event);
        if (event.step === "complete" && event.result) {
          setResult({
            filename: (event.result as Record<string, unknown>).filename as string || selectedFile.name,
            chunk_count: (event.result as Record<string, unknown>).chunk_count as number || 0,
          });
        } else if (event.step === "error") {
          setError(event.message);
        }
      });
      setSelectedFile(null);
      setTitle("");
      setSubject("");
      setGradeLevel("");
      if (fileInputRef.current) fileInputRef.current.value = "";
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      setProgress(null);
    }
  };

  const clearFile = () => {
    setSelectedFile(null);
    setError(null);
    setResult(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => !uploading && fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          uploading ? "cursor-not-allowed opacity-60" : "cursor-pointer"
        } ${
          dragOver
            ? "border-blue-500 bg-blue-500/10"
            : "border-gray-700 hover:border-gray-600 bg-gray-900/50"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept={ACCEPTED_EXTENSIONS.join(",")}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
          }}
        />
        <Upload className="mx-auto h-8 w-8 text-gray-500 mb-3" />
        <p className="text-sm text-gray-300 mb-1">
          Drag & drop a file here, or click to browse
        </p>
        <div className="flex items-center justify-center gap-2 mt-2">
          {["PDF", "DOCX", "PPTX", "XLSX", "CSV", "EPUB", "HTML", "TXT", "MD"].map((fmt) => (
            <span
              key={fmt}
              className="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-400 border border-gray-700"
            >
              {fmt}
            </span>
          ))}
          <span className="text-xs text-gray-500">
            max {MAX_SIZE_MB}MB
          </span>
        </div>
      </div>

      {/* Selected file */}
      {selectedFile && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-blue-400" />
              <span className="text-sm text-gray-200 font-medium">
                {selectedFile.name}
              </span>
              <span className="text-xs text-gray-500">
                ({formatSize(selectedFile.size)})
              </span>
            </div>
            {!uploading && (
              <button
                onClick={clearFile}
                className="text-gray-500 hover:text-gray-300"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          {/* Optional fields */}
          <div className="grid grid-cols-3 gap-3 mb-3">
            <input
              type="text"
              placeholder="Title (optional)"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              disabled={uploading}
              className="px-3 py-1.5 text-sm bg-gray-800 border border-gray-700 rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500 disabled:opacity-50"
            />
            <input
              type="text"
              placeholder="Subject (optional)"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              disabled={uploading}
              className="px-3 py-1.5 text-sm bg-gray-800 border border-gray-700 rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500 disabled:opacity-50"
            />
            <input
              type="text"
              placeholder="Grade level (optional)"
              value={gradeLevel}
              onChange={(e) => setGradeLevel(e.target.value)}
              disabled={uploading}
              className="px-3 py-1.5 text-sm bg-gray-800 border border-gray-700 rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500 disabled:opacity-50"
            />
          </div>

          <button
            onClick={handleSubmit}
            disabled={uploading}
            className="w-full px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            <Upload className="h-4 w-4" />
            {uploading ? "Uploading..." : "Upload & Process"}
          </button>
        </div>
      )}

      {/* Progress bar */}
      {uploading && progress && <UploadProgress progress={progress} />}

      {/* Error */}
      {error && (
        <div className="p-3 rounded-lg bg-red-900/30 border border-red-700 text-red-300 text-sm flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Success */}
      {result && (
        <div className="p-3 rounded-lg bg-green-900/30 border border-green-700 text-green-300 text-sm flex items-center gap-2">
          <CheckCircle className="h-4 w-4 shrink-0" />
          <span>
            Uploaded &ldquo;{result.filename}&rdquo; — {result.chunk_count} chunks created
          </span>
        </div>
      )}
    </div>
  );
}
