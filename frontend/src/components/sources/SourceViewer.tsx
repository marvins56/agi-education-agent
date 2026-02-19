'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  FileText, 
  Calendar, 
  User, 
  MapPin, 
  Eye, 
  Target, 
  Users, 
  AlertCircle,
  BookOpen,
  Image as ImageIcon,
  Film,
  Music,
  Archive,
  ExternalLink
} from 'lucide-react'

interface PrimarySource {
  id: string
  title: string
  author?: string
  date: string
  year: number
  location?: string
  type: 'document' | 'letter' | 'diary' | 'speech' | 'newspaper' | 'photograph' | 'artifact' | 'audio' | 'video'
  content: string
  description: string
  historicalContext: string
  perspective: string
  purpose: string
  audience: string
  reliability: 'high' | 'medium' | 'low'
  bias?: string[]
  significance: string
  relatedEvents?: string[]
  tags: string[]
  sourceUrl?: string
  imageUrl?: string
}

interface SourceAnalysis {
  pointOfView: string
  purpose: string
  audience: string
  situation: string
  credibility: {
    score: number
    factors: string[]
  }
  biases: string[]
  limitations: string[]
}

interface SourceViewerProps {
  source: PrimarySource
  onAnalyze?: (analysis: SourceAnalysis) => void
  className?: string
}

const sourceTypeIcons = {
  document: FileText,
  letter: FileText,
  diary: BookOpen,
  speech: Users,
  newspaper: FileText,
  photograph: ImageIcon,
  artifact: Archive,
  audio: Music,
  video: Film
}

const reliabilityColors = {
  high: 'bg-green-500',
  medium: 'bg-yellow-500',
  low: 'bg-red-500'
}

export function SourceViewer({ source, onAnalyze, className }: SourceViewerProps) {
  const [activeTab, setActiveTab] = useState('content')
  const [analysisMode, setAnalysisMode] = useState<'guided' | 'free'>('guided')
  const [showAnalysis, setShowAnalysis] = useState(false)
  
  const Icon = sourceTypeIcons[source.type]
  
  const handleAnalyzeSource = () => {
    // Mock analysis for demonstration
    const mockAnalysis: SourceAnalysis = {
      pointOfView: "Written from the perspective of a European colonizer, showing clear bias toward European 'civilization' and viewing African societies as primitive.",
      purpose: "To justify colonial expansion and present it as a civilizing mission rather than economic exploitation.",
      audience: "European political leaders and the educated public who needed to be convinced of colonial ventures.",
      situation: "Written during the height of the 'Scramble for Africa' when European powers were competing for African territories.",
      credibility: {
        score: 6,
        factors: [
          "Author was present during events described",
          "Written close to the time of events",
          "Contains specific details and names",
          "However, shows clear cultural bias",
          "Omits African perspectives entirely"
        ]
      },
      biases: [
        "Cultural superiority complex",
        "Economic interests not mentioned",
        "Paternalistic attitude toward Africans",
        "Selective presentation of facts"
      ],
      limitations: [
        "Only European perspective represented",
        "Economic motivations downplayed",
        "African agency and resistance ignored",
        "Written to justify actions, not objectively report"
      ]
    }
    
    setShowAnalysis(true)
    onAnalyze?.(mockAnalysis)
  }
  
  return (
    <div className={`space-y-4 ${className}`}>
      {/* Source Header */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle className="flex items-center gap-2 mb-2">
                <Icon className="h-5 w-5" />
                {source.title}
              </CardTitle>
              
              <div className="flex flex-wrap items-center gap-2 mb-3">
                <Badge variant="outline" className="flex items-center gap-1">
                  <Calendar className="h-3 w-3" />
                  {source.date}
                </Badge>
                
                {source.author && (
                  <Badge variant="outline" className="flex items-center gap-1">
                    <User className="h-3 w-3" />
                    {source.author}
                  </Badge>
                )}
                
                {source.location && (
                  <Badge variant="outline" className="flex items-center gap-1">
                    <MapPin className="h-3 w-3" />
                    {source.location}
                  </Badge>
                )}
                
                <Badge variant="secondary">
                  {source.type.charAt(0).toUpperCase() + source.type.slice(1)}
                </Badge>
                
                <Badge 
                  className={`${reliabilityColors[source.reliability]} text-white`}
                >
                  {source.reliability.toUpperCase()} Reliability
                </Badge>
              </div>
              
              <p className="text-sm text-muted-foreground">
                {source.description}
              </p>
            </div>
            
            {source.imageUrl && (
              <div className="ml-4">
                <img
                  src={source.imageUrl}
                  alt={source.title}
                  className="w-24 h-24 object-cover rounded-md border"
                />
              </div>
            )}
          </div>
        </CardHeader>
      </Card>
      
      {/* Source Content */}
      <Card>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <CardHeader className="pb-2">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="content">Content</TabsTrigger>
              <TabsTrigger value="context">Context</TabsTrigger>
              <TabsTrigger value="analysis">Analysis</TabsTrigger>
              <TabsTrigger value="questions">Questions</TabsTrigger>
            </TabsList>
          </CardHeader>
          
          <CardContent>
            <TabsContent value="content" className="space-y-4">
              <ScrollArea className="h-96 w-full rounded-md border p-4">
                <div className="whitespace-pre-wrap text-sm leading-relaxed">
                  {source.content}
                </div>
              </ScrollArea>
              
              {source.sourceUrl && (
                <a href={source.sourceUrl} target="_blank" rel="noopener noreferrer">
                  <Button variant="outline" size="sm">
                    <ExternalLink className="h-4 w-4 mr-2" />
                    View Original Source
                  </Button>
                </a>
              )}
            </TabsContent>
            
            <TabsContent value="context" className="space-y-4">
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium mb-2">Historical Context</h4>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {source.historicalContext}
                  </p>
                </div>
                
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-medium mb-2 flex items-center gap-2">
                      <Eye className="h-4 w-4" />
                      Perspective
                    </h4>
                    <p className="text-sm text-muted-foreground">
                      {source.perspective}
                    </p>
                  </div>
                  
                  <div>
                    <h4 className="font-medium mb-2 flex items-center gap-2">
                      <Target className="h-4 w-4" />
                      Purpose
                    </h4>
                    <p className="text-sm text-muted-foreground">
                      {source.purpose}
                    </p>
                  </div>
                  
                  <div>
                    <h4 className="font-medium mb-2 flex items-center gap-2">
                      <Users className="h-4 w-4" />
                      Intended Audience
                    </h4>
                    <p className="text-sm text-muted-foreground">
                      {source.audience}
                    </p>
                  </div>
                  
                  <div>
                    <h4 className="font-medium mb-2">Historical Significance</h4>
                    <p className="text-sm text-muted-foreground">
                      {source.significance}
                    </p>
                  </div>
                </div>
                
                {source.bias && source.bias.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2 flex items-center gap-2">
                      <AlertCircle className="h-4 w-4 text-yellow-500" />
                      Potential Biases
                    </h4>
                    <div className="flex flex-wrap gap-1">
                      {source.bias.map((bias, index) => (
                        <Badge key={index} variant="outline" className="text-yellow-700">
                          {bias}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
                
                <div>
                  <h4 className="font-medium mb-2">Tags</h4>
                  <div className="flex flex-wrap gap-1">
                    {source.tags.map((tag, index) => (
                      <Badge key={index} variant="secondary">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
            </TabsContent>
            
            <TabsContent value="analysis" className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-medium">Source Analysis</h3>
                
                <div className="flex items-center gap-2">
                  <Select value={analysisMode} onValueChange={(value: string) => setAnalysisMode(value as 'guided' | 'free')}>
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="guided">Guided</SelectItem>
                      <SelectItem value="free">Free Form</SelectItem>
                    </SelectContent>
                  </Select>
                  
                  <Button onClick={handleAnalyzeSource}>
                    Analyze Source
                  </Button>
                </div>
              </div>
              
              {showAnalysis ? (
                <div className="space-y-4">
                  <Card className="p-4">
                    <h4 className="font-medium mb-2 flex items-center gap-2">
                      <Eye className="h-4 w-4" />
                      Point of View
                    </h4>
                    <p className="text-sm leading-relaxed">
                      Written from the perspective of a European colonizer, showing clear bias toward European 'civilization' and viewing African societies as primitive.
                    </p>
                  </Card>
                  
                  <Card className="p-4">
                    <h4 className="font-medium mb-2 flex items-center gap-2">
                      <Target className="h-4 w-4" />
                      Purpose & Audience
                    </h4>
                    <p className="text-sm leading-relaxed">
                      To justify colonial expansion and present it as a civilizing mission rather than economic exploitation. Written for European political leaders and the educated public.
                    </p>
                  </Card>
                  
                  <Card className="p-4">
                    <h4 className="font-medium mb-2">Credibility Assessment</h4>
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">Score:</span>
                        <Badge variant="outline">6/10</Badge>
                      </div>
                      <ul className="text-sm space-y-1 list-disc list-inside">
                        <li>Author was present during events described (+)</li>
                        <li>Written close to the time of events (+)</li>
                        <li>Contains specific details and names (+)</li>
                        <li>However, shows clear cultural bias (-)</li>
                        <li>Omits African perspectives entirely (-)</li>
                      </ul>
                    </div>
                  </Card>
                  
                  <Card className="p-4">
                    <h4 className="font-medium mb-2 flex items-center gap-2">
                      <AlertCircle className="h-4 w-4 text-yellow-500" />
                      Limitations & Biases
                    </h4>
                    <div className="grid md:grid-cols-2 gap-4">
                      <div>
                        <h5 className="text-sm font-medium mb-1">Biases:</h5>
                        <ul className="text-sm space-y-1">
                          <li>• Cultural superiority complex</li>
                          <li>• Economic interests not mentioned</li>
                          <li>• Paternalistic attitude toward Africans</li>
                          <li>• Selective presentation of facts</li>
                        </ul>
                      </div>
                      
                      <div>
                        <h5 className="text-sm font-medium mb-1">Limitations:</h5>
                        <ul className="text-sm space-y-1">
                          <li>• Only European perspective represented</li>
                          <li>• Economic motivations downplayed</li>
                          <li>• African agency and resistance ignored</li>
                          <li>• Written to justify actions</li>
                        </ul>
                      </div>
                    </div>
                  </Card>
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-muted-foreground mb-4">
                    Click "Analyze Source" to see a detailed analysis of this primary source.
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Analysis will examine the source's perspective, purpose, audience, and historical situation.
                  </p>
                </div>
              )}
            </TabsContent>
            
            <TabsContent value="questions" className="space-y-4">
              <div>
                <h3 className="font-medium mb-4">Source Analysis Questions</h3>
                
                <div className="space-y-4">
                  <Card className="p-4">
                    <h4 className="font-medium mb-2">Understanding the Source</h4>
                    <ul className="text-sm space-y-2 list-disc list-inside">
                      <li>Who created this source and when was it created?</li>
                      <li>What type of source is this (letter, speech, diary, etc.)?</li>
                      <li>What is the main message or argument of the source?</li>
                      <li>What specific details or evidence does the source provide?</li>
                    </ul>
                  </Card>
                  
                  <Card className="p-4">
                    <h4 className="font-medium mb-2">Analyzing Perspective & Purpose</h4>
                    <ul className="text-sm space-y-2 list-disc list-inside">
                      <li>From whose point of view is this source written?</li>
                      <li>What was the author's purpose in creating this source?</li>
                      <li>Who was the intended audience for this source?</li>
                      <li>How might the author's background influence their perspective?</li>
                    </ul>
                  </Card>
                  
                  <Card className="p-4">
                    <h4 className="font-medium mb-2">Evaluating Reliability</h4>
                    <ul className="text-sm space-y-2 list-disc list-inside">
                      <li>How close in time was this source created to the events it describes?</li>
                      <li>What might the author's motivations have been?</li>
                      <li>What biases might be present in this source?</li>
                      <li>What information might be missing or omitted?</li>
                    </ul>
                  </Card>
                  
                  <Card className="p-4">
                    <h4 className="font-medium mb-2">Historical Significance</h4>
                    <ul className="text-sm space-y-2 list-disc list-inside">
                      <li>How does this source relate to the broader historical context?</li>
                      <li>What does this source reveal about the time period?</li>
                      <li>How might different groups have viewed this source differently?</li>
                      <li>What questions does this source raise that require further investigation?</li>
                    </ul>
                  </Card>
                </div>
              </div>
            </TabsContent>
          </CardContent>
        </Tabs>
      </Card>
    </div>
  )
}