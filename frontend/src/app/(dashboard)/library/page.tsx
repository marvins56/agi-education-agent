"use client";

import { useState } from "react";
import { useLibrary } from "@/hooks/useLibrary";

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    completed: "bg-green-600/20 text-green-400 border-green-600/30",
    processing: "bg-yellow-600/20 text-yellow-400 border-yellow-600/30",
    failed: "bg-red-600/20 text-red-400 border-red-600/30",
  };
  const cls =
    colors[status.toLowerCase()] ||
    "bg-gray-600/20 text-gray-400 border-gray-600/30";
  return (
    <span className={`text-xs px-2 py-0.5 rounded border ${cls}`}>
      {status}
    </span>
  );
}

function FileTypeBadge({ fileType }: { fileType: string }) {
  const colors: Record<string, string> = {
    pdf: "bg-red-600/20 text-red-400 border-red-600/30",
    docx: "bg-blue-600/20 text-blue-400 border-blue-600/30",
    txt: "bg-gray-600/20 text-gray-300 border-gray-600/30",
    web: "bg-purple-600/20 text-purple-400 border-purple-600/30",
  };
  const cls =
    colors[fileType.toLowerCase()] ||
    "bg-gray-600/20 text-gray-400 border-gray-600/30";
  return (
    <span className={`text-xs px-2 py-0.5 rounded border ${cls} uppercase`}>
      {fileType}
    </span>
  );
}

export default function LibraryPage() {
  const {
    documents,
    total,
    page,
    totalPages,
    loading,
    error,
    searchResults,
    searchQuery,
    searching,
    search,
    clearSearch,
    goToPage,
  } = useLibrary();

  const [inputValue, setInputValue] = useState("");

  const handleSearch = () => {
    search(inputValue);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleSearch();
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 max-w-4xl mx-auto w-full">
      <h1 className="text-2xl font-bold text-gray-100 mb-6">Library</h1>

      {error && (
        <div className="mb-4 p-3 rounded bg-red-900/30 border border-red-700 text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Search Bar */}
      <div className="mb-6 flex gap-2">
        <div className="relative flex-1">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search content..."
            className="w-full pl-10 pr-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />
        </div>
        <button
          onClick={handleSearch}
          disabled={searching}
          className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-500 disabled:opacity-50 transition-colors"
        >
          {searching ? "Searching..." : "Search"}
        </button>
      </div>

      {/* Search Results */}
      {searchQuery && (
        <section className="mb-8">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold text-gray-200">
              Search Results for &quot;{searchQuery}&quot;
            </h2>
            <button
              onClick={() => {
                clearSearch();
                setInputValue("");
              }}
              className="text-sm text-gray-400 hover:text-gray-200"
            >
              Clear
            </button>
          </div>
          {searching ? (
            <div className="flex items-center gap-2 text-gray-400 text-sm p-4">
              <svg
                className="animate-spin h-4 w-4"
                viewBox="0 0 24 24"
                fill="none"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
              Searching...
            </div>
          ) : searchResults.length === 0 ? (
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 text-center text-gray-500">
              No results found.
            </div>
          ) : (
            <div className="space-y-3">
              {searchResults.map((result, i) => (
                <div
                  key={i}
                  className="bg-gray-900 border border-gray-800 rounded-lg p-4"
                >
                  <p className="text-sm text-gray-300 mb-2">
                    {result.content_preview}
                  </p>
                  <div className="flex items-center gap-3 text-xs text-gray-500">
                    <span>
                      Relevance: {((1 - result.distance) * 100).toFixed(0)}%
                    </span>
                    {Object.entries(result.metadata)
                      .slice(0, 3)
                      .map(([key, val]) => (
                        <span
                          key={key}
                          className="bg-gray-800 px-2 py-0.5 rounded"
                        >
                          {key}: {String(val)}
                        </span>
                      ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {/* Documents Section */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-200">
            Documents{" "}
            <span className="text-sm font-normal text-gray-500">
              ({total})
            </span>
          </h2>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="flex items-center gap-3 text-gray-400">
              <svg
                className="animate-spin h-5 w-5"
                viewBox="0 0 24 24"
                fill="none"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
              Loading documents...
            </div>
          </div>
        ) : documents.length === 0 ? (
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-8 text-center text-gray-500">
            No documents uploaded yet.
          </div>
        ) : (
          <>
            <div className="grid gap-3 sm:grid-cols-2">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className="bg-gray-900 border border-gray-800 rounded-lg p-4"
                >
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-sm font-medium text-gray-200 truncate mr-2">
                      {doc.title}
                    </h3>
                    <div className="flex gap-1.5 shrink-0">
                      <FileTypeBadge fileType={doc.file_type} />
                      <StatusBadge status={doc.status} />
                    </div>
                  </div>
                  {doc.subject && (
                    <p className="text-xs text-gray-500 mb-1">{doc.subject}</p>
                  )}
                  <div className="flex items-center justify-between text-xs text-gray-500 mt-2">
                    <span>{doc.chunk_count} chunks</span>
                    {doc.created_at && (
                      <span>
                        {new Date(doc.created_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-3 mt-6">
                <button
                  onClick={() => goToPage(page - 1)}
                  disabled={page <= 1}
                  className="px-3 py-1.5 text-sm bg-gray-800 text-gray-300 rounded hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Previous
                </button>
                <span className="text-sm text-gray-500">
                  Page {page} of {totalPages}
                </span>
                <button
                  onClick={() => goToPage(page + 1)}
                  disabled={page >= totalPages}
                  className="px-3 py-1.5 text-sm bg-gray-800 text-gray-300 rounded hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </section>
    </div>
  );
}
