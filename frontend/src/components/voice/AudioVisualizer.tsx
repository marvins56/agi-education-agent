'use client'

import React, { useMemo } from 'react'

interface AudioVisualizerProps {
  isRecording: boolean
  isPlaying: boolean
  audioLevel: number
  className?: string
}

export function AudioVisualizer({
  isRecording,
  isPlaying,
  audioLevel,
  className
}: AudioVisualizerProps) {
  // Generate bars for visualization
  const bars = useMemo(() => {
    const numBars = 20
    return Array.from({ length: numBars }, (_, i) => {
      // Create wave-like pattern
      const baseHeight = Math.sin((i / numBars) * Math.PI) * 0.3 + 0.1
      
      // Add audio level influence
      const audioInfluence = isRecording || isPlaying ? audioLevel * 0.8 : 0.05
      
      // Add some randomness for more natural look
      const randomness = Math.random() * 0.1
      
      return Math.min(1, baseHeight + audioInfluence + randomness)
    })
  }, [audioLevel, isRecording, isPlaying])

  return (
    <div className={`flex items-end justify-center gap-1 h-20 ${className}`}>
      {bars.map((height, index) => (
        <div
          key={index}
          className={`rounded-sm transition-all duration-150 ${
            isRecording
              ? 'bg-red-500'
              : isPlaying
              ? 'bg-blue-500'
              : 'bg-muted-foreground/20'
          }`}
          style={{
            height: `${Math.max(4, height * 80)}px`,
            width: '3px',
            animationDelay: `${index * 50}ms`
          }}
        />
      ))}
    </div>
  )
}

interface WaveformVisualizerProps {
  audioData?: number[]
  isActive?: boolean
  className?: string
}

export function WaveformVisualizer({
  audioData = [],
  isActive = false,
  className
}: WaveformVisualizerProps) {
  // Normalize audio data to 0-1 range
  const normalizedData = useMemo(() => {
    if (audioData.length === 0) return Array(50).fill(0.1)
    
    const maxValue = Math.max(...audioData.map(Math.abs))
    if (maxValue === 0) return audioData.map(() => 0.1)
    
    return audioData.map(value => Math.abs(value) / maxValue)
  }, [audioData])

  return (
    <div className={`flex items-center justify-center gap-0.5 h-16 overflow-hidden ${className}`}>
      {normalizedData.map((amplitude, index) => (
        <div
          key={index}
          className={`rounded-full transition-all duration-100 ${
            isActive ? 'bg-primary' : 'bg-muted-foreground/30'
          }`}
          style={{
            height: `${Math.max(2, amplitude * 60)}px`,
            width: '2px'
          }}
        />
      ))}
    </div>
  )
}

interface CircularVisualizerProps {
  audioLevel: number
  isActive: boolean
  size?: number
  className?: string
}

export function CircularVisualizer({
  audioLevel,
  isActive,
  size = 100,
  className
}: CircularVisualizerProps) {
  // Create circular bars
  const bars = useMemo(() => {
    const numBars = 24
    return Array.from({ length: numBars }, (_, i) => {
      const angle = (i / numBars) * 360
      const baseRadius = 0.3
      const audioRadius = isActive ? audioLevel * 0.4 : 0.05
      const randomness = Math.random() * 0.1
      
      return {
        angle,
        radius: Math.min(0.9, baseRadius + audioRadius + randomness)
      }
    })
  }, [audioLevel, isActive])

  return (
    <div 
      className={`relative ${className}`}
      style={{ width: size, height: size }}
    >
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="absolute inset-0"
      >
        <circle
          cx={size / 2}
          cy={size / 2}
          r={size * 0.15}
          className={`transition-colors duration-200 ${
            isActive ? 'fill-primary' : 'fill-muted-foreground/30'
          }`}
        />
        
        {bars.map((bar, index) => {
          const centerX = size / 2
          const centerY = size / 2
          const innerRadius = size * 0.25
          const outerRadius = size * (0.25 + bar.radius * 0.25)
          
          const startAngle = (bar.angle - 2) * (Math.PI / 180)
          const endAngle = (bar.angle + 2) * (Math.PI / 180)
          
          const x1 = centerX + Math.cos(startAngle) * innerRadius
          const y1 = centerY + Math.sin(startAngle) * innerRadius
          const x2 = centerX + Math.cos(startAngle) * outerRadius
          const y2 = centerY + Math.sin(startAngle) * outerRadius
          
          return (
            <line
              key={index}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke={isActive ? 'currentColor' : 'currentColor'}
              strokeWidth="2"
              strokeLinecap="round"
              className={`transition-all duration-150 ${
                isActive ? 'text-primary' : 'text-muted-foreground/30'
              }`}
              style={{ animationDelay: `${index * 25}ms` }}
            />
          )
        })}
      </svg>
    </div>
  )
}