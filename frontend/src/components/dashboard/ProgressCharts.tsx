"use client";

import React, { useMemo } from 'react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface ProgressData {
  date: string;
  overallProgress: number;
  topicMastery: number;
  assessmentScore: number;
  studyTime: number;
  engagement: number;
}

interface ProgressChartsProps {
  data: ProgressData[];
  timeRange: string;
  selectedMetric: string;
  onMetricChange: (metric: string) => void;
}

const CHART_COLORS = {
  primary: '#3b82f6',
  secondary: '#10b981',
  tertiary: '#f59e0b',
  quaternary: '#ef4444',
  quinary: '#8b5cf6'
};

const PIE_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export function ProgressCharts({ data, timeRange, selectedMetric, onMetricChange }: ProgressChartsProps) {
  // Calculate trend
  const trend = useMemo(() => {
    if (data.length < 2) return null;
    
    const recent = data.slice(-5);
    const older = data.slice(-10, -5);
    
    if (recent.length === 0 || older.length === 0) return null;
    
    const recentAvg = recent.reduce((sum, d) => sum + d.overallProgress, 0) / recent.length;
    const olderAvg = older.reduce((sum, d) => sum + d.overallProgress, 0) / older.length;
    
    const change = recentAvg - olderAvg;
    
    return {
      direction: change > 2 ? 'up' : change < -2 ? 'down' : 'stable',
      change: Math.abs(change),
    };
  }, [data]);

  // Prepare subject mastery data for pie chart
  const subjectMasteryData = useMemo(() => {
    // Mock data - in real app would come from API
    return [
      { name: 'Ancient History', value: 85, color: PIE_COLORS[0] },
      { name: 'Medieval History', value: 72, color: PIE_COLORS[1] },
      { name: 'Modern History', value: 91, color: PIE_COLORS[2] },
      { name: 'World Wars', value: 68, color: PIE_COLORS[3] },
      { name: 'American History', value: 79, color: PIE_COLORS[4] },
    ];
  }, []);

  // Prepare assessment performance data
  const assessmentData = useMemo(() => {
    if (data.length === 0) return [];
    
    return data.slice(-12).map(d => ({
      date: new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      score: d.assessmentScore,
      average: 75, // Mock average line
    }));
  }, [data]);

  // Prepare study time data
  const studyTimeData = useMemo(() => {
    if (data.length === 0) return [];
    
    return data.slice(-7).map(d => ({
      day: new Date(d.date).toLocaleDateString('en-US', { weekday: 'short' }),
      minutes: d.studyTime,
      target: 60, // Mock target line
    }));
  }, [data]);

  const getTrendIcon = () => {
    if (!trend) return <Minus className="h-4 w-4" />;
    
    switch (trend.direction) {
      case 'up': return <TrendingUp className="h-4 w-4 text-green-600" />;
      case 'down': return <TrendingDown className="h-4 w-4 text-red-600" />;
      default: return <Minus className="h-4 w-4 text-gray-600" />;
    }
  };

  const getTrendColor = () => {
    if (!trend) return 'text-gray-600';
    
    switch (trend.direction) {
      case 'up': return 'text-green-600';
      case 'down': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="space-y-6">
      {/* Chart Controls */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Learning Progress</h3>
          {trend && (
            <div className="flex items-center gap-2 mt-1">
              {getTrendIcon()}
              <span className={`text-sm ${getTrendColor()}`}>
                {trend.direction === 'stable' ? 'Stable progress' : 
                 `${trend.direction === 'up' ? 'Improving' : 'Declining'} by ${trend.change.toFixed(1)}%`}
              </span>
            </div>
          )}
        </div>
        
        <Select value={selectedMetric} onValueChange={onMetricChange}>
          <SelectTrigger className="w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="overall">Overall Progress</SelectItem>
            <SelectItem value="mastery">Topic Mastery</SelectItem>
            <SelectItem value="assessment">Assessment Scores</SelectItem>
            <SelectItem value="studyTime">Study Time</SelectItem>
            <SelectItem value="engagement">Engagement</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Main Progress Chart */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Progress Over Time</span>
              <Badge variant="outline">{timeRange}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis 
                  dataKey="date" 
                  stroke="#9CA3AF"
                  fontSize={12}
                  tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                />
                <YAxis stroke="#9CA3AF" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '6px',
                    color: '#F9FAFB'
                  }}
                  formatter={((value: any, name: any) => [`${value ?? 0}%`, name ?? '']) as any}
                  labelFormatter={(label) => new Date(label).toLocaleDateString()}
                />
                <Area
                  type="monotone"
                  dataKey={selectedMetric === 'overall' ? 'overallProgress' : 
                          selectedMetric === 'mastery' ? 'topicMastery' :
                          selectedMetric === 'assessment' ? 'assessmentScore' :
                          selectedMetric === 'studyTime' ? 'studyTime' :
                          'engagement'}
                  stroke={CHART_COLORS.primary}
                  fill={CHART_COLORS.primary}
                  fillOpacity={0.2}
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Subject Mastery Pie Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Subject Mastery</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={subjectMasteryData}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {subjectMasteryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '6px',
                    color: '#F9FAFB'
                  }}
                  formatter={((value: any) => [`${value ?? 0}%`, 'Mastery']) as any}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="mt-4 space-y-2">
              {subjectMasteryData.map((subject, index) => (
                <div key={index} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <div 
                      className="w-3 h-3 rounded-full" 
                      style={{ backgroundColor: subject.color }}
                    />
                    <span className="truncate">{subject.name}</span>
                  </div>
                  <span className="font-medium">{subject.value}%</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Assessment Performance */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Assessment Scores</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={assessmentData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="day" stroke="#9CA3AF" fontSize={12} />
                <YAxis stroke="#9CA3AF" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '6px',
                    color: '#F9FAFB'
                  }}
                />
                <Line 
                  type="monotone" 
                  dataKey="score" 
                  stroke={CHART_COLORS.secondary} 
                  strokeWidth={2}
                  dot={{ fill: CHART_COLORS.secondary, strokeWidth: 2, r: 4 }}
                />
                <Line 
                  type="monotone" 
                  dataKey="average" 
                  stroke={CHART_COLORS.tertiary} 
                  strokeDasharray="5 5"
                  strokeWidth={1}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Weekly Study Time */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Weekly Study Pattern</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={studyTimeData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="day" stroke="#9CA3AF" fontSize={12} />
                <YAxis stroke="#9CA3AF" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '6px',
                    color: '#F9FAFB'
                  }}
                  formatter={((value: any) => [`${value ?? 0} min`, 'Study Time']) as any}
                />
                <Bar dataKey="minutes" fill={CHART_COLORS.primary} radius={[4, 4, 0, 0]} />
                <Line 
                  type="monotone" 
                  dataKey="target" 
                  stroke={CHART_COLORS.tertiary} 
                  strokeDasharray="5 5"
                  strokeWidth={2}
                />
              </BarChart>
            </ResponsiveContainer>
            <div className="mt-4 flex items-center justify-center gap-6 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded" style={{ backgroundColor: CHART_COLORS.primary }} />
                <span>Actual Study Time</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-1 rounded" style={{ backgroundColor: CHART_COLORS.tertiary }} />
                <span>Daily Target (60 min)</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}