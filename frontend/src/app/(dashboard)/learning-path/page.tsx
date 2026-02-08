"use client";

import { useState } from "react";
import { useLearningPath } from "@/hooks/useLearningPath";
import type { ReviewDue } from "@/lib/types/api";

const QUALITY_LABELS: Record<number, string> = {
  0: "Complete blackout",
  1: "Incorrect; remembered on seeing answer",
  2: "Incorrect; answer seemed easy to recall",
  3: "Correct with serious difficulty",
  4: "Correct after hesitation",
  5: "Perfect response",
};

function DifficultyBadge({ difficulty }: { difficulty: string }) {
  const colors: Record<string, string> = {
    easy: "bg-green-600/20 text-green-400 border-green-600/30",
    medium: "bg-yellow-600/20 text-yellow-400 border-yellow-600/30",
    hard: "bg-red-600/20 text-red-400 border-red-600/30",
  };
  const cls = colors[difficulty.toLowerCase()] || "bg-gray-600/20 text-gray-400 border-gray-600/30";
  return (
    <span className={`text-xs px-2 py-0.5 rounded border ${cls}`}>
      {difficulty}
    </span>
  );
}

function ReviewModal({
  review,
  onSubmit,
  onClose,
}: {
  review: ReviewDue;
  onSubmit: (quality: number) => void;
  onClose: () => void;
}) {
  const [quality, setQuality] = useState<number | null>(null);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 w-full max-w-md mx-4">
        <h3 className="text-lg font-semibold text-gray-100 mb-1">
          Rate Your Review
        </h3>
        <p className="text-sm text-gray-400 mb-4">
          Topic: {review.topic_id} (Review #{review.review_count + 1})
        </p>

        <div className="space-y-2 mb-6">
          {[0, 1, 2, 3, 4, 5].map((q) => (
            <button
              key={q}
              onClick={() => setQuality(q)}
              className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                quality === q
                  ? "bg-blue-600 text-white"
                  : "bg-gray-800 text-gray-300 hover:bg-gray-700"
              }`}
            >
              <span className="font-medium">{q}</span> - {QUALITY_LABELS[q]}
            </button>
          ))}
        </div>

        <div className="flex gap-3 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-400 hover:text-gray-200"
          >
            Cancel
          </button>
          <button
            onClick={() => quality !== null && onSubmit(quality)}
            disabled={quality === null}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Submit
          </button>
        </div>
      </div>
    </div>
  );
}

export default function LearningPathPage() {
  const { recommended, reviewsDue, loading, error, completeReview } =
    useLearningPath();
  const [activeReview, setActiveReview] = useState<ReviewDue | null>(null);

  const handleReviewSubmit = async (quality: number) => {
    if (!activeReview) return;
    await completeReview(activeReview.topic_id, quality);
    setActiveReview(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
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
          Loading learning path...
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-6 max-w-4xl mx-auto w-full">
      <h1 className="text-2xl font-bold text-gray-100 mb-6">Learning Path</h1>

      {error && (
        <div className="mb-4 p-3 rounded bg-red-900/30 border border-red-700 text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Reviews Due Section */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-gray-200 mb-3">
          Reviews Due
        </h2>
        {reviewsDue.length === 0 ? (
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 text-center text-gray-500">
            No reviews due. Great job staying on top of your studies!
          </div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {reviewsDue.map((review) => (
              <div
                key={review.id}
                className="bg-gray-900 border border-gray-800 rounded-lg p-4"
              >
                <div className="flex items-start justify-between mb-2">
                  <h3 className="text-sm font-medium text-gray-200">
                    {review.topic_id}
                  </h3>
                  <span className="text-xs text-gray-500">
                    Review #{review.review_count}
                  </span>
                </div>
                <div className="text-xs text-gray-500 mb-3 space-y-1">
                  <p>
                    Due:{" "}
                    {new Date(review.next_review_date).toLocaleDateString()}
                  </p>
                  <p>Interval: {review.interval_days} days</p>
                </div>
                <button
                  onClick={() => setActiveReview(review)}
                  className="w-full text-center text-sm py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white transition-colors"
                >
                  Review Now
                </button>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Recommended Topics Section */}
      <section>
        <h2 className="text-lg font-semibold text-gray-200 mb-3">
          Recommended Topics
        </h2>
        {recommended.length === 0 ? (
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 text-center text-gray-500">
            Set learning goals to get personalized recommendations.
          </div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {recommended.map((topic) => (
              <div
                key={topic.topic_id}
                className="bg-gray-900 border border-gray-800 rounded-lg p-4"
              >
                <div className="flex items-start justify-between mb-1">
                  <h3 className="text-sm font-medium text-gray-200">
                    {topic.display_name}
                  </h3>
                  <DifficultyBadge difficulty={topic.difficulty} />
                </div>
                <p className="text-xs text-gray-500 mb-2">{topic.subject}</p>
                <p className="text-xs text-gray-400 mb-3">{topic.reason}</p>
                <div className="text-xs text-gray-500">
                  ~{topic.estimated_minutes} min
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Review Modal */}
      {activeReview && (
        <ReviewModal
          review={activeReview}
          onSubmit={handleReviewSubmit}
          onClose={() => setActiveReview(null)}
        />
      )}
    </div>
  );
}
