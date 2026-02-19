'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { VoiceControls } from './VoiceControls'
import { AudioVisualizer } from './AudioVisualizer'
import { ConversationFlow } from './ConversationFlow'
import { VoiceSettings } from './VoiceSettings'
import { Mic, MicOff, Volume2, VolumeX, Settings, MessageSquare } from 'lucide-react'

interface VoiceChatMessage {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  audioUrl?: string
  transcription?: string
}

interface VoiceChatProps {
  onMessage?: (message: VoiceChatMessage) => void
  className?: string
}

export function VoiceChat({ onMessage, className }: VoiceChatProps) {
  const [isRecording, setIsRecording] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [showTranscript, setShowTranscript] = useState(true)
  const [messages, setMessages] = useState<VoiceChatMessage[]>([])
  const [currentAudioLevel, setCurrentAudioLevel] = useState(0)
  const [isProcessing, setIsProcessing] = useState(false)
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const streamRef = useRef<MediaStream | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const animationFrameRef = useRef<number>(0)
  
  // Initialize audio context for visualization
  useEffect(() => {
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
    }
  }, [])
  
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        } 
      })
      
      streamRef.current = stream
      
      // Set up audio visualization
      audioContextRef.current = new AudioContext()
      analyserRef.current = audioContextRef.current.createAnalyser()
      const source = audioContextRef.current.createMediaStreamSource(stream)
      source.connect(analyserRef.current)
      
      analyserRef.current.fftSize = 256
      const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount)
      
      const updateAudioLevel = () => {
        if (analyserRef.current) {
          analyserRef.current.getByteFrequencyData(dataArray)
          const average = dataArray.reduce((a, b) => a + b) / dataArray.length
          setCurrentAudioLevel(average / 255)
          animationFrameRef.current = requestAnimationFrame(updateAudioLevel)
        }
      }
      updateAudioLevel()
      
      // Set up recording
      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      
      audioChunksRef.current = []
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }
      
      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        await processAudioRecording(audioBlob)
      }
      
      mediaRecorderRef.current.start(100) // Record in 100ms chunks
      setIsRecording(true)
      
    } catch (error) {
      console.error('Error starting recording:', error)
      alert('Could not access microphone. Please check permissions.')
    }
  }
  
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      setCurrentAudioLevel(0)
      
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
    }
  }
  
  const processAudioRecording = async (audioBlob: Blob) => {
    setIsProcessing(true)
    
    try {
      // Create user message
      const userMessage: VoiceChatMessage = {
        id: Date.now().toString(),
        type: 'user',
        content: 'Processing audio...',
        timestamp: new Date(),
        audioUrl: URL.createObjectURL(audioBlob)
      }
      
      setMessages(prev => [...prev, userMessage])
      onMessage?.(userMessage)
      
      // TODO: Send audio to backend for transcription and processing
      // For now, simulate the process
      await simulateProcessing(audioBlob, userMessage.id)
      
    } catch (error) {
      console.error('Error processing audio:', error)
    } finally {
      setIsProcessing(false)
    }
  }
  
  const simulateProcessing = async (audioBlob: Blob, messageId: string) => {
    // Simulate transcription
    setTimeout(() => {
      setMessages(prev => prev.map(msg => 
        msg.id === messageId 
          ? { ...msg, content: 'What were the main causes of World War I?', transcription: 'What were the main causes of World War I?' }
          : msg
      ))
    }, 1500)
    
    // Simulate assistant response
    setTimeout(() => {
      const assistantMessage: VoiceChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: 'The main causes of World War I can be understood through the acronym MAIN: Militarism, Alliances, Imperialism, and Nationalism. The immediate trigger was the assassination of Archduke Franz Ferdinand, but underlying tensions had been building for years.',
        timestamp: new Date()
      }
      
      setMessages(prev => [...prev, assistantMessage])
      onMessage?.(assistantMessage)
      
      // Simulate TTS
      speakMessage(assistantMessage.content)
    }, 3000)
  }
  
  const speakMessage = async (text: string) => {
    if ('speechSynthesis' in window && !isMuted) {
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.rate = 0.9
      utterance.pitch = 1.0
      utterance.volume = 1.0
      
      utterance.onstart = () => setIsPlaying(true)
      utterance.onend = () => setIsPlaying(false)
      utterance.onerror = () => setIsPlaying(false)
      
      speechSynthesis.speak(utterance)
    }
  }
  
  const toggleMute = () => {
    setIsMuted(!isMuted)
    if (!isMuted && speechSynthesis.speaking) {
      speechSynthesis.cancel()
      setIsPlaying(false)
    }
  }
  
  const stopSpeaking = () => {
    speechSynthesis.cancel()
    setIsPlaying(false)
  }
  
  const clearConversation = () => {
    setMessages([])
    if (speechSynthesis.speaking) {
      speechSynthesis.cancel()
      setIsPlaying(false)
    }
  }
  
  return (
    <div className={`flex flex-col h-full max-w-4xl mx-auto p-4 ${className}`}>
      <Card className="flex-1 flex flex-col">
        <CardHeader className="flex-row items-center justify-between space-y-0 pb-4">
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Voice Chat
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowTranscript(!showTranscript)}
            >
              Transcript: {showTranscript ? 'On' : 'Off'}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowSettings(!showSettings)}
            >
              <Settings className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        
        <CardContent className="flex-1 flex flex-col space-y-4">
          {/* Audio Visualizer */}
          <div className="flex justify-center">
            <AudioVisualizer
              isRecording={isRecording}
              isPlaying={isPlaying}
              audioLevel={currentAudioLevel}
              className="w-full max-w-md"
            />
          </div>
          
          {/* Voice Controls */}
          <div className="flex justify-center">
            <VoiceControls
              isRecording={isRecording}
              isPlaying={isPlaying}
              isMuted={isMuted}
              isProcessing={isProcessing}
              onStartRecording={startRecording}
              onStopRecording={stopRecording}
              onToggleMute={toggleMute}
              onStopSpeaking={stopSpeaking}
              onClear={clearConversation}
            />
          </div>
          
          {/* Status */}
          <div className="text-center text-sm text-muted-foreground">
            {isProcessing && 'Processing your message...'}
            {isRecording && 'Listening... Speak now'}
            {isPlaying && 'Speaking response...'}
            {!isRecording && !isPlaying && !isProcessing && 'Click the microphone to start speaking'}
          </div>
          
          {/* Conversation History */}
          {showTranscript && (
            <div className="flex-1 min-h-0">
              <ConversationFlow
                messages={messages}
                onPlayAudio={speakMessage}
                className="h-full"
              />
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Voice Settings Modal */}
      {showSettings && (
        <VoiceSettings
          onClose={() => setShowSettings(false)}
          onSave={(settings) => {
            console.log('Voice settings saved:', settings)
            setShowSettings(false)
          }}
        />
      )}
    </div>
  )
}