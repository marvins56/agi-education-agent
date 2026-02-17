"use client";

import { useState, useEffect, useCallback, useRef } from 'react';
import { VoiceSession, VoiceMessage, VoiceSettings, startVoiceSession, endVoiceSession, sendVoiceMessage, getVoiceHistory, getVoiceSettings, updateVoiceSettings } from '@/lib/api/voice';

export interface VoiceState {
  isConnected: boolean;
  isListening: boolean;
  isSpeaking: boolean;
  conversationState: 'idle' | 'listening' | 'thinking' | 'speaking' | 'error';
  audioLevel: number;
  error: string | null;
}

export const useVoiceChat = (sessionId?: string) => {
  const [voiceState, setVoiceState] = useState<VoiceState>({
    isConnected: false,
    isListening: false,
    isSpeaking: false,
    conversationState: 'idle',
    audioLevel: 0,
    error: null,
  });
  
  const [session, setSession] = useState<VoiceSession | null>(null);
  const [messages, setMessages] = useState<VoiceMessage[]>([]);
  const [settings, setSettings] = useState<VoiceSettings | null>(null);
  const [transcription, setTranscription] = useState<string>('');
  const [voiceResponse, setVoiceResponse] = useState<VoiceMessage | null>(null);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationRef = useRef<number>();

  // Check if voice is supported
  const isVoiceSupported = typeof navigator !== 'undefined' && 
    'mediaDevices' in navigator && 
    'getUserMedia' in navigator.mediaDevices &&
    'MediaRecorder' in window;

  // Initialize audio context and analyzer
  const initializeAudio = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        } 
      });
      
      audioStreamRef.current = stream;
      
      // Set up audio context for visualization
      audioContextRef.current = new AudioContext();
      analyserRef.current = audioContextRef.current.createAnalyser();
      
      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);
      
      analyserRef.current.fftSize = 256;
      
      // Set up media recorder
      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      return true;
    } catch (error) {
      console.error('Failed to initialize audio:', error);
      setVoiceState(prev => ({ 
        ...prev, 
        error: 'Failed to access microphone. Please check permissions.' 
      }));
      return false;
    }
  }, []);

  // Monitor audio level
  const monitorAudioLevel = useCallback(() => {
    if (!analyserRef.current) return;
    
    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    
    const updateLevel = () => {
      if (analyserRef.current && voiceState.isListening) {
        analyserRef.current.getByteFrequencyData(dataArray);
        
        // Calculate RMS (Root Mean Square) for audio level
        const sum = dataArray.reduce((acc, value) => acc + value * value, 0);
        const rms = Math.sqrt(sum / dataArray.length);
        const normalizedLevel = Math.min(rms / 128, 1);
        
        setVoiceState(prev => ({ ...prev, audioLevel: normalizedLevel }));
        animationRef.current = requestAnimationFrame(updateLevel);
      }
    };
    
    updateLevel();
  }, [voiceState.isListening]);

  // Connect to voice session
  const connect = useCallback(async () => {
    if (!isVoiceSupported) {
      setVoiceState(prev => ({ 
        ...prev, 
        error: 'Voice chat is not supported in this browser.' 
      }));
      return;
    }

    try {
      setVoiceState(prev => ({ ...prev, error: null }));
      
      // Initialize audio
      const audioInitialized = await initializeAudio();
      if (!audioInitialized) return;
      
      // Start voice session
      const newSession = await startVoiceSession();
      setSession(newSession);
      
      // Load settings
      const voiceSettings = await getVoiceSettings();
      setSettings(voiceSettings);
      
      // Load message history
      if (newSession.conversationHistory.length > 0) {
        setMessages(newSession.conversationHistory);
      }
      
      setVoiceState(prev => ({ 
        ...prev, 
        isConnected: true, 
        conversationState: 'idle' 
      }));
    } catch (error) {
      console.error('Failed to connect to voice service:', error);
      setVoiceState(prev => ({ 
        ...prev, 
        error: 'Failed to connect to voice service.' 
      }));
    }
  }, [isVoiceSupported, initializeAudio]);

  // Disconnect from voice session
  const disconnect = useCallback(async () => {
    try {
      // Stop recording if active
      if (mediaRecorderRef.current && voiceState.isListening) {
        mediaRecorderRef.current.stop();
      }
      
      // Stop audio monitoring
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      
      // Close audio stream
      if (audioStreamRef.current) {
        audioStreamRef.current.getTracks().forEach(track => track.stop());
      }
      
      // Close audio context
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
      
      // End session
      if (session) {
        await endVoiceSession(session.id);
      }
      
      setVoiceState({
        isConnected: false,
        isListening: false,
        isSpeaking: false,
        conversationState: 'idle',
        audioLevel: 0,
        error: null,
      });
      
      setSession(null);
      setMessages([]);
      setTranscription('');
      setVoiceResponse(null);
    } catch (error) {
      console.error('Failed to disconnect:', error);
    }
  }, [session, voiceState.isListening]);

  // Start listening
  const startListening = useCallback(async () => {
    if (!mediaRecorderRef.current || !session) return;
    
    try {
      setVoiceState(prev => ({ 
        ...prev, 
        isListening: true, 
        conversationState: 'listening',
        error: null 
      }));
      
      const chunks: BlobPart[] = [];
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };
      
      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: 'audio/webm' });
        
        // Convert to base64 for API
        const reader = new FileReader();
        reader.onloadend = async () => {
          const base64Audio = (reader.result as string).split(',')[1];
          
          setVoiceState(prev => ({ 
            ...prev, 
            isListening: false, 
            conversationState: 'thinking' 
          }));
          
          try {
            // Send audio to API
            const response = await sendVoiceMessage(session.id, base64Audio);
            setMessages(prev => [...prev, response]);
            setVoiceResponse(response);
            
            setVoiceState(prev => ({ 
              ...prev, 
              conversationState: 'speaking',
              isSpeaking: true 
            }));
            
            // Simulate speaking completion
            setTimeout(() => {
              setVoiceState(prev => ({ 
                ...prev, 
                conversationState: 'idle',
                isSpeaking: false 
              }));
            }, 3000);
            
          } catch (error) {
            console.error('Failed to send voice message:', error);
            setVoiceState(prev => ({ 
              ...prev, 
              conversationState: 'error',
              error: 'Failed to process voice message.' 
            }));
          }
        };
        
        reader.readAsDataURL(audioBlob);
      };
      
      mediaRecorderRef.current.start();
      monitorAudioLevel();
    } catch (error) {
      console.error('Failed to start listening:', error);
      setVoiceState(prev => ({ 
        ...prev, 
        error: 'Failed to start recording.' 
      }));
    }
  }, [session, monitorAudioLevel]);

  // Stop listening
  const stopListening = useCallback(() => {
    if (mediaRecorderRef.current && voiceState.isListening) {
      mediaRecorderRef.current.stop();
      
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    }
  }, [voiceState.isListening]);

  // Pause speaking
  const pauseSpeaking = useCallback(() => {
    // This would integrate with actual audio playback
    setVoiceState(prev => ({ 
      ...prev, 
      isSpeaking: false,
      conversationState: 'idle' 
    }));
  }, []);

  // Resume speaking
  const resumeSpeaking = useCallback(() => {
    setVoiceState(prev => ({ 
      ...prev, 
      isSpeaking: true,
      conversationState: 'speaking' 
    }));
  }, []);

  // Update settings
  const updateVoiceSettings = useCallback(async (newSettings: Partial<VoiceSettings>) => {
    try {
      const updatedSettings = await updateVoiceSettings(newSettings);
      setSettings(updatedSettings);
    } catch (error) {
      console.error('Failed to update voice settings:', error);
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    // State
    ...voiceState,
    session,
    messages,
    settings,
    transcription,
    voiceResponse,
    isVoiceSupported,
    hasActiveSession: !!session,
    
    // Actions
    connect,
    disconnect,
    startListening,
    stopListening,
    pauseSpeaking,
    resumeSpeaking,
    updateSettings: updateVoiceSettings,
  };
};