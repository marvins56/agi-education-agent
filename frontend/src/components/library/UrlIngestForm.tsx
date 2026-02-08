"use client";

import { useState } from "react";
import { Globe, CheckCircle } from "lucide-react";
import { Spinner } from "@/components/ui/Spinner";
import type { UploadUrlRequest, UploadUrlResponse } from "@/lib/types/api";

interface UrlIngestFormProps {
  onIngest: (data: UploadUrlRequest) => Promise<UploadUrlResponse>;
  uploading: boolean;
}

export function UrlIngestForm({ onIngest, uploading }: UrlIngestFormProps) {
  const [url, setUrl] = useState("");
  const [title, setTitle] = useState("");
  const [subject, setSubject] = useState("");
  const [gradeLevel, setGradeLevel] = useState("");
  const [result, setResult] = useState<UploadUrlResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!url.trim()) return;
    setError(null);
    setResult(null);
    try {
      const data: UploadUrlRequest = { url: url.trim() };
      if (title.trim()) data.title = title.trim();
      if (subject.trim()) data.subject = subject.trim();
      if (gradeLevel.trim()) data.grade_level = gradeLevel.trim();
      const res = await onIngest(data);
      setResult(res);
      setUrl("");
      setTitle("");
      setSubject("");
      setGradeLevel("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ingestion failed");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !uploading) handleSubmit();
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
            className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Optional fields */}
        <div className="grid grid-cols-3 gap-3">
          <input
            type="text"
            placeholder="Title (optional)"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="px-3 py-1.5 text-sm bg-gray-800 border border-gray-700 rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />
          <input
            type="text"
            placeholder="Subject (optional)"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            className="px-3 py-1.5 text-sm bg-gray-800 border border-gray-700 rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />
          <input
            type="text"
            placeholder="Grade level (optional)"
            value={gradeLevel}
            onChange={(e) => setGradeLevel(e.target.value)}
            className="px-3 py-1.5 text-sm bg-gray-800 border border-gray-700 rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        <button
          onClick={handleSubmit}
          disabled={uploading || !url.trim()}
          className="w-full px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          {uploading ? (
            <>
              <Spinner size="sm" />
              Ingesting...
            </>
          ) : (
            <>
              <Globe className="h-4 w-4" />
              Ingest URL
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-900/30 border border-red-700 text-red-300 text-sm">
          {error}
        </div>
      )}

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
