"use client";

import { useCallback, useEffect, useState } from "react";
import * as libraryApi from "@/lib/api/library";
import type {
  DocumentItem,
  SearchResultItem,
} from "@/lib/types/api";

export function useLibrary() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Search state
  const [searchResults, setSearchResults] = useState<SearchResultItem[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searching, setSearching] = useState(false);

  const fetchDocuments = useCallback(
    async (p = page) => {
      setLoading(true);
      setError(null);
      try {
        const res = await libraryApi.listDocuments(p, pageSize);
        setDocuments(res.items);
        setTotal(res.total);
        setPage(res.page);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load documents"
        );
      } finally {
        setLoading(false);
      }
    },
    [page, pageSize]
  );

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const search = useCallback(async (query: string) => {
    if (!query.trim()) {
      setSearchResults([]);
      setSearchQuery("");
      return;
    }
    setSearching(true);
    setError(null);
    setSearchQuery(query);
    try {
      const res = await libraryApi.searchContent(query);
      setSearchResults(res.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setSearching(false);
    }
  }, []);

  const clearSearch = useCallback(() => {
    setSearchResults([]);
    setSearchQuery("");
  }, []);

  const goToPage = useCallback(
    (p: number) => {
      fetchDocuments(p);
    },
    [fetchDocuments]
  );

  const deleteDocument = useCallback(
    async (id: string) => {
      try {
        await libraryApi.deleteDocument(id);
        await fetchDocuments();
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to delete document"
        );
      }
    },
    [fetchDocuments]
  );

  const totalPages = Math.ceil(total / pageSize);

  return {
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
    refresh: fetchDocuments,
  };
}
