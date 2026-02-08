"use client";

import { useState } from "react";
import { FlaskConical, Search, Clock, Database, Zap, FileText } from "lucide-react";
import { apiClient } from "@/lib/api/client";

interface ChunkResult {
  rank: number;
  chunk_id: string;
  content: string;
  distance: number;
  relevance: number;
  metadata: {
    source_type: string;
    subject: string;
    title: string;
    document_id: string;
  };
  char_count: number;
}

interface RAGResponse {
  query: string;
  rewritten_query: string;
  subject_filter: string | null;
  chunks: ChunkResult[];
  timing: {
    rewrite_ms: number;
    search_ms: number;
    rank_ms: number;
    total_ms: number;
  };
  stats: {
    total_chunks_in_db: number;
    results_found: number;
    limit: number;
  };
  error?: string;
}

const SOURCE_COLORS: Record<string, string> = {
  youtube: "bg-red-900/40 text-red-300 border-red-700",
  wikipedia: "bg-blue-900/40 text-blue-300 border-blue-700",
  arxiv: "bg-orange-900/40 text-orange-300 border-orange-700",
  pubmed: "bg-green-900/40 text-green-300 border-green-700",
  gutenberg: "bg-purple-900/40 text-purple-300 border-purple-700",
  github: "bg-gray-700/40 text-gray-300 border-gray-600",
  web_crawl: "bg-cyan-900/40 text-cyan-300 border-cyan-700",
  url: "bg-cyan-900/40 text-cyan-300 border-cyan-700",
};

function getSourceColor(sourceType: string): string {
  return SOURCE_COLORS[sourceType] || "bg-gray-800/40 text-gray-300 border-gray-600";
}

function RelevanceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color =
    pct >= 70 ? "bg-green-500" : pct >= 50 ? "bg-yellow-500" : pct >= 30 ? "bg-orange-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="w-24 h-2 bg-gray-800 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono text-gray-400">{pct}%</span>
    </div>
  );
}

export default function RAGTestPage() {
  const [query, setQuery] = useState("");
  const [subject, setSubject] = useState("");
  const [limit, setLimit] = useState(10);
  const [result, setResult] = useState<RAGResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [expandedChunks, setExpandedChunks] = useState<Set<number>>(new Set());

  const runQuery = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setResult(null);
    setExpandedChunks(new Set());
    try {
      const params = new URLSearchParams({ q: query, limit: String(limit) });
      if (subject.trim()) params.set("subject", subject.trim());
      const data = await apiClient<RAGResponse>(`/api/v1/content/rag-test?${params}`);
      setResult(data);
    } catch (err) {
      setResult({
        query,
        rewritten_query: "",
        subject_filter: null,
        chunks: [],
        timing: { rewrite_ms: 0, search_ms: 0, rank_ms: 0, total_ms: 0 },
        stats: { total_chunks_in_db: 0, results_found: 0, limit },
        error: err instanceof Error ? err.message : "Search failed",
      });
    } finally {
      setLoading(false);
    }
  };

  const toggleChunk = (rank: number) => {
    setExpandedChunks((prev) => {
      const next = new Set(prev);
      if (next.has(rank)) next.delete(rank);
      else next.add(rank);
      return next;
    });
  };

  const expandAll = () => {
    if (!result) return;
    setExpandedChunks(new Set(result.chunks.map((c) => c.rank)));
  };

  const collapseAll = () => setExpandedChunks(new Set());

  return (
    <div className="flex-1 overflow-y-auto p-6 max-w-5xl mx-auto w-full">
      {/* Header */}
      <div className="flex items-center gap-3 mb-8">
        <FlaskConical className="h-7 w-7 text-purple-500" />
        <div>
          <h1 className="text-2xl font-bold text-gray-100">RAG Test Lab</h1>
          <p className="text-sm text-gray-500">
            Test retrieval-augmented generation — see raw chunks before they reach the LLM
          </p>
        </div>
      </div>

      {/* Query Form */}
      <section className="mb-6">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div className="flex gap-3 mb-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && runQuery()}
                placeholder="Ask a question... (e.g. 'How does photosynthesis work?')"
                className="w-full pl-10 pr-4 py-3 bg-gray-950 border border-gray-700 rounded-lg text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-purple-500"
              />
            </div>
            <button
              onClick={runQuery}
              disabled={loading || !query.trim()}
              className="px-6 py-3 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {loading ? (
                <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <Zap className="h-4 w-4" />
              )}
              Retrieve
            </button>
          </div>
          <div className="flex gap-3">
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="Subject filter (optional)"
              className="w-48 px-3 py-2 bg-gray-950 border border-gray-700 rounded-lg text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-purple-500"
            />
            <select
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="w-32 px-3 py-2 bg-gray-950 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-purple-500"
            >
              <option value={3}>Top 3</option>
              <option value={5}>Top 5</option>
              <option value={10}>Top 10</option>
              <option value={20}>Top 20</option>
            </select>
          </div>
        </div>
      </section>

      {/* Error */}
      {result?.error && (
        <div className="mb-6 p-3 rounded-lg bg-red-900/30 border border-red-700 text-red-300 text-sm">
          {result.error}
        </div>
      )}

      {/* Results */}
      {result && !result.error && (
        <>
          {/* Timing & Stats Bar */}
          <section className="mb-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                <div className="flex items-center gap-2 text-gray-500 text-xs mb-1">
                  <Clock className="h-3.5 w-3.5" />
                  Total Time
                </div>
                <div className="text-2xl font-bold text-gray-100">
                  {result.timing.total_ms.toFixed(1)}
                  <span className="text-sm font-normal text-gray-500 ml-1">ms</span>
                </div>
              </div>
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                <div className="flex items-center gap-2 text-gray-500 text-xs mb-1">
                  <Database className="h-3.5 w-3.5" />
                  Chunks in DB
                </div>
                <div className="text-2xl font-bold text-gray-100">
                  {result.stats.total_chunks_in_db.toLocaleString()}
                </div>
              </div>
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                <div className="flex items-center gap-2 text-gray-500 text-xs mb-1">
                  <Search className="h-3.5 w-3.5" />
                  Results Found
                </div>
                <div className="text-2xl font-bold text-gray-100">
                  {result.stats.results_found}
                </div>
              </div>
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                <div className="flex items-center gap-2 text-gray-500 text-xs mb-1">
                  <Zap className="h-3.5 w-3.5" />
                  Pipeline Breakdown
                </div>
                <div className="text-xs font-mono text-gray-300 space-y-0.5">
                  <div>Rewrite: {result.timing.rewrite_ms.toFixed(1)}ms</div>
                  <div>Search: {result.timing.search_ms.toFixed(1)}ms</div>
                  <div>Rank: {result.timing.rank_ms.toFixed(1)}ms</div>
                </div>
              </div>
            </div>
          </section>

          {/* Query info */}
          {result.rewritten_query && result.rewritten_query !== result.query && (
            <div className="mb-4 p-3 bg-purple-900/20 border border-purple-800 rounded-lg text-sm">
              <span className="text-purple-400 font-medium">Query rewritten:</span>{" "}
              <span className="text-gray-300">{result.rewritten_query}</span>
            </div>
          )}

          {/* Chunks */}
          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-200">
                Retrieved Chunks{" "}
                <span className="text-sm font-normal text-gray-500">
                  ({result.chunks.length})
                </span>
              </h2>
              {result.chunks.length > 0 && (
                <div className="flex gap-2">
                  <button
                    onClick={expandAll}
                    className="text-xs px-3 py-1.5 bg-gray-800 text-gray-400 rounded-lg hover:bg-gray-700 transition-colors"
                  >
                    Expand All
                  </button>
                  <button
                    onClick={collapseAll}
                    className="text-xs px-3 py-1.5 bg-gray-800 text-gray-400 rounded-lg hover:bg-gray-700 transition-colors"
                  >
                    Collapse All
                  </button>
                </div>
              )}
            </div>

            {result.chunks.length === 0 ? (
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center">
                <Database className="h-12 w-12 text-gray-700 mx-auto mb-3" />
                <p className="text-gray-400 mb-1">No chunks found</p>
                <p className="text-sm text-gray-600">
                  Try a different query or ingest some documents first
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {result.chunks.map((chunk) => {
                  const expanded = expandedChunks.has(chunk.rank);
                  return (
                    <div
                      key={chunk.rank}
                      className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden"
                    >
                      {/* Chunk header */}
                      <button
                        onClick={() => toggleChunk(chunk.rank)}
                        className="w-full flex items-center gap-3 p-4 text-left hover:bg-gray-800/50 transition-colors"
                      >
                        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-purple-900/30 text-purple-400 text-sm font-bold shrink-0">
                          #{chunk.rank}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span
                              className={`text-xs px-2 py-0.5 rounded border ${getSourceColor(
                                chunk.metadata.source_type
                              )}`}
                            >
                              {chunk.metadata.source_type.toUpperCase()}
                            </span>
                            {chunk.metadata.subject && (
                              <span className="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-400 border border-gray-700">
                                {chunk.metadata.subject}
                              </span>
                            )}
                            {chunk.metadata.title && (
                              <span className="text-xs text-gray-500 truncate">
                                {chunk.metadata.title}
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-300 truncate">
                            {chunk.content.slice(0, 120)}...
                          </p>
                        </div>
                        <div className="shrink-0 text-right">
                          <RelevanceBar value={chunk.relevance} />
                          <div className="text-xs text-gray-600 mt-0.5">
                            {chunk.char_count} chars
                          </div>
                        </div>
                      </button>

                      {/* Expanded content */}
                      {expanded && (
                        <div className="border-t border-gray-800 p-4">
                          <div className="flex gap-4 mb-3 text-xs text-gray-500">
                            <span>
                              <FileText className="inline h-3 w-3 mr-1" />
                              {chunk.char_count} chars
                            </span>
                            <span>Distance: {chunk.distance}</span>
                            <span>Relevance: {(chunk.relevance * 100).toFixed(1)}%</span>
                            <span className="text-gray-600 truncate">ID: {chunk.chunk_id}</span>
                          </div>
                          <div className="bg-gray-950 border border-gray-800 rounded-lg p-4 text-sm text-gray-300 leading-relaxed whitespace-pre-wrap font-mono max-h-96 overflow-y-auto">
                            {chunk.content}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </section>

          {/* Raw context preview */}
          {result.chunks.length > 0 && (
            <section className="mt-8 mb-8">
              <h2 className="text-lg font-semibold text-gray-200 mb-3">
                Context Sent to LLM{" "}
                <span className="text-sm font-normal text-gray-500">
                  (all chunks concatenated)
                </span>
              </h2>
              <div className="bg-gray-950 border border-gray-800 rounded-xl p-4 text-sm text-gray-400 leading-relaxed whitespace-pre-wrap font-mono max-h-80 overflow-y-auto">
                {result.chunks
                  .map(
                    (c, i) =>
                      `--- Chunk ${i + 1} [${c.metadata.source_type}/${c.metadata.title || "unknown"}] (relevance: ${(
                        c.relevance * 100
                      ).toFixed(1)}%) ---\n${c.content}`
                  )
                  .join("\n\n")}
              </div>
              <div className="mt-2 text-xs text-gray-600">
                Total context size:{" "}
                {result.chunks.reduce((acc, c) => acc + c.char_count, 0).toLocaleString()} characters
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
