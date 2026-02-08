"use client";

import { useState } from "react";
import {
  Video,
  BookOpen,
  GraduationCap,
  Microscope,
  Library,
  Github,
  Globe,
  CheckCircle,
} from "lucide-react";
import { Spinner } from "@/components/ui/Spinner";
import * as sourcesApi from "@/lib/api/sources";
import type {
  IngestResult,
  IngestMultiResult,
} from "@/lib/types/api";

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------

const inputClass =
  "w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500";

const optionalInputClass =
  "px-3 py-1.5 text-sm bg-gray-800 border border-gray-700 rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500";

const selectClass =
  "px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-blue-500";

const submitBtnClass =
  "w-full px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2";

function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="p-3 rounded-lg bg-red-900/30 border border-red-700 text-red-300 text-sm">
      {message}
    </div>
  );
}

function SingleSuccess({ result }: { result: IngestResult }) {
  return (
    <div className="p-3 rounded-lg bg-green-900/30 border border-green-700 text-green-300 text-sm flex items-center gap-2">
      <CheckCircle className="h-4 w-4 shrink-0" />
      <span>
        Ingested &ldquo;{result.title}&rdquo; — {result.chunk_count} chunks
        created
      </span>
    </div>
  );
}

function MultiSuccess({ result }: { result: IngestMultiResult }) {
  const totalChunks = result.documents.reduce(
    (sum, d) => sum + d.chunk_count,
    0
  );
  return (
    <div className="p-3 rounded-lg bg-green-900/30 border border-green-700 text-green-300 text-sm flex items-center gap-2">
      <CheckCircle className="h-4 w-4 shrink-0" />
      <span>
        Ingested {result.documents.length} document
        {result.documents.length !== 1 ? "s" : ""} ({totalChunks} total chunks)
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 1. YouTubeForm
// ---------------------------------------------------------------------------

interface SourceFormProps {
  onSuccess?: () => void;
}

export function YouTubeForm({ onSuccess }: SourceFormProps) {
  const [videoInput, setVideoInput] = useState("");
  const [subject, setSubject] = useState("");
  const [gradeLevel, setGradeLevel] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<IngestResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  function extractVideoId(input: string): string {
    const trimmed = input.trim();
    // Handle full URLs
    try {
      const url = new URL(trimmed);
      if (url.hostname.includes("youtube.com")) {
        return url.searchParams.get("v") || trimmed;
      }
      if (url.hostname === "youtu.be") {
        return url.pathname.slice(1);
      }
    } catch {
      // not a URL, treat as raw ID
    }
    return trimmed;
  }

  const handleSubmit = async () => {
    const videoId = extractVideoId(videoInput);
    if (!videoId) return;
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const data: Parameters<typeof sourcesApi.ingestYouTube>[0] = {
        video_id: videoId,
      };
      if (subject.trim()) data.subject = subject.trim();
      if (gradeLevel.trim()) data.grade_level = gradeLevel.trim();
      const res = await sourcesApi.ingestYouTube(data);
      setResult(res);
      setVideoInput("");
      setSubject("");
      setGradeLevel("");
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "YouTube ingestion failed");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !loading) handleSubmit();
  };

  return (
    <div className="space-y-4">
      <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4 space-y-3">
        <div className="relative">
          <Video className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
          <input
            type="text"
            value={videoInput}
            onChange={(e) => setVideoInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="YouTube URL or video ID (e.g. dQw4w9WgXcQ)"
            className={`${inputClass} pl-10`}
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <input
            type="text"
            placeholder="Subject (optional)"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            className={optionalInputClass}
          />
          <input
            type="text"
            placeholder="Grade level (optional)"
            value={gradeLevel}
            onChange={(e) => setGradeLevel(e.target.value)}
            className={optionalInputClass}
          />
        </div>

        <button
          onClick={handleSubmit}
          disabled={loading || !videoInput.trim()}
          className={submitBtnClass}
        >
          {loading ? (
            <>
              <Spinner size="sm" />
              Ingesting...
            </>
          ) : (
            <>
              <Video className="h-4 w-4" />
              Ingest YouTube Video
            </>
          )}
        </button>
      </div>

      {error && <ErrorBanner message={error} />}
      {result && <SingleSuccess result={result} />}
    </div>
  );
}

// ---------------------------------------------------------------------------
// 2. WikipediaForm
// ---------------------------------------------------------------------------

const LANG_OPTIONS = [
  { value: "en", label: "English" },
  { value: "es", label: "Spanish" },
  { value: "fr", label: "French" },
  { value: "de", label: "German" },
  { value: "pt", label: "Portuguese" },
  { value: "ja", label: "Japanese" },
  { value: "ko", label: "Korean" },
  { value: "zh", label: "Chinese" },
];

export function WikipediaForm({ onSuccess }: SourceFormProps) {
  const [query, setQuery] = useState("");
  const [lang, setLang] = useState("en");
  const [subject, setSubject] = useState("");
  const [gradeLevel, setGradeLevel] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<IngestResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!query.trim()) return;
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const data: Parameters<typeof sourcesApi.ingestWikipedia>[0] = {
        query: query.trim(),
      };
      if (lang !== "en") data.lang = lang;
      if (subject.trim()) data.subject = subject.trim();
      if (gradeLevel.trim()) data.grade_level = gradeLevel.trim();
      const res = await sourcesApi.ingestWikipedia(data);
      setResult(res);
      setQuery("");
      setSubject("");
      setGradeLevel("");
      onSuccess?.();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Wikipedia ingestion failed"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !loading) handleSubmit();
  };

  return (
    <div className="space-y-4">
      <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4 space-y-3">
        <div className="relative">
          <BookOpen className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search Wikipedia (e.g. Quantum mechanics)"
            className={`${inputClass} pl-10`}
          />
        </div>

        <div className="grid grid-cols-3 gap-3">
          <select
            value={lang}
            onChange={(e) => setLang(e.target.value)}
            className={selectClass}
          >
            {LANG_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
          <input
            type="text"
            placeholder="Subject (optional)"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            className={optionalInputClass}
          />
          <input
            type="text"
            placeholder="Grade level (optional)"
            value={gradeLevel}
            onChange={(e) => setGradeLevel(e.target.value)}
            className={optionalInputClass}
          />
        </div>

        <button
          onClick={handleSubmit}
          disabled={loading || !query.trim()}
          className={submitBtnClass}
        >
          {loading ? (
            <>
              <Spinner size="sm" />
              Ingesting...
            </>
          ) : (
            <>
              <BookOpen className="h-4 w-4" />
              Ingest Wikipedia Article
            </>
          )}
        </button>
      </div>

      {error && <ErrorBanner message={error} />}
      {result && <SingleSuccess result={result} />}
    </div>
  );
}

// ---------------------------------------------------------------------------
// 3. ArxivForm
// ---------------------------------------------------------------------------

export function ArxivForm({ onSuccess }: SourceFormProps) {
  const [query, setQuery] = useState("");
  const [maxResults, setMaxResults] = useState(5);
  const [subject, setSubject] = useState("");
  const [gradeLevel, setGradeLevel] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<IngestMultiResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!query.trim()) return;
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const data: Parameters<typeof sourcesApi.ingestArxiv>[0] = {
        query: query.trim(),
        max_results: maxResults,
      };
      if (subject.trim()) data.subject = subject.trim();
      if (gradeLevel.trim()) data.grade_level = gradeLevel.trim();
      const res = await sourcesApi.ingestArxiv(data);
      setResult(res);
      setQuery("");
      setSubject("");
      setGradeLevel("");
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "ArXiv ingestion failed");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !loading) handleSubmit();
  };

  return (
    <div className="space-y-4">
      <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4 space-y-3">
        <div className="relative">
          <GraduationCap className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search ArXiv (e.g. transformer attention mechanisms)"
            className={`${inputClass} pl-10`}
          />
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">
              Max results
            </label>
            <select
              value={maxResults}
              onChange={(e) => setMaxResults(Number(e.target.value))}
              className={`w-full ${selectClass}`}
            >
              {Array.from({ length: 10 }, (_, i) => i + 1).map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </div>
          <input
            type="text"
            placeholder="Subject (optional)"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            className={optionalInputClass}
          />
          <input
            type="text"
            placeholder="Grade level (optional)"
            value={gradeLevel}
            onChange={(e) => setGradeLevel(e.target.value)}
            className={optionalInputClass}
          />
        </div>

        <button
          onClick={handleSubmit}
          disabled={loading || !query.trim()}
          className={submitBtnClass}
        >
          {loading ? (
            <>
              <Spinner size="sm" />
              Ingesting...
            </>
          ) : (
            <>
              <GraduationCap className="h-4 w-4" />
              Ingest ArXiv Papers
            </>
          )}
        </button>
      </div>

      {error && <ErrorBanner message={error} />}
      {result && <MultiSuccess result={result} />}
    </div>
  );
}

// ---------------------------------------------------------------------------
// 4. PubMedForm
// ---------------------------------------------------------------------------

export function PubMedForm({ onSuccess }: SourceFormProps) {
  const [query, setQuery] = useState("");
  const [maxResults, setMaxResults] = useState(5);
  const [subject, setSubject] = useState("");
  const [gradeLevel, setGradeLevel] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<IngestMultiResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!query.trim()) return;
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const data: Parameters<typeof sourcesApi.ingestPubMed>[0] = {
        query: query.trim(),
        max_results: maxResults,
      };
      if (subject.trim()) data.subject = subject.trim();
      if (gradeLevel.trim()) data.grade_level = gradeLevel.trim();
      const res = await sourcesApi.ingestPubMed(data);
      setResult(res);
      setQuery("");
      setSubject("");
      setGradeLevel("");
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "PubMed ingestion failed");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !loading) handleSubmit();
  };

  return (
    <div className="space-y-4">
      <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4 space-y-3">
        <div className="relative">
          <Microscope className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search PubMed (e.g. CRISPR gene editing)"
            className={`${inputClass} pl-10`}
          />
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">
              Max results
            </label>
            <select
              value={maxResults}
              onChange={(e) => setMaxResults(Number(e.target.value))}
              className={`w-full ${selectClass}`}
            >
              {Array.from({ length: 10 }, (_, i) => i + 1).map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </div>
          <input
            type="text"
            placeholder="Subject (optional)"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            className={optionalInputClass}
          />
          <input
            type="text"
            placeholder="Grade level (optional)"
            value={gradeLevel}
            onChange={(e) => setGradeLevel(e.target.value)}
            className={optionalInputClass}
          />
        </div>

        <button
          onClick={handleSubmit}
          disabled={loading || !query.trim()}
          className={submitBtnClass}
        >
          {loading ? (
            <>
              <Spinner size="sm" />
              Ingesting...
            </>
          ) : (
            <>
              <Microscope className="h-4 w-4" />
              Ingest PubMed Articles
            </>
          )}
        </button>
      </div>

      {error && <ErrorBanner message={error} />}
      {result && <MultiSuccess result={result} />}
    </div>
  );
}

// ---------------------------------------------------------------------------
// 5. GutenbergForm
// ---------------------------------------------------------------------------

export function GutenbergForm({ onSuccess }: SourceFormProps) {
  const [query, setQuery] = useState("");
  const [maxResults, setMaxResults] = useState(5);
  const [subject, setSubject] = useState("");
  const [gradeLevel, setGradeLevel] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<IngestMultiResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!query.trim()) return;
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const data: Parameters<typeof sourcesApi.ingestGutenberg>[0] = {
        query: query.trim(),
        max_results: maxResults,
      };
      if (subject.trim()) data.subject = subject.trim();
      if (gradeLevel.trim()) data.grade_level = gradeLevel.trim();
      const res = await sourcesApi.ingestGutenberg(data);
      setResult(res);
      setQuery("");
      setSubject("");
      setGradeLevel("");
      onSuccess?.();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Gutenberg ingestion failed"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !loading) handleSubmit();
  };

  return (
    <div className="space-y-4">
      <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4 space-y-3">
        <div className="relative">
          <Library className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search Project Gutenberg (e.g. Pride and Prejudice)"
            className={`${inputClass} pl-10`}
          />
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">
              Max results
            </label>
            <select
              value={maxResults}
              onChange={(e) => setMaxResults(Number(e.target.value))}
              className={`w-full ${selectClass}`}
            >
              {Array.from({ length: 10 }, (_, i) => i + 1).map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </div>
          <input
            type="text"
            placeholder="Subject (optional)"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            className={optionalInputClass}
          />
          <input
            type="text"
            placeholder="Grade level (optional)"
            value={gradeLevel}
            onChange={(e) => setGradeLevel(e.target.value)}
            className={optionalInputClass}
          />
        </div>

        <button
          onClick={handleSubmit}
          disabled={loading || !query.trim()}
          className={submitBtnClass}
        >
          {loading ? (
            <>
              <Spinner size="sm" />
              Ingesting...
            </>
          ) : (
            <>
              <Library className="h-4 w-4" />
              Ingest Gutenberg Books
            </>
          )}
        </button>
      </div>

      {error && <ErrorBanner message={error} />}
      {result && <MultiSuccess result={result} />}
    </div>
  );
}

// ---------------------------------------------------------------------------
// 6. GitHubForm
// ---------------------------------------------------------------------------

export function GitHubForm({ onSuccess }: SourceFormProps) {
  const [repo, setRepo] = useState("");
  const [filePath, setFilePath] = useState("");
  const [branch, setBranch] = useState("");
  const [subject, setSubject] = useState("");
  const [gradeLevel, setGradeLevel] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<IngestResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!repo.trim()) return;
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const data: Parameters<typeof sourcesApi.ingestGitHub>[0] = {
        repo: repo.trim(),
      };
      if (filePath.trim()) data.file_path = filePath.trim();
      if (branch.trim()) data.branch = branch.trim();
      if (subject.trim()) data.subject = subject.trim();
      if (gradeLevel.trim()) data.grade_level = gradeLevel.trim();
      const res = await sourcesApi.ingestGitHub(data);
      setResult(res);
      setRepo("");
      setFilePath("");
      setBranch("");
      setSubject("");
      setGradeLevel("");
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "GitHub ingestion failed");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !loading) handleSubmit();
  };

  return (
    <div className="space-y-4">
      <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4 space-y-3">
        <div className="relative">
          <Github className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
          <input
            type="text"
            value={repo}
            onChange={(e) => setRepo(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Repository (e.g. owner/repo)"
            className={`${inputClass} pl-10`}
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <input
            type="text"
            placeholder="File path (optional, e.g. src/main.py)"
            value={filePath}
            onChange={(e) => setFilePath(e.target.value)}
            className={optionalInputClass}
          />
          <input
            type="text"
            placeholder="Branch (optional, default: main)"
            value={branch}
            onChange={(e) => setBranch(e.target.value)}
            className={optionalInputClass}
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <input
            type="text"
            placeholder="Subject (optional)"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            className={optionalInputClass}
          />
          <input
            type="text"
            placeholder="Grade level (optional)"
            value={gradeLevel}
            onChange={(e) => setGradeLevel(e.target.value)}
            className={optionalInputClass}
          />
        </div>

        <button
          onClick={handleSubmit}
          disabled={loading || !repo.trim()}
          className={submitBtnClass}
        >
          {loading ? (
            <>
              <Spinner size="sm" />
              Ingesting...
            </>
          ) : (
            <>
              <Github className="h-4 w-4" />
              Ingest GitHub Repository
            </>
          )}
        </button>
      </div>

      {error && <ErrorBanner message={error} />}
      {result && <SingleSuccess result={result} />}
    </div>
  );
}

// ---------------------------------------------------------------------------
// 7. CrawlForm
// ---------------------------------------------------------------------------

export function CrawlForm({ onSuccess }: SourceFormProps) {
  const [url, setUrl] = useState("");
  const [maxDepth, setMaxDepth] = useState(2);
  const [maxPages, setMaxPages] = useState(10);
  const [subject, setSubject] = useState("");
  const [gradeLevel, setGradeLevel] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<IngestMultiResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!url.trim()) return;
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const data: Parameters<typeof sourcesApi.ingestCrawl>[0] = {
        url: url.trim(),
        max_depth: maxDepth,
        max_pages: maxPages,
      };
      if (subject.trim()) data.subject = subject.trim();
      if (gradeLevel.trim()) data.grade_level = gradeLevel.trim();
      const res = await sourcesApi.ingestCrawl(data);
      setResult(res);
      setUrl("");
      setSubject("");
      setGradeLevel("");
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Web crawl failed");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !loading) handleSubmit();
  };

  return (
    <div className="space-y-4">
      <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4 space-y-3">
        <div className="relative">
          <Globe className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="https://example.com (starting URL to crawl)"
            className={`${inputClass} pl-10`}
          />
        </div>

        <div className="grid grid-cols-4 gap-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">
              Max depth
            </label>
            <select
              value={maxDepth}
              onChange={(e) => setMaxDepth(Number(e.target.value))}
              className={`w-full ${selectClass}`}
            >
              {[1, 2, 3, 4, 5].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">
              Max pages
            </label>
            <select
              value={maxPages}
              onChange={(e) => setMaxPages(Number(e.target.value))}
              className={`w-full ${selectClass}`}
            >
              {[5, 10, 15, 20, 25, 30, 40, 50].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </div>
          <input
            type="text"
            placeholder="Subject (optional)"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            className={optionalInputClass}
          />
          <input
            type="text"
            placeholder="Grade level (optional)"
            value={gradeLevel}
            onChange={(e) => setGradeLevel(e.target.value)}
            className={optionalInputClass}
          />
        </div>

        <button
          onClick={handleSubmit}
          disabled={loading || !url.trim()}
          className={submitBtnClass}
        >
          {loading ? (
            <>
              <Spinner size="sm" />
              Crawling...
            </>
          ) : (
            <>
              <Globe className="h-4 w-4" />
              Crawl Website
            </>
          )}
        </button>
      </div>

      {error && <ErrorBanner message={error} />}
      {result && <MultiSuccess result={result} />}
    </div>
  );
}
