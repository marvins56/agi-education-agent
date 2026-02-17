'use client'

import React, { useState, useEffect } from 'react'
import { TimelineViewer } from '@/components/timeline/TimelineViewer'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Search, Plus, Filter, Download } from 'lucide-react'

// Mock data for demonstration
const mockTimeline = {
  id: "world-war-1",
  title: "World War I Timeline",
  description: "Major events and developments during the Great War (1914-1918)",
  timeRange: {
    start: 1914,
    end: 1918
  },
  events: [
    {
      id: "1",
      title: "Assassination of Archduke Franz Ferdinand",
      date: "June 28, 1914",
      year: 1914,
      description: "Archduke Franz Ferdinand of Austria-Hungary was assassinated by a Serbian nationalist in Sarajevo, providing the spark that ignited World War I.",
      category: "political" as const,
      significance: "critical" as const,
      location: "Sarajevo, Bosnia-Herzegovina",
      relatedEvents: ["2", "3"],
      sources: ["Primary source documents about the assassination"]
    },
    {
      id: "2",
      title: "Austria-Hungary declares war on Serbia",
      date: "July 28, 1914",
      year: 1914,
      description: "Following the assassination of Archduke Franz Ferdinand, Austria-Hungary declared war on Serbia, beginning World War I.",
      category: "political" as const,
      significance: "critical" as const,
      location: "Vienna, Austria-Hungary",
      relatedEvents: ["1", "3"]
    },
    {
      id: "3",
      title: "Germany declares war on Russia",
      date: "August 1, 1914",
      year: 1914,
      description: "Germany declared war on Russia, escalating the conflict from a regional dispute to a world war.",
      category: "political" as const,
      significance: "critical" as const,
      location: "Berlin, Germany",
      relatedEvents: ["1", "2", "4"]
    },
    {
      id: "4",
      title: "Battle of the Somme",
      date: "July 1 - November 18, 1916",
      year: 1916,
      description: "One of the bloodiest battles in human history, with over one million casualties. The British offensive aimed to break German lines.",
      category: "military" as const,
      significance: "high" as const,
      location: "Somme River, France",
      relatedEvents: ["5"]
    },
    {
      id: "5",
      title: "United States enters the war",
      date: "April 6, 1917",
      year: 1917,
      description: "The United States declared war on Germany, bringing fresh troops and resources to the Allied cause.",
      category: "political" as const,
      significance: "critical" as const,
      location: "Washington, D.C., United States",
      relatedEvents: ["4", "6"]
    },
    {
      id: "6",
      title: "Armistice signed",
      date: "November 11, 1918",
      year: 1918,
      description: "The Armistice was signed, ending hostilities on the Western Front and effectively ending World War I.",
      category: "political" as const,
      significance: "critical" as const,
      location: "Compiègne, France",
      relatedEvents: ["5"]
    }
  ]
}

const availableTimelines = [
  { id: "world-war-1", title: "World War I (1914-1918)", subject: "History", events: 45 },
  { id: "renaissance", title: "Renaissance Period (1300-1600)", subject: "History", events: 78 },
  { id: "colonial-africa", title: "Colonial Africa (1880-1960)", subject: "History", events: 62 },
  { id: "cold-war", title: "Cold War (1945-1991)", subject: "History", events: 89 }
]

export default function TimelinePage() {
  const [selectedTimeline, setSelectedTimeline] = useState(mockTimeline)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTimelineId, setSelectedTimelineId] = useState('world-war-1')

  const handleEventSelect = (event: any) => {
    console.log('Selected event:', event)
    // Here you could open a detail modal or navigate to event details
  }

  const handleTimelineChange = (timelineId: string) => {
    setSelectedTimelineId(timelineId)
    // In a real app, you would fetch the timeline data here
    if (timelineId === 'world-war-1') {
      setSelectedTimeline(mockTimeline)
    }
  }

  const handleCreateTimeline = () => {
    console.log('Create new timeline')
    // Here you would open a timeline creation modal
  }

  const handleExportTimeline = () => {
    console.log('Export timeline')
    // Here you would trigger timeline export
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Interactive Timelines</h1>
          <p className="text-muted-foreground mt-1">
            Explore historical events in chronological context
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={handleExportTimeline}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <Button onClick={handleCreateTimeline}>
            <Plus className="h-4 w-4 mr-2" />
            Create Timeline
          </Button>
        </div>
      </div>

      {/* Timeline Selection and Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Browse Timelines</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <Select value={selectedTimelineId} onValueChange={handleTimelineChange}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a timeline" />
                </SelectTrigger>
                <SelectContent>
                  {availableTimelines.map(timeline => (
                    <SelectItem key={timeline.id} value={timeline.id}>
                      <div className="flex items-center justify-between w-full">
                        <span>{timeline.title}</span>
                        <Badge variant="outline" className="ml-2">
                          {timeline.events} events
                        </Badge>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                <Input
                  placeholder="Search events..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 w-64"
                />
              </div>
              <Button variant="outline" size="sm">
                <Filter className="h-4 w-4 mr-2" />
                Filters
              </Button>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="flex items-center gap-4 mt-4 pt-4 border-t">
            <div className="text-sm">
              <span className="text-muted-foreground">Events:</span>
              <span className="ml-1 font-medium">{selectedTimeline.events.length}</span>
            </div>
            <div className="text-sm">
              <span className="text-muted-foreground">Time Span:</span>
              <span className="ml-1 font-medium">
                {selectedTimeline.timeRange.end - selectedTimeline.timeRange.start} years
              </span>
            </div>
            <div className="text-sm">
              <span className="text-muted-foreground">Categories:</span>
              <span className="ml-1 font-medium">
                {Array.from(new Set(selectedTimeline.events.map(e => e.category))).length}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Timeline Visualization */}
      <TimelineViewer
        timeline={selectedTimeline}
        onEventSelect={handleEventSelect}
        className="min-h-[600px]"
      />
      
      {/* Timeline Templates */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Popular Timeline Templates</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {availableTimelines.map(timeline => (
              <Card 
                key={timeline.id}
                className={`cursor-pointer transition-colors hover:bg-muted/50 ${
                  selectedTimelineId === timeline.id ? 'ring-2 ring-primary' : ''
                }`}
                onClick={() => handleTimelineChange(timeline.id)}
              >
                <CardHeader className="pb-2">
                  <div className="text-sm font-medium line-clamp-2">
                    {timeline.title}
                  </div>
                  <Badge variant="secondary" className="w-fit">
                    {timeline.subject}
                  </Badge>
                </CardHeader>
                <CardContent>
                  <div className="text-xs text-muted-foreground">
                    {timeline.events} events
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Study Tips */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Timeline Study Tips</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <h4 className="font-medium">Understanding Context</h4>
              <p className="text-sm text-muted-foreground">
                Pay attention to how events connect and influence each other over time.
              </p>
            </div>
            <div className="space-y-2">
              <h4 className="font-medium">Event Significance</h4>
              <p className="text-sm text-muted-foreground">
                Notice the size of event markers - they indicate historical significance.
              </p>
            </div>
            <div className="space-y-2">
              <h4 className="font-medium">Multiple Perspectives</h4>
              <p className="text-sm text-muted-foreground">
                Consider how different groups might have experienced the same events differently.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}