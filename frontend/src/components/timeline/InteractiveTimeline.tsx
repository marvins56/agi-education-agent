"use client";

import React, { useEffect, useRef, useState, useMemo } from 'react';
import * as d3 from 'd3';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { 
  ZoomIn, 
  ZoomOut, 
  RotateCcw, 
  Calendar,
  Filter,
  Info
} from 'lucide-react';
import { HistoricalEvent } from '@/lib/api/history';

interface InteractiveTimelineProps {
  events: HistoricalEvent[];
  onEventSelect?: (event: HistoricalEvent | null) => void;
  selectedEventId?: string;
  height?: number;
  className?: string;
}

export function InteractiveTimeline({ 
  events, 
  onEventSelect, 
  selectedEventId, 
  height = 400,
  className 
}: InteractiveTimelineProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height });
  const [zoomLevel, setZoomLevel] = useState(1);
  const [selectedEvent, setSelectedEvent] = useState<HistoricalEvent | null>(null);
  const [hoveredEvent, setHoveredEvent] = useState<HistoricalEvent | null>(null);

  // Process events and create scales
  const processedEvents = useMemo(() => {
    if (!events.length) return [];
    
    return events
      .filter(event => event.date)
      .map(event => ({
        ...event,
        parsedDate: new Date(event.date)
      }))
      .sort((a, b) => a.parsedDate.getTime() - b.parsedDate.getTime());
  }, [events]);

  // Category colors
  const categoryColors = useMemo(() => {
    const categories = [...new Set(processedEvents.map(e => e.category))];
    return d3.scaleOrdinal(d3.schemeCategory10).domain(categories);
  }, [processedEvents]);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setDimensions({ width: rect.width, height });
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [height]);

  // D3 Timeline Rendering
  useEffect(() => {
    if (!svgRef.current || !processedEvents.length) return;

    const svg = d3.select(svgRef.current);
    const margin = { top: 40, right: 40, bottom: 60, left: 40 };
    const innerWidth = dimensions.width - margin.left - margin.right;
    const innerHeight = dimensions.height - margin.top - margin.bottom;

    // Clear previous content
    svg.selectAll('*').remove();

    // Create scales
    const xScale = d3.scaleTime()
      .domain(d3.extent(processedEvents, d => d.parsedDate) as [Date, Date])
      .range([0, innerWidth]);

    // Group events by category for y-positioning
    const categories = [...new Set(processedEvents.map(e => e.category))];
    const yScale = d3.scaleBand()
      .domain(categories)
      .range([0, innerHeight])
      .padding(0.2);

    // Create main group
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Add background grid
    const xAxis = d3.axisBottom(xScale)
      .tickSize(-innerHeight)
      .tickFormat(() => '');

    g.append('g')
      .attr('class', 'grid')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(xAxis)
      .selectAll('line')
      .style('stroke', '#e5e7eb')
      .style('stroke-width', 0.5);

    // Add timeline axis
    const timeAxis = d3.axisBottom(xScale)
      .tickFormat(d3.timeFormat('%Y'));

    g.append('g')
      .attr('class', 'x-axis')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(timeAxis)
      .selectAll('text')
      .style('font-size', '12px')
      .style('fill', '#6b7280');

    // Add category labels
    g.selectAll('.category-label')
      .data(categories)
      .enter()
      .append('text')
      .attr('class', 'category-label')
      .attr('x', -10)
      .attr('y', d => (yScale(d) || 0) + yScale.bandwidth() / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', 'end')
      .style('font-size', '12px')
      .style('fill', '#6b7280')
      .style('font-weight', '500')
      .text(d => d);

    // Add events
    const eventGroups = g.selectAll('.event-group')
      .data(processedEvents)
      .enter()
      .append('g')
      .attr('class', 'event-group')
      .attr('transform', d => `translate(${xScale(d.parsedDate)}, ${(yScale(d.category) || 0) + yScale.bandwidth() / 2})`);

    // Event circles
    eventGroups.append('circle')
      .attr('class', 'event-circle')
      .attr('r', d => Math.max(4, Math.min(12, 4 + d.importance * 4)))
      .attr('fill', d => categoryColors(d.category))
      .attr('stroke', d => selectedEventId === d.id ? '#2563eb' : '#ffffff')
      .attr('stroke-width', d => selectedEventId === d.id ? 3 : 2)
      .style('cursor', 'pointer')
      .style('opacity', 0.9)
      .on('click', function(event, d) {
        const newSelection = selectedEvent?.id === d.id ? null : d;
        setSelectedEvent(newSelection);
        onEventSelect?.(newSelection);
      })
      .on('mouseover', function(event, d) {
        setHoveredEvent(d);
        d3.select(this)
          .transition()
          .duration(200)
          .attr('r', Math.max(6, Math.min(16, 6 + d.importance * 4)))
          .style('opacity', 1);
      })
      .on('mouseout', function(event, d) {
        setHoveredEvent(null);
        d3.select(this)
          .transition()
          .duration(200)
          .attr('r', Math.max(4, Math.min(12, 4 + d.importance * 4)))
          .style('opacity', 0.9);
      });

    // Event connection lines (if events have connections)
    const connections = processedEvents.flatMap(event =>
      event.connections.map(connId => {
        const connectedEvent = processedEvents.find(e => e.id === connId);
        return connectedEvent ? { source: event, target: connectedEvent } : null;
      }).filter(Boolean)
    ) as Array<{ source: typeof processedEvents[0], target: typeof processedEvents[0] }>;

    if (connections.length > 0) {
      g.selectAll('.connection-line')
        .data(connections)
        .enter()
        .append('line')
        .attr('class', 'connection-line')
        .attr('x1', d => xScale(d.source.parsedDate))
        .attr('y1', d => (yScale(d.source.category) || 0) + yScale.bandwidth() / 2)
        .attr('x2', d => xScale(d.target.parsedDate))
        .attr('y2', d => (yScale(d.target.category) || 0) + yScale.bandwidth() / 2)
        .attr('stroke', '#94a3b8')
        .attr('stroke-width', 1)
        .attr('stroke-dasharray', '3,3')
        .style('opacity', 0.6);
    }

    // Add zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 10])
      .on('zoom', (event) => {
        const { transform } = event;
        setZoomLevel(transform.k);
        g.attr('transform', 
          `translate(${margin.left + transform.x}, ${margin.top + transform.y}) scale(${transform.k})`
        );
      });

    svg.call(zoom);

  }, [processedEvents, dimensions, selectedEventId, categoryColors, onEventSelect, selectedEvent]);

  // Handle zoom controls
  const handleZoomIn = () => {
    if (svgRef.current) {
      const svg = d3.select(svgRef.current);
      svg.transition().call(
        svg.property('__zoom').scaleBy as any, 1.5
      );
    }
  };

  const handleZoomOut = () => {
    if (svgRef.current) {
      const svg = d3.select(svgRef.current);
      svg.transition().call(
        svg.property('__zoom').scaleBy as any, 1 / 1.5
      );
    }
  };

  const handleResetZoom = () => {
    if (svgRef.current) {
      const svg = d3.select(svgRef.current);
      svg.transition().call(
        svg.property('__zoom').transform as any,
        d3.zoomIdentity
      );
      setZoomLevel(1);
    }
  };

  if (!processedEvents.length) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center h-64">
          <div className="text-center space-y-2">
            <Calendar className="h-12 w-12 text-muted-foreground mx-auto" />
            <p className="text-muted-foreground">No timeline events to display</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Timeline Controls */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Historical Timeline
            </CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant="outline">
                Zoom: {Math.round(zoomLevel * 100)}%
              </Badge>
              <Separator orientation="vertical" className="h-6" />
              <Button variant="outline" size="sm" onClick={handleZoomIn}>
                <ZoomIn className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm" onClick={handleZoomOut}>
                <ZoomOut className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm" onClick={handleResetZoom}>
                <RotateCcw className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Timeline Visualization */}
      <Card>
        <CardContent className="p-0">
          <div ref={containerRef} className="w-full">
            <svg
              ref={svgRef}
              width={dimensions.width}
              height={dimensions.height}
              style={{ display: 'block' }}
            />
          </div>
        </CardContent>
      </Card>

      {/* Event Details */}
      {(selectedEvent || hoveredEvent) && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Info className="h-5 w-5" />
              {selectedEvent ? 'Selected Event' : 'Event Preview'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div>
                <h4 className="font-semibold text-lg">
                  {(selectedEvent || hoveredEvent)?.title}
                </h4>
                <div className="flex items-center gap-2 mt-1">
                  <Badge variant="secondary">
                    {(selectedEvent || hoveredEvent)?.category}
                  </Badge>
                  <span className="text-sm text-muted-foreground">
                    {new Date((selectedEvent || hoveredEvent)?.date || '').toLocaleDateString()}
                  </span>
                  <Badge variant="outline">
                    Importance: {(selectedEvent || hoveredEvent)?.importance}/10
                  </Badge>
                </div>
              </div>
              <p className="text-muted-foreground leading-relaxed">
                {(selectedEvent || hoveredEvent)?.description}
              </p>
              {(selectedEvent || hoveredEvent)?.tags && (
                <div className="flex flex-wrap gap-1">
                  {(selectedEvent || hoveredEvent)?.tags.map((tag: string, index: number) => (
                    <Badge key={index} variant="outline" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Legend */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Categories</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {[...new Set(processedEvents.map(e => e.category))].map(category => (
              <div key={category} className="flex items-center gap-2">
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: categoryColors(category) }}
                />
                <span className="text-sm">{category}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}