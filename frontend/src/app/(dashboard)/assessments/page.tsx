"use client";

import { useEffect, useState } from "react";
import { useAssessments } from "@/hooks/useAssessments";

const DIFFICULTIES = ["easy", "medium", "hard"];
const QUESTION_COUNTS = [3, 4, 5, 6, 7, 8, 9, 10];

export default function AssessmentsPage() {
  const {
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
  } = useAssessments();

  const [subject, setSubject] = useState("");
  const [topic, setTopic] = useState("");
  const [questionCount, setQuestionCount] = useState(5);
  const [difficulty, setDifficulty] = useState("medium");

  useEffect(() => {
    loadAssessments();
  }, [loadAssessments]);

  const handleStartQuiz = () => {
    if (!subject.trim() || !topic.trim()) return;
    startQuickQuiz({
      subject: subject.trim(),
      topic: topic.trim(),
      question_count: questionCount,
      difficulty,
    });
  };

  // Results view
  if (results) {
    return (
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-3xl mx-auto space-y-6">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-100">Quiz Results</h1>
            <button
              onClick={resetQuiz}
              className="px-4 py-2 bg-gray-700 text-gray-200 rounded-lg hover:bg-gray-600 transition-colors"
            >
              Back to Assessments
            </button>
          </div>

          {/* Score summary */}
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 text-center">
            <div
              className={`text-5xl font-bold mb-2 ${
                results.percentage >= 70
                  ? "text-green-400"
                  : results.percentage >= 40
                  ? "text-yellow-400"
                  : "text-red-400"
              }`}
            >
              {results.percentage}%
            </div>
            <p className="text-gray-300 text-lg">
              {results.total_score} / {results.max_score} points
            </p>
            <p className="text-gray-500 text-sm mt-1">
              {results.grades.filter((g) => g.correct).length} of{" "}
              {results.grades.length} correct
            </p>
          </div>

          {/* Per-question results */}
          <div className="space-y-4">
            {results.grades.map((grade, i) => {
              const question = quiz?.questions[i];
              return (
                <div
                  key={grade.question_id}
                  className="bg-gray-800 rounded-xl border border-gray-700 p-5"
                >
                  <div className="flex items-start justify-between mb-3">
                    <p className="text-gray-100 font-medium flex-1">
                      <span className="text-gray-500 mr-2">Q{i + 1}.</span>
                      {question?.content || `Question ${i + 1}`}
                    </p>
                    <span
                      className={`ml-3 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                        grade.correct
                          ? "bg-green-900/50 text-green-300 border border-green-700"
                          : "bg-red-900/50 text-red-300 border border-red-700"
                      }`}
                    >
                      {grade.correct ? "Correct" : "Incorrect"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <p className="text-gray-400 text-sm">{grade.feedback}</p>
                    <span className="text-gray-500 text-sm ml-3 whitespace-nowrap">
                      {grade.score}/{grade.max_score} pts
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  // Quiz mode
  if (quiz) {
    const currentQ = quiz.questions[quiz.currentIndex];
    const isLast = quiz.currentIndex === quiz.questions.length - 1;
    const isFirst = quiz.currentIndex === 0;
    const currentAnswer = quiz.answers[String(quiz.currentIndex)] || "";

    return (
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-3xl mx-auto space-y-6">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-100">
              {quiz.subject} - {quiz.topic}
            </h1>
            <button
              onClick={resetQuiz}
              className="text-sm text-gray-400 hover:text-gray-200 transition-colors"
            >
              Exit Quiz
            </button>
          </div>

          {/* Progress indicator */}
          <div className="flex items-center gap-3">
            <span className="text-gray-300 text-sm font-medium">
              Question {quiz.currentIndex + 1} of {quiz.questions.length}
            </span>
            <div className="flex-1 bg-gray-800 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all"
                style={{
                  width: `${
                    ((quiz.currentIndex + 1) / quiz.questions.length) * 100
                  }%`,
                }}
              />
            </div>
          </div>

          {/* Question card */}
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
            <div className="flex items-center gap-2 mb-4">
              <span className="text-xs px-2 py-0.5 rounded bg-gray-700 text-gray-400">
                {currentQ.difficulty}
              </span>
              <span className="text-xs px-2 py-0.5 rounded bg-gray-700 text-gray-400">
                {currentQ.points} pts
              </span>
              <span className="text-xs px-2 py-0.5 rounded bg-gray-700 text-gray-400">
                {currentQ.type}
              </span>
            </div>

            <p className="text-gray-100 text-lg mb-6">{currentQ.content}</p>

            {/* MCQ options */}
            {currentQ.options && currentQ.options.length > 0 ? (
              <div className="space-y-3">
                {currentQ.options.map((option, optIdx) => {
                  const optionLetter = String.fromCharCode(65 + optIdx);
                  const isSelected = currentAnswer === option;
                  return (
                    <label
                      key={optIdx}
                      className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                        isSelected
                          ? "bg-blue-900/30 border-blue-500 text-gray-100"
                          : "bg-gray-900 border-gray-700 text-gray-300 hover:border-gray-500"
                      }`}
                    >
                      <input
                        type="radio"
                        name={`question-${quiz.currentIndex}`}
                        value={option}
                        checked={isSelected}
                        onChange={() => setAnswer(quiz.currentIndex, option)}
                        className="sr-only"
                      />
                      <span
                        className={`w-7 h-7 rounded-full border-2 flex items-center justify-center text-sm font-semibold flex-shrink-0 ${
                          isSelected
                            ? "border-blue-500 bg-blue-500 text-white"
                            : "border-gray-600 text-gray-400"
                        }`}
                      >
                        {optionLetter}
                      </span>
                      <span>{option}</span>
                    </label>
                  );
                })}
              </div>
            ) : (
              /* Short answer / text input */
              <textarea
                value={currentAnswer}
                onChange={(e) => setAnswer(quiz.currentIndex, e.target.value)}
                placeholder="Type your answer..."
                rows={3}
                className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500 resize-none"
              />
            )}
          </div>

          {/* Navigation buttons */}
          <div className="flex items-center justify-between">
            <button
              onClick={() => goToQuestion(quiz.currentIndex - 1)}
              disabled={isFirst}
              className={`px-5 py-2.5 rounded-lg font-medium transition-colors ${
                isFirst
                  ? "bg-gray-800 text-gray-600 cursor-not-allowed"
                  : "bg-gray-700 text-gray-200 hover:bg-gray-600"
              }`}
            >
              Previous
            </button>

            {isLast ? (
              <button
                onClick={submitQuiz}
                disabled={loading}
                className="px-6 py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-500 transition-colors disabled:opacity-50"
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <svg
                      className="animate-spin h-4 w-4"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                        fill="none"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                      />
                    </svg>
                    Submitting...
                  </span>
                ) : (
                  "Submit Quiz"
                )}
              </button>
            ) : (
              <button
                onClick={() => goToQuestion(quiz.currentIndex + 1)}
                className="px-5 py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-500 transition-colors"
              >
                Next
              </button>
            )}
          </div>

          {/* Question dots for quick navigation */}
          <div className="flex items-center justify-center gap-2">
            {quiz.questions.map((_, i) => {
              const answered = quiz.answers[String(i)] !== undefined;
              const isCurrent = i === quiz.currentIndex;
              return (
                <button
                  key={i}
                  onClick={() => goToQuestion(i)}
                  className={`w-8 h-8 rounded-full text-xs font-semibold transition-colors ${
                    isCurrent
                      ? "bg-blue-500 text-white"
                      : answered
                      ? "bg-blue-900/50 text-blue-300 border border-blue-700"
                      : "bg-gray-800 text-gray-500 border border-gray-700"
                  }`}
                >
                  {i + 1}
                </button>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  // Default list view
  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-3xl mx-auto space-y-8">
        <h1 className="text-2xl font-bold text-gray-100">Assessments</h1>

        {error && (
          <div className="bg-red-900/30 border border-red-700 text-red-300 rounded-lg px-4 py-3 text-sm">
            {error}
          </div>
        )}

        {/* Quick Quiz card */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
          <h2 className="text-lg font-semibold text-gray-100 mb-4">
            Quick Quiz
          </h2>
          <p className="text-gray-400 text-sm mb-5">
            Generate a quiz on any subject and topic. Choose the number of
            questions and difficulty level.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-5">
            <div>
              <label className="block text-sm text-gray-400 mb-1.5">
                Subject
              </label>
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="e.g. Mathematics"
                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1.5">
                Topic
              </label>
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="e.g. Quadratic Equations"
                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1.5">
                Questions
              </label>
              <select
                value={questionCount}
                onChange={(e) => setQuestionCount(Number(e.target.value))}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:border-blue-500 text-sm"
              >
                {QUESTION_COUNTS.map((n) => (
                  <option key={n} value={n}>
                    {n} questions
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1.5">
                Difficulty
              </label>
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:border-blue-500 text-sm"
              >
                {DIFFICULTIES.map((d) => (
                  <option key={d} value={d}>
                    {d.charAt(0).toUpperCase() + d.slice(1)}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <button
            onClick={handleStartQuiz}
            disabled={loading || !subject.trim() || !topic.trim()}
            className="px-5 py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
                Generating...
              </span>
            ) : (
              "Start Quiz"
            )}
          </button>
        </div>

        {/* Past assessments list */}
        <div>
          <h2 className="text-lg font-semibold text-gray-100 mb-4">
            Past Assessments
          </h2>

          {loading && assessments.length === 0 ? (
            <div className="flex items-center justify-center py-12">
              <svg
                className="animate-spin h-6 w-6 text-blue-500"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                  fill="none"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
            </div>
          ) : assessments.length === 0 ? (
            <div className="bg-gray-800 rounded-xl border border-gray-700 p-8 text-center">
              <p className="text-gray-400">
                No assessments yet. Start a quick quiz above!
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {assessments.map((assessment) => (
                <div
                  key={assessment.id}
                  className="bg-gray-800 rounded-xl border border-gray-700 p-4 flex items-center justify-between hover:border-gray-600 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <h3 className="text-gray-100 font-medium truncate">
                      {assessment.title}
                    </h3>
                    <div className="flex items-center gap-3 mt-1">
                      <span className="text-xs text-gray-400">
                        {assessment.subject}
                      </span>
                      <span className="text-xs px-2 py-0.5 rounded bg-gray-700 text-gray-400">
                        {assessment.type}
                      </span>
                      <span className="text-xs text-gray-500">
                        {assessment.question_count} questions
                      </span>
                      <span className="text-xs text-gray-500">
                        {assessment.total_points} pts
                      </span>
                    </div>
                  </div>
                  <div className="text-right ml-4">
                    <span className="text-xs text-gray-500">
                      {new Date(assessment.created_at).toLocaleDateString()}
                    </span>
                    {assessment.due_at && (
                      <p className="text-xs text-yellow-400 mt-0.5">
                        Due: {new Date(assessment.due_at).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
