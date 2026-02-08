"use client";

import { useState } from "react";
import { User, BookOpen, Target, TrendingUp } from "lucide-react";
import { Spinner } from "@/components/ui/Spinner";
import { useAuth } from "@/hooks/useAuth";
import { useProfile } from "@/hooks/useProfile";
import type { TopicMastery } from "@/lib/types/api";

function MasteryBar({ value, label }: { value: number; label: string }) {
  const pct = Math.round(value * 100);
  return (
    <div className="flex items-center gap-3">
      <span className="w-32 truncate text-sm text-gray-300">{label}</span>
      <div className="flex-1 h-2 rounded-full bg-gray-800">
        <div
          className="h-2 rounded-full bg-blue-500 transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-10 text-right text-xs text-gray-400">{pct}%</span>
    </div>
  );
}

function SubjectCard({
  subject,
  topics,
  averageMastery,
}: {
  subject: string;
  topics: TopicMastery[];
  averageMastery: number;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between"
      >
        <div className="flex items-center gap-2">
          <BookOpen className="h-4 w-4 text-blue-400" />
          <span className="font-medium text-gray-100">{subject}</span>
        </div>
        <span className="text-sm text-gray-400">
          {Math.round(averageMastery * 100)}% avg
        </span>
      </button>

      <div className="mt-3">
        <MasteryBar value={averageMastery} label="Overall" />
      </div>

      {expanded && topics.length > 0 && (
        <div className="mt-3 space-y-2 border-t border-gray-800 pt-3">
          {topics.map((t) => (
            <div key={`${t.subject}-${t.topic}`}>
              <MasteryBar value={t.mastery_score} label={t.topic} />
              <div className="ml-[8.5rem] flex gap-3 text-xs text-gray-500 mt-0.5">
                <span>Confidence: {Math.round(t.confidence * 100)}%</span>
                <span>Attempts: {t.attempts}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ProfilePage() {
  const { user } = useAuth();
  const { profile, mastery, loading, saving, error, updateProfile } =
    useProfile();

  const [learningStyle, setLearningStyle] = useState("");
  const [pace, setPace] = useState("");
  const [gradeLevel, setGradeLevel] = useState("");
  const [formInit, setFormInit] = useState(false);

  // Initialize form fields once profile loads
  if (profile && !formInit) {
    setLearningStyle(profile.learning_style || "balanced");
    setPace(profile.pace || "moderate");
    setGradeLevel(profile.grade_level || "");
    setFormInit(true);
  }

  // Group mastery by subject
  const subjects = mastery.reduce<
    Record<string, { topics: TopicMastery[]; avg: number }>
  >((acc, item) => {
    if (!acc[item.subject]) {
      acc[item.subject] = { topics: [], avg: 0 };
    }
    acc[item.subject].topics.push(item);
    return acc;
  }, {});

  for (const key of Object.keys(subjects)) {
    const s = subjects[key];
    s.avg =
      s.topics.reduce((sum, t) => sum + t.mastery_score, 0) / s.topics.length;
  }

  const handleSave = () => {
    updateProfile({
      learning_style: learningStyle,
      pace,
      grade_level: gradeLevel || undefined,
    });
  };

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center bg-gray-950">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto bg-gray-950 p-6">
      <div className="mx-auto max-w-3xl space-y-6">
        <h1 className="text-2xl font-bold text-gray-100">Profile</h1>

        {error && (
          <div className="rounded-lg border border-red-800 bg-red-900/30 p-3 text-sm text-red-300">
            {error}
          </div>
        )}

        {/* User Info */}
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-gray-800">
              <User className="h-7 w-7 text-blue-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-100">
                {user?.name || profile?.name || "Student"}
              </h2>
              <p className="text-sm text-gray-400">
                {user?.email || profile?.email}
              </p>
              <span className="mt-1 inline-block rounded-full bg-blue-600/20 px-2.5 py-0.5 text-xs font-medium text-blue-400">
                {user?.role || "student"}
              </span>
            </div>
          </div>
        </div>

        {/* Learning Preferences */}
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
          <h3 className="mb-4 text-lg font-semibold text-gray-100">
            Learning Preferences
          </h3>
          <div className="grid gap-4 sm:grid-cols-3">
            <div>
              <label className="mb-1 block text-sm text-gray-400">
                Learning Style
              </label>
              <select
                value={learningStyle}
                onChange={(e) => setLearningStyle(e.target.value)}
                className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 focus:border-blue-500 focus:outline-none"
              >
                <option value="visual">Visual</option>
                <option value="auditory">Auditory</option>
                <option value="kinesthetic">Kinesthetic</option>
                <option value="reading">Reading</option>
                <option value="balanced">Balanced</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm text-gray-400">Pace</label>
              <select
                value={pace}
                onChange={(e) => setPace(e.target.value)}
                className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 focus:border-blue-500 focus:outline-none"
              >
                <option value="slow">Slow</option>
                <option value="moderate">Moderate</option>
                <option value="fast">Fast</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm text-gray-400">
                Grade Level
              </label>
              <input
                type="text"
                value={gradeLevel}
                onChange={(e) => setGradeLevel(e.target.value)}
                placeholder="e.g. 10th grade"
                className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:border-blue-500 focus:outline-none"
              />
            </div>
          </div>
          <button
            onClick={handleSave}
            disabled={saving}
            className="mt-4 rounded-lg bg-blue-600 px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-500 disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save Changes"}
          </button>
        </div>

        {/* Strengths & Weaknesses */}
        {profile && (profile.strengths.length > 0 || profile.weaknesses.length > 0) && (
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
              <div className="mb-3 flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-green-400" />
                <h3 className="font-semibold text-gray-100">Strengths</h3>
              </div>
              <div className="flex flex-wrap gap-2">
                {profile.strengths.length > 0 ? (
                  profile.strengths.map((s) => (
                    <span
                      key={s}
                      className="rounded-full bg-green-900/30 border border-green-800 px-3 py-1 text-xs text-green-300"
                    >
                      {s}
                    </span>
                  ))
                ) : (
                  <p className="text-sm text-gray-500">No strengths recorded yet</p>
                )}
              </div>
            </div>
            <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
              <div className="mb-3 flex items-center gap-2">
                <Target className="h-4 w-4 text-amber-400" />
                <h3 className="font-semibold text-gray-100">
                  Areas to Improve
                </h3>
              </div>
              <div className="flex flex-wrap gap-2">
                {profile.weaknesses.length > 0 ? (
                  profile.weaknesses.map((w) => (
                    <span
                      key={w}
                      className="rounded-full bg-amber-900/30 border border-amber-800 px-3 py-1 text-xs text-amber-300"
                    >
                      {w}
                    </span>
                  ))
                ) : (
                  <p className="text-sm text-gray-500">No areas recorded yet</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Mastery by Subject */}
        <div>
          <h3 className="mb-3 text-lg font-semibold text-gray-100">
            Mastery by Subject
          </h3>
          {Object.keys(subjects).length > 0 ? (
            <div className="space-y-3">
              {Object.entries(subjects).map(([subject, data]) => (
                <SubjectCard
                  key={subject}
                  subject={subject}
                  topics={data.topics}
                  averageMastery={data.avg}
                />
              ))}
            </div>
          ) : (
            <div className="rounded-lg border border-gray-800 bg-gray-900 p-8 text-center">
              <p className="text-sm text-gray-500">
                No mastery data yet. Start learning to track your progress!
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
