import { apiClient } from "./client";
import type {
  IngestYouTubeRequest,
  IngestWikipediaRequest,
  IngestArxivRequest,
  IngestPubMedRequest,
  IngestGutenbergRequest,
  IngestGitHubRequest,
  IngestCrawlRequest,
  IngestResult,
  IngestMultiResult,
} from "../types/api";

export async function ingestYouTube(
  data: IngestYouTubeRequest
): Promise<IngestResult> {
  return apiClient<IngestResult>("/api/v1/content/ingest/youtube", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function ingestWikipedia(
  data: IngestWikipediaRequest
): Promise<IngestResult> {
  return apiClient<IngestResult>("/api/v1/content/ingest/wikipedia", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function ingestArxiv(
  data: IngestArxivRequest
): Promise<IngestMultiResult> {
  return apiClient<IngestMultiResult>("/api/v1/content/ingest/arxiv", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function ingestPubMed(
  data: IngestPubMedRequest
): Promise<IngestMultiResult> {
  return apiClient<IngestMultiResult>("/api/v1/content/ingest/pubmed", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function ingestGutenberg(
  data: IngestGutenbergRequest
): Promise<IngestMultiResult> {
  return apiClient<IngestMultiResult>("/api/v1/content/ingest/gutenberg", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function ingestGitHub(
  data: IngestGitHubRequest
): Promise<IngestResult> {
  return apiClient<IngestResult>("/api/v1/content/ingest/github", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function ingestCrawl(
  data: IngestCrawlRequest
): Promise<IngestMultiResult> {
  return apiClient<IngestMultiResult>("/api/v1/content/ingest/crawl", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
