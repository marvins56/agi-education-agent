"use client";

import { useCallback, useEffect, useState } from "react";
import * as analyticsApi from "@/lib/api/analytics";
import type { AnalyticsSummary, TopicMastery, ActivityHeatmap, Alert } from "@/lib/types/api";

export function useAnalytics() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [mastery, setMastery] = useState<TopicMastery[]>([]);
  const [activity, setActivity] = useState<ActivityHeatmap[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAnalytics = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [summaryData, masteryData, activityData, alertsData] =
        await Promise.all([
          analyticsApi.getSummary(),
          analyticsApi.getMastery(),
          analyticsApi.getActivity(30),
          analyticsApi.getAlerts(),
        ]);
      setSummary(summaryData);
      setMastery(masteryData);
      setActivity(activityData);
      setAlerts(alertsData);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load analytics"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAnalytics();
  }, [loadAnalytics]);

  return {
    summary,
    mastery,
    activity,
    alerts,
    loading,
    error,
    reload: loadAnalytics,
  };
}
