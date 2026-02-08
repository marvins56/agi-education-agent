"use client";

import { X, Search } from "lucide-react";
import { Spinner } from "@/components/ui/Spinner";
import type { SearchResultItem } from "@/lib/types/api";

interface SearchResultsProps {
  query: string;
  results: SearchResultItem[];
  searching: boolean;
  onClear: () => void;
}

export function SearchResults({
  query,
  results,
  searching,
  onClear,
}: SearchResultsProps) {
  if (!query) return null;

  return (
    <section className="mb-8">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-semibold text-gray-200">
          Results for &quot;{query}&quot;
        </h2>
        <button
          onClick={onClear}
          className="text-sm text-gray-400 hover:text-gray-200 flex items-center gap-1"
        >
          <X className="h-3.5 w-3.5" />
          Clear
        </button>
      </div>

      {searching ? (
        <div className="flex items-center gap-3 text-gray-400 text-sm p-6 justify-center">
          <Spinner size="sm" />
          Searching knowledge base...
        </div>
      ) : results.length === 0 ? (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-8 text-center">
          <Search className="h-8 w-8 text-gray-600 mx-auto mb-2" />
          <p className="text-gray-500 text-sm">No results found.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {results.map((result, i) => {
            const relevance = Math.max(0, Math.min(100, (1 - result.distance) * 100));
            return (
              <div
                key={i}
                className="bg-gray-900 border border-gray-800 rounded-lg p-4 hover:border-gray-700 transition-colors"
              >
                <p className="text-sm text-gray-300 mb-3 leading-relaxed">
                  {result.content_preview}
                </p>

                {/* Relevance bar */}
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-xs text-gray-500 w-20 shrink-0">
                    Relevance
                  </span>
                  <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full bg-blue-500 transition-all"
                      style={{ width: `${relevance}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-400 w-10 text-right">
                    {relevance.toFixed(0)}%
                  </span>
                </div>

                {/* Metadata tags */}
                <div className="flex flex-wrap gap-2 mt-2">
                  {Object.entries(result.metadata)
                    .filter(([, val]) => val != null && val !== "")
                    .slice(0, 5)
                    .map(([key, val]) => (
                      <span
                        key={key}
                        className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded border border-gray-700"
                      >
                        {key}: {String(val)}
                      </span>
                    ))}
                </div>

                {/* Citation */}
                {result.citation &&
                  Object.keys(result.citation).length > 0 && (
                    <div className="mt-2 text-xs text-gray-500">
                      {Object.entries(result.citation)
                        .filter(([, val]) => val != null && val !== "")
                        .map(([key, val]) => (
                          <span key={key} className="mr-3">
                            {key}: {String(val)}
                          </span>
                        ))}
                    </div>
                  )}
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
