"use client";

import { useState } from "react";
import { Globe, CheckCircle, AlertTriangle } from "lucide-react";
import { useSSEIngest, type SSEProgress } from "@/hooks/useSSEIngest";

interface UrlIngestFormProps {
  onSuccess?: () => void;
}

function IngestionProgress({ progress }: { progress: SSEProgress }) {
  const isComplete = progress.step === "complete";
  const isError = progress.step === "error";
  if (isComplete || isError) return null;

  const barColor = progress.step === "warning" ? "bg-yellow-500" : "bg-blue-500";
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

interface IngestResult {
  document_id: string;
  status: string;
  chunk_count: number;
}

export function UrlIngestForm({ onSuccess }: UrlIngestFormProps) {
  const [url, setUrl] = useState("");
  const [title, setTitle] = useState("");
  const [subject, setSubject] = useState("");
  const [gradeLevel, setGradeLevel] = useState("");
  const { ingest, progress, loading, result, error, reset } = useSSEIngest<IngestResult>();

  const handleSubmit = async () => {
    if (!url.trim()) return;
    reset();
    const body: Record<string, unknown> = { url: url.trim() };
    if (title.trim()) body.title = title.trim();
    if (subject.trim()) body.subject = subject.trim();
    if (gradeLevel.trim()) body.grade_level = gradeLevel.trim();

    const res = await ingest("/api/v1/content/upload-url", body);
    if (res) {
      setUrl("");
      setTitle("");
      setSubject("");
      setGradeLevel("");
      onSuccess?.();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !loading) handleSubmit();
  };

  return (
    <div className="space-y-4">
      <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4 space-y-3">
        {/* URL input */}
        <div className="relative">
          <Globe className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="https://example.com/article"
            disabled={loading}
            className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500 disabled:opacity-50"
          />
        </div>

        {/* Optional fields */}
        <div className="grid grid-cols-3 gap-3">
          <input
            type="text"
            placeholder="Title (optional)"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            disabled={loading}
            className="px-3 py-1.5 text-sm bg-gray-800 border border-gray-700 rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500 disabled:opacity-50"
          />
          <input
            type="text"
            placeholder="Subject (optional)"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            disabled={loading}
            className="px-3 py-1.5 text-sm bg-gray-800 border border-gray-700 rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500 disabled:opacity-50"
          />
          <input
            type="text"
            placeholder="Grade level (optional)"
            value={gradeLevel}
            onChange={(e) => setGradeLevel(e.target.value)}
            disabled={loading}
            className="px-3 py-1.5 text-sm bg-gray-800 border border-gray-700 rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500 disabled:opacity-50"
          />
        </div>

        <button
          onClick={handleSubmit}
          disabled={loading || !url.trim()}
          className="w-full px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          <Globe className="h-4 w-4" />
          {loading ? "Ingesting..." : "Ingest URL"}
        </button>
      </div>

      {/* Progress bar */}
      {loading && progress && <IngestionProgress progress={progress} />}

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
            Ingested successfully — {result.chunk_count} chunks created
          </span>
        </div>
      )}
    </div>
  );
}
