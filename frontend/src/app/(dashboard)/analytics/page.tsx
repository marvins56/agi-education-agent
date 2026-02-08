"use client";

import {
  Activity,
  Calendar,
  Flame,
  TrendingUp,
  AlertTriangle,
} from "lucide-react";
import { Spinner } from "@/components/ui/Spinner";
import { useAnalytics } from "@/hooks/useAnalytics";
import { cn } from "@/lib/utils/cn";

function StatCard({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
}) {
  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-800">
          <Icon className="h-5 w-5 text-blue-400" />
        </div>
        <div>
          <p className="text-sm text-gray-400">{label}</p>
          <p className="text-xl font-bold text-gray-100">{value}</p>
        </div>
      </div>
    </div>
  );
}

function SeverityBadge({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    high: "bg-red-900/40 border-red-800 text-red-300",
    medium: "bg-amber-900/40 border-amber-800 text-amber-300",
    low: "bg-blue-900/40 border-blue-800 text-blue-300",
  };

  return (
    <span
      className={cn(
        "inline-block rounded-full border px-2 py-0.5 text-xs font-medium",
        colors[severity] || colors.low
      )}
    >
      {severity}
    </span>
  );
}

function ActivityGrid({
  data,
}: {
  data: { date: string; count: number }[];
}) {
  const maxCount = Math.max(...data.map((d) => d.count), 1);

  function getIntensity(count: number): string {
    if (count === 0) return "bg-gray-800";
    const ratio = count / maxCount;
    if (ratio < 0.25) return "bg-green-900";
    if (ratio < 0.5) return "bg-green-700";
    if (ratio < 0.75) return "bg-green-500";
    return "bg-green-400";
  }

  return (
    <div className="flex flex-wrap gap-1">
      {data.map((d) => (
        <div
          key={d.date}
          title={`${d.date}: ${d.count} events`}
          className={cn("h-4 w-4 rounded-sm", getIntensity(d.count))}
        />
      ))}
    </div>
  );
}

export default function AnalyticsPage() {
  const { summary, mastery, activity, alerts, loading, error } = useAnalytics();

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center bg-gray-950">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto bg-gray-950 p-6">
      <div className="mx-auto max-w-4xl space-y-6">
        <h1 className="text-2xl font-bold text-gray-100">Analytics</h1>

        {error && (
          <div className="rounded-lg border border-red-800 bg-red-900/30 p-3 text-sm text-red-300">
            {error}
          </div>
        )}

        {/* Summary Cards */}
        {summary && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="Total Events"
              value={summary.total_events}
              icon={Activity}
            />
            <StatCard
              label="Active Days"
              value={summary.active_days}
              icon={Calendar}
            />
            <StatCard
              label="Current Streak"
              value={summary.streak}
              icon={Flame}
            />
            <StatCard
              label="Engagement Rate"
              value={`${Math.round(summary.engagement_rate * 100)}%`}
              icon={TrendingUp}
            />
          </div>
        )}

        {/* Mastery Bars */}
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
          <h3 className="mb-4 text-lg font-semibold text-gray-100">
            Subject Mastery
          </h3>
          {mastery.length > 0 ? (
            <div className="space-y-3">
              {/* Group by subject and average */}
              {Object.entries(
                mastery.reduce<Record<string, number[]>>((acc, m) => {
                  if (!acc[m.subject]) acc[m.subject] = [];
                  acc[m.subject].push(m.mastery_score);
                  return acc;
                }, {})
              ).map(([subject, scores]) => {
                const avg =
                  scores.reduce((a, b) => a + b, 0) / scores.length;
                const pct = Math.round(avg * 100);
                return (
                  <div key={subject} className="flex items-center gap-3">
                    <span className="w-28 truncate text-sm text-gray-300">
                      {subject}
                    </span>
                    <div className="flex-1 h-3 rounded-full bg-gray-800">
                      <div
                        className="h-3 rounded-full bg-blue-500 transition-all"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="w-10 text-right text-sm font-medium text-gray-300">
                      {pct}%
                    </span>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-gray-500">No mastery data available yet.</p>
          )}
        </div>

        {/* Activity Heatmap */}
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
          <h3 className="mb-4 text-lg font-semibold text-gray-100">
            Activity (Last 30 Days)
          </h3>
          {activity.length > 0 ? (
            <>
              <ActivityGrid data={activity} />
              <div className="mt-3 flex items-center gap-2 text-xs text-gray-500">
                <span>Less</span>
                <div className="h-3 w-3 rounded-sm bg-gray-800" />
                <div className="h-3 w-3 rounded-sm bg-green-900" />
                <div className="h-3 w-3 rounded-sm bg-green-700" />
                <div className="h-3 w-3 rounded-sm bg-green-500" />
                <div className="h-3 w-3 rounded-sm bg-green-400" />
                <span>More</span>
              </div>
            </>
          ) : (
            <p className="text-sm text-gray-500">No activity data yet.</p>
          )}
        </div>

        {/* Alerts */}
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
          <div className="mb-4 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-400" />
            <h3 className="text-lg font-semibold text-gray-100">Alerts</h3>
          </div>
          {alerts.length > 0 ? (
            <div className="space-y-3">
              {alerts.map((alert, i) => (
                <div
                  key={i}
                  className="flex items-start gap-3 rounded-lg border border-gray-800 bg-gray-950 p-3"
                >
                  <SeverityBadge severity={alert.severity} />
                  <div className="flex-1">
                    <p className="text-sm text-gray-200">{alert.message}</p>
                    <p className="mt-0.5 text-xs text-gray-500">{alert.type}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">No alerts at this time.</p>
          )}
        </div>
      </div>
    </div>
  );
}
