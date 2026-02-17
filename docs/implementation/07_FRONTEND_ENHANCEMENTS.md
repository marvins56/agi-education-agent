# Frontend Enhancements Implementation

**Document:** 07_FRONTEND_ENHANCEMENTS.md  
**Version:** 1.0  
**Date:** February 17, 2026  
**Dependencies:** React, TypeScript, D3.js, Material-UI, WebSocket, WebRTC  

---

## Overview

This document details the implementation of comprehensive frontend enhancements for EduAGI, including voice chat UI, interactive timeline visualization, primary source analysis components, enhanced dashboard with learning analytics, and mobile-responsive design.

## Architecture Design

### Frontend Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ PRESENTATION LAYER           STATE MANAGEMENT                   │
│                                                                 │
│ ┌─────────────────────┐     ┌─────────────────────┐             │
│ │ VOICE CHAT UI       │     │ GLOBAL STATE        │             │
│ │ • Voice Controls    │────►│ • User Session     │             │
│ │ • Audio Visualizer  │     │ • Voice State      │             │
│ │ • Conversation Flow │     │ • Chat History     │             │
│ │ • Real-time Status  │     │ • Learning Data    │             │
│ └─────────────────────┘     └─────────────────────┘             │
│                                                                 │
│ ┌─────────────────────┐     ┌─────────────────────┐             │
│ │ TIMELINE VIEWER     │     │ API CLIENT          │             │
│ │ • D3.js Rendering   │────►│ • RESTful APIs      │             │
│ │ • Interactive Zoom  │     │ • WebSocket Mgmt    │             │
│ │ • Event Details     │     │ • Cache Layer       │             │
│ │ • Causal Links      │     │ • Error Handling    │             │
│ └─────────────────────┘     └─────────────────────┘             │
│                                                                 │
│ ┌─────────────────────┐     ┌─────────────────────┐             │
│ │ SOURCE ANALYZER     │     │ COMPONENT LIBRARY   │             │
│ │ • Document Viewer   │────►│ • UI Components     │             │
│ │ • Annotation Tools  │     │ • Custom Hooks      │             │
│ │ • Analysis Panel    │     │ • Utility Functions │             │
│ │ • Compare Mode      │     │ • Theme System      │             │
│ └─────────────────────┘     └─────────────────────┘             │
│                                                                 │
│ ┌─────────────────────┐     ┌─────────────────────┐             │
│ │ ANALYTICS DASHBOARD │     │ RESPONSIVE SYSTEM   │             │
│ │ • Progress Charts   │────►│ • Mobile First      │             │
│ │ • Skill Tracking    │     │ • Adaptive Layout   │             │
│ │ • Performance Views │     │ • Touch Support     │             │
│ │ • Goal Setting      │     │ • Offline Ready     │             │
│ └─────────────────────┘     └─────────────────────┘             │
│                                                                 │
│                    ROUTING & NAVIGATION                         │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ • Dynamic Routes     • Protected Routes   • Deep Linking   │ │
│ │ • Navigation Guards  • Route Preloading  • SEO Friendly   │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Structure and Components

### Enhanced Directory Structure
```
frontend/src/
├── components/
│   ├── voice/
│   │   ├── VoiceChat.tsx              # Main voice chat interface
│   │   ├── VoiceControls.tsx          # Voice control buttons
│   │   ├── AudioVisualizer.tsx        # Real-time audio visualization
│   │   ├── ConversationFlow.tsx       # Conversation state display
│   │   └── VoiceSettings.tsx          # Voice preferences
│   ├── timeline/
│   │   ├── InteractiveTimeline.tsx    # Main timeline component
│   │   ├── TimelineZoom.tsx           # Zoom controls
│   │   ├── EventDetails.tsx           # Event detail panels
│   │   ├── CausalConnections.tsx      # Causal relationship display
│   │   └── TimelineControls.tsx       # Timeline navigation
│   ├── sources/
│   │   ├── SourceAnalyzer.tsx         # Primary source analysis
│   │   ├── DocumentViewer.tsx         # Document display
│   │   ├── AnnotationTools.tsx        # Annotation interface
│   │   ├── BiasIndicator.tsx          # Bias detection display
│   │   └── SourceComparison.tsx       # Multi-source comparison
│   ├── dashboard/
│   │   ├── LearningDashboard.tsx      # Main dashboard
│   │   ├── ProgressCharts.tsx         # Progress visualization
│   │   ├── SkillTracker.tsx           # Historical thinking skills
│   │   ├── ActivityFeed.tsx           # Recent learning activities
│   │   └── GoalSetting.tsx            # Learning goal management
│   ├── assessment/
│   │   ├── QuestionRenderer.tsx       # Render different question types
│   │   ├── EssayEditor.tsx            # Essay writing interface
│   │   ├── FeedbackDisplay.tsx        # Assessment feedback
│   │   └── ProgressTracker.tsx        # Assessment progress
│   ├── layout/
│   │   ├── AppLayout.tsx              # Main application layout
│   │   ├── Navigation.tsx             # Enhanced navigation
│   │   ├── Sidebar.tsx                # Collapsible sidebar
│   │   └── MobileNav.tsx              # Mobile-optimized navigation
│   └── common/
│       ├── LoadingStates.tsx          # Loading indicators
│       ├── ErrorBoundary.tsx          # Error handling
│       ├── ToastSystem.tsx            # Notification system
│       └── ConfirmDialog.tsx          # Confirmation dialogs
├── hooks/
│   ├── useVoiceChat.tsx               # Voice chat functionality
│   ├── useTimeline.tsx                # Timeline data management
│   ├── useSourceAnalysis.tsx          # Source analysis hooks
│   ├── useAnalytics.tsx               # Analytics data hooks
│   └── useResponsive.tsx              # Responsive utilities
├── store/
│   ├── slices/
│   │   ├── voiceSlice.ts              # Voice chat state
│   │   ├── timelineSlice.ts           # Timeline state
│   │   ├── sourceSlice.ts             # Source analysis state
│   │   ├── dashboardSlice.ts          # Dashboard state
│   │   └── userSlice.ts               # User preferences
│   └── store.ts                       # Redux store configuration
├── services/
│   ├── voiceService.ts                # Voice API integration
│   ├── timelineService.ts             # Timeline data service
│   ├── sourceService.ts               # Source analysis service
│   ├── analyticsService.ts            # Analytics API service
│   └── websocketService.ts            # WebSocket management
├── utils/
│   ├── audioUtils.ts                  # Audio processing utilities
│   ├── timelineUtils.ts               # Timeline calculations
│   ├── formatUtils.ts                 # Data formatting
│   └── responsiveUtils.ts             # Responsive helpers
└── styles/
    ├── themes/
    │   ├── lightTheme.ts              # Light theme
    │   ├── darkTheme.ts               # Dark theme
    │   └── highContrast.ts            # Accessibility theme
    ├── components/
    │   ├── voice.scss                 # Voice component styles
    │   ├── timeline.scss              # Timeline component styles
    │   └── dashboard.scss             # Dashboard styles
    └── globals.scss                   # Global styles
```

---

## Core Component Implementations

### 1. Voice Chat Interface

#### `frontend/src/components/voice/VoiceChat.tsx`
```typescript
import React, { useEffect, useRef, useState, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Chip,
  LinearProgress,
  Fade,
  Zoom
} from '@mui/material';
import {
  Mic,
  MicOff,
  VolumeUp,
  Settings,
  Close,
  Pause,
  PlayArrow
} from '@mui/icons-material';
import { useVoiceChat } from '../../hooks/useVoiceChat';
import { AudioVisualizer } from './AudioVisualizer';
import { ConversationFlow } from './ConversationFlow';
import { VoiceSettings } from './VoiceSettings';

interface VoiceChatProps {
  sessionId: string;
  onClose: () => void;
  isOpen: boolean;
}

export const VoiceChat: React.FC<VoiceChatProps> = ({
  sessionId,
  onClose,
  isOpen
}) => {
  const {
    isConnected,
    isListening,
    isSpeaking,
    conversationState,
    transcription,
    voiceResponse,
    audioLevel,
    error,
    connect,
    disconnect,
    startListening,
    stopListening,
    pauseSpeaking,
    resumeSpeaking,
    updateSettings
  } = useVoiceChat(sessionId);

  const [showSettings, setShowSettings] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    if (isOpen && !isConnected) {
      connect();
    }
    
    return () => {
      if (isConnected) {
        disconnect();
      }
    };
  }, [isOpen, isConnected, connect, disconnect]);

  useEffect(() => {
    // Auto-play voice responses
    if (voiceResponse?.audioData && audioRef.current) {
      const audioBlob = new Blob([
        Uint8Array.from(atob(voiceResponse.audioData), c => c.charCodeAt(0))
      ], { type: 'audio/mpeg' });
      
      const audioUrl = URL.createObjectURL(audioBlob);
      audioRef.current.src = audioUrl;
      audioRef.current.play();
      
      return () => URL.revokeObjectURL(audioUrl);
    }
  }, [voiceResponse]);

  const handleMicToggle = useCallback(() => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [isListening, startListening, stopListening]);

  const getStateColor = (state: string) => {
    switch (state) {
      case 'listening': return 'success';
      case 'thinking': return 'warning';
      case 'speaking': return 'info';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const getStateIcon = (state: string) => {
    switch (state) {
      case 'listening': return <Mic />;
      case 'speaking': return <VolumeUp />;
      case 'thinking': return <Pause />;
      default: return <MicOff />;
    }
  };

  if (!isOpen) return null;

  return (
    <Fade in={isOpen}>
      <Paper
        sx={{
          position: 'fixed',
          bottom: isMinimized ? 16 : 'auto',
          right: 16,
          top: isMinimized ? 'auto' : 16,
          width: isMinimized ? 200 : 400,
          height: isMinimized ? 60 : 600,
          zIndex: 1300,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          transition: 'all 0.3s ease',
        }}
        elevation={8}
      >
        {/* Header */}
        <Box
          sx={{
            p: 2,
            borderBottom: 1,
            borderColor: 'divider',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            bgcolor: 'primary.main',
            color: 'primary.contrastText'
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Zoom in={isConnected}>
              <Box>
                {getStateIcon(conversationState)}
              </Box>
            </Zoom>
            <Typography variant="h6" sx={{ fontSize: isMinimized ? '0.9rem' : '1.1rem' }}>
              Voice Chat
            </Typography>
            <Chip
              label={conversationState}
              color={getStateColor(conversationState) as any}
              size="small"
              sx={{ color: 'white' }}
            />
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <IconButton
              onClick={() => setIsMinimized(!isMinimized)}
              size="small"
              sx={{ color: 'inherit' }}
            >
              {isMinimized ? <PlayArrow /> : <Pause />}
            </IconButton>
            <IconButton
              onClick={() => setShowSettings(!showSettings)}
              size="small"
              sx={{ color: 'inherit' }}
            >
              <Settings />
            </IconButton>
            <IconButton
              onClick={onClose}
              size="small"
              sx={{ color: 'inherit' }}
            >
              <Close />
            </IconButton>
          </Box>
        </Box>

        {!isMinimized && (
          <>
            {/* Connection Status */}
            {!isConnected && (
              <Box sx={{ p: 1 }}>
                <LinearProgress />
                <Typography variant="caption" sx={{ textAlign: 'center', display: 'block', mt: 1 }}>
                  Connecting to voice services...
                </Typography>
              </Box>
            )}

            {/* Error Display */}
            {error && (
              <Box sx={{ p: 2, bgcolor: 'error.light', color: 'error.contrastText' }}>
                <Typography variant="body2">{error}</Typography>
              </Box>
            )}

            {/* Main Content */}
            <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              {/* Audio Visualizer */}
              <Box sx={{ height: 80, p: 1 }}>
                <AudioVisualizer
                  audioLevel={audioLevel}
                  isListening={isListening}
                  isSpeaking={isSpeaking}
                />
              </Box>

              {/* Conversation Flow */}
              <Box sx={{ flex: 1, overflow: 'auto' }}>
                <ConversationFlow
                  transcription={transcription}
                  voiceResponse={voiceResponse}
                  conversationState={conversationState}
                />
              </Box>

              {/* Controls */}
              <Box
                sx={{
                  p: 2,
                  borderTop: 1,
                  borderColor: 'divider',
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  gap: 2
                }}
              >
                <IconButton
                  onClick={handleMicToggle}
                  color={isListening ? 'secondary' : 'primary'}
                  size="large"
                  sx={{
                    width: 64,
                    height: 64,
                    bgcolor: isListening ? 'secondary.light' : 'primary.light',
                    '&:hover': {
                      bgcolor: isListening ? 'secondary.main' : 'primary.main',
                    }
                  }}
                  disabled={!isConnected}
                >
                  {isListening ? <MicOff /> : <Mic />}
                </IconButton>

                {isSpeaking && (
                  <IconButton
                    onClick={pauseSpeaking}
                    color="info"
                    size="medium"
                  >
                    <Pause />
                  </IconButton>
                )}
              </Box>
            </Box>

            {/* Settings Panel */}
            <VoiceSettings
              open={showSettings}
              onClose={() => setShowSettings(false)}
              onSettingsUpdate={updateSettings}
            />
          </>
        )}

        {/* Hidden audio element for playback */}
        <audio ref={audioRef} style={{ display: 'none' }} />
      </Paper>
    </Fade>
  );
};
```

#### `frontend/src/components/voice/AudioVisualizer.tsx`
```typescript
import React, { useEffect, useRef, useState } from 'react';
import { Box } from '@mui/material';

interface AudioVisualizerProps {
  audioLevel: number;
  isListening: boolean;
  isSpeaking: boolean;
}

export const AudioVisualizer: React.FC<AudioVisualizerProps> = ({
  audioLevel,
  isListening,
  isSpeaking
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();
  const [bars, setBars] = useState<number[]>(new Array(32).fill(0));

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const animate = () => {
      // Clear canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      const barWidth = canvas.width / bars.length;
      
      bars.forEach((height, index) => {
        const x = index * barWidth;
        const normalizedHeight = height * canvas.height;
        
        // Color based on state
        let color = '#e0e0e0'; // Default gray
        if (isListening) {
          color = '#4caf50'; // Green for listening
        } else if (isSpeaking) {
          color = '#2196f3'; // Blue for speaking
        }
        
        // Gradient effect
        const gradient = ctx.createLinearGradient(0, canvas.height, 0, canvas.height - normalizedHeight);
        gradient.addColorStop(0, color);
        gradient.addColorStop(1, color + '40');
        
        ctx.fillStyle = gradient;
        ctx.fillRect(x, canvas.height - normalizedHeight, barWidth - 2, normalizedHeight);
      });
      
      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [bars, isListening, isSpeaking]);

  useEffect(() => {
    // Update bars based on audio level
    if (isListening || isSpeaking) {
      const newBars = bars.map((_, index) => {
        // Create wave pattern with some randomness
        const wave = Math.sin((Date.now() / 1000) * 2 + index * 0.5) * 0.5 + 0.5;
        const randomVariation = Math.random() * 0.3;
        const baseLevel = audioLevel * (wave + randomVariation);
        
        return Math.min(1, baseLevel);
      });
      
      setBars(newBars);
    } else {
      // Decay bars when not active
      setBars(prev => prev.map(bar => Math.max(0, bar * 0.9)));
    }
  }, [audioLevel, isListening, isSpeaking]);

  return (
    <Box
      sx={{
        width: '100%',
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'grey.100',
        borderRadius: 1,
        overflow: 'hidden'
      }}
    >
      <canvas
        ref={canvasRef}
        width={300}
        height={60}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'contain'
        }}
      />
    </Box>
  );
};
```

### 2. Interactive Timeline Component

#### `frontend/src/components/timeline/InteractiveTimeline.tsx`
```typescript
import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Box, Paper, Typography, IconButton, Tooltip, Zoom } from '@mui/material';
import { ZoomIn, ZoomOut, FullscreenExit, Fullscreen, FilterList } from '@mui/icons-material';
import * as d3 from 'd3';
import { useTimeline } from '../../hooks/useTimeline';
import { TimelineZoom } from './TimelineZoom';
import { EventDetails } from './EventDetails';
import { CausalConnections } from './CausalConnections';

interface HistoricalEvent {
  id: string;
  title: string;
  date: Date;
  description: string;
  importance: number;
  category: string;
  connections: string[];
}

interface InteractiveTimelineProps {
  topic: string;
  events: HistoricalEvent[];
  onEventSelect: (event: HistoricalEvent | null) => void;
  selectedEventId?: string;
  showConnections?: boolean;
  height?: number;
}

export const InteractiveTimeline: React.FC<InteractiveTimelineProps> = ({
  topic,
  events,
  onEventSelect,
  selectedEventId,
  showConnections = true,
  height = 400
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [selectedEvent, setSelectedEvent] = useState<HistoricalEvent | null>(null);
  const [zoomLevel, setZoomLevel] = useState('decade');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [dimensions, setDimensions] = useState({ width: 800, height });

  const {
    timeRange,
    filteredEvents,
    zoomTransform,
    updateZoomLevel,
    updateTimeRange,
    resetZoom
  } = useTimeline(events, zoomLevel);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setDimensions({
          width: rect.width,
          height: isFullscreen ? window.innerHeight - 100 : height
        });
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [isFullscreen, height]);

  // D3 Timeline Rendering
  useEffect(() => {
    if (!svgRef.current || filteredEvents.length === 0) return;

    const svg = d3.select(svgRef.current);
    const margin = { top: 60, right: 60, bottom: 60, left: 60 };
    const innerWidth = dimensions.width - margin.left - margin.right;
    const innerHeight = dimensions.height - margin.top - margin.bottom;

    // Clear previous content
    svg.selectAll('*').remove();

    // Create scales
    const xScale = d3.scaleTime()
      .domain(d3.extent(filteredEvents, d => d.date) as [Date, Date])
      .range([0, innerWidth]);

    const yScale = d3.scaleOrdinal()
      .domain([...new Set(filteredEvents.map(d => d.category))])
      .range(d3.range(0, innerHeight, innerHeight / [...new Set(filteredEvents.map(d => d.category))].length));

    // Create main group
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Add axes
    const xAxis = d3.axisBottom(xScale)
      .tickFormat(d3.timeFormat('%Y'))
      .ticks(10);

    g.append('g')
      .attr('class', 'x-axis')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(xAxis)
      .selectAll('text')
      .style('font-size', '12px');

    // Add timeline line
    g.append('line')
      .attr('class', 'timeline-line')
      .attr('x1', 0)
      .attr('y1', innerHeight / 2)
      .attr('x2', innerWidth)
      .attr('y2', innerHeight / 2)
      .attr('stroke', '#ddd')
      .attr('stroke-width', 2);

    // Color scale for categories
    const colorScale = d3.scaleOrdinal(d3.schemeSet3);

    // Add events
    const eventGroups = g.selectAll('.event-group')
      .data(filteredEvents)
      .enter()
      .append('g')
      .attr('class', 'event-group')
      .attr('transform', d => `translate(${xScale(d.date)}, ${yScale(d.category)})`);

    // Event circles
    eventGroups.append('circle')
      .attr('class', 'event-circle')
      .attr('r', d => 4 + (d.importance * 8))
      .attr('fill', d => colorScale(d.category))
      .attr('stroke', d => selectedEventId === d.id ? '#1976d2' : '#fff')
      .attr('stroke-width', d => selectedEventId === d.id ? 3 : 2)
      .style('cursor', 'pointer')
      .on('click', (event, d) => {
        setSelectedEvent(selectedEvent?.id === d.id ? null : d);
        onEventSelect(selectedEvent?.id === d.id ? null : d);
      })
      .on('mouseover', function(event, d) {
        d3.select(this)
          .transition()
          .duration(200)
          .attr('r', 6 + (d.importance * 8));
        
        // Show tooltip
        showTooltip(event, d);
      })
      .on('mouseout', function(event, d) {
        d3.select(this)
          .transition()
          .duration(200)
          .attr('r', 4 + (d.importance * 8));
        
        hideTooltip();
      });

    // Event labels
    eventGroups.append('text')
      .attr('class', 'event-label')
      .attr('dy', -15)
      .attr('text-anchor', 'middle')
      .style('font-size', '10px')
      .style('font-weight', 'bold')
      .style('pointer-events', 'none')
      .text(d => d.title.length > 20 ? d.title.substring(0, 20) + '...' : d.title);

    // Add causal connections if enabled
    if (showConnections) {
      drawCausalConnections(g, filteredEvents, xScale, yScale, colorScale);
    }

    // Add zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 10])
      .on('zoom', (event) => {
        g.attr('transform', 
          `translate(${margin.left + event.transform.x},${margin.top + event.transform.y}) scale(${event.transform.k})`
        );
      });

    svg.call(zoom);

  }, [filteredEvents, dimensions, selectedEventId, showConnections, onEventSelect]);

  const drawCausalConnections = (
    g: d3.Selection<SVGGElement, unknown, null, undefined>,
    events: HistoricalEvent[],
    xScale: d3.ScaleTime<number, number>,
    yScale: d3.ScaleOrdinal<string, number>,
    colorScale: d3.ScaleOrdinal<string, string>
  ) => {
    const connections = events.flatMap(event =>
      event.connections.map(connId => {
        const connectedEvent = events.find(e => e.id === connId);
        return connectedEvent ? { source: event, target: connectedEvent } : null;
      }).filter(Boolean)
    );

    g.selectAll('.connection-line')
      .data(connections)
      .enter()
      .append('path')
      .attr('class', 'connection-line')
      .attr('d', d => {
        const sourceX = xScale(d!.source.date);
        const sourceY = yScale(d!.source.category);
        const targetX = xScale(d!.target.date);
        const targetY = yScale(d!.target.category);

        // Create curved path
        const midX = (sourceX + targetX) / 2;
        const midY = (sourceY + targetY) / 2 - 30;

        return `M ${sourceX} ${sourceY} Q ${midX} ${midY} ${targetX} ${targetY}`;
      })
      .attr('fill', 'none')
      .attr('stroke', '#999')
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '5,5')
      .style('opacity', 0.6);
  };

  const showTooltip = (event: any, d: HistoricalEvent) => {
    const tooltip = d3.select('body')
      .selectAll('.timeline-tooltip')
      .data([d]);

    const tooltipEnter = tooltip.enter()
      .append('div')
      .attr('class', 'timeline-tooltip')
      .style('position', 'absolute')
      .style('background', 'rgba(0, 0, 0, 0.8)')
      .style('color', 'white')
      .style('padding', '8px')
      .style('border-radius', '4px')
      .style('font-size', '12px')
      .style('pointer-events', 'none')
      .style('z-index', 1000);

    tooltip.merge(tooltipEnter)
      .html(`
        <strong>${d.title}</strong><br/>
        Date: ${d.date.toLocaleDateString()}<br/>
        Category: ${d.category}<br/>
        ${d.description.substring(0, 100)}...
      `)
      .style('left', `${event.pageX + 10}px`)
      .style('top', `${event.pageY - 10}px`)
      .style('opacity', 1);
  };

  const hideTooltip = () => {
    d3.select('body')
      .selectAll('.timeline-tooltip')
      .style('opacity', 0)
      .remove();
  };

  const handleZoomIn = useCallback(() => {
    if (svgRef.current) {
      const svg = d3.select(svgRef.current);
      svg.transition().call(
        svg.property('zoom').scaleBy, 1.5
      );
    }
  }, []);

  const handleZoomOut = useCallback(() => {
    if (svgRef.current) {
      const svg = d3.select(svgRef.current);
      svg.transition().call(
        svg.property('zoom').scaleBy, 1 / 1.5
      );
    }
  }, []);

  const toggleFullscreen = useCallback(() => {
    setIsFullscreen(!isFullscreen);
  }, [isFullscreen]);

  return (
    <Paper
      sx={{
        position: isFullscreen ? 'fixed' : 'relative',
        top: isFullscreen ? 0 : 'auto',
        left: isFullscreen ? 0 : 'auto',
        right: isFullscreen ? 0 : 'auto',
        bottom: isFullscreen ? 0 : 'auto',
        zIndex: isFullscreen ? 1300 : 1,
        width: isFullscreen ? '100vw' : '100%',
        height: isFullscreen ? '100vh' : height,
        overflow: 'hidden'
      }}
      elevation={isFullscreen ? 24 : 1}
    >
      {/* Header */}
      <Box
        sx={{
          p: 2,
          borderBottom: 1,
          borderColor: 'divider',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          bgcolor: 'primary.main',
          color: 'primary.contrastText'
        }}
      >
        <Typography variant="h6">
          Timeline: {topic}
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Tooltip title="Zoom In">
            <IconButton onClick={handleZoomIn} size="small" sx={{ color: 'inherit' }}>
              <ZoomIn />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Zoom Out">
            <IconButton onClick={handleZoomOut} size="small" sx={{ color: 'inherit' }}>
              <ZoomOut />
            </IconButton>
          </Tooltip>
          
          <Tooltip title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}>
            <IconButton onClick={toggleFullscreen} size="small" sx={{ color: 'inherit' }}>
              {isFullscreen ? <FullscreenExit /> : <Fullscreen />}
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Timeline Container */}
      <Box
        ref={containerRef}
        sx={{
          flex: 1,
          position: 'relative',
          overflow: 'hidden'
        }}
      >
        <svg
          ref={svgRef}
          width={dimensions.width}
          height={dimensions.height - 64} // Account for header
          style={{ display: 'block' }}
        />
      </Box>

      {/* Event Details Panel */}
      {selectedEvent && (
        <Zoom in={!!selectedEvent}>
          <Box
            sx={{
              position: 'absolute',
              top: 80,
              right: 16,
              width: 300,
              maxHeight: 400,
              bgcolor: 'background.paper',
              boxShadow: 3,
              borderRadius: 1,
              overflow: 'hidden'
            }}
          >
            <EventDetails
              event={selectedEvent}
              onClose={() => {
                setSelectedEvent(null);
                onEventSelect(null);
              }}
            />
          </Box>
        </Zoom>
      )}
    </Paper>
  );
};
```

### 3. Learning Dashboard with Analytics

#### `frontend/src/components/dashboard/LearningDashboard.tsx`
```typescript
import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  Avatar,
  IconButton,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material';
import {
  TrendingUp,
  School,
  Assessment,
  Timeline,
  EmojiEvents,
  Settings,
  Refresh
} from '@mui/icons-material';
import { useAnalytics } from '../../hooks/useAnalytics';
import { ProgressCharts } from './ProgressCharts';
import { SkillTracker } from './SkillTracker';
import { ActivityFeed } from './ActivityFeed';
import { GoalSetting } from './GoalSetting';

interface LearningDashboardProps {
  studentId: string;
}

export const LearningDashboard: React.FC<LearningDashboardProps> = ({
  studentId
}) => {
  const [timeRange, setTimeRange] = useState('week');
  const [selectedMetric, setSelectedMetric] = useState('overall');
  
  const {
    analytics,
    progressData,
    skillsData,
    activitiesData,
    achievements,
    goals,
    isLoading,
    error,
    refreshAnalytics
  } = useAnalytics(studentId, timeRange);

  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = async () => {
    setRefreshing(true);
    await refreshAnalytics();
    setRefreshing(false);
  };

  const getGradeColor = (percentage: number) => {
    if (percentage >= 90) return 'success';
    if (percentage >= 80) return 'info';
    if (percentage >= 70) return 'warning';
    return 'error';
  };

  const formatPercentage = (value: number) => `${Math.round(value)}%`;

  if (isLoading) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
        <Typography variant="body2" sx={{ mt: 2, textAlign: 'center' }}>
          Loading your learning analytics...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography color="error" variant="h6">
          Failed to load analytics
        </Typography>
        <Typography variant="body2" sx={{ mt: 1, mb: 2 }}>
          {error}
        </Typography>
        <IconButton onClick={handleRefresh} color="primary">
          <Refresh />
        </IconButton>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3, maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Learning Dashboard
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Track your History learning progress and achievements
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Time Range</InputLabel>
            <Select
              value={timeRange}
              label="Time Range"
              onChange={(e) => setTimeRange(e.target.value)}
            >
              <MenuItem value="week">This Week</MenuItem>
              <MenuItem value="month">This Month</MenuItem>
              <MenuItem value="quarter">This Quarter</MenuItem>
              <MenuItem value="year">This Year</MenuItem>
            </Select>
          </FormControl>
          
          <IconButton
            onClick={handleRefresh}
            disabled={refreshing}
            color="primary"
          >
            <Refresh sx={{ animation: refreshing ? 'spin 1s linear infinite' : 'none' }} />
          </IconButton>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Key Metrics Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%', bgcolor: 'primary.main', color: 'primary.contrastText' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar sx={{ bgcolor: 'primary.dark', mr: 2 }}>
                  <TrendingUp />
                </Avatar>
                <Typography variant="h6">Overall Progress</Typography>
              </Box>
              <Typography variant="h3">
                {formatPercentage(analytics?.overallProgress || 0)}
              </Typography>
              <LinearProgress
                variant="determinate"
                value={analytics?.overallProgress || 0}
                sx={{
                  mt: 1,
                  bgcolor: 'primary.dark',
                  '& .MuiLinearProgress-bar': { bgcolor: 'common.white' }
                }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
                  <School />
                </Avatar>
                <Typography variant="h6">Topics Mastered</Typography>
              </Box>
              <Typography variant="h3">
                {analytics?.topicsMastered || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                out of {analytics?.totalTopics || 0} topics
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar sx={{ bgcolor: 'info.main', mr: 2 }}>
                  <Assessment />
                </Avatar>
                <Typography variant="h6">Assessment Average</Typography>
              </Box>
              <Typography variant="h3">
                {formatPercentage(analytics?.averageAssessmentScore || 0)}
              </Typography>
              <Chip
                label={analytics?.assessmentTrend === 'up' ? 'Improving' : 'Stable'}
                color={analytics?.assessmentTrend === 'up' ? 'success' : 'default'}
                size="small"
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar sx={{ bgcolor: 'warning.main', mr: 2 }}>
                  <Timeline />
                </Avatar>
                <Typography variant="h6">Study Streak</Typography>
              </Box>
              <Typography variant="h3">
                {analytics?.studyStreak || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                days in a row
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Progress Charts */}
        <Grid item xs={12} lg={8}>
          <Paper sx={{ p: 3, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              Learning Progress Over Time
            </Typography>
            <ProgressCharts
              data={progressData}
              timeRange={timeRange}
              selectedMetric={selectedMetric}
              onMetricChange={setSelectedMetric}
            />
          </Paper>
        </Grid>

        {/* Achievements */}
        <Grid item xs={12} lg={4}>
          <Paper sx={{ p: 3, height: 400, overflow: 'auto' }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <EmojiEvents />
              Recent Achievements
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {achievements?.map((achievement, index) => (
                <Card key={index} variant="outlined">
                  <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Avatar sx={{ bgcolor: achievement.color }}>
                        {achievement.icon}
                      </Avatar>
                      <Box>
                        <Typography variant="subtitle2">
                          {achievement.title}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {achievement.description}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {achievement.earnedAt}
                        </Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              )) || (
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                  No achievements yet. Keep learning to earn your first badge!
                </Typography>
              )}
            </Box>
          </Paper>
        </Grid>

        {/* Historical Thinking Skills */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: 350 }}>
            <Typography variant="h6" gutterBottom>
              Historical Thinking Skills
            </Typography>
            <SkillTracker
              skillsData={skillsData}
              onSkillSelect={(skill) => {
                // Navigate to skill-specific activities
                console.log('Selected skill:', skill);
              }}
            />
          </Paper>
        </Grid>

        {/* Activity Feed */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: 350 }}>
            <Typography variant="h6" gutterBottom>
              Recent Learning Activities
            </Typography>
            <ActivityFeed
              activities={activitiesData}
              maxItems={5}
            />
          </Paper>
        </Grid>

        {/* Goal Setting and Progress */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Learning Goals
            </Typography>
            <GoalSetting
              goals={goals}
              onGoalUpdate={(updatedGoals) => {
                // Handle goal updates
                console.log('Updated goals:', updatedGoals);
              }}
            />
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};
```

### 4. Mobile-Responsive Layout System

#### `frontend/src/components/layout/AppLayout.tsx`
```typescript
import React, { useState, useEffect } from 'react';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  useMediaQuery,
  useTheme,
  Fab,
  Zoom,
  Badge
} from '@mui/material';
import {
  Menu as MenuIcon,
  Close as CloseIcon,
  Mic,
  Notifications,
  AccountCircle
} from '@mui/icons-material';
import { useLocation } from 'react-router-dom';
import { Navigation } from './Navigation';
import { MobileNav } from './MobileNav';
import { VoiceChat } from '../voice/VoiceChat';
import { useResponsive } from '../../hooks/useResponsive';
import { useVoiceChat } from '../../hooks/useVoiceChat';

interface AppLayoutProps {
  children: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const theme = useTheme();
  const location = useLocation();
  const { isMobile, isTablet, isDesktop } = useResponsive();
  
  const [mobileOpen, setMobileOpen] = useState(false);
  const [voiceChatOpen, setVoiceChatOpen] = useState(false);
  const [notificationCount, setNotificationCount] = useState(3);
  
  const { isVoiceSupported, hasActiveSession } = useVoiceChat();

  // Drawer width responsive to screen size
  const drawerWidth = isDesktop ? 280 : isTablet ? 240 : 200;

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleVoiceChatToggle = () => {
    setVoiceChatOpen(!voiceChatOpen);
  };

  // Close mobile drawer on route change
  useEffect(() => {
    if (isMobile) {
      setMobileOpen(false);
    }
  }, [location.pathname, isMobile]);

  // Auto-close drawer on desktop
  useEffect(() => {
    if (isDesktop && mobileOpen) {
      setMobileOpen(false);
    }
  }, [isDesktop, mobileOpen]);

  const getPageTitle = () => {
    const pathSegments = location.pathname.split('/').filter(Boolean);
    const lastSegment = pathSegments[pathSegments.length - 1];
    
    const titleMap: { [key: string]: string } = {
      'dashboard': 'Learning Dashboard',
      'chat': 'AI Tutor Chat',
      'timeline': 'Historical Timeline',
      'sources': 'Primary Sources',
      'assessments': 'Assessments',
      'progress': 'Progress Tracking',
      'goals': 'Learning Goals',
      'settings': 'Settings'
    };
    
    return titleMap[lastSegment] || 'EduAGI History Tutor';
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* App Bar */}
      <AppBar
        position="fixed"
        sx={{
          width: { lg: isDesktop ? `calc(100% - ${drawerWidth}px)` : '100%' },
          ml: { lg: isDesktop ? `${drawerWidth}px` : 0 },
          zIndex: theme.zIndex.drawer + 1
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { lg: isDesktop ? 'none' : 'block' } }}
          >
            <MenuIcon />
          </IconButton>
          
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            {getPageTitle()}
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {/* Notifications */}
            <IconButton color="inherit">
              <Badge badgeContent={notificationCount} color="error">
                <Notifications />
              </Badge>
            </IconButton>
            
            {/* Profile */}
            <IconButton color="inherit">
              <AccountCircle />
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Navigation Drawer */}
      <Box
        component="nav"
        sx={{ width: { lg: isDesktop ? drawerWidth : 0 }, flexShrink: { lg: 0 } }}
      >
        {/* Mobile drawer */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better mobile performance
          }}
          sx={{
            display: { xs: 'block', lg: isDesktop ? 'none' : 'block' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
            },
          }}
        >
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', p: 1 }}>
            <IconButton onClick={handleDrawerToggle}>
              <CloseIcon />
            </IconButton>
          </Box>
          {isMobile ? (
            <MobileNav onNavigate={() => setMobileOpen(false)} />
          ) : (
            <Navigation />
          )}
        </Drawer>

        {/* Desktop drawer */}
        {isDesktop && (
          <Drawer
            variant="permanent"
            sx={{
              display: { xs: 'none', lg: 'block' },
              '& .MuiDrawer-paper': {
                boxSizing: 'border-box',
                width: drawerWidth,
              },
            }}
            open
          >
            <Toolbar /> {/* Spacer for app bar */}
            <Navigation />
          </Drawer>
        )}
      </Box>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { lg: isDesktop ? `calc(100% - ${drawerWidth}px)` : '100%' },
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        <Toolbar /> {/* Spacer for app bar */}
        
        <Box sx={{ flex: 1, overflow: 'auto' }}>
          {children}
        </Box>
      </Box>

      {/* Voice Chat FAB */}
      {isVoiceSupported && (
        <Zoom in={!voiceChatOpen}>
          <Fab
            color="primary"
            aria-label="voice chat"
            sx={{
              position: 'fixed',
              bottom: isMobile ? 16 : 32,
              right: isMobile ? 16 : 32,
              zIndex: 1000
            }}
            onClick={handleVoiceChatToggle}
          >
            <Badge
              color="secondary"
              variant="dot"
              invisible={!hasActiveSession}
            >
              <Mic />
            </Badge>
          </Fab>
        </Zoom>
      )}

      {/* Voice Chat Component */}
      <VoiceChat
        sessionId="current-session"
        isOpen={voiceChatOpen}
        onClose={() => setVoiceChatOpen(false)}
      />
    </Box>
  );
};
```

### 5. Custom Hooks for State Management

#### `frontend/src/hooks/useResponsive.tsx`
```typescript
import { useMediaQuery, useTheme } from '@mui/material';
import { useEffect, useState } from 'react';

export interface ResponsiveState {
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  isSmallScreen: boolean;
  screenWidth: number;
  screenHeight: number;
}

export const useResponsive = (): ResponsiveState => {
  const theme = useTheme();
  const [dimensions, setDimensions] = useState({
    width: window.innerWidth,
    height: window.innerHeight
  });

  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const isTablet = useMediaQuery(theme.breakpoints.between('md', 'lg'));
  const isDesktop = useMediaQuery(theme.breakpoints.up('lg'));
  const isSmallScreen = useMediaQuery(theme.breakpoints.down('sm'));

  useEffect(() => {
    const handleResize = () => {
      setDimensions({
        width: window.innerWidth,
        height: window.innerHeight
      });
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return {
    isMobile,
    isTablet,
    isDesktop,
    isSmallScreen,
    screenWidth: dimensions.width,
    screenHeight: dimensions.height
  };
};

export const useBreakpoints = () => {
  const theme = useTheme();
  
  return {
    xs: useMediaQuery(theme.breakpoints.only('xs')),
    sm: useMediaQuery(theme.breakpoints.only('sm')),
    md: useMediaQuery(theme.breakpoints.only('md')),
    lg: useMediaQuery(theme.breakpoints.only('lg')),
    xl: useMediaQuery(theme.breakpoints.only('xl')),
    
    upXs: useMediaQuery(theme.breakpoints.up('xs')),
    upSm: useMediaQuery(theme.breakpoints.up('sm')),
    upMd: useMediaQuery(theme.breakpoints.up('md')),
    upLg: useMediaQuery(theme.breakpoints.up('lg')),
    upXl: useMediaQuery(theme.breakpoints.up('xl')),
    
    downXs: useMediaQuery(theme.breakpoints.down('xs')),
    downSm: useMediaQuery(theme.breakpoints.down('sm')),
    downMd: useMediaQuery(theme.breakpoints.down('md')),
    downLg: useMediaQuery(theme.breakpoints.down('lg')),
    downXl: useMediaQuery(theme.breakpoints.down('xl'))
  };
};

// Utility hook for adaptive component sizing
export const useAdaptiveSize = () => {
  const { isMobile, isTablet, isDesktop } = useResponsive();
  
  const getSize = (mobile: number, tablet: number, desktop: number) => {
    if (isMobile) return mobile;
    if (isTablet) return tablet;
    return desktop;
  };

  const getSizeString = (mobile: string, tablet: string, desktop: string) => {
    if (isMobile) return mobile;
    if (isTablet) return tablet;
    return desktop;
  };

  const getSpacing = (mobile: number, tablet?: number, desktop?: number) => {
    return getSize(mobile, tablet || mobile * 1.5, desktop || mobile * 2);
  };

  return {
    getSize,
    getSizeString,
    getSpacing,
    isMobile,
    isTablet,
    isDesktop
  };
};
```

---

## Accessibility and Performance

### Accessibility Features
```typescript
// Accessibility utilities
export const accessibilityConfig = {
  // ARIA labels and descriptions
  ariaLabels: {
    voiceChat: 'Voice chat interface',
    timeline: 'Interactive historical timeline',
    sourceAnalyzer: 'Primary source analysis tool',
    dashboard: 'Learning analytics dashboard'
  },

  // Keyboard navigation
  keyboardShortcuts: {
    'Alt+V': 'Toggle voice chat',
    'Alt+T': 'Focus timeline',
    'Alt+S': 'Open source analyzer',
    'Alt+D': 'Go to dashboard',
    'Escape': 'Close current modal',
    'Tab': 'Navigate forward',
    'Shift+Tab': 'Navigate backward'
  },

  // Screen reader support
  screenReaderAnnouncements: {
    voiceStateChange: (state: string) => `Voice chat state changed to ${state}`,
    timelineUpdate: (eventCount: number) => `Timeline updated with ${eventCount} events`,
    assessmentComplete: (score: number) => `Assessment completed with score ${score}%`
  },

  // High contrast mode
  highContrastSupport: true,
  
  // Focus management
  focusTrap: true,
  
  // Reduced motion support
  respectsReducedMotion: true
};
```

### Performance Optimizations
```typescript
// Performance optimization strategies
export const performanceConfig = {
  // Code splitting
  lazyLoading: {
    voiceChat: () => import('../components/voice/VoiceChat'),
    timeline: () => import('../components/timeline/InteractiveTimeline'),
    sourceAnalyzer: () => import('../components/sources/SourceAnalyzer'),
    dashboard: () => import('../components/dashboard/LearningDashboard')
  },

  // Virtual scrolling for large lists
  virtualScrolling: {
    itemHeight: 80,
    bufferSize: 10,
    overscan: 5
  },

  // Memoization strategies
  memoization: {
    timelineEvents: true,
    analyticsCharts: true,
    sourceAnnotations: true
  },

  // Image optimization
  imageOptimization: {
    lazy: true,
    webpSupport: true,
    responsiveImages: true
  },

  // Bundle optimization
  bundleOptimization: {
    treeShaking: true,
    modulePreloading: true,
    resourceHints: true
  }
};
```

This comprehensive frontend implementation provides a modern, responsive, and accessible interface for the EduAGI History tutoring system, with sophisticated voice interaction, data visualization, and mobile-first design principles.