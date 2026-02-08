"use client";

import { useState, useRef, useEffect } from "react";
import { useLibrary } from "@/hooks/useLibrary";
import { UploadZone } from "@/components/library/UploadZone";
import { UrlIngestForm } from "@/components/library/UrlIngestForm";
import { DocumentCard } from "@/components/library/DocumentCard";
import { SearchResults } from "@/components/library/SearchResults";
import {
  YouTubeForm,
  WikipediaForm,
  ArxivForm,
  PubMedForm,
  GutenbergForm,
  GitHubForm,
  CrawlForm,
} from "@/components/library/SourceForms";
import {
  Search,
  Upload,
  Globe,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Video,
  GraduationCap,
  Microscope,
  Library,
  Github,
} from "lucide-react";
import { Spinner } from "@/components/ui/Spinner";

type UploadTab =
  | "file"
  | "url"
  | "youtube"
  | "wikipedia"
  | "arxiv"
  | "pubmed"
  | "gutenberg"
  | "github"
  | "crawl";

interface TabDef {
  id: UploadTab;
  label: string;
  icon: React.ReactNode;
}

const TABS: TabDef[] = [
  { id: "file", label: "Upload File", icon: <Upload className="h-4 w-4" /> },
  { id: "url", label: "Ingest URL", icon: <Globe className="h-4 w-4" /> },
  { id: "youtube", label: "YouTube", icon: <Video className="h-4 w-4" /> },
  {
    id: "wikipedia",
    label: "Wikipedia",
    icon: <BookOpen className="h-4 w-4" />,
  },
  {
    id: "arxiv",
    label: "ArXiv",
    icon: <GraduationCap className="h-4 w-4" />,
  },
  {
    id: "pubmed",
    label: "PubMed",
    icon: <Microscope className="h-4 w-4" />,
  },
  {
    id: "gutenberg",
    label: "Gutenberg",
    icon: <Library className="h-4 w-4" />,
  },
  { id: "github", label: "GitHub", icon: <Github className="h-4 w-4" /> },
  { id: "crawl", label: "Web Crawl", icon: <Globe className="h-4 w-4" /> },
];

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
    refresh,
  } = useLibrary();

  const [uploadTab, setUploadTab] = useState<UploadTab>("file");
  const [searchInput, setSearchInput] = useState("");
  const [searchSubject, setSearchSubject] = useState("");
  const [searchLimit, setSearchLimit] = useState(10);

  // Scrollable tab bar refs
  const tabBarRef = useRef<HTMLDivElement>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);

  const updateScrollState = () => {
    const el = tabBarRef.current;
    if (!el) return;
    setCanScrollLeft(el.scrollLeft > 0);
    setCanScrollRight(el.scrollLeft + el.clientWidth < el.scrollWidth - 1);
  };

  useEffect(() => {
    updateScrollState();
    const el = tabBarRef.current;
    if (!el) return;
    el.addEventListener("scroll", updateScrollState);
    const ro = new ResizeObserver(updateScrollState);
    ro.observe(el);
    return () => {
      el.removeEventListener("scroll", updateScrollState);
      ro.disconnect();
    };
  }, []);

  const scrollTabs = (dir: "left" | "right") => {
    const el = tabBarRef.current;
    if (!el) return;
    el.scrollBy({ left: dir === "left" ? -160 : 160, behavior: "smooth" });
  };

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

  const handleSourceSuccess = () => {
    refresh(1);
  };

  const renderTabContent = () => {
    switch (uploadTab) {
      case "file":
        return <UploadZone onUpload={uploadFile} uploading={uploading} />;
      case "url":
        return <UrlIngestForm onIngest={uploadUrl} uploading={uploading} />;
      case "youtube":
        return <YouTubeForm onSuccess={handleSourceSuccess} />;
      case "wikipedia":
        return <WikipediaForm onSuccess={handleSourceSuccess} />;
      case "arxiv":
        return <ArxivForm onSuccess={handleSourceSuccess} />;
      case "pubmed":
        return <PubMedForm onSuccess={handleSourceSuccess} />;
      case "gutenberg":
        return <GutenbergForm onSuccess={handleSourceSuccess} />;
      case "github":
        return <GitHubForm onSuccess={handleSourceSuccess} />;
      case "crawl":
        return <CrawlForm onSuccess={handleSourceSuccess} />;
    }
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
          {/* Scrollable tab bar */}
          <div className="relative border-b border-gray-800">
            {canScrollLeft && (
              <button
                onClick={() => scrollTabs("left")}
                className="absolute left-0 top-0 bottom-0 z-10 px-1.5 bg-gradient-to-r from-gray-950 via-gray-950 to-transparent text-gray-400 hover:text-gray-200 transition-colors"
                aria-label="Scroll tabs left"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
            )}
            <div
              ref={tabBarRef}
              className="flex overflow-x-auto scrollbar-hide"
              style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
            >
              {TABS.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setUploadTab(tab.id)}
                  className={`flex items-center gap-2 px-5 py-3 text-sm font-medium transition-colors whitespace-nowrap shrink-0 ${
                    uploadTab === tab.id
                      ? "text-blue-400 border-b-2 border-blue-500 bg-gray-900/50"
                      : "text-gray-400 hover:text-gray-300"
                  }`}
                >
                  {tab.icon}
                  {tab.label}
                </button>
              ))}
            </div>
            {canScrollRight && (
              <button
                onClick={() => scrollTabs("right")}
                className="absolute right-0 top-0 bottom-0 z-10 px-1.5 bg-gradient-to-l from-gray-950 via-gray-950 to-transparent text-gray-400 hover:text-gray-200 transition-colors"
                aria-label="Scroll tabs right"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            )}
          </div>

          {/* Tab content */}
          <div className="p-5">{renderTabContent()}</div>
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
            {searching ? (
              <Spinner size="sm" />
            ) : (
              <Search className="h-4 w-4" />
            )}
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
