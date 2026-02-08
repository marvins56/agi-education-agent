"use client";

import { useCallback, useEffect, useState } from "react";
import * as learningPathApi from "@/lib/api/learningPath";
import type { RecommendedTopic, ReviewDue } from "@/lib/types/api";

export function useLearningPath() {
  const [recommended, setRecommended] = useState<RecommendedTopic[]>([]);
  const [reviewsDue, setReviewsDue] = useState<ReviewDue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [recs, reviews] = await Promise.all([
        learningPathApi.getRecommended(),
        learningPathApi.getReviewsDue(),
      ]);
      setRecommended(recs);
      setReviewsDue(reviews);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load learning path"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const completeReview = useCallback(
    async (topicId: string, quality: number) => {
      try {
        await learningPathApi.completeReview(topicId, quality);
        await fetchData();
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to complete review"
        );
      }
    },
    [fetchData]
  );

  return { recommended, reviewsDue, loading, error, completeReview, refresh: fetchData };
}
