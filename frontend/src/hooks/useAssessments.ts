"use client";

import { useCallback, useState } from "react";
import * as assessmentsApi from "@/lib/api/assessments";
import type {
  Assessment,
  QuickQuizRequest,
  QuickQuizResponse,
  QuizQuestion,
  SubmissionResponse,
} from "@/lib/types/api";

interface QuizState {
  questions: QuizQuestion[];
  currentIndex: number;
  answers: Record<string, string>;
  subject: string;
  topic: string;
}

export function useAssessments() {
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [quiz, setQuiz] = useState<QuizState | null>(null);
  const [results, setResults] = useState<SubmissionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadAssessments = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await assessmentsApi.listAssessments();
      setAssessments(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load assessments"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  const startQuickQuiz = useCallback(async (data: QuickQuizRequest) => {
    setLoading(true);
    setError(null);
    setResults(null);
    try {
      const response: QuickQuizResponse = await assessmentsApi.quickQuiz(data);
      setQuiz({
        questions: response.questions,
        currentIndex: 0,
        answers: {},
        subject: response.subject,
        topic: response.topic,
      });
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to start quiz"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  const setAnswer = useCallback((questionIndex: number, answer: string) => {
    setQuiz((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        answers: { ...prev.answers, [String(questionIndex)]: answer },
      };
    });
  }, []);

  const goToQuestion = useCallback((index: number) => {
    setQuiz((prev) => {
      if (!prev) return prev;
      if (index < 0 || index >= prev.questions.length) return prev;
      return { ...prev, currentIndex: index };
    });
  }, []);

  const submitQuiz = useCallback(async () => {
    if (!quiz) return;
    setLoading(true);
    setError(null);
    try {
      // For quick quizzes we grade client-side since we have correct_answer
      const grades = quiz.questions.map((q, i) => {
        const userAnswer = (quiz.answers[String(i)] || "").trim().toLowerCase();
        const correct = q.correct_answer.trim().toLowerCase();
        const isCorrect = userAnswer === correct;
        return {
          question_id: String(i),
          score: isCorrect ? q.points : 0,
          max_score: q.points,
          feedback: isCorrect
            ? "Correct!"
            : `Incorrect. The correct answer is: ${q.correct_answer}`,
          correct: isCorrect,
        };
      });

      const totalScore = grades.reduce((sum, g) => sum + g.score, 0);
      const maxScore = grades.reduce((sum, g) => sum + g.max_score, 0);

      const result: SubmissionResponse = {
        id: crypto.randomUUID(),
        assessment_id: "quick-quiz",
        total_score: totalScore,
        max_score: maxScore,
        percentage: maxScore > 0 ? Math.round((totalScore / maxScore) * 100) : 0,
        grades,
        submitted_at: new Date().toISOString(),
        graded_at: new Date().toISOString(),
      };
      setResults(result);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to submit quiz"
      );
    } finally {
      setLoading(false);
    }
  }, [quiz]);

  const resetQuiz = useCallback(() => {
    setQuiz(null);
    setResults(null);
    setError(null);
  }, []);

  return {
    assessments,
    quiz,
    results,
    loading,
    error,
    loadAssessments,
    startQuickQuiz,
    setAnswer,
    goToQuestion,
    submitQuiz,
    resetQuiz,
  };
}
