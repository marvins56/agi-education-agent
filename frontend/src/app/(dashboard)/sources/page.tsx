'use client'

import React, { useState } from 'react'
import { SourceViewer } from '@/components/sources/SourceViewer'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  Search, 
  Filter, 
  FileText, 
  Image as ImageIcon, 
  Calendar, 
  User,
  MapPin,
  BookOpen,
  Plus
} from 'lucide-react'

// Mock data for demonstration
const mockSources = [
  {
    id: "source-1",
    title: "Cecil Rhodes' Speech on British Expansion in Africa",
    author: "Cecil Rhodes",
    date: "October 15, 1895",
    year: 1895,
    location: "Cape Town, South Africa",
    type: "speech" as const,
    content: `My fellow countrymen, we are engaged in a great work of civilization in this dark continent. It is our duty, nay our destiny, to bring the light of British civilization to these benighted lands. The native races, while possessed of certain childlike virtues, lack the capacity for self-government and the industrial development which this rich continent demands.

Through our settlements, our mines, and our railways, we are opening up vast territories that have lain dormant for centuries. Where once there was wilderness, we are creating order. Where once there was ignorance, we are bringing education. Where once there was barbarism, we are establishing the rule of law.

I do not speak merely of conquest, but of a sacred trust. We are the trustees of civilization in Africa, charged with developing its resources not for our own benefit alone, but for the benefit of all mankind. The gold and diamonds we extract, the agricultural lands we cultivate, the trade routes we establish - all these serve the greater good of human progress.

Let no man say that we come as mere exploiters. We come as builders of empire, as architects of a new world order in which the superior races guide and educate the inferior ones toward a better future. This is our burden, our responsibility, and our glory.`,
    description: "A speech by British imperial administrator Cecil Rhodes advocating for British colonial expansion in Africa.",
    historicalContext: "Delivered during the height of the 'Scramble for Africa' when European powers were rapidly colonizing African territories. Rhodes was a key figure in British expansion, controlling vast mining operations and political influence in southern Africa.",
    perspective: "The perspective of a wealthy British colonial administrator and businessman who saw African colonization as both profitable and a civilizing mission.",
    purpose: "To justify British colonial expansion in Africa by presenting it as a civilizing mission rather than economic exploitation.",
    audience: "British colonial officials, investors, and the educated British public who supported imperial expansion.",
    reliability: "medium" as const,
    bias: [
      "Racial superiority complex",
      "Economic interests concealed as moral duty",
      "Paternalistic colonial mindset",
      "European-centered worldview"
    ],
    significance: "This speech exemplifies the racist ideologies and economic motivations behind European colonialism in Africa. It reveals how colonizers justified their actions through claims of civilizing missions while pursuing economic gain.",
    relatedEvents: ["Berlin Conference", "Anglo-Zulu War", "Discovery of gold in Witwatersrand"],
    tags: ["colonialism", "imperialism", "racism", "economic exploitation", "British Empire", "Africa"],
    sourceUrl: "https://example.com/rhodes-speech-1895",
    imageUrl: "/api/placeholder/200/150"
  },
  {
    id: "source-2", 
    title: "Letter from African Chief to Colonial Administrator",
    author: "Chief Mwanga of Buganda",
    date: "March 3, 1890",
    year: 1890,
    location: "Kampala, Uganda",
    type: "letter" as const,
    content: `To the representative of the Queen across the waters,

I write to you with a heavy heart, for I see the changes that your people bring to our land, and I do not understand why they are necessary. For many generations, my ancestors have ruled this kingdom with wisdom, guided by our customs and our gods. Our people have known prosperity, our warriors have been strong, and our traders have dealt fairly with neighbors far and wide.

You speak of bringing us civilization, but we have always been civilized in our own way. We have laws that keep order, schools where our children learn wisdom, and markets where goods from many lands are traded. Why then do you say we need your laws, your schools, your ways of trade?

Your administrators tell us we must change our customs, abandon our gods, and adopt your manner of living. But these customs have served us well. They connect us to our ancestors, to our land, and to each other. To abandon them would be to lose our very souls.

I have seen what has happened in other kingdoms where your people have come. The old ways are forgotten, the young people become strangers to their own heritage, and the wealth of the land flows away to distant shores. Is this the civilization you offer?

I do not write in anger, but in hope that you might understand our position. We are willing to trade with your people, to learn what is useful from your knowledge, but we wish to remain masters in our own house. Can there not be respect between our peoples without one consuming the other?`,
    description: "A letter from a Buganda chief expressing concerns about British colonial policies and their impact on traditional African society.",
    historicalContext: "Written during the early period of British colonial expansion in East Africa, when traditional African rulers were being forced to accept British authority and administrative systems.",
    perspective: "The perspective of an African traditional ruler witnessing the disruption of established political, social, and cultural systems by European colonizers.",
    purpose: "To express concerns about colonial policies and advocate for maintaining traditional African autonomy and customs while engaging with Europeans.",
    audience: "British colonial administrators, intended to persuade them to adopt less intrusive colonial policies.",
    reliability: "high" as const,
    bias: [
      "Defense of traditional systems",
      "Idealization of pre-colonial society",
      "Limited understanding of European perspectives"
    ],
    significance: "This letter provides crucial insight into African perspectives on colonialism, revealing resistance to cultural imperialism and the value placed on traditional governance systems.",
    relatedEvents: ["Uganda Agreement of 1900", "Scramble for Africa", "Berlin Conference"],
    tags: ["African resistance", "traditional governance", "cultural preservation", "colonial impact", "Uganda"],
    sourceUrl: "https://example.com/mwanga-letter-1890"
  }
]

export default function SourcesPage() {
  const [selectedSource, setSelectedSource] = useState(mockSources[0])
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedType, setSelectedType] = useState('all')
  const [selectedReliability, setSelectedReliability] = useState('all')

  const handleAnalyze = (analysis: any) => {
    console.log('Source analysis:', analysis)
    // Here you would save the analysis or display it in a modal
  }

  const handleSourceSelect = (source: any) => {
    setSelectedSource(source)
  }

  const filteredSources = mockSources.filter(source => {
    const matchesSearch = source.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         source.author?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         source.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
    
    const matchesType = selectedType === 'all' || source.type === selectedType
    const matchesReliability = selectedReliability === 'all' || source.reliability === selectedReliability
    
    return matchesSearch && matchesType && matchesReliability
  })

  return (
    <div className="container mx-auto p-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-screen">
        {/* Sources List */}
        <div className="lg:col-span-1 space-y-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold">Primary Sources</h1>
            <Button size="sm">
              <Plus className="h-4 w-4 mr-2" />
              Add Source
            </Button>
          </div>

          {/* Search and Filters */}
          <Card>
            <CardContent className="p-4 space-y-3">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                <Input
                  placeholder="Search sources..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>
              
              <div className="flex gap-2">
                <Select value={selectedType} onValueChange={setSelectedType}>
                  <SelectTrigger className="flex-1">
                    <SelectValue placeholder="Type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Types</SelectItem>
                    <SelectItem value="document">Documents</SelectItem>
                    <SelectItem value="letter">Letters</SelectItem>
                    <SelectItem value="speech">Speeches</SelectItem>
                    <SelectItem value="diary">Diaries</SelectItem>
                    <SelectItem value="photograph">Photographs</SelectItem>
                  </SelectContent>
                </Select>
                
                <Select value={selectedReliability} onValueChange={setSelectedReliability}>
                  <SelectTrigger className="flex-1">
                    <SelectValue placeholder="Reliability" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Reliability</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="low">Low</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Sources List */}
          <div className="space-y-3 overflow-y-auto max-h-[calc(100vh-300px)]">
            {filteredSources.map((source) => (
              <Card
                key={source.id}
                className={`cursor-pointer transition-colors hover:bg-muted/50 ${
                  selectedSource.id === source.id ? 'ring-2 ring-primary bg-muted/30' : ''
                }`}
                onClick={() => handleSourceSelect(source)}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-sm line-clamp-2 leading-tight">
                        {source.title}
                      </h3>
                      <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                        {source.author && (
                          <div className="flex items-center gap-1">
                            <User className="h-3 w-3" />
                            <span className="truncate">{source.author}</span>
                          </div>
                        )}
                        <div className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          <span>{source.year}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-1 ml-2">
                      <Badge variant="outline" className="text-xs">
                        {source.type}
                      </Badge>
                      <Badge 
                        variant="secondary"
                        className={`text-xs ${
                          source.reliability === 'high' ? 'bg-green-100 text-green-800' :
                          source.reliability === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}
                      >
                        {source.reliability}
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <p className="text-xs text-muted-foreground line-clamp-2">
                    {source.description}
                  </p>
                  <div className="flex items-center gap-1 mt-2">
                    {source.location && (
                      <div className="flex items-center gap-1 text-xs text-muted-foreground">
                        <MapPin className="h-3 w-3" />
                        <span className="truncate">{source.location}</span>
                      </div>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {source.tags.slice(0, 3).map((tag) => (
                      <Badge key={tag} variant="outline" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                    {source.tags.length > 3 && (
                      <Badge variant="outline" className="text-xs">
                        +{source.tags.length - 3} more
                      </Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Source Viewer */}
        <div className="lg:col-span-2">
          <SourceViewer
            source={selectedSource}
            onAnalyze={handleAnalyze}
            className="h-full overflow-y-auto"
          />
        </div>
      </div>
    </div>
  )
}