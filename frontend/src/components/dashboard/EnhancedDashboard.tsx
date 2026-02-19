'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  BookOpen, 
  Calendar, 
  Target, 
  TrendingUp, 
  Award, 
  Clock, 
  Brain,
  MessageCircle,
  FileText,
  CalendarRange as Timeline,
  Users,
  Star,
  Flame,
  CheckCircle2,
  AlertCircle,
  BarChart3
} from 'lucide-react'

interface LearningProgress {
  totalTopics: number
  completedTopics: number
  inProgressTopics: number
  masteredTopics: number
  overallProgress: number
}

interface Subject {
  id: string
  name: string
  progress: number
  masteryLevel: 'beginner' | 'intermediate' | 'advanced' | 'expert'
  topics: {
    id: string
    name: string
    progress: number
    status: 'not_started' | 'in_progress' | 'completed' | 'mastered'
  }[]
  recentActivity: Date
}

interface Achievement {
  id: string
  title: string
  description: string
  icon: React.ComponentType<any>
  earnedAt: Date
  rarity: 'common' | 'rare' | 'epic' | 'legendary'
}

interface StudyStreak {
  current: number
  longest: number
  lastStudyDate: Date
}

interface UpcomingReview {
  id: string
  title: string
  type: 'spaced_repetition' | 'assessment' | 'essay_review'
  dueDate: Date
  priority: 'low' | 'medium' | 'high' | 'urgent'
}

interface DashboardData {
  user: {
    name: string
    level: number
    xp: number
    nextLevelXp: number
  }
  learningProgress: LearningProgress
  subjects: Subject[]
  achievements: Achievement[]
  studyStreak: StudyStreak
  upcomingReviews: UpcomingReview[]
  recentSessions: {
    id: string
    type: 'chat' | 'voice' | 'timeline' | 'source_analysis'
    topic: string
    duration: number
    date: Date
  }[]
  weeklyGoal: {
    target: number
    current: number
    unit: 'minutes' | 'sessions' | 'topics'
  }
}

interface EnhancedDashboardProps {
  data: DashboardData
  onStartSession?: (type: string, subjectId?: string) => void
  className?: string
}

const masteryColors = {
  beginner: 'bg-red-100 text-red-800',
  intermediate: 'bg-yellow-100 text-yellow-800',
  advanced: 'bg-blue-100 text-blue-800',
  expert: 'bg-purple-100 text-purple-800'
}

const rarityColors = {
  common: 'bg-gray-100 text-gray-800 border-gray-300',
  rare: 'bg-blue-100 text-blue-800 border-blue-300',
  epic: 'bg-purple-100 text-purple-800 border-purple-300',
  legendary: 'bg-yellow-100 text-yellow-800 border-yellow-300'
}

const priorityColors = {
  low: 'border-l-gray-300',
  medium: 'border-l-yellow-300',
  high: 'border-l-orange-300',
  urgent: 'border-l-red-300'
}

export function EnhancedDashboard({ data, onStartSession, className }: EnhancedDashboardProps) {
  const progressPercentage = (data.user.xp / data.user.nextLevelXp) * 100
  const weeklyGoalPercentage = (data.weeklyGoal.current / data.weeklyGoal.target) * 100

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Welcome Header */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="md:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-2xl">
                  Welcome back, {data.user.name}!
                </CardTitle>
                <p className="text-muted-foreground mt-1">
                  Ready to continue your learning journey?
                </p>
              </div>
              <div className="text-right">
                <div className="flex items-center gap-2 mb-1">
                  <Star className="h-5 w-5 text-yellow-500" />
                  <span className="font-semibold">Level {data.user.level}</span>
                </div>
                <div className="text-sm text-muted-foreground">
                  {data.user.xp} / {data.user.nextLevelXp} XP
                </div>
              </div>
            </div>
            <Progress value={progressPercentage} className="mt-3" />
          </CardHeader>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Flame className="h-5 w-5 text-orange-500" />
              Study Streak
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="text-3xl font-bold text-center">
                {data.studyStreak.current}
              </div>
              <div className="text-center text-sm text-muted-foreground">
                days in a row
              </div>
              <div className="text-xs text-center text-muted-foreground">
                Longest: {data.studyStreak.longest} days
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="subjects">Subjects</TabsTrigger>
          <TabsTrigger value="achievements">Achievements</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {/* Learning Progress */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5" />
                  Learning Progress
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span>Overall Progress</span>
                  <span>{data.learningProgress.overallProgress}%</span>
                </div>
                <Progress value={data.learningProgress.overallProgress} />
                
                <div className="grid grid-cols-2 gap-4 text-center text-sm">
                  <div>
                    <div className="font-semibold text-green-600">
                      {data.learningProgress.masteredTopics}
                    </div>
                    <div className="text-muted-foreground">Mastered</div>
                  </div>
                  <div>
                    <div className="font-semibold text-blue-600">
                      {data.learningProgress.inProgressTopics}
                    </div>
                    <div className="text-muted-foreground">In Progress</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Weekly Goal */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="h-5 w-5" />
                  Weekly Goal
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span>Progress</span>
                  <span>
                    {data.weeklyGoal.current} / {data.weeklyGoal.target} {data.weeklyGoal.unit}
                  </span>
                </div>
                <Progress value={weeklyGoalPercentage} />
                
                <div className="text-center">
                  {weeklyGoalPercentage >= 100 ? (
                    <Badge className="bg-green-100 text-green-800">
                      <CheckCircle2 className="h-3 w-3 mr-1" />
                      Goal Achieved!
                    </Badge>
                  ) : (
                    <Badge variant="outline">
                      {Math.round(weeklyGoalPercentage)}% Complete
                    </Badge>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-5 w-5" />
                  Quick Start
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button 
                  className="w-full justify-start" 
                  variant="outline"
                  onClick={() => onStartSession?.('chat')}
                >
                  <MessageCircle className="h-4 w-4 mr-2" />
                  Start Chat Session
                </Button>
                <Button 
                  className="w-full justify-start" 
                  variant="outline"
                  onClick={() => onStartSession?.('voice')}
                >
                  <MessageCircle className="h-4 w-4 mr-2" />
                  Voice Conversation
                </Button>
                <Button 
                  className="w-full justify-start" 
                  variant="outline"
                  onClick={() => onStartSession?.('timeline')}
                >
                  <Timeline className="h-4 w-4 mr-2" />
                  Explore Timeline
                </Button>
                <Button 
                  className="w-full justify-start" 
                  variant="outline"
                  onClick={() => onStartSession?.('sources')}
                >
                  <FileText className="h-4 w-4 mr-2" />
                  Analyze Sources
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Upcoming Reviews */}
          {data.upcomingReviews.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="h-5 w-5" />
                  Upcoming Reviews
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {data.upcomingReviews.slice(0, 5).map((review) => (
                    <div
                      key={review.id}
                      className={`flex items-center justify-between p-3 rounded-md border-l-4 ${
                        priorityColors[review.priority]
                      } bg-muted/30`}
                    >
                      <div className="flex-1">
                        <div className="font-medium text-sm">{review.title}</div>
                        <div className="text-xs text-muted-foreground">
                          {review.type.replace('_', ' ')} • Due {review.dueDate.toLocaleDateString()}
                        </div>
                      </div>
                      <Badge variant="outline">
                        {review.priority}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Recent Sessions */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Recent Activity
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {data.recentSessions.slice(0, 5).map((session) => (
                  <div key={session.id} className="flex items-center justify-between p-2 rounded-md hover:bg-muted/50">
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 bg-primary rounded-full" />
                      <div>
                        <div className="font-medium text-sm">{session.topic}</div>
                        <div className="text-xs text-muted-foreground">
                          {session.type} • {session.duration} min • {session.date.toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="subjects" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {data.subjects.map((subject) => (
              <Card key={subject.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{subject.name}</CardTitle>
                    <Badge className={masteryColors[subject.masteryLevel]}>
                      {subject.masteryLevel}
                    </Badge>
                  </div>
                  <div className="flex justify-between text-sm text-muted-foreground">
                    <span>Progress: {subject.progress}%</span>
                    <span>Last activity: {subject.recentActivity.toLocaleDateString()}</span>
                  </div>
                  <Progress value={subject.progress} />
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <h4 className="font-medium text-sm">Recent Topics</h4>
                    {subject.topics.slice(0, 4).map((topic) => (
                      <div key={topic.id} className="flex items-center justify-between">
                        <span className="text-sm">{topic.name}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1 bg-muted rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-primary rounded-full"
                              style={{ width: `${topic.progress}%` }}
                            />
                          </div>
                          <Badge variant="outline">
                            {topic.status.replace('_', ' ')}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  <Button 
                    className="w-full mt-4" 
                    variant="outline"
                    onClick={() => onStartSession?.('chat', subject.id)}
                  >
                    Continue Learning
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="achievements" className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.achievements.map((achievement) => (
              <Card key={achievement.id} className={`border-2 ${rarityColors[achievement.rarity]}`}>
                <CardHeader className="text-center">
                  <div className="mx-auto mb-2">
                    <achievement.icon className="h-12 w-12" />
                  </div>
                  <CardTitle className="text-lg">{achievement.title}</CardTitle>
                  <Badge variant="outline" className={rarityColors[achievement.rarity]}>
                    {achievement.rarity}
                  </Badge>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-center text-muted-foreground">
                    {achievement.description}
                  </p>
                  <div className="text-center mt-2">
                    <span className="text-xs text-muted-foreground">
                      Earned on {achievement.earnedAt.toLocaleDateString()}
                    </span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  Learning Statistics
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {data.learningProgress.totalTopics}
                    </div>
                    <div className="text-sm text-muted-foreground">Total Topics</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {data.learningProgress.completedTopics}
                    </div>
                    <div className="text-sm text-muted-foreground">Completed</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {data.learningProgress.masteredTopics}
                    </div>
                    <div className="text-sm text-muted-foreground">Mastered</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-600">
                      {data.recentSessions.length}
                    </div>
                    <div className="text-sm text-muted-foreground">Recent Sessions</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Learning Insights</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5" />
                  <div>
                    <div className="font-medium text-sm">Strong Performance</div>
                    <div className="text-xs text-muted-foreground">
                      You're excelling in primary source analysis
                    </div>
                  </div>
                </div>
                
                <div className="flex items-start gap-2">
                  <AlertCircle className="h-4 w-4 text-yellow-500 mt-0.5" />
                  <div>
                    <div className="font-medium text-sm">Focus Area</div>
                    <div className="text-xs text-muted-foreground">
                      Consider spending more time on cause-and-effect relationships
                    </div>
                  </div>
                </div>
                
                <div className="flex items-start gap-2">
                  <TrendingUp className="h-4 w-4 text-blue-500 mt-0.5" />
                  <div>
                    <div className="font-medium text-sm">Progress Trend</div>
                    <div className="text-xs text-muted-foreground">
                      Your learning velocity has increased 23% this week
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}