'use client'

import React from 'react'
import { VoiceChat } from '@/components/voice/VoiceChat'

export default function VoicePage() {
  const handleMessage = (message: any) => {
    console.log('Voice message:', message)
    // Here you could integrate with the chat API
  }

  return (
    <div className="container mx-auto p-4 h-screen">
      <VoiceChat 
        onMessage={handleMessage}
        className="h-full"
      />
    </div>
  )
}