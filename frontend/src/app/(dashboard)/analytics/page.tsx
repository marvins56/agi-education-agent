"use client";

import { useState, useEffect } from 'react';
import {
  Activity,
  Calendar,
  Flame,
  TrendingUp,
  AlertTriangle,
  Award,
  Target,
  Clock,
  BookOpen,
  Brain,
  Zap,
  RefreshCw
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { ProgressCharts } from '@/components/dashboard/ProgressCharts';
import { Spinner } from "@/components/ui/spinner";
import { useAnalytics } from "@/hooks/useAnalytics";
import { cn } from "@/lib/utils/cn";

// Enhanced stat card with trend indicators
function StatCard({
  label,
  value,
  icon: Icon,
  trend,
  trendValue,
  color = "blue"
}: {
  label: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: string;
  color?: string;
}) {
  const colorClasses = {
    blue: "bg-blue-500",
    green: "bg-green-500",
    yellow: "bg-yellow-500", 
    red: "bg-red-500",
    purple: "bg-purple-500"
  };

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <p className="text-sm font-medium text-muted-foreground">{label}</p>
            <div className="flex items-center gap-2">
              <p className="text-3xl font-bold">{value}</p>
              {trend && trendValue && (
                <div className={`flex items-center gap-1 text-sm ${
                  trend === 'up' ? 'text-green-600' : 
                  trend === 'down' ? 'text-red-600' : 
                  'text-gray-600'
                }`}>
                  {trend === 'up' ? (
                    <TrendingUp className="h-3 w-3" />
                  ) : trend === 'down' ? (
                    <TrendingUp className="h-3 w-3 rotate-180" />
                  ) : null}
                  <span>{trendValue}</span>
                </div>
              )}
            </div>
          </div>
          <div className={`p-3 rounded-full ${colorClasses[color as keyof typeof colorClasses] || colorClasses.blue}`}>
            <Icon className="h-6 w-6 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Learning goal component
function LearningGoals() {
  const goals = [
    { id: 1, title: "Master World War II", progress: 78, target: 90, dueDate: "2026-03-15" },
    { id: 2, title: "Complete Renaissance Module", progress: 45, target: 100, dueDate: "2026-04-01" },
    { id: 3, title: "Ancient Civilizations", progress: 92, target: 85, dueDate: "2026-02-28" },
  ];

  return (
    <div className="space-y-4">
      {goals.map((goal) => (
        <div key={goal.id} className="space-y-2">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium">{goal.title}</h4>
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">
                {goal.progress}%
              </span>
              {goal.progress >= goal.target && (
                <Award className="h-4 w-4 text-yellow-500" />
              )}
            </div>
          </div>
          <Progress value={goal.progress} className="h-2" />
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Target: {goal.target}%</span>
            <span>Due: {new Date(goal.dueDate).toLocaleDateString()}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

// Historical thinking skills tracker
function ThinkingSkills() {
  const skills = [
    { name: "Chronological Thinking", level: 85, maxLevel: 100 },
    { name: "Historical Comprehension", level: 78, maxLevel: 100 },
    { name: "Historical Analysis", level: 91, maxLevel: 100 },
    { name: "Historical Interpretation", level: 67, maxLevel: 100 },
    { name: "Historical Research", level: 73, maxLevel: 100 },
  ];

  const getSkillColor = (level: number) => {
    if (level >= 90) return "text-green-600";
    if (level >= 70) return "text-blue-600";
    if (level >= 50) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <div className="space-y-4">
      {skills.map((skill, index) => (
        <div key={index} className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">{skill.name}</span>
            <span className={`text-sm font-semibold ${getSkillColor(skill.level)}`}>
              {skill.level}/100
            </span>
          </div>
          <Progress 
            value={skill.level} 
            className="h-2"
          />
        </div>
      ))}
    </div>
  );
}

// Recent achievements
function RecentAchievements() {
  const achievements = [
    {
      title: "Timeline Master",
      description: "Completed 10 timeline exercises",
      icon: Calendar,
      color: "bg-blue-500",
      date: "2026-02-15"
    },
    {
      title: "Source Detective",
      description: "Analyzed 25 primary sources",
      icon: BookOpen,
      color: "bg-green-500",
      date: "2026-02-14"
    },
    {
      title: "Critical Thinker",
      description: "Scored 90%+ on analysis assessment",
      icon: Brain,
      color: "bg-purple-500",
      date: "2026-02-13"
    },
  ];

  return (
    <div className="space-y-3">
      {achievements.map((achievement, index) => (
        <div key={index} className="flex items-start gap-3 p-3 rounded-lg border bg-card">
          <div className={`p-2 rounded-full ${achievement.color}`}>
            <achievement.icon className="h-4 w-4 text-white" />
          </div>
          <div className="flex-1 space-y-1">
            <h4 className="text-sm font-medium">{achievement.title}</h4>
            <p className="text-xs text-muted-foreground">{achievement.description}</p>
            <p className="text-xs text-muted-foreground">
              {new Date(achievement.date).toLocaleDateString()}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function AnalyticsPage() {
  const { summary, mastery, activity, alerts, loading, error } = useAnalytics();
  const [selectedMetric, setSelectedMetric] = useState('overall');
  const [timeRange, setTimeRange] = useState('week');
  const [refreshing, setRefreshing] = useState(false);

  // Mock progress data - in real app would come from API
  const progressData = Array.from({ length: 30 }, (_, i) => ({
    date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString(),
    overallProgress: Math.max(20, Math.min(95, 45 + Math.random() * 30 + i * 0.5)),
    topicMastery: Math.max(15, Math.min(90, 40 + Math.random() * 25 + i * 0.7)),
    assessmentScore: Math.max(30, Math.min(100, 60 + Math.random() * 35)),
    studyTime: Math.max(15, Math.min(180, 60 + Math.random() * 60)),
    engagement: Math.max(20, Math.min(100, 70 + Math.random() * 25)),
  }));

  const handleRefresh = async () => {
    setRefreshing(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500));
    setRefreshing(false);
  };

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Learning Analytics</h1>
          <p className="text-muted-foreground">
            Track your progress and achievements in historical learning
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="week">This Week</SelectItem>
              <SelectItem value="month">This Month</SelectItem>
              <SelectItem value="quarter">This Quarter</SelectItem>
              <SelectItem value="year">This Year</SelectItem>
            </SelectContent>
          </Select>
          
          <Button 
            onClick={handleRefresh} 
            disabled={refreshing}
            variant="outline"
            size="sm"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="text-red-700">
              <strong>Error:</strong> {error}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          label="Overall Progress"
          value={summary ? `${Math.round(summary.engagement_rate * 75)}%` : "78%"}
          icon={TrendingUp}
          trend="up"
          trendValue="+5.2%"
          color="blue"
        />
        <StatCard
          label="Current Streak"
          value={summary ? summary.streak : 12}
          icon={Flame}
          trend="up"
          trendValue="+2 days"
          color="yellow"
        />
        <StatCard
          label="Study Time"
          value="4.2h"
          icon={Clock}
          trend="stable"
          trendValue="±0.1h"
          color="green"
        />
        <StatCard
          label="Topics Mastered"
          value="7/12"
          icon={Award}
          trend="up"
          trendValue="+1 this week"
          color="purple"
        />
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Progress Charts - Takes 2/3 width */}
        <div className="lg:col-span-2">
          <ProgressCharts
            data={progressData}
            timeRange={timeRange}
            selectedMetric={selectedMetric}
            onMetricChange={setSelectedMetric}
          />
        </div>

        {/* Sidebar Content - Takes 1/3 width */}
        <div className="space-y-6">
          {/* Learning Goals */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                Learning Goals
              </CardTitle>
            </CardHeader>
            <CardContent>
              <LearningGoals />
            </CardContent>
          </Card>

          {/* Recent Achievements */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Award className="h-5 w-5" />
                Recent Achievements
              </CardTitle>
            </CardHeader>
            <CardContent>
              <RecentAchievements />
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Secondary Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Historical Thinking Skills */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5" />
              Historical Thinking Skills
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ThinkingSkills />
          </CardContent>
        </Card>

        {/* Activity Overview & Alerts */}
        <div className="space-y-6">
          {/* Activity Heatmap */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Activity (Last 30 Days)
              </CardTitle>
            </CardHeader>
            <CardContent>
              {activity.length > 0 ? (
                <>
                  <div className="flex flex-wrap gap-1">
                    {activity.map((d, i) => {
                      const maxCount = Math.max(...activity.map((d) => d.count), 1);
                      const ratio = d.count / maxCount;
                      const getIntensity = (count: number): string => {
                        if (count === 0) return "bg-gray-200";
                        if (ratio < 0.25) return "bg-blue-200";
                        if (ratio < 0.5) return "bg-blue-400";
                        if (ratio < 0.75) return "bg-blue-600";
                        return "bg-blue-800";
                      };
                      
                      return (
                        <div
                          key={i}
                          title={`${d.date}: ${d.count} activities`}
                          className={cn("h-3 w-3 rounded-sm", getIntensity(d.count))}
                        />
                      );
                    })}
                  </div>
                  <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
                    <span>Less</span>
                    <div className="h-3 w-3 rounded-sm bg-gray-200" />
                    <div className="h-3 w-3 rounded-sm bg-blue-200" />
                    <div className="h-3 w-3 rounded-sm bg-blue-400" />
                    <div className="h-3 w-3 rounded-sm bg-blue-600" />
                    <div className="h-3 w-3 rounded-sm bg-blue-800" />
                    <span>More</span>
                  </div>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">No activity data yet.</p>
              )}
            </CardContent>
          </Card>

          {/* Alerts */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5" />
                Alerts & Recommendations
              </CardTitle>
            </CardHeader>
            <CardContent>
              {alerts.length > 0 ? (
                <div className="space-y-3">
                  {alerts.map((alert, i) => (
                    <div key={i} className="flex items-start gap-3 p-3 rounded-lg border">
                      <div className={`p-1 rounded-full ${
                        alert.severity === 'high' ? 'bg-red-100' :
                        alert.severity === 'medium' ? 'bg-yellow-100' :
                        'bg-blue-100'
                      }`}>
                        <AlertTriangle className={`h-3 w-3 ${
                          alert.severity === 'high' ? 'text-red-600' :
                          alert.severity === 'medium' ? 'text-yellow-600' :
                          'text-blue-600'
                        }`} />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm">{alert.message}</p>
                        <p className="text-xs text-muted-foreground mt-1">{alert.type}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center space-y-2">
                  <Zap className="h-8 w-8 text-green-500 mx-auto" />
                  <p className="text-sm text-muted-foreground">All good! No alerts at this time.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
