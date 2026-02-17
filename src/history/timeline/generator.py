"""Timeline generation and management system."""
import logging
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple, Any
import json
import os

from src.history.schemas import (
    Timeline, HistoricalEvent, EventType, HistoricalPeriod,
    CausalRelationship
)

logger = logging.getLogger(__name__)


class TimelineGenerator:
    """Generate interactive timelines from historical data."""
    
    def __init__(self, data_path: str = "data/history"):
        self.data_path = data_path
        self.events_cache: Dict[str, HistoricalEvent] = {}
        self.timelines_cache: Dict[str, Timeline] = {}
        self._load_historical_data()
    
    def _load_historical_data(self):
        """Load historical data from JSON fixtures."""
        try:
            # Load World Wars data
            world_wars_file = os.path.join(self.data_path, "world_wars.json")
            if os.path.exists(world_wars_file):
                with open(world_wars_file, 'r') as f:
                    world_wars_data = json.load(f)
                self._process_historical_data("world_wars", world_wars_data)
            
            # Load Cold War data
            cold_war_file = os.path.join(self.data_path, "cold_war.json")
            if os.path.exists(cold_war_file):
                with open(cold_war_file, 'r') as f:
                    cold_war_data = json.load(f)
                self._process_historical_data("cold_war", cold_war_data)
            
            logger.info(f"Loaded {len(self.events_cache)} historical events")
            
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
            self._create_default_events()
    
    def _process_historical_data(self, era_key: str, data: Dict[str, Any]):
        """Process historical data from JSON into events."""
        
        era_name = data.get("era", era_key)
        concepts = data.get("key_concepts", [])
        
        for i, concept in enumerate(concepts):
            if not isinstance(concept, dict):
                continue
            
            event_id = f"{era_key}_{i:03d}"
            
            # Parse timeline data
            timeline_entries = concept.get("timeline", [])
            if timeline_entries:
                for j, entry in enumerate(timeline_entries):
                    sub_event_id = f"{event_id}_{j:03d}"
                    
                    event = HistoricalEvent(
                        event_id=sub_event_id,
                        title=entry.get("event", concept.get("concept_name", "Unknown Event")),
                        description=entry.get("event", ""),
                        date_start=self._parse_date(entry.get("date", "1900")),
                        event_type=self._determine_event_type(concept.get("concept_name", "")),
                        period=self._determine_period(era_key),
                        significance=concept.get("importance", 0.5),
                        key_figures=concept.get("key_points", [])[:3],  # First 3 as key figures
                        concepts_taught=[concept.get("concept_name", "")]
                    )
                    
                    self.events_cache[sub_event_id] = event
            else:
                # Create main concept event
                event = HistoricalEvent(
                    event_id=event_id,
                    title=concept.get("concept_name", "Unknown Concept"),
                    description=concept.get("description", ""),
                    date_start=self._estimate_date_from_era(era_key),
                    event_type=self._determine_event_type(concept.get("concept_name", "")),
                    period=self._determine_period(era_key),
                    significance=concept.get("importance", 0.5),
                    key_figures=concept.get("key_points", [])[:3],
                    concepts_taught=[concept.get("concept_name", "")]
                )
                
                self.events_cache[event_id] = event
    
    def _parse_date(self, date_str: str) -> str:
        """Parse various date formats into consistent format."""
        if not date_str:
            return "1900"
        
        # Handle common date formats
        date_str = date_str.strip()
        
        # Extract year from complex dates
        if "," in date_str:
            parts = date_str.split(",")
            for part in parts:
                if part.strip().isdigit() and len(part.strip()) == 4:
                    return part.strip()
        
        # Handle ranges like "1914-1918"
        if "-" in date_str and not date_str.startswith("-"):
            return date_str.split("-")[0].strip()
        
        # Handle simple years
        if date_str.isdigit() and len(date_str) == 4:
            return date_str
        
        # Extract first 4-digit number found
        import re
        year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
        if year_match:
            return year_match.group()
        
        # Fallback
        return "1900"
    
    def _determine_event_type(self, concept_name: str) -> EventType:
        """Determine event type from concept name."""
        name_lower = concept_name.lower()
        
        if any(word in name_lower for word in ["war", "battle", "invasion", "attack"]):
            return EventType.MILITARY
        elif any(word in name_lower for word in ["treaty", "alliance", "government", "politics"]):
            return EventType.POLITICAL
        elif any(word in name_lower for word in ["economy", "trade", "depression", "industrial"]):
            return EventType.ECONOMIC
        elif any(word in name_lower for word in ["revolution", "movement", "rights", "society"]):
            return EventType.SOCIAL
        elif any(word in name_lower for word in ["culture", "art", "religion", "belief"]):
            return EventType.CULTURAL
        elif any(word in name_lower for word in ["technology", "invention", "discovery"]):
            return EventType.TECHNOLOGICAL
        else:
            return EventType.POLITICAL  # Default
    
    def _determine_period(self, era_key: str) -> HistoricalPeriod:
        """Determine historical period from era key."""
        period_mapping = {
            "world_wars": HistoricalPeriod.MODERN_ERA,
            "cold_war": HistoricalPeriod.CONTEMPORARY,
            "renaissance": HistoricalPeriod.RENAISSANCE,
            "medieval": HistoricalPeriod.MEDIEVAL,
            "ancient": HistoricalPeriod.ANCIENT_WORLD
        }
        
        return period_mapping.get(era_key, HistoricalPeriod.MODERN_ERA)
    
    def _estimate_date_from_era(self, era_key: str) -> str:
        """Estimate a date based on era."""
        date_mapping = {
            "world_wars": "1914",
            "cold_war": "1945", 
            "renaissance": "1400",
            "medieval": "1000",
            "ancient": "500"
        }
        
        return date_mapping.get(era_key, "1900")
    
    def _create_default_events(self):
        """Create some default events if data loading fails."""
        default_events = [
            HistoricalEvent(
                event_id="default_001",
                title="World War I Begins",
                description="The assassination of Archduke Franz Ferdinand triggers the start of World War I",
                date_start="1914-06-28",
                event_type=EventType.MILITARY,
                period=HistoricalPeriod.MODERN_ERA,
                significance=1.0
            ),
            HistoricalEvent(
                event_id="default_002",
                title="Treaty of Versailles",
                description="Peace treaty that ended World War I and imposed heavy penalties on Germany",
                date_start="1919-06-28",
                event_type=EventType.POLITICAL,
                period=HistoricalPeriod.MODERN_ERA,
                significance=0.9
            )
        ]
        
        for event in default_events:
            self.events_cache[event.event_id] = event
    
    def create_timeline(
        self,
        title: str,
        theme: str,
        event_filters: Optional[Dict[str, Any]] = None,
        date_range: Optional[Tuple[str, str]] = None
    ) -> Timeline:
        """Create a timeline with filtered events."""
        
        timeline_id = f"timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Filter events based on criteria
        filtered_events = self._filter_events(event_filters, date_range)
        
        # Sort events chronologically
        sorted_events = sorted(filtered_events, key=lambda e: self._parse_date_for_sorting(e.date_start))
        
        # Determine date range
        if date_range:
            date_start, date_end = date_range
        else:
            dates = [self._parse_date_for_sorting(e.date_start) for e in sorted_events]
            date_start = min(dates) if dates else "1900"
            date_end = max(dates) if dates else "2000"
        
        timeline = Timeline(
            timeline_id=timeline_id,
            title=title,
            description=f"Timeline of {theme} with {len(sorted_events)} key events",
            theme=theme,
            events=sorted_events,
            date_range_start=date_start,
            date_range_end=date_end,
            difficulty_level=self._calculate_timeline_difficulty(sorted_events),
            estimated_study_time_minutes=len(sorted_events) * 3  # 3 minutes per event
        )
        
        self.timelines_cache[timeline_id] = timeline
        return timeline
    
    def _filter_events(
        self,
        filters: Optional[Dict[str, Any]] = None,
        date_range: Optional[Tuple[str, str]] = None
    ) -> List[HistoricalEvent]:
        """Filter events based on criteria."""
        
        events = list(self.events_cache.values())
        
        if not filters and not date_range:
            return events
        
        filtered = []
        
        for event in events:
            # Date range filter
            if date_range:
                event_year = int(self._parse_date_for_sorting(event.date_start))
                start_year = int(self._parse_date_for_sorting(date_range[0]))
                end_year = int(self._parse_date_for_sorting(date_range[1]))
                
                if not (start_year <= event_year <= end_year):
                    continue
            
            # Other filters
            if filters:
                # Event type filter
                if "event_type" in filters:
                    if event.event_type != filters["event_type"]:
                        continue
                
                # Period filter
                if "period" in filters:
                    if event.period != filters["period"]:
                        continue
                
                # Significance filter
                if "min_significance" in filters:
                    if event.significance < filters["min_significance"]:
                        continue
                
                # Theme/keyword filter
                if "keywords" in filters:
                    keywords = filters["keywords"]
                    if not any(keyword.lower() in event.title.lower() or 
                             keyword.lower() in event.description.lower() 
                             for keyword in keywords):
                        continue
            
            filtered.append(event)
        
        return filtered
    
    def _parse_date_for_sorting(self, date_str: str) -> str:
        """Parse date for sorting purposes."""
        try:
            # Extract year and pad to 4 digits for consistent sorting
            year = self._parse_date(date_str)
            return year.zfill(4)
        except:
            return "1900"
    
    def _calculate_timeline_difficulty(self, events: List[HistoricalEvent]) -> float:
        """Calculate overall difficulty of timeline."""
        if not events:
            return 0.5
        
        # Base difficulty on number of events and their complexity
        num_events = len(events)
        avg_significance = sum(e.significance for e in events) / num_events
        
        # More events = higher difficulty
        event_difficulty = min(1.0, num_events / 20)  # Cap at 20 events = max difficulty
        
        # Higher significance events are more important but not necessarily harder
        significance_factor = avg_significance * 0.3
        
        return min(1.0, (event_difficulty * 0.7) + significance_factor)
    
    def get_event_relationships(self, event_id: str) -> Dict[str, List[str]]:
        """Get causal and other relationships for an event."""
        
        event = self.events_cache.get(event_id)
        if not event:
            return {}
        
        return {
            "causes": event.causes,
            "effects": event.effects,
            "related_events": event.related_events,
            "key_figures": event.key_figures,
            "concepts_taught": event.concepts_taught
        }
    
    def create_causal_chain_timeline(
        self,
        root_event_id: str,
        title: str = "Cause and Effect Timeline"
    ) -> Timeline:
        """Create a timeline showing cause-and-effect relationships."""
        
        root_event = self.events_cache.get(root_event_id)
        if not root_event:
            raise ValueError(f"Event {root_event_id} not found")
        
        # Collect all related events through causal chains
        related_events = set()
        self._collect_causal_events(root_event_id, related_events, depth=3)
        
        # Get event objects
        events = [self.events_cache[event_id] for event_id in related_events 
                 if event_id in self.events_cache]
        
        # Sort chronologically
        events.sort(key=lambda e: self._parse_date_for_sorting(e.date_start))
        
        return Timeline(
            timeline_id=f"causal_{root_event_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title=title,
            description=f"Causal chain timeline starting from {root_event.title}",
            theme=f"Causes and Effects of {root_event.title}",
            events=events,
            date_range_start=events[0].date_start if events else "1900",
            date_range_end=events[-1].date_start if events else "2000",
            difficulty_level=0.8,  # Causal analysis is typically harder
            learning_objectives=[
                "Understand cause-and-effect relationships",
                "Analyze historical causation",
                "Connect events across time periods"
            ]
        )
    
    def _collect_causal_events(self, event_id: str, collected: set, depth: int):
        """Recursively collect causally related events."""
        
        if depth <= 0 or event_id in collected:
            return
        
        collected.add(event_id)
        event = self.events_cache.get(event_id)
        
        if not event:
            return
        
        # Collect causes and effects
        for cause_id in event.causes:
            self._collect_causal_events(cause_id, collected, depth - 1)
        
        for effect_id in event.effects:
            self._collect_causal_events(effect_id, collected, depth - 1)
    
    def get_timeline_by_theme(self, theme: str) -> Optional[Timeline]:
        """Get existing timeline by theme."""
        for timeline in self.timelines_cache.values():
            if timeline.theme.lower() == theme.lower():
                return timeline
        return None
    
    def create_comparative_timeline(
        self,
        themes: List[str],
        title: str = "Comparative Timeline"
    ) -> Timeline:
        """Create timeline comparing multiple themes/regions."""
        
        all_events = []
        
        # Collect events for each theme
        for theme in themes:
            theme_events = self._filter_events({"keywords": [theme]})
            all_events.extend(theme_events)
        
        # Remove duplicates
        unique_events = {e.event_id: e for e in all_events}
        events = list(unique_events.values())
        
        # Sort chronologically
        events.sort(key=lambda e: self._parse_date_for_sorting(e.date_start))
        
        return Timeline(
            timeline_id=f"comparative_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title=title,
            description=f"Comparative timeline of {', '.join(themes)}",
            theme=f"Comparison: {', '.join(themes)}",
            events=events,
            date_range_start=events[0].date_start if events else "1900",
            date_range_end=events[-1].date_start if events else "2000",
            difficulty_level=0.9,  # Comparison is high-level skill
            learning_objectives=[
                "Compare historical developments",
                "Analyze similarities and differences",
                "Understand parallel historical processes"
            ]
        )
    
    def export_timeline_data(self, timeline_id: str) -> Dict[str, Any]:
        """Export timeline data for frontend visualization."""
        
        timeline = self.timelines_cache.get(timeline_id)
        if not timeline:
            return {}
        
        # Convert to format suitable for D3.js or similar
        return {
            "timeline": {
                "id": timeline.timeline_id,
                "title": timeline.title,
                "description": timeline.description,
                "theme": timeline.theme,
                "dateRange": {
                    "start": timeline.date_range_start,
                    "end": timeline.date_range_end
                },
                "difficulty": timeline.difficulty_level,
                "studyTime": timeline.estimated_study_time_minutes
            },
            "events": [
                {
                    "id": event.event_id,
                    "title": event.title,
                    "description": event.description,
                    "date": event.date_start,
                    "endDate": event.date_end,
                    "type": event.event_type.value,
                    "period": event.period.value,
                    "significance": event.significance,
                    "location": event.location,
                    "keyFigures": event.key_figures,
                    "causes": event.causes,
                    "effects": event.effects,
                    "relatedEvents": event.related_events
                }
                for event in timeline.events
            ],
            "metadata": {
                "totalEvents": len(timeline.events),
                "timeSpan": self._calculate_time_span(timeline),
                "eventTypes": self._get_event_type_distribution(timeline.events),
                "createdAt": timeline.created_at.isoformat()
            }
        }
    
    def _calculate_time_span(self, timeline: Timeline) -> Dict[str, Any]:
        """Calculate time span statistics."""
        if not timeline.events:
            return {"years": 0, "description": "No events"}
        
        start_year = int(self._parse_date_for_sorting(timeline.date_range_start))
        end_year = int(self._parse_date_for_sorting(timeline.date_range_end))
        span_years = end_year - start_year
        
        return {
            "years": span_years,
            "description": f"{span_years} years ({start_year} - {end_year})"
        }
    
    def _get_event_type_distribution(self, events: List[HistoricalEvent]) -> Dict[str, int]:
        """Get distribution of event types."""
        distribution = {}
        for event in events:
            event_type = event.event_type.value
            distribution[event_type] = distribution.get(event_type, 0) + 1
        return distribution
    
    def get_available_timelines(self) -> List[Dict[str, Any]]:
        """Get list of available timelines."""
        return [
            {
                "id": timeline.timeline_id,
                "title": timeline.title,
                "theme": timeline.theme,
                "events_count": len(timeline.events),
                "difficulty": timeline.difficulty_level,
                "study_time": timeline.estimated_study_time_minutes,
                "created_at": timeline.created_at.isoformat()
            }
            for timeline in self.timelines_cache.values()
        ]