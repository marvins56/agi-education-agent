'use client'

import React, { useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Play, Pause, Volume2, User, Bot, Clock } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

interface VoiceChatMessage {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  audioUrl?: string
  transcription?: string
}

interface ConversationFlowProps {
  messages: VoiceChatMessage[]
  onPlayAudio?: (text: string) => void
  className?: string
}

export function ConversationFlow({
  messages,
  onPlayAudio,
  className
}: ConversationFlowProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const [playingAudio, setPlayingAudio] = React.useState<string | null>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages])

  const handlePlayAudio = (messageId: string, audioUrl?: string, text?: string) => {
    if (playingAudio === messageId) {
      // Stop current audio
      setPlayingAudio(null)
      return
    }

    setPlayingAudio(messageId)

    if (audioUrl) {
      // Play recorded audio
      const audio = new Audio(audioUrl)
      audio.onended = () => setPlayingAudio(null)
      audio.onerror = () => setPlayingAudio(null)
      audio.play().catch(() => setPlayingAudio(null))
    } else if (text && onPlayAudio) {
      // Use TTS
      onPlayAudio(text)
      // Reset playing state after a delay (estimate TTS duration)
      setTimeout(() => setPlayingAudio(null), text.length * 50)
    }
  }

  if (messages.length === 0) {
    return (
      <div className={`flex flex-col items-center justify-center h-full text-center p-8 ${className}`}>
        <div className="text-muted-foreground mb-4">
          <Bot className="h-16 w-16 mx-auto mb-4 opacity-50" />
          <h3 className="text-lg font-medium mb-2">Start a Voice Conversation</h3>
          <p className="text-sm">
            Click the microphone button to begin speaking with your AI history tutor
          </p>
        </div>
      </div>
    )
  }

  return (
    <ScrollArea className={`h-full ${className}`}>
      <div className="space-y-4 p-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-3 ${
              message.type === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {message.type === 'assistant' && (
              <Avatar className="h-8 w-8 mt-1">
                <AvatarImage src="/bot-avatar.png" />
                <AvatarFallback>
                  <Bot className="h-4 w-4" />
                </AvatarFallback>
              </Avatar>
            )}
            
            <div
              className={`flex flex-col max-w-[75%] ${
                message.type === 'user' ? 'items-end' : 'items-start'
              }`}
            >
              {/* Message Header */}
              <div className="flex items-center gap-2 mb-1">
                <Badge
                  variant={message.type === 'user' ? 'default' : 'secondary'}
                  className="text-xs"
                >
                  {message.type === 'user' ? 'You' : 'AI Tutor'}
                </Badge>
                <span className="text-xs text-muted-foreground flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {formatDistanceToNow(message.timestamp, { addSuffix: true })}
                </span>
              </div>

              {/* Message Content */}
              <div
                className={`rounded-lg p-3 max-w-full ${
                  message.type === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted'
                }`}
              >
                {message.transcription && message.type === 'user' && (
                  <div className="text-sm opacity-90 mb-2 italic">
                    {message.transcription}
                  </div>
                )}
                
                <div className="whitespace-pre-wrap text-sm leading-relaxed">
                  {message.content}
                </div>

                {/* Audio Controls */}
                <div className="flex items-center justify-between mt-3 pt-2 border-t border-current/10">
                  <div className="flex items-center gap-2">
                    {(message.audioUrl || message.type === 'assistant') && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className={`h-6 px-2 ${
                          message.type === 'user'
                            ? 'text-primary-foreground/80 hover:text-primary-foreground hover:bg-primary-foreground/10'
                            : ''
                        }`}
                        onClick={() => handlePlayAudio(
                          message.id,
                          message.audioUrl,
                          message.content
                        )}
                      >
                        {playingAudio === message.id ? (
                          <>
                            <Pause className="h-3 w-3 mr-1" />
                            Stop
                          </>
                        ) : (
                          <>
                            <Play className="h-3 w-3 mr-1" />
                            Play
                          </>
                        )}
                      </Button>
                    )}
                    
                    {message.audioUrl && (
                      <Badge
                        variant="outline"
                        className={`text-xs ${
                          message.type === 'user'
                            ? 'border-primary-foreground/20 text-primary-foreground/60'
                            : ''
                        }`}
                      >
                        <Volume2 className="h-2 w-2 mr-1" />
                        Audio
                      </Badge>
                    )}
                  </div>
                  
                  {playingAudio === message.id && (
                    <div className="flex items-center gap-1">
                      <div className="flex space-x-0.5">
                        <div className="w-1 h-1 bg-current rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                        <div className="w-1 h-1 bg-current rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <div className="w-1 h-1 bg-current rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {message.type === 'user' && (
              <Avatar className="h-8 w-8 mt-1">
                <AvatarImage src="/user-avatar.png" />
                <AvatarFallback>
                  <User className="h-4 w-4" />
                </AvatarFallback>
              </Avatar>
            )}
          </div>
        ))}
        
        {/* Scroll anchor */}
        <div ref={scrollRef} />
      </div>
    </ScrollArea>
  )
}