'use client'

import React from 'react'
import { EnhancedDashboard } from '@/components/dashboard/EnhancedDashboard'
import { useRouter } from 'next/navigation'

// Mock data for demonstration
const mockDashboardData = {
  user: {
    name: "Alex Johnson",
    level: 12,
    xp: 2840,
    nextLevelXp: 3200
  },
  learningProgress: {
    totalTopics: 45,
    completedTopics: 28,
    inProgressTopics: 12,
    masteredTopics: 15,
    overallProgress: 68
  },
  subjects: [
    {
      id: "world-history",
      name: "World History",
      progress: 75,
      masteryLevel: "intermediate" as const,
      topics: [
        {
          id: "ww1",
          name: "World War I",
          progress: 90,
          status: "completed" as const
        },
        {
          id: "renaissance",
          name: "Renaissance",
          progress: 65,
          status: "in_progress" as const
        },
        {
          id: "colonial-africa",
          name: "Colonial Africa",
          progress: 45,
          status: "in_progress" as const
        },
        {
          id: "cold-war",
          name: "Cold War",
          progress: 0,
          status: "not_started" as const
        }
      ],
      recentActivity: new Date(2024, 11, 15)
    },
    {
      id: "american-history",
      name: "American History", 
      progress: 45,
      masteryLevel: "beginner" as const,
      topics: [
        {
          id: "civil-war",
          name: "American Civil War",
          progress: 80,
          status: "completed" as const
        },
        {
          id: "revolutionary-war",
          name: "Revolutionary War",
          progress: 30,
          status: "in_progress" as const
        },
        {
          id: "great-depression",
          name: "Great Depression",
          progress: 0,
          status: "not_started" as const
        }
      ],
      recentActivity: new Date(2024, 11, 12)
    }
  ],
  achievements: [
    {
      id: "first-essay",
      title: "First Essay Complete",
      description: "Successfully completed your first historical analysis essay",
      icon: ({ className }: { className?: string }) => (
        <div className={`bg-blue-500 rounded-full flex items-center justify-center ${className}`}>
          📝
        </div>
      ),
      earnedAt: new Date(2024, 11, 10),
      rarity: "common" as const
    },
    {
      id: "source-analyzer",
      title: "Source Detective",
      description: "Analyzed 10 primary sources with detailed insights",
      icon: ({ className }: { className?: string }) => (
        <div className={`bg-purple-500 rounded-full flex items-center justify-center ${className}`}>
          🔍
        </div>
      ),
      earnedAt: new Date(2024, 11, 8),
      rarity: "rare" as const
    },
    {
      id: "streak-master",
      title: "Week Warrior",
      description: "Maintained a 7-day study streak",
      icon: ({ className }: { className?: string }) => (
        <div className={`bg-orange-500 rounded-full flex items-center justify-center ${className}`}>
          🔥
        </div>
      ),
      earnedAt: new Date(2024, 11, 5),
      rarity: "epic" as const
    }
  ],
  studyStreak: {
    current: 5,
    longest: 12,
    lastStudyDate: new Date(2024, 11, 15)
  },
  upcomingReviews: [
    {
      id: "review-1",
      title: "World War I Causes",
      type: "spaced_repetition" as const,
      dueDate: new Date(2024, 11, 16),
      priority: "high" as const
    },
    {
      id: "review-2",
      title: "Renaissance Art Analysis Essay",
      type: "essay_review" as const,
      dueDate: new Date(2024, 11, 17),
      priority: "medium" as const
    },
    {
      id: "review-3",
      title: "Primary Source Analysis Quiz",
      type: "assessment" as const,
      dueDate: new Date(2024, 11, 18),
      priority: "urgent" as const
    }
  ],
  recentSessions: [
    {
      id: "session-1",
      type: "chat" as const,
      topic: "Causes of World War I",
      duration: 25,
      date: new Date(2024, 11, 15)
    },
    {
      id: "session-2", 
      type: "voice" as const,
      topic: "Renaissance Artists",
      duration: 18,
      date: new Date(2024, 11, 14)
    },
    {
      id: "session-3",
      type: "timeline" as const,
      topic: "Colonial Africa Timeline",
      duration: 32,
      date: new Date(2024, 11, 13)
    },
    {
      id: "session-4",
      type: "source_analysis" as const,
      topic: "Cecil Rhodes Speech Analysis",
      duration: 41,
      date: new Date(2024, 11, 12)
    }
  ],
  weeklyGoal: {
    target: 180,
    current: 135,
    unit: "minutes" as const
  }
}

export default function DashboardPage() {
  const router = useRouter()

  const handleStartSession = (type: string, subjectId?: string) => {
    switch (type) {
      case 'chat':
        router.push('/chat')
        break
      case 'voice':
        router.push('/voice')
        break
      case 'timeline':
        router.push('/timeline')
        break
      case 'sources':
        router.push('/sources')
        break
      default:
        console.log('Starting session:', type, subjectId)
    }
  }

  return (
    <div className="container mx-auto p-6">
      <EnhancedDashboard
        data={mockDashboardData}
        onStartSession={handleStartSession}
      />
    </div>
  )
}