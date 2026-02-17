"use client";

import { useState, useEffect, useCallback, useMemo } from 'react';
import { Timeline, HistoricalEvent, TimelineFilters, getTimelines, getTimeline, getEvents, generateTimeline } from '@/lib/api/history';

export interface TimelineHookState {
  timelines: Timeline[];
  currentTimeline: Timeline | null;
  events: HistoricalEvent[];
  filteredEvents: HistoricalEvent[];
  selectedEvent: HistoricalEvent | null;
  isLoading: boolean;
  error: string | null;
}

export interface ZoomLevel {
  value: string;
  label: string;
  scale: number;
}

const ZOOM_LEVELS: ZoomLevel[] = [
  { value: 'century', label: 'Century', scale: 100 },
  { value: 'decade', label: 'Decade', scale: 10 },
  { value: 'year', label: 'Year', scale: 1 },
  { value: 'month', label: 'Month', scale: 1/12 },
];

export const useTimeline = (initialTopic?: string) => {
  const [state, setState] = useState<TimelineHookState>({
    timelines: [],
    currentTimeline: null,
    events: [],
    filteredEvents: [],
    selectedEvent: null,
    isLoading: false,
    error: null,
  });

  const [filters, setFilters] = useState<TimelineFilters>({});
  const [zoomLevel, setZoomLevel] = useState<string>('decade');
  const [timeRange, setTimeRange] = useState<{ start: Date; end: Date } | null>(null);

  // Load timelines for a topic
  const loadTimelines = useCallback(async (topic?: string) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const timelines = await getTimelines(topic);
      setState(prev => ({ 
        ...prev, 
        timelines, 
        isLoading: false 
      }));
      
      // Auto-select first timeline if available
      if (timelines.length > 0 && !state.currentTimeline) {
        loadTimeline(timelines[0].id);
      }
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        error: 'Failed to load timelines', 
        isLoading: false 
      }));
    }
  }, [state.currentTimeline]);

  // Load specific timeline
  const loadTimeline = useCallback(async (timelineId: string) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const timeline = await getTimeline(timelineId);
      
      setState(prev => ({ 
        ...prev, 
        currentTimeline: timeline,
        events: timeline.events,
        isLoading: false 
      }));
      
      // Set time range based on timeline events
      if (timeline.events.length > 0) {
        const dates = timeline.events.map(e => new Date(e.date));
        const minDate = new Date(Math.min(...dates.map(d => d.getTime())));
        const maxDate = new Date(Math.max(...dates.map(d => d.getTime())));
        setTimeRange({ start: minDate, end: maxDate });
      }
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        error: 'Failed to load timeline', 
        isLoading: false 
      }));
    }
  }, []);

  // Load events with filters
  const loadEvents = useCallback(async (eventFilters?: TimelineFilters) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const events = await getEvents(eventFilters || filters);
      setState(prev => ({ 
        ...prev, 
        events, 
        isLoading: false 
      }));
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        error: 'Failed to load events', 
        isLoading: false 
      }));
    }
  }, [filters]);

  // Generate new timeline
  const generateNewTimeline = useCallback(async (topic: string, timeRange?: { start: string; end: string }) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const newTimeline = await generateTimeline(topic, timeRange);
      setState(prev => ({ 
        ...prev, 
        currentTimeline: newTimeline,
        events: newTimeline.events,
        timelines: [newTimeline, ...prev.timelines],
        isLoading: false 
      }));
      
      return newTimeline;
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        error: 'Failed to generate timeline', 
        isLoading: false 
      }));
      throw error;
    }
  }, []);

  // Filter events based on current filters and zoom level
  const filteredEvents = useMemo(() => {
    let filtered = [...state.events];
    
    // Apply filters
    if (filters.startDate) {
      filtered = filtered.filter(event => new Date(event.date) >= new Date(filters.startDate!));
    }
    
    if (filters.endDate) {
      filtered = filtered.filter(event => new Date(event.date) <= new Date(filters.endDate!));
    }
    
    if (filters.categories && filters.categories.length > 0) {
      filtered = filtered.filter(event => filters.categories!.includes(event.category));
    }
    
    if (filters.minImportance !== undefined) {
      filtered = filtered.filter(event => event.importance >= filters.minImportance!);
    }
    
    if (filters.tags && filters.tags.length > 0) {
      filtered = filtered.filter(event => 
        filters.tags!.some(tag => event.tags.includes(tag))
      );
    }
    
    if (filters.verified !== undefined) {
      filtered = filtered.filter(event => event.verified === filters.verified);
    }
    
    // Apply zoom level filtering
    if (timeRange && zoomLevel) {
      const zoomConfig = ZOOM_LEVELS.find(z => z.value === zoomLevel);
      if (zoomConfig) {
        // Additional filtering based on zoom level could be implemented here
        // For now, we'll keep all events in range
      }
    }
    
    // Sort by date
    return filtered.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  }, [state.events, filters, zoomLevel, timeRange]);

  // Update filtered events in state
  useEffect(() => {
    setState(prev => ({ ...prev, filteredEvents }));
  }, [filteredEvents]);

  // Select event
  const selectEvent = useCallback((event: HistoricalEvent | null) => {
    setState(prev => ({ ...prev, selectedEvent: event }));
  }, []);

  // Update filters
  const updateFilters = useCallback((newFilters: Partial<TimelineFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  }, []);

  // Clear filters
  const clearFilters = useCallback(() => {
    setFilters({});
  }, []);

  // Update zoom level
  const updateZoomLevel = useCallback((level: string) => {
    setZoomLevel(level);
  }, []);

  // Update time range
  const updateTimeRange = useCallback((range: { start: Date; end: Date }) => {
    setTimeRange(range);
  }, []);

  // Reset timeline view
  const resetView = useCallback(() => {
    setZoomLevel('decade');
    setTimeRange(null);
    clearFilters();
    selectEvent(null);
  }, [clearFilters, selectEvent]);

  // Initialize with topic if provided
  useEffect(() => {
    if (initialTopic) {
      loadTimelines(initialTopic);
    }
  }, [initialTopic, loadTimelines]);

  // Get categories from current events
  const availableCategories = useMemo(() => {
    const categories = state.events.map(event => event.category);
    return [...new Set(categories)];
  }, [state.events]);

  // Get tags from current events
  const availableTags = useMemo(() => {
    const tags = state.events.flatMap(event => event.tags);
    return [...new Set(tags)];
  }, [state.events]);

  // Get date range from events
  const eventDateRange = useMemo(() => {
    if (state.events.length === 0) return null;
    
    const dates = state.events.map(e => new Date(e.date));
    return {
      start: new Date(Math.min(...dates.map(d => d.getTime()))),
      end: new Date(Math.max(...dates.map(d => d.getTime()))),
    };
  }, [state.events]);

  return {
    // State
    ...state,
    filters,
    zoomLevel,
    timeRange,
    availableCategories,
    availableTags,
    eventDateRange,
    zoomLevels: ZOOM_LEVELS,
    
    // Actions
    loadTimelines,
    loadTimeline,
    loadEvents,
    generateNewTimeline,
    selectEvent,
    updateFilters,
    clearFilters,
    updateZoomLevel,
    updateTimeRange,
    resetView,
  };
};