"use client";

import { useCallback, useEffect, useState } from "react";
import * as libraryApi from "@/lib/api/library";
import type {
  DocumentItem,
  SearchResultItem,
  UploadFileResponse,
  UploadUrlRequest,
  UploadUrlResponse,
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

  // Upload state
  const [uploading, setUploading] = useState(false);

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

  const search = useCallback(
    async (query: string, subject?: string, limit?: number) => {
      if (!query.trim()) {
        setSearchResults([]);
        setSearchQuery("");
        return;
      }
      setSearching(true);
      setError(null);
      setSearchQuery(query);
      try {
        const res = await libraryApi.searchContent(query, subject, limit);
        setSearchResults(res.results);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Search failed");
      } finally {
        setSearching(false);
      }
    },
    []
  );

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

  const uploadFile = useCallback(
    async (
      file: File,
      options?: { title?: string; subject?: string; grade_level?: string }
    ): Promise<UploadFileResponse> => {
      setUploading(true);
      setError(null);
      try {
        const res = await libraryApi.uploadFile(file, options);
        await fetchDocuments(1);
        return res;
      } catch (err) {
        const msg =
          err instanceof Error ? err.message : "Upload failed";
        setError(msg);
        throw err;
      } finally {
        setUploading(false);
      }
    },
    [fetchDocuments]
  );

  const uploadUrl = useCallback(
    async (data: UploadUrlRequest): Promise<UploadUrlResponse> => {
      setUploading(true);
      setError(null);
      try {
        const res = await libraryApi.uploadUrl(data);
        await fetchDocuments(1);
        return res;
      } catch (err) {
        const msg =
          err instanceof Error ? err.message : "URL ingestion failed";
        setError(msg);
        throw err;
      } finally {
        setUploading(false);
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
    uploadFile,
    uploadUrl,
    uploading,
  };
}
