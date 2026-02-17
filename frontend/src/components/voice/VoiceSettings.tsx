'use client'

import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { X, Volume2, Mic, Settings2 } from 'lucide-react'

interface VoiceSettingsData {
  // Text-to-Speech Settings
  ttsVoice: string
  ttsSpeed: number
  ttsPitch: number
  ttsVolume: number
  autoPlay: boolean
  
  // Speech Recognition Settings
  language: string
  noiseSupression: boolean
  echoCancellation: boolean
  autoGainControl: boolean
  
  // UI Settings
  showTranscript: boolean
  showAudioVisualizer: boolean
  darkMode: boolean
}

interface VoiceSettingsProps {
  onClose: () => void
  onSave: (settings: VoiceSettingsData) => void
  initialSettings?: Partial<VoiceSettingsData>
}

export function VoiceSettings({
  onClose,
  onSave,
  initialSettings = {}
}: VoiceSettingsProps) {
  const [settings, setSettings] = useState<VoiceSettingsData>({
    // Default values
    ttsVoice: 'default',
    ttsSpeed: 1.0,
    ttsPitch: 1.0,
    ttsVolume: 1.0,
    autoPlay: true,
    
    language: 'en-US',
    noiseSupression: true,
    echoCancellation: true,
    autoGainControl: true,
    
    showTranscript: true,
    showAudioVisualizer: true,
    darkMode: false,
    
    // Override with initial settings
    ...initialSettings
  })
  
  const [availableVoices, setAvailableVoices] = useState<SpeechSynthesisVoice[]>([])
  const [testingTTS, setTestingTTS] = useState(false)
  
  // Load available voices
  useEffect(() => {
    const loadVoices = () => {
      const voices = speechSynthesis.getVoices()
      setAvailableVoices(voices)
    }
    
    loadVoices()
    speechSynthesis.addEventListener('voiceschanged', loadVoices)
    
    return () => {
      speechSynthesis.removeEventListener('voiceschanged', loadVoices)
    }
  }, [])
  
  const updateSetting = <K extends keyof VoiceSettingsData>(
    key: K,
    value: VoiceSettingsData[K]
  ) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }))
  }
  
  const testTTSSettings = () => {
    if ('speechSynthesis' in window && !testingTTS) {
      setTestingTTS(true)
      
      const utterance = new SpeechSynthesisUtterance(
        'This is a test of your text-to-speech settings. How does this sound?'
      )
      
      // Apply current settings
      const selectedVoice = availableVoices.find(voice => voice.name === settings.ttsVoice)
      if (selectedVoice) {
        utterance.voice = selectedVoice
      }
      
      utterance.rate = settings.ttsSpeed
      utterance.pitch = settings.ttsPitch
      utterance.volume = settings.ttsVolume
      
      utterance.onend = () => setTestingTTS(false)
      utterance.onerror = () => setTestingTTS(false)
      
      speechSynthesis.speak(utterance)
    }
  }
  
  const stopTTSTest = () => {
    speechSynthesis.cancel()
    setTestingTTS(false)
  }
  
  const handleSave = () => {
    onSave(settings)
  }
  
  const handleReset = () => {
    setSettings({
      ttsVoice: 'default',
      ttsSpeed: 1.0,
      ttsPitch: 1.0,
      ttsVolume: 1.0,
      autoPlay: true,
      language: 'en-US',
      noiseSupression: true,
      echoCancellation: true,
      autoGainControl: true,
      showTranscript: true,
      showAudioVisualizer: true,
      darkMode: false
    })
  }
  
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-hidden">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <CardTitle className="flex items-center gap-2">
            <Settings2 className="h-5 w-5" />
            Voice Settings
          </CardTitle>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </CardHeader>
        
        <CardContent className="overflow-y-auto">
          <Tabs defaultValue="tts" className="space-y-6">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="tts">Text-to-Speech</TabsTrigger>
              <TabsTrigger value="speech">Speech Recognition</TabsTrigger>
              <TabsTrigger value="ui">Interface</TabsTrigger>
            </TabsList>
            
            {/* Text-to-Speech Settings */}
            <TabsContent value="tts" className="space-y-6">
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Voice</Label>
                  <Select
                    value={settings.ttsVoice}
                    onValueChange={(value) => updateSetting('ttsVoice', value)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select a voice" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="default">Default Voice</SelectItem>
                      {availableVoices.map((voice) => (
                        <SelectItem key={voice.name} value={voice.name}>
                          {voice.name} ({voice.lang})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label>Speed: {settings.ttsSpeed.toFixed(1)}x</Label>
                  <Slider
                    value={[settings.ttsSpeed]}
                    onValueChange={([value]) => updateSetting('ttsSpeed', value)}
                    min={0.5}
                    max={2.0}
                    step={0.1}
                    className="w-full"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label>Pitch: {settings.ttsPitch.toFixed(1)}</Label>
                  <Slider
                    value={[settings.ttsPitch]}
                    onValueChange={([value]) => updateSetting('ttsPitch', value)}
                    min={0.5}
                    max={2.0}
                    step={0.1}
                    className="w-full"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label>Volume: {Math.round(settings.ttsVolume * 100)}%</Label>
                  <Slider
                    value={[settings.ttsVolume]}
                    onValueChange={([value]) => updateSetting('ttsVolume', value)}
                    min={0.0}
                    max={1.0}
                    step={0.05}
                    className="w-full"
                  />
                </div>
                
                <div className="flex items-center space-x-2">
                  <Switch
                    checked={settings.autoPlay}
                    onCheckedChange={(checked) => updateSetting('autoPlay', checked)}
                  />
                  <Label>Auto-play AI responses</Label>
                </div>
                
                <div className="flex gap-2">
                  <Button
                    onClick={testingTTS ? stopTTSTest : testTTSSettings}
                    variant="outline"
                    disabled={!('speechSynthesis' in window)}
                  >
                    <Volume2 className="h-4 w-4 mr-2" />
                    {testingTTS ? 'Stop Test' : 'Test Voice'}
                  </Button>
                </div>
              </div>
            </TabsContent>
            
            {/* Speech Recognition Settings */}
            <TabsContent value="speech" className="space-y-6">
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Language</Label>
                  <Select
                    value={settings.language}
                    onValueChange={(value) => updateSetting('language', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="en-US">English (US)</SelectItem>
                      <SelectItem value="en-GB">English (UK)</SelectItem>
                      <SelectItem value="es-ES">Spanish (Spain)</SelectItem>
                      <SelectItem value="fr-FR">French (France)</SelectItem>
                      <SelectItem value="de-DE">German (Germany)</SelectItem>
                      <SelectItem value="it-IT">Italian (Italy)</SelectItem>
                      <SelectItem value="pt-BR">Portuguese (Brazil)</SelectItem>
                      <SelectItem value="zh-CN">Chinese (Simplified)</SelectItem>
                      <SelectItem value="ja-JP">Japanese</SelectItem>
                      <SelectItem value="ko-KR">Korean</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-4">
                  <h4 className="font-medium flex items-center gap-2">
                    <Mic className="h-4 w-4" />
                    Audio Processing
                  </h4>
                  
                  <div className="space-y-3">
                    <div className="flex items-center space-x-2">
                      <Switch
                        checked={settings.noiseSupression}
                        onCheckedChange={(checked) => updateSetting('noiseSupression', checked)}
                      />
                      <div className="space-y-1">
                        <Label>Noise Suppression</Label>
                        <p className="text-sm text-muted-foreground">
                          Reduce background noise during recording
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <Switch
                        checked={settings.echoCancellation}
                        onCheckedChange={(checked) => updateSetting('echoCancellation', checked)}
                      />
                      <div className="space-y-1">
                        <Label>Echo Cancellation</Label>
                        <p className="text-sm text-muted-foreground">
                          Prevent audio feedback and echoes
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <Switch
                        checked={settings.autoGainControl}
                        onCheckedChange={(checked) => updateSetting('autoGainControl', checked)}
                      />
                      <div className="space-y-1">
                        <Label>Auto Gain Control</Label>
                        <p className="text-sm text-muted-foreground">
                          Automatically adjust microphone sensitivity
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </TabsContent>
            
            {/* UI Settings */}
            <TabsContent value="ui" className="space-y-6">
              <div className="space-y-4">
                <h4 className="font-medium">Display Options</h4>
                
                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <Switch
                      checked={settings.showTranscript}
                      onCheckedChange={(checked) => updateSetting('showTranscript', checked)}
                    />
                    <div className="space-y-1">
                      <Label>Show Conversation Transcript</Label>
                      <p className="text-sm text-muted-foreground">
                        Display text version of voice conversations
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Switch
                      checked={settings.showAudioVisualizer}
                      onCheckedChange={(checked) => updateSetting('showAudioVisualizer', checked)}
                    />
                    <div className="space-y-1">
                      <Label>Show Audio Visualizer</Label>
                      <p className="text-sm text-muted-foreground">
                        Display animated bars during audio recording/playback
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </TabsContent>
          </Tabs>
          
          {/* Action Buttons */}
          <div className="flex justify-between pt-6 border-t">
            <Button variant="outline" onClick={handleReset}>
              Reset to Defaults
            </Button>
            
            <div className="flex gap-2">
              <Button variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button onClick={handleSave}>
                Save Settings
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}