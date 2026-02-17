'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { ZoomIn, ZoomOut, Calendar, MapPin, Users, Swords, Crown, BookOpen } from 'lucide-react'

interface TimelineEvent {
  id: string
  title: string
  date: string
  year: number
  description: string
  category: 'political' | 'military' | 'social' | 'economic' | 'cultural' | 'religious'
  significance: 'low' | 'medium' | 'high' | 'critical'
  location?: string
  relatedEvents?: string[]
  sources?: string[]
}

interface TimelineData {
  id: string
  title: string
  description: string
  timeRange: {
    start: number
    end: number
  }
  events: TimelineEvent[]
}

interface TimelineViewerProps {
  timeline: TimelineData
  onEventSelect?: (event: TimelineEvent) => void
  className?: string
}

const categoryIcons = {
  political: Crown,
  military: Swords,
  social: Users,
  economic: MapPin,
  cultural: BookOpen,
  religious: Calendar
}

const categoryColors = {
  political: 'bg-purple-500',
  military: 'bg-red-500',
  social: 'bg-blue-500',
  economic: 'bg-green-500',
  cultural: 'bg-yellow-500',
  religious: 'bg-indigo-500'
}

const significanceSize = {
  low: 'h-3 w-3',
  medium: 'h-4 w-4',
  high: 'h-5 w-5',
  critical: 'h-6 w-6'
}

export function TimelineViewer({ timeline, onEventSelect, className }: TimelineViewerProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [zoomLevel, setZoomLevel] = useState<number>(1)
  const [selectedEvent, setSelectedEvent] = useState<TimelineEvent | null>(null)
  const timelineRef = useRef<HTMLDivElement>(null)
  
  const { start: startYear, end: endYear } = timeline.timeRange
  const totalYears = endYear - startYear
  
  // Filter events by category
  const filteredEvents = timeline.events.filter(event => 
    selectedCategory === 'all' || event.category === selectedCategory
  )
  
  // Get unique categories
  const categories = Array.from(new Set(timeline.events.map(e => e.category)))
  
  const handleZoomIn = () => {
    setZoomLevel(prev => Math.min(prev * 1.5, 5))
  }
  
  const handleZoomOut = () => {
    setZoomLevel(prev => Math.max(prev / 1.5, 0.5))
  }
  
  const getEventPosition = (year: number) => {
    const yearProgress = (year - startYear) / totalYears
    return `${yearProgress * 100}%`
  }
  
  const handleEventClick = (event: TimelineEvent) => {
    setSelectedEvent(event)
    onEventSelect?.(event)
  }
  
  return (
    <div className={`space-y-4 ${className}`}>
      {/* Timeline Header */}
      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                {timeline.title}
              </CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                {timeline.description}
              </p>
              <Badge variant="outline" className="mt-2">
                {startYear} - {endYear} ({totalYears} years)
              </Badge>
            </div>
            
            <div className="flex items-center gap-2">
              <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="All categories" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  {categories.map(category => (
                    <SelectItem key={category} value={category}>
                      {category.charAt(0).toUpperCase() + category.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              <Button variant="outline" size="sm" onClick={handleZoomOut}>
                <ZoomOut className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm" onClick={handleZoomIn}>
                <ZoomIn className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>
      
      {/* Timeline Visualization */}
      <Card className="overflow-hidden">
        <CardContent className="p-0">
          <ScrollArea className="w-full">
            <div 
              ref={timelineRef}
              className="relative p-8 min-w-full"
              style={{ width: `${100 * zoomLevel}%` }}
            >
              {/* Main Timeline Line */}
              <div className="relative">
                {/* Timeline base line */}
                <div className="absolute top-1/2 left-0 right-0 h-1 bg-border rounded-full" />
                
                {/* Year markers */}
                <div className="relative">
                  {Array.from({ length: Math.ceil(totalYears / 10) + 1 }, (_, i) => {
                    const year = startYear + (i * 10)
                    if (year > endYear) return null
                    
                    return (
                      <div
                        key={year}
                        className="absolute flex flex-col items-center"
                        style={{ left: getEventPosition(year) }}
                      >
                        <div className="w-2 h-2 bg-muted-foreground rounded-full -translate-y-1/2" />
                        <span className="text-xs text-muted-foreground mt-2 font-mono">
                          {year}
                        </span>
                      </div>
                    )
                  })}
                </div>
                
                {/* Events */}
                <div className="relative pt-12 pb-8">
                  {filteredEvents.map((event, index) => {
                    const Icon = categoryIcons[event.category]
                    const isAbove = index % 2 === 0
                    
                    return (
                      <div
                        key={event.id}
                        className={`absolute flex flex-col items-center cursor-pointer transition-transform hover:scale-110 ${
                          isAbove ? '-translate-y-full' : 'translate-y-full'
                        }`}
                        style={{ left: getEventPosition(event.year) }}
                        onClick={() => handleEventClick(event)}
                      >
                        {/* Connection line */}
                        <div
                          className={`w-px bg-border ${
                            isAbove ? 'h-8 order-2' : 'h-8 order-1'
                          }`}
                        />
                        
                        {/* Event marker */}
                        <div
                          className={`${
                            categoryColors[event.category]
                          } ${
                            significanceSize[event.significance]
                          } rounded-full border-2 border-background shadow-sm ${
                            isAbove ? 'order-1' : 'order-2'
                          } ${
                            selectedEvent?.id === event.id ? 'ring-2 ring-primary ring-offset-2' : ''
                          }`}
                        >
                          <Icon className="h-full w-full p-0.5 text-white" />
                        </div>
                        
                        {/* Event card */}
                        <div
                          className={`bg-background border rounded-lg shadow-sm p-3 max-w-xs ${
                            isAbove ? 'order-0 mb-2' : 'order-3 mt-2'
                          }`}
                        >
                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <Badge
                                variant="outline"
                                className="text-xs"
                              >
                                {event.year}
                              </Badge>
                              <Badge
                                variant="secondary"
                                className="text-xs"
                              >
                                {event.category}
                              </Badge>
                            </div>
                            
                            <h4 className="font-medium text-sm leading-tight">
                              {event.title}
                            </h4>
                            
                            <p className="text-xs text-muted-foreground line-clamp-2">
                              {event.description}
                            </p>
                            
                            {event.location && (
                              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                <MapPin className="h-3 w-3" />
                                {event.location}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
      
      {/* Event Detail Panel */}
      {selectedEvent && (
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  {React.createElement(categoryIcons[selectedEvent.category], {
                    className: "h-5 w-5"
                  })}
                  {selectedEvent.title}
                </CardTitle>
                <div className="flex items-center gap-2 mt-2">
                  <Badge>{selectedEvent.year}</Badge>
                  <Badge variant="secondary">{selectedEvent.category}</Badge>
                  <Badge variant="outline">{selectedEvent.significance} significance</Badge>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedEvent(null)}
              >
                ×
              </Button>
            </div>
          </CardHeader>
          
          <CardContent className="space-y-4">
            <p className="text-sm leading-relaxed">
              {selectedEvent.description}
            </p>
            
            {selectedEvent.location && (
              <div className="flex items-center gap-2 text-sm">
                <MapPin className="h-4 w-4 text-muted-foreground" />
                <span>{selectedEvent.location}</span>
              </div>
            )}
            
            {selectedEvent.relatedEvents && selectedEvent.relatedEvents.length > 0 && (
              <div>
                <h5 className="font-medium mb-2">Related Events</h5>
                <div className="flex flex-wrap gap-1">
                  {selectedEvent.relatedEvents.map(eventId => {
                    const relatedEvent = timeline.events.find(e => e.id === eventId)
                    return relatedEvent ? (
                      <Button
                        key={eventId}
                        variant="outline"
                        size="sm"
                        className="text-xs"
                        onClick={() => handleEventClick(relatedEvent)}
                      >
                        {relatedEvent.title}
                      </Button>
                    ) : null
                  })}
                </div>
              </div>
            )}
            
            {selectedEvent.sources && selectedEvent.sources.length > 0 && (
              <div>
                <h5 className="font-medium mb-2">Sources</h5>
                <div className="space-y-1">
                  {selectedEvent.sources.map((source, index) => (
                    <p key={index} className="text-xs text-muted-foreground">
                      {source}
                    </p>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
      
      {/* Category Legend */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Legend</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {categories.map(category => {
              const Icon = categoryIcons[category]
              return (
                <div key={category} className="flex items-center gap-2">
                  <div className={`${categoryColors[category]} h-3 w-3 rounded-full`}>
                    <Icon className="h-full w-full p-0.5 text-white" />
                  </div>
                  <span className="text-sm capitalize">
                    {category}
                  </span>
                </div>
              )
            })}
          </div>
          
          <div className="mt-4 pt-4 border-t">
            <h5 className="font-medium mb-2">Event Significance</h5>
            <div className="flex items-center gap-6 text-sm">
              <div className="flex items-center gap-2">
                <div className="h-3 w-3 bg-muted rounded-full" />
                <span>Low</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-4 w-4 bg-muted rounded-full" />
                <span>Medium</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-5 w-5 bg-muted rounded-full" />
                <span>High</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-6 w-6 bg-muted rounded-full" />
                <span>Critical</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}