"use client";

import { useState } from "react";
import { useLibrary } from "@/hooks/useLibrary";
import { UploadZone } from "@/components/library/UploadZone";
import { UrlIngestForm } from "@/components/library/UrlIngestForm";
import { DocumentCard } from "@/components/library/DocumentCard";
import { SearchResults } from "@/components/library/SearchResults";
import {
  Search,
  Upload,
  Globe,
  BookOpen,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { Spinner } from "@/components/ui/Spinner";

type UploadTab = "file" | "url";

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
    deleteDocument,
    uploadFile,
    uploadUrl,
    uploading,
  } = useLibrary();

  const [uploadTab, setUploadTab] = useState<UploadTab>("file");
  const [searchInput, setSearchInput] = useState("");
  const [searchSubject, setSearchSubject] = useState("");
  const [searchLimit, setSearchLimit] = useState(10);

  const handleSearch = () => {
    search(searchInput, searchSubject || undefined, searchLimit);
  };

  const handleSearchKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleSearch();
  };

  const handleClearSearch = () => {
    clearSearch();
    setSearchInput("");
    setSearchSubject("");
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 max-w-5xl mx-auto w-full">
      <div className="flex items-center gap-3 mb-8">
        <BookOpen className="h-7 w-7 text-blue-500" />
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Library</h1>
          <p className="text-sm text-gray-500">
            Upload documents, ingest web content, and search your knowledge base
          </p>
        </div>
      </div>

      {/* Global error */}
      {error && (
        <div className="mb-6 p-3 rounded-lg bg-red-900/30 border border-red-700 text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* ========== UPLOAD SECTION ========== */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-gray-200 mb-3">
          Add Content
        </h2>
        <div className="bg-gray-950 border border-gray-800 rounded-xl overflow-hidden">
          {/* Tabs */}
          <div className="flex border-b border-gray-800">
            <button
              onClick={() => setUploadTab("file")}
              className={`flex items-center gap-2 px-5 py-3 text-sm font-medium transition-colors ${
                uploadTab === "file"
                  ? "text-blue-400 border-b-2 border-blue-500 bg-gray-900/50"
                  : "text-gray-400 hover:text-gray-300"
              }`}
            >
              <Upload className="h-4 w-4" />
              Upload File
            </button>
            <button
              onClick={() => setUploadTab("url")}
              className={`flex items-center gap-2 px-5 py-3 text-sm font-medium transition-colors ${
                uploadTab === "url"
                  ? "text-blue-400 border-b-2 border-blue-500 bg-gray-900/50"
                  : "text-gray-400 hover:text-gray-300"
              }`}
            >
              <Globe className="h-4 w-4" />
              Ingest URL
            </button>
          </div>

          {/* Tab content */}
          <div className="p-5">
            {uploadTab === "file" ? (
              <UploadZone onUpload={uploadFile} uploading={uploading} />
            ) : (
              <UrlIngestForm onIngest={uploadUrl} uploading={uploading} />
            )}
          </div>
        </div>
      </section>

      {/* ========== SEARCH SECTION ========== */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-gray-200 mb-3">
          Knowledge Base Search
        </h2>
        <div className="flex gap-2 mb-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onKeyDown={handleSearchKeyDown}
              placeholder="Search your knowledge base..."
              className="w-full pl-10 pr-4 py-2.5 bg-gray-900 border border-gray-700 rounded-lg text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />
          </div>
          <input
            type="text"
            value={searchSubject}
            onChange={(e) => setSearchSubject(e.target.value)}
            placeholder="Subject filter"
            className="w-36 px-3 py-2.5 bg-gray-900 border border-gray-700 rounded-lg text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />
          <select
            value={searchLimit}
            onChange={(e) => setSearchLimit(Number(e.target.value))}
            className="w-20 px-2 py-2.5 bg-gray-900 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-blue-500"
          >
            <option value={5}>5</option>
            <option value={10}>10</option>
            <option value={20}>20</option>
          </select>
          <button
            onClick={handleSearch}
            disabled={searching || !searchInput.trim()}
            className="px-5 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {searching ? <Spinner size="sm" /> : <Search className="h-4 w-4" />}
            Search
          </button>
        </div>

        <SearchResults
          query={searchQuery}
          results={searchResults}
          searching={searching}
          onClear={handleClearSearch}
        />
      </section>

      {/* ========== DOCUMENTS GRID ========== */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-200">
            Documents{" "}
            <span className="text-sm font-normal text-gray-500">
              ({total})
            </span>
          </h2>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-16">
            <div className="flex items-center gap-3 text-gray-400">
              <Spinner size="md" />
              <span>Loading documents...</span>
            </div>
          </div>
        ) : documents.length === 0 ? (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center">
            <BookOpen className="h-12 w-12 text-gray-700 mx-auto mb-3" />
            <p className="text-gray-400 mb-1">No documents yet</p>
            <p className="text-sm text-gray-600">
              Upload a file or ingest a URL to get started
            </p>
          </div>
        ) : (
          <>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {documents.map((doc) => (
                <DocumentCard
                  key={doc.id}
                  document={doc}
                  onDelete={deleteDocument}
                />
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-3 mt-6">
                <button
                  onClick={() => goToPage(page - 1)}
                  disabled={page <= 1}
                  className="p-2 bg-gray-800 text-gray-300 rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <span className="text-sm text-gray-500">
                  Page {page} of {totalPages}
                </span>
                <button
                  onClick={() => goToPage(page + 1)}
                  disabled={page >= totalPages}
                  className="p-2 bg-gray-800 text-gray-300 rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            )}
          </>
        )}
      </section>
    </div>
  );
}
