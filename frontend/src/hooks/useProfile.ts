"use client";

import { useCallback, useEffect, useState } from "react";
import * as profileApi from "@/lib/api/profile";
import type { Profile, ProfileUpdateRequest, MasteryBySubject, TopicMastery } from "@/lib/types/api";

export function useProfile() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [mastery, setMastery] = useState<TopicMastery[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadProfile = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [profileData, masteryData] = await Promise.all([
        profileApi.getProfile(),
        profileApi.getMastery(),
      ]);
      setProfile(profileData);
      setMastery(masteryData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load profile");
    } finally {
      setLoading(false);
    }
  }, []);

  const updateProfile = useCallback(
    async (data: ProfileUpdateRequest) => {
      setSaving(true);
      setError(null);
      try {
        const updated = await profileApi.updateProfile(data);
        setProfile(updated);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to update profile"
        );
      } finally {
        setSaving(false);
      }
    },
    []
  );

  const getMasteryBySubject = useCallback(
    (subject: string): MasteryBySubject | null => {
      const topics = mastery.filter((m) => m.subject === subject);
      if (topics.length === 0) return null;
      const avg =
        topics.reduce((sum, t) => sum + t.mastery_score, 0) / topics.length;
      return { subject, topics, average_mastery: avg };
    },
    [mastery]
  );

  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  return {
    profile,
    mastery,
    loading,
    saving,
    error,
    updateProfile,
    getMasteryBySubject,
    reload: loadProfile,
  };
}
