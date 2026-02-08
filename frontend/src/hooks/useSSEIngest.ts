"use client";

import { useState, useCallback } from "react";
import { apiClientSSE, type SSEProgress } from "@/lib/api/client";

export type { SSEProgress };

export function useSSEIngest<TResult>() {
  const [progress, setProgress] = useState<SSEProgress | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const ingest = useCallback(
    async (
      path: string,
      body: Record<string, unknown>
    ): Promise<TResult | null> => {
      setLoading(true);
      setProgress(null);
      setResult(null);
      setError(null);

      let finalResult: TResult | null = null;

      try {
        for await (const event of apiClientSSE(`${path}?stream=true`, {
          method: "POST",
          body: JSON.stringify(body),
        })) {
          setProgress(event);
          if (event.step === "complete" && event.result) {
            finalResult = event.result as TResult;
            setResult(finalResult);
          } else if (event.step === "error") {
            setError(event.message);
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Ingestion failed");
      } finally {
        setLoading(false);
        setProgress(null);
      }

      return finalResult;
    },
    []
  );

  const reset = useCallback(() => {
    setProgress(null);
    setResult(null);
    setError(null);
    setLoading(false);
  }, []);

  return { ingest, progress, loading, result, error, reset };
}
