"""Tests for history sources module."""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from src.history.schemas import PrimarySource, SourceType, HistoricalPeriod
from src.history.sources.analyzer import PrimarySourceAnalyzer
from src.history.sources.bias_detector import BiasDetector
from src.history.sources.document_processor import DocumentProcessor


class TestPrimarySourceAnalyzer:
    """Test the primary source analyzer."""
    
    @pytest.fixture
    def mock_retriever(self):
        """Create mock knowledge retriever."""
        return Mock()
    
    @pytest.fixture
    def analyzer(self, mock_retriever):
        """Create primary source analyzer."""
        return PrimarySourceAnalyzer(mock_retriever)
    
    @pytest.fixture
    def sample_source(self):
        """Create sample primary source."""
        return PrimarySource(
            source_id="test_001",
            title="Letter from President Lincoln",
            description="Personal letter discussing Civil War strategy",
            source_type=SourceType.LETTER,
            content="My dear General, the situation requires immediate action...",
            date_created="1863-07-15",
            author="Abraham Lincoln",
            historical_period=HistoricalPeriod.MODERN_ERA,
            complexity_level=0.6
        )
    
    @pytest.mark.asyncio
    async def test_analyze_primary_source(self, analyzer, sample_source):
        """Test primary source analysis."""
        # Mock LLM response
        analyzer.llm = AsyncMock()
        mock_response = Mock()
        mock_response.content = "Historical analysis of the source..."
        analyzer.llm.ainvoke.return_value = mock_response
        
        result = await analyzer.analyze_primary_source(
            source=sample_source,
            student_level="intermediate"
        )
        
        assert result["source_id"] == sample_source.source_id
        assert "basic_analysis" in result
        assert "bias_analysis" in result
        assert "educational_analysis" in result
        assert "generated_questions" in result
    
    def test_infer_thinking_skill(self, analyzer):
        """Test thinking skill inference from questions."""
        from src.history.schemas import HistoricalThinkingSkill
        
        # Test different question types
        questions = [
            ("Who wrote this document?", HistoricalThinkingSkill.SOURCE_ANALYSIS),
            ("When did this event occur?", HistoricalThinkingSkill.CHRONOLOGICAL_REASONING),
            ("What was the historical context?", HistoricalThinkingSkill.COMPARISON_CONTEXTUALIZATION),
            ("What argument does this support?", HistoricalThinkingSkill.CRAFTING_ARGUMENTS)
        ]
        
        for question, expected_skill in questions:
            result = analyzer._infer_thinking_skill(question)
            assert result == expected_skill
    
    @pytest.mark.asyncio
    async def test_create_source_comparison_activity(self, analyzer, sample_source):
        """Test source comparison activity creation."""
        # Create multiple sources
        source2 = PrimarySource(
            source_id="test_002",
            title="Confederate General's Report", 
            description="Military report from Confederate perspective",
            source_type=SourceType.GOVERNMENT_RECORD,
            content="The Union forces have advanced...",
            date_created="1863-07-20",
            author="General Robert E. Lee",
            historical_period=HistoricalPeriod.MODERN_ERA
        )
        
        sources = [sample_source, source2]
        
        # Mock LLM for question generation
        analyzer.llm = AsyncMock()
        mock_response = Mock()
        mock_response.content = "1. How do perspectives differ? 2. What evidence is presented?"
        analyzer.llm.ainvoke.return_value = mock_response
        
        activity = await analyzer.create_source_comparison_activity(
            sources=sources,
            comparison_theme="Civil War Perspectives",
            student_level="intermediate"
        )
        
        assert activity["title"] == "Comparative Analysis: Civil War Perspectives"
        assert len(activity["sources"]) == 2
        assert "comparison_framework" in activity
        assert "synthesis_task" in activity


class TestBiasDetector:
    """Test the bias detection system."""
    
    @pytest.fixture
    def bias_detector(self):
        """Create bias detector."""
        return BiasDetector()
    
    @pytest.fixture
    def biased_source(self):
        """Create source with potential bias."""
        return PrimarySource(
            source_id="bias_001",
            title="Newspaper Editorial on Immigration",
            description="Editorial expressing strong anti-immigration views",
            source_type=SourceType.NEWSPAPER,
            content="These foreign elements are destroying our civilization and must be stopped at all costs...",
            date_created="1920-03-15",
            author="Editorial Board",
            historical_period=HistoricalPeriod.MODERN_ERA
        )
    
    @pytest.mark.asyncio
    async def test_detect_bias(self, bias_detector, biased_source):
        """Test bias detection in primary source."""
        # Mock LLM response
        bias_detector.llm = AsyncMock()
        mock_response = Mock()
        mock_response.content = "The source shows clear cultural bias and loaded language..."
        bias_detector.llm.ainvoke.return_value = mock_response
        
        result = await bias_detector.detect_bias(biased_source)
        
        assert result["source_id"] == biased_source.source_id
        assert "bias_types_detected" in result
        assert "reliability_impact" in result
        assert "teaching_opportunities" in result
        
        # Should detect some bias types
        assert len(result["bias_types_detected"]) > 0
    
    def test_bias_pattern_detection(self, bias_detector, biased_source):
        """Test automated bias pattern detection."""
        detected_biases = asyncio.run(
            bias_detector._detect_bias_patterns(biased_source)
        )
        
        # Should detect bias based on content
        assert len(detected_biases) > 0
        assert any(bias in ["personal_bias", "cultural_bias", "political_bias"] 
                  for bias in detected_biases)
    
    def test_assess_reliability_impact(self, bias_detector):
        """Test reliability impact assessment."""
        bias_types = ["cultural_bias", "political_bias", "selection_bias"]
        bias_indicators = {"language_indicators": ["loaded language"]}
        
        impact = bias_detector._assess_reliability_impact(bias_types, bias_indicators)
        
        assert "reliability_score" in impact
        assert "major_concerns" in impact  
        assert "impact_assessment" in impact
        assert 0.0 <= impact["reliability_score"] <= 1.0


class TestDocumentProcessor:
    """Test the document processing system."""
    
    @pytest.fixture
    def processor(self):
        """Create document processor."""
        return DocumentProcessor()
    
    def test_determine_source_type(self, processor):
        """Test source type determination."""
        # Test with different content types
        test_cases = [
            ("Dear Sir, I write to inform you...", SourceType.LETTER),
            ("Today I visited the battlefield...", SourceType.DIARY),
            ("Ladies and gentlemen, we gather today...", SourceType.SPEECH),
            ("Article 1: The following terms shall apply...", SourceType.TREATY)
        ]
        
        for content, expected_type in test_cases:
            file_info = {"format": "text", "filename": "test.txt"}
            extracted_content = {"text": content}
            
            result = processor._determine_source_type(
                file_info, extracted_content, {}, {}
            )
            
            assert result == expected_type
    
    @pytest.mark.asyncio
    async def test_extract_date_from_content(self, processor):
        """Test date extraction from text content."""
        test_content = "On July 4, 1776, the Continental Congress approved..."
        
        result = await processor._extract_date_from_content(test_content)
        
        assert result is not None
        assert "1776" in result
    
    @pytest.mark.asyncio
    async def test_extract_author_from_content(self, processor):
        """Test author extraction from text content."""
        test_content = "Signed by George Washington, Commander in Chief..."
        
        result = await processor._extract_author_from_content(test_content)
        
        # Should find some author information
        assert result is not None
    
    def test_calculate_complexity_level(self, processor):
        """Test complexity level calculation."""
        # Simple content
        simple_content = {"text": "The war began in 1914."}
        simple_metadata = {"date_created": "1920"}
        
        simple_complexity = processor._calculate_complexity_level(simple_content, simple_metadata)
        
        # Complex content  
        complex_content = {"text": "The multifaceted socioeconomic ramifications of industrialization fundamentally transformed the societal infrastructure..."}
        complex_metadata = {"date_created": "1850"}
        
        complex_complexity = processor._calculate_complexity_level(complex_content, complex_metadata)
        
        assert 0.0 <= simple_complexity <= 1.0
        assert 0.0 <= complex_complexity <= 1.0
        assert complex_complexity > simple_complexity
    
    @pytest.mark.asyncio
    async def test_process_document_text_content(self, processor):
        """Test processing of text document."""
        test_content = b"My fellow citizens, we face a great challenge..."
        
        result = await processor.process_document(
            file_content=test_content,
            metadata={
                "title": "Presidential Address",
                "author": "President Roosevelt",
                "date_created": "1941-12-07"
            }
        )
        
        assert result.source_type in [SourceType.SPEECH, SourceType.DOCUMENT]
        assert result.title == "Presidential Address"
        assert result.author == "President Roosevelt"
        assert result.content is not None
    
    def test_file_format_detection(self, processor):
        """Test file format detection from content."""
        # JPEG signature
        jpeg_content = b'\xFF\xD8\xFF\xE0'
        format_type = processor._detect_format_from_content(jpeg_content)
        assert format_type == "image"
        
        # PDF signature  
        pdf_content = b'%PDF-1.4'
        format_type = processor._detect_format_from_content(pdf_content)
        assert format_type == "text"
        
        # Plain text
        text_content = b'This is plain text content'
        format_type = processor._detect_format_from_content(text_content)
        assert format_type == "text"


class TestHistoryIntegration:
    """Integration tests for history module components."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_source_analysis(self):
        """Test complete source analysis workflow."""
        # Create a realistic primary source
        source = PrimarySource(
            source_id="integration_001",
            title="Emancipation Proclamation",
            description="Presidential proclamation freeing slaves in rebellious states",
            source_type=SourceType.GOVERNMENT_RECORD,
            content="""By the President of the United States of America:
            A Proclamation.
            Whereas, on the twenty-second day of September, in the year of our Lord one thousand eight hundred and sixty-two...
            That all persons held as slaves within any State or designated part of a State, the people whereof shall then be in rebellion against the United States, shall be then, thenceforward, and forever free...""",
            date_created="1863-01-01",
            author="Abraham Lincoln",
            historical_period=HistoricalPeriod.MODERN_ERA,
            complexity_level=0.8
        )
        
        # Create analyzer with mocked dependencies
        mock_retriever = Mock()
        analyzer = PrimarySourceAnalyzer(mock_retriever)
        
        # Mock LLM responses
        analyzer.llm = AsyncMock()
        mock_response = Mock()
        mock_response.content = """
        This source demonstrates significant historical importance as a pivotal document
        in American Civil War history. The language is formal and legal, reflecting
        the presidential authority behind the proclamation.
        """
        analyzer.llm.ainvoke.return_value = mock_response
        
        # Perform analysis
        result = await analyzer.analyze_primary_source(
            source=source,
            student_level="advanced",
            focus_skills=None
        )
        
        # Verify comprehensive analysis
        assert result["source_id"] == source.source_id
        assert "basic_analysis" in result
        assert "educational_analysis" in result
        assert "generated_questions" in result
        
        # Check educational analysis components
        educational_analysis = result["educational_analysis"]
        assert "difficulty_assessment" in educational_analysis
        assert "skill_development" in educational_analysis
        
        # Verify questions were generated
        questions = result["generated_questions"]
        assert len(questions) > 0
        assert all(isinstance(q, dict) for q in questions)
        assert all("question" in q for q in questions)
    
    def test_source_type_detection_accuracy(self):
        """Test accuracy of source type detection across different content."""
        processor = DocumentProcessor()
        
        test_cases = [
            {
                "content": "My Dearest Wife, I hope this letter finds you well during these troubled times of war...",
                "expected": SourceType.LETTER,
                "filename": "soldier_letter.txt"
            },
            {
                "content": "We, the representatives of the United States of America, in General Congress assembled...",
                "expected": SourceType.GOVERNMENT_RECORD,
                "filename": "declaration.txt"
            },
            {
                "content": "Today marks the third week of our journey across the plains. The oxen are growing weary...",
                "expected": SourceType.DIARY,
                "filename": "pioneer_diary.txt"
            },
            {
                "content": "Article I: The High Contracting Parties agree to the following terms...",
                "expected": SourceType.TREATY,
                "filename": "peace_treaty.txt"
            }
        ]
        
        for test_case in test_cases:
            file_info = {"format": "text", "filename": test_case["filename"]}
            extracted_content = {"text": test_case["content"]}
            
            detected_type = processor._determine_source_type(
                file_info, extracted_content, {}, {}
            )
            
            assert detected_type == test_case["expected"], f"Failed for content: {test_case['content'][:50]}..."