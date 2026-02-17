'use client'

import React from 'react'
import { Button } from '@/components/ui/button'
import { Mic, MicOff, Volume2, VolumeX, Square, Trash2, Loader2 } from 'lucide-react'

interface VoiceControlsProps {
  isRecording: boolean
  isPlaying: boolean
  isMuted: boolean
  isProcessing: boolean
  onStartRecording: () => void
  onStopRecording: () => void
  onToggleMute: () => void
  onStopSpeaking: () => void
  onClear: () => void
  className?: string
}

export function VoiceControls({
  isRecording,
  isPlaying,
  isMuted,
  isProcessing,
  onStartRecording,
  onStopRecording,
  onToggleMute,
  onStopSpeaking,
  onClear,
  className
}: VoiceControlsProps) {
  return (
    <div className={`flex items-center justify-center gap-3 ${className}`}>
      {/* Main Record Button */}
      <Button
        size="lg"
        variant={isRecording ? "destructive" : "default"}
        className={`relative h-16 w-16 rounded-full transition-all duration-200 ${
          isRecording ? 'animate-pulse shadow-lg shadow-red-200' : ''
        }`}
        onClick={isRecording ? onStopRecording : onStartRecording}
        disabled={isProcessing}
      >
        {isProcessing ? (
          <Loader2 className="h-6 w-6 animate-spin" />
        ) : isRecording ? (
          <Square className="h-6 w-6 fill-current" />
        ) : (
          <Mic className="h-6 w-6" />
        )}
      </Button>

      {/* Mute/Volume Toggle */}
      <Button
        variant="outline"
        size="lg"
        className="h-12 w-12 rounded-full"
        onClick={onToggleMute}
        disabled={isProcessing}
      >
        {isMuted ? (
          <VolumeX className="h-5 w-5 text-muted-foreground" />
        ) : (
          <Volume2 className="h-5 w-5" />
        )}
      </Button>

      {/* Stop Speaking (only show when playing) */}
      {isPlaying && (
        <Button
          variant="outline"
          size="lg"
          className="h-12 w-12 rounded-full"
          onClick={onStopSpeaking}
        >
          <Square className="h-4 w-4 fill-current" />
        </Button>
      )}

      {/* Clear Conversation */}
      <Button
        variant="outline"
        size="lg"
        className="h-12 w-12 rounded-full text-destructive hover:text-destructive"
        onClick={onClear}
        disabled={isProcessing || isRecording}
      >
        <Trash2 className="h-4 w-4" />
      </Button>
    </div>
  )
}