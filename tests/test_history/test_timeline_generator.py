"""Tests for timeline generator."""
import pytest
from unittest.mock import patch, mock_open
import json
from datetime import datetime

from src.history.timeline.generator import TimelineGenerator
from src.history.schemas import EventType, HistoricalPeriod


@pytest.fixture
def mock_historical_data():
    """Mock historical data for testing."""
    return {
        "era": "World Wars (1914-1945)",
        "key_concepts": [
            {
                "concept_name": "World War I",
                "description": "The Great War",
                "importance": 1.0,
                "timeline": [
                    {"date": "June 28, 1914", "event": "Assassination of Archduke Franz Ferdinand"},
                    {"date": "July 28, 1914", "event": "Austria-Hungary declares war on Serbia"},
                    {"date": "November 11, 1918", "event": "Armistice signed, fighting ends"}
                ]
            },
            {
                "concept_name": "Treaty of Versailles",
                "description": "Peace treaty ending WWI",
                "importance": 0.9,
                "timeline": [
                    {"date": "June 28, 1919", "event": "Treaty of Versailles signed"}
                ]
            }
        ]
    }


@pytest.fixture 
def timeline_generator(mock_historical_data):
    """Create timeline generator with mocked data."""
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_historical_data))):
            generator = TimelineGenerator()
            return generator


def test_timeline_generator_initialization(timeline_generator):
    """Test timeline generator initializes correctly."""
    
    assert len(timeline_generator.events_cache) > 0
    
    # Check that events were created from mock data
    event_titles = [event.title for event in timeline_generator.events_cache.values()]
    assert "Assassination of Archduke Franz Ferdinand" in event_titles
    assert "Treaty of Versailles signed" in event_titles


def test_parse_date(timeline_generator):
    """Test date parsing functionality."""
    
    # Test various date formats
    assert timeline_generator._parse_date("1914") == "1914"
    assert timeline_generator._parse_date("June 28, 1914") == "1914"
    assert timeline_generator._parse_date("1914-1918") == "1914"
    assert timeline_generator._parse_date("Summer 1941") == "1941"
    assert timeline_generator._parse_date("") == "1900"


def test_determine_event_type(timeline_generator):
    """Test event type determination."""
    
    assert timeline_generator._determine_event_type("World War I") == EventType.MILITARY
    assert timeline_generator._determine_event_type("Treaty of Versailles") == EventType.POLITICAL
    assert timeline_generator._determine_event_type("Industrial Revolution") == EventType.ECONOMIC
    assert timeline_generator._determine_event_type("Civil Rights Movement") == EventType.SOCIAL


def test_determine_period(timeline_generator):
    """Test historical period determination."""
    
    assert timeline_generator._determine_period("world_wars") == HistoricalPeriod.MODERN_ERA
    assert timeline_generator._determine_period("cold_war") == HistoricalPeriod.CONTEMPORARY
    assert timeline_generator._determine_period("medieval") == HistoricalPeriod.MEDIEVAL


def test_create_timeline(timeline_generator):
    """Test timeline creation."""
    
    timeline = timeline_generator.create_timeline(
        title="World War I Timeline",
        theme="World War I",
        event_filters=None,
        date_range=None
    )
    
    assert timeline.title == "World War I Timeline"
    assert timeline.theme == "World War I"
    assert len(timeline.events) > 0
    assert timeline.timeline_id.startswith("timeline_")
    assert timeline.difficulty_level >= 0.0
    assert timeline.difficulty_level <= 1.0


def test_create_timeline_with_filters(timeline_generator):
    """Test timeline creation with filters."""
    
    timeline = timeline_generator.create_timeline(
        title="Military Events",
        theme="Military History",
        event_filters={"event_type": EventType.MILITARY},
        date_range=("1914", "1918")
    )
    
    assert timeline.title == "Military Events"
    
    # All events should be military type (if any match the filter)
    for event in timeline.events:
        if event.event_type:  # Some might not have type set
            assert event.event_type == EventType.MILITARY


def test_filter_events(timeline_generator):
    """Test event filtering functionality."""
    
    # Test date range filter
    filtered_events = timeline_generator._filter_events(
        filters=None,
        date_range=("1914", "1920")
    )
    
    # Should only include events in the date range
    for event in filtered_events:
        event_year = int(timeline_generator._parse_date_for_sorting(event.date_start))
        assert 1914 <= event_year <= 1920
    
    # Test event type filter
    filtered_events = timeline_generator._filter_events(
        filters={"event_type": EventType.MILITARY}
    )
    
    for event in filtered_events:
        assert event.event_type == EventType.MILITARY


def test_filter_events_by_keywords(timeline_generator):
    """Test filtering events by keywords."""
    
    filtered_events = timeline_generator._filter_events(
        filters={"keywords": ["war"]}
    )
    
    # Should only include events with "war" in title or description
    for event in filtered_events:
        assert ("war" in event.title.lower() or 
                "war" in event.description.lower())


def test_filter_events_by_significance(timeline_generator):
    """Test filtering events by significance level."""
    
    filtered_events = timeline_generator._filter_events(
        filters={"min_significance": 0.8}
    )
    
    # Should only include high-significance events
    for event in filtered_events:
        assert event.significance >= 0.8


def test_calculate_timeline_difficulty(timeline_generator):
    """Test timeline difficulty calculation."""
    
    # Create events with different characteristics
    easy_events = [
        timeline_generator.events_cache[list(timeline_generator.events_cache.keys())[0]]
    ]
    
    hard_events = list(timeline_generator.events_cache.values())[:10]  # More events = harder
    
    easy_difficulty = timeline_generator._calculate_timeline_difficulty(easy_events)
    hard_difficulty = timeline_generator._calculate_timeline_difficulty(hard_events)
    
    assert 0.0 <= easy_difficulty <= 1.0
    assert 0.0 <= hard_difficulty <= 1.0
    assert hard_difficulty >= easy_difficulty  # More events should be harder


def test_get_event_relationships(timeline_generator):
    """Test getting event relationships."""
    
    # Get first event ID
    event_id = list(timeline_generator.events_cache.keys())[0]
    
    relationships = timeline_generator.get_event_relationships(event_id)
    
    assert isinstance(relationships, dict)
    assert "causes" in relationships
    assert "effects" in relationships
    assert "related_events" in relationships
    assert "key_figures" in relationships
    assert "concepts_taught" in relationships


def test_create_causal_chain_timeline(timeline_generator):
    """Test creating causal chain timeline."""
    
    # Get first event ID
    root_event_id = list(timeline_generator.events_cache.keys())[0]
    
    timeline = timeline_generator.create_causal_chain_timeline(root_event_id)
    
    assert timeline.title.startswith("Cause and Effect Timeline")
    assert timeline.difficulty_level == 0.8  # Should be harder
    assert "causation" in [obj.lower() for obj in timeline.learning_objectives]


def test_create_causal_chain_timeline_nonexistent_event(timeline_generator):
    """Test creating causal chain timeline with nonexistent event."""
    
    with pytest.raises(ValueError, match="Event nonexistent_event not found"):
        timeline_generator.create_causal_chain_timeline("nonexistent_event")


def test_create_comparative_timeline(timeline_generator):
    """Test creating comparative timeline."""
    
    themes = ["war", "politics"]
    
    timeline = timeline_generator.create_comparative_timeline(themes)
    
    assert timeline.title == "Comparative Timeline"
    assert timeline.theme == "Comparison: war, politics"
    assert timeline.difficulty_level == 0.9  # Comparison is high-level
    assert "comparison" in [obj.lower() for obj in timeline.learning_objectives]


def test_export_timeline_data(timeline_generator):
    """Test exporting timeline data for visualization."""
    
    # Create a timeline first
    timeline = timeline_generator.create_timeline("Test Timeline", "Test Theme")
    
    # Export the data
    exported_data = timeline_generator.export_timeline_data(timeline.timeline_id)
    
    assert "timeline" in exported_data
    assert "events" in exported_data
    assert "metadata" in exported_data
    
    # Check timeline data
    timeline_data = exported_data["timeline"]
    assert timeline_data["id"] == timeline.timeline_id
    assert timeline_data["title"] == "Test Timeline"
    assert timeline_data["theme"] == "Test Theme"
    
    # Check events data
    events_data = exported_data["events"]
    assert isinstance(events_data, list)
    
    if events_data:  # If there are events
        event = events_data[0]
        assert "id" in event
        assert "title" in event
        assert "date" in event
        assert "type" in event
        assert "significance" in event
    
    # Check metadata
    metadata = exported_data["metadata"]
    assert "totalEvents" in metadata
    assert "timeSpan" in metadata
    assert "eventTypes" in metadata


def test_export_timeline_data_nonexistent_timeline(timeline_generator):
    """Test exporting data for nonexistent timeline."""
    
    exported_data = timeline_generator.export_timeline_data("nonexistent_timeline")
    
    assert exported_data == {}


def test_get_available_timelines(timeline_generator):
    """Test getting available timelines."""
    
    # Create some timelines first
    timeline1 = timeline_generator.create_timeline("Timeline 1", "Theme 1")
    timeline2 = timeline_generator.create_timeline("Timeline 2", "Theme 2")
    
    available = timeline_generator.get_available_timelines()
    
    assert isinstance(available, list)
    assert len(available) >= 2
    
    # Check structure of timeline info
    timeline_info = available[0]
    assert "id" in timeline_info
    assert "title" in timeline_info
    assert "theme" in timeline_info
    assert "events_count" in timeline_info
    assert "difficulty" in timeline_info


def test_get_timeline_by_theme(timeline_generator):
    """Test getting timeline by theme."""
    
    # Create a timeline with specific theme
    original_timeline = timeline_generator.create_timeline("Test Timeline", "Unique Theme")
    
    # Retrieve by theme
    retrieved_timeline = timeline_generator.get_timeline_by_theme("Unique Theme")
    
    assert retrieved_timeline is not None
    assert retrieved_timeline.theme == "Unique Theme"
    assert retrieved_timeline.timeline_id == original_timeline.timeline_id
    
    # Test nonexistent theme
    nonexistent = timeline_generator.get_timeline_by_theme("Nonexistent Theme")
    assert nonexistent is None


def test_parse_date_for_sorting(timeline_generator):
    """Test date parsing for sorting."""
    
    # Test various date formats
    assert timeline_generator._parse_date_for_sorting("1914") == "1914"
    assert timeline_generator._parse_date_for_sorting("914") == "0914"  # Padded
    assert timeline_generator._parse_date_for_sorting("invalid") == "1900"  # Fallback


def test_calculate_time_span(timeline_generator):
    """Test time span calculation."""
    
    timeline = timeline_generator.create_timeline("Test Timeline", "Test Theme")
    timeline.date_range_start = "1914"
    timeline.date_range_end = "1918"
    
    time_span = timeline_generator._calculate_time_span(timeline)
    
    assert time_span["years"] == 4
    assert "1914" in time_span["description"]
    assert "1918" in time_span["description"]


def test_get_event_type_distribution(timeline_generator):
    """Test event type distribution calculation."""
    
    events = list(timeline_generator.events_cache.values())[:5]
    
    distribution = timeline_generator._get_event_type_distribution(events)
    
    assert isinstance(distribution, dict)
    
    # All values should be positive integers
    for event_type, count in distribution.items():
        assert isinstance(count, int)
        assert count > 0