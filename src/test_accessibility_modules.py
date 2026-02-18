"""
Comprehensive tests for accessibility modules

Tests both accessibility_engine.py and disability_aware_fsrs.py
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from accessibility_engine import (
    AccessibilityEngine, AccessibilityProfile, VoiceOnlyMode, 
    SimplifiedLanguageProcessor, PatienceMode, AccessibilityDetector,
    SpeechConfig, HighContrastConfig, DyslexiaFriendlyConfig,
    ImpairmentType, SeverityLevel
)

from disability_aware_fsrs import (
    DisabilityAwareFSRS, CognitiveMemoryProfile, CardState, 
    ReviewOutcome, CognitiveProfile
)


class TestAccessibilityProfile:
    """Test AccessibilityProfile class"""
    
    def test_profile_creation(self):
        """Test basic profile creation"""
        profile = AccessibilityProfile(user_id="test_user")
        assert profile.user_id == "test_user"
        assert not profile.requires_voice_only
        assert not profile.needs_simplified_language
        assert not profile.requires_patience_mode
        
    def test_add_visual_impairment(self):
        """Test adding visual impairment"""
        profile = AccessibilityProfile(user_id="test_user")
        profile.add_impairment(ImpairmentType.VISUAL, "blindness", SeverityLevel.SEVERE)
        
        assert "blindness" in profile.visual_impairments
        assert profile.visual_impairments["blindness"] == SeverityLevel.SEVERE
        assert profile.requires_voice_only  # Should auto-enable for severe visual impairment
        
    def test_add_cognitive_impairment(self):
        """Test adding cognitive impairment"""
        profile = AccessibilityProfile(user_id="test_user")
        profile.add_impairment(ImpairmentType.COGNITIVE, "dyslexia", SeverityLevel.MODERATE)
        
        assert "dyslexia" in profile.cognitive_impairments
        assert profile.needs_simplified_language  # Should auto-enable
        assert profile.requires_patience_mode  # Should auto-enable
        
    def test_add_motor_impairment(self):
        """Test adding motor impairment"""
        profile = AccessibilityProfile(user_id="test_user")
        profile.add_impairment(ImpairmentType.MOTOR, "limited_mobility", SeverityLevel.MILD)
        
        assert "limited_mobility" in profile.motor_impairments
        assert not profile.requires_patience_mode  # Mild should not trigger patience mode
        
        # Test moderate motor impairment
        profile.add_impairment(ImpairmentType.MOTOR, "limited_mobility", SeverityLevel.MODERATE)
        assert profile.requires_patience_mode  # Should trigger patience mode


class TestVoiceOnlyMode:
    """Test VoiceOnlyMode class"""
    
    def test_voice_only_initialization(self):
        """Test voice-only mode initialization"""
        speech_config = SpeechConfig(rate=0.8, pitch=1.2)
        voice_mode = VoiceOnlyMode(speech_config)
        
        assert voice_mode.speech_config.rate == 0.8
        assert voice_mode.speech_config.pitch == 1.2
        assert len(voice_mode.conversation_history) == 0
        
    def test_start_lesson(self):
        """Test starting a lesson in voice-only mode"""
        voice_mode = VoiceOnlyMode()
        intro = voice_mode.start_lesson("Today we'll learn about photosynthesis")
        
        assert "Welcome" in intro
        assert "step by step" in intro
        assert len(voice_mode.conversation_history) == 1
        assert voice_mode.conversation_history[0]["type"] == "lesson_start"
        
    def test_present_text_content(self):
        """Test presenting text content"""
        voice_mode = VoiceOnlyMode()
        content = "Plants use sunlight to make food."
        adapted = voice_mode.present_content(content, "text")
        
        assert "<pause>" in adapted
        assert len(voice_mode.conversation_history) == 1
        
    def test_present_math_content(self):
        """Test presenting mathematical content"""
        voice_mode = VoiceOnlyMode()
        math_content = "2 + 3 = 5"
        adapted = voice_mode.present_content(math_content, "math")
        
        assert "plus" in adapted
        assert "equals" in adapted
        assert "2 plus 3 equals 5" == adapted
        
    def test_math_to_speech_conversion(self):
        """Test various math-to-speech conversions"""
        voice_mode = VoiceOnlyMode()
        
        test_cases = [
            ("x² + 4", "x squared plus 4"),
            ("y³ - 2", "y cubed minus 2"), 
            ("10 / 5", "10 divided by 5"),
            ("6 * 7", "6 times 7")
        ]
        
        for math_input, expected in test_cases:
            result = voice_mode._math_to_speech(math_input)
            assert result == expected
            
    def test_handle_user_response(self):
        """Test handling user responses"""
        voice_mode = VoiceOnlyMode()
        response = voice_mode.handle_user_response("I understand photosynthesis")
        
        assert "I understand you said" in response
        assert len(voice_mode.conversation_history) == 1
        assert voice_mode.conversation_history[0]["type"] == "user_interaction"


class TestSimplifiedLanguageProcessor:
    """Test SimplifiedLanguageProcessor class"""
    
    def test_word_simplification(self):
        """Test complex word replacement"""
        processor = SimplifiedLanguageProcessor()
        text = "I will demonstrate how to utilize this tool."
        simplified = processor.simplify_text(text)
        
        assert "show" in simplified
        assert "use" in simplified
        assert "demonstrate" not in simplified
        assert "utilize" not in simplified
        
    def test_sentence_splitting(self):
        """Test long sentence splitting"""
        processor = SimplifiedLanguageProcessor(max_sentence_length=5)
        text = "This is a very long sentence that should be split into smaller parts."
        simplified = processor.simplify_text(text)
        
        # Should be split into multiple sentences
        sentences = simplified.split('. ')
        assert len(sentences) > 1
        
    def test_conjunction_splitting(self):
        """Test splitting on conjunctions"""
        processor = SimplifiedLanguageProcessor(max_sentence_length=5)  # Force splitting
        sentence = "Plants need water and they also need sunlight to grow properly."
        result = processor._split_long_sentence(sentence)
        
        assert len(result) == 2
        assert "water" in result[0]
        assert "sunlight" in result[1]
        
    def test_add_examples(self):
        """Test adding examples to concepts"""
        processor = SimplifiedLanguageProcessor()
        concept = "Photosynthesis is how plants make food"
        with_examples = processor.add_examples(concept, ["A tree using sunlight"])
        
        assert "For example" in with_examples
        assert "A tree using sunlight" in with_examples


class TestPatienceMode:
    """Test PatienceMode class"""
    
    def test_base_timeout(self):
        """Test basic timeout functionality"""
        patience = PatienceMode(base_timeout=30.0)
        timeout = patience.get_adaptive_timeout("user1")
        
        assert timeout == 30.0  # Should return base timeout initially
        
    def test_adaptive_timeout(self):
        """Test adaptive timeout based on response times"""
        patience = PatienceMode(base_timeout=30.0)
        
        # Record some response times
        patience.record_response_time(20.0)
        patience.record_response_time(25.0)
        patience.record_response_time(30.0)
        
        timeout = patience.get_adaptive_timeout("user1")
        expected = max(30.0, 25.0 * 3)  # 3x average, minimum base_timeout
        assert timeout == expected
        
    def test_encouragement_messages(self):
        """Test encouragement messages at different wait times"""
        patience = PatienceMode()
        
        # No message for short waits
        message = patience.get_encouragement_message(10.0)
        assert message is None
        
        # Messages for longer waits
        message = patience.get_encouragement_message(20.0)
        assert message is not None
        assert "Take your time" in message
        
        message = patience.get_encouragement_message(70.0)
        assert "all the time you need" in message
        
    def test_response_time_history_limit(self):
        """Test that response time history is limited"""
        patience = PatienceMode()
        
        # Add more than 50 response times
        for i in range(60):
            patience.record_response_time(float(i))
            
        assert len(patience.user_response_times) == 50


class TestAccessibilityDetector:
    """Test AccessibilityDetector class"""
    
    def test_slow_typing_detection(self):
        """Test detection of slow typing patterns"""
        detector = AccessibilityDetector()
        
        # Simulate slow typing (10 WPM = very slow)
        for _ in range(6):  # Need at least 5 measurements
            slow_typing = detector.analyze_typing_pattern("user1", 20, 24.0)  # 20 chars in 24 seconds
            
        assert slow_typing  # Should detect slow typing pattern
        
    def test_error_pattern_detection(self):
        """Test detection of frequent error patterns"""
        detector = AccessibilityDetector()
        
        # Simulate interactions with errors
        detector.response_times["user1"] = [10.0] * 15  # 15 total interactions
        
        # Record errors (8 out of 15 = 53% error rate)
        for _ in range(8):
            frequent_errors = detector.analyze_error_pattern("user1", True)
            
        assert frequent_errors  # Should detect frequent error pattern
        
    def test_accommodation_suggestions(self):
        """Test suggestion of accommodations"""
        detector = AccessibilityDetector()
        
        # Set up patterns that should trigger suggestions
        detector.typing_speeds["user1"] = [15.0] * 10  # Slow typing
        detector.error_counts["user1"] = 5
        detector.response_times["user1"] = [50.0] * 10  # Slow responses (total: 10 interactions)
        
        suggestions = detector.suggest_accommodations("user1")
        
        assert "voice_input" in suggestions
        assert "simplified_language" in suggestions
        assert "patience_mode" in suggestions


class TestAccessibilityEngine:
    """Test main AccessibilityEngine class"""
    
    def test_engine_initialization(self):
        """Test engine initialization"""
        engine = AccessibilityEngine()
        
        assert len(engine.profiles) == 0
        assert len(engine.voice_only_sessions) == 0
        assert engine.language_processor is not None
        assert engine.patience_mode is not None
        assert engine.detector is not None
        
    def test_create_and_get_profile(self):
        """Test profile creation and retrieval"""
        engine = AccessibilityEngine()
        
        profile = engine.create_profile("user1")
        assert profile.user_id == "user1"
        
        retrieved = engine.get_profile("user1")
        assert retrieved == profile
        
        # Test non-existent user
        assert engine.get_profile("non_existent") is None
        
    def test_voice_only_session(self):
        """Test voice-only session management"""
        engine = AccessibilityEngine()
        speech_config = SpeechConfig(rate=0.9)
        
        session = engine.start_voice_only_session("user1", speech_config)
        assert "user1" in engine.voice_only_sessions
        assert engine.voice_only_sessions["user1"] == session
        assert session.speech_config.rate == 0.9
        
    def test_content_processing(self):
        """Test content processing based on accessibility needs"""
        engine = AccessibilityEngine()
        
        # Create profile with accessibility needs
        profile = engine.create_profile("user1")
        profile.needs_simplified_language = True
        profile.requires_voice_only = True
        
        # Start voice session
        engine.start_voice_only_session("user1")
        
        original_content = "I will demonstrate how to utilize this methodology."
        processed = engine.process_content("user1", original_content)
        
        # Should be simplified and voice-adapted
        assert "show" in processed or "use" in processed  # Word simplification
        assert processed != original_content
        
    def test_ui_config_generation(self):
        """Test UI configuration generation"""
        engine = AccessibilityEngine()
        
        # Create profile with visual impairments
        profile = engine.create_profile("user1")
        profile.add_impairment(ImpairmentType.VISUAL, "low_vision", SeverityLevel.MODERATE)
        profile.add_impairment(ImpairmentType.COGNITIVE, "dyslexia", SeverityLevel.MILD)
        
        config = engine.get_ui_config("user1")
        
        assert "high_contrast" in config
        assert config["high_contrast"].enabled
        assert "dyslexia_friendly" in config
        assert config["dyslexia_friendly"].enabled
        
    def test_interaction_analysis(self):
        """Test interaction analysis for pattern detection"""
        engine = AccessibilityEngine()
        
        # Simulate slow typing interaction
        interaction_data = {
            "typing_time": 30.0,
            "text_length": 25,
            "has_error": True
        }
        
        with patch.object(engine.detector, 'analyze_typing_pattern', return_value=True):
            with patch.object(engine.detector, 'analyze_error_pattern', return_value=False):
                with patch.object(engine.detector, 'suggest_accommodations', return_value=['voice_input']):
                    engine.analyze_interaction("user1", interaction_data)
                    
                    # Should create profile and apply suggestions
                    profile = engine.get_profile("user1")
                    assert profile is not None


class TestCognitiveMemoryProfile:
    """Test CognitiveMemoryProfile class"""
    
    def test_standard_profile_creation(self):
        """Test creation of standard cognitive profile"""
        profile = CognitiveMemoryProfile(profile_type=CognitiveProfile.STANDARD)
        
        assert profile.profile_type == CognitiveProfile.STANDARD
        assert profile.stability_modifier == 1.0
        assert profile.retention_target == 0.9
        
    def test_adhd_profile_creation(self):
        """Test creation of ADHD-specific profile"""
        profile = CognitiveMemoryProfile.create_for_condition("adhd", SeverityLevel.MODERATE)
        
        assert profile.profile_type == CognitiveProfile.ATTENTION_DEFICIT
        assert profile.stability_modifier < 1.0  # Should be reduced
        assert profile.frequent_review_multiplier > 1.0  # More frequent reviews
        assert profile.max_difficulty_ceiling <= 6.0
        
    def test_dyslexia_profile_creation(self):
        """Test creation of dyslexia-specific profile"""
        profile = CognitiveMemoryProfile.create_for_condition("dyslexia", SeverityLevel.SEVERE)
        
        assert profile.profile_type == CognitiveProfile.LEARNING_DISABILITY
        assert profile.consolidation_speed < 1.0  # Slower consolidation
        assert profile.difficulty_sensitivity < 1.0  # Less sensitive to difficulty
        
    def test_autism_profile_creation(self):
        """Test creation of autism spectrum profile"""
        profile = CognitiveMemoryProfile.create_for_condition("autism", SeverityLevel.MILD)
        
        assert profile.profile_type == CognitiveProfile.AUTISM_SPECTRUM
        assert profile.stability_modifier >= 1.0  # Often good memory
        assert profile.encouragement_threshold > 0.6  # Need more positive reinforcement


class TestDisabilityAwareFSRS:
    """Test DisabilityAwareFSRS class"""
    
    def test_fsrs_initialization(self):
        """Test FSRS initialization"""
        fsrs = DisabilityAwareFSRS()
        
        assert len(fsrs.parameters) == 18  # Standard FSRS parameter count
        assert len(fsrs.cognitive_profiles) == 0
        assert len(fsrs.encouragement_messages) > 0
        
    def test_profile_registration(self):
        """Test cognitive profile registration"""
        fsrs = DisabilityAwareFSRS()
        
        # Create accessibility profile
        accessibility_profile = AccessibilityProfile(user_id="user1")
        accessibility_profile.add_impairment(ImpairmentType.COGNITIVE, "dyslexia", SeverityLevel.MODERATE)
        
        fsrs.register_cognitive_profile("user1", accessibility_profile)
        
        profile = fsrs.get_cognitive_profile("user1")
        assert profile.profile_type == CognitiveProfile.LEARNING_DISABILITY
        
    def test_new_card_scheduling(self):
        """Test scheduling of new cards"""
        fsrs = DisabilityAwareFSRS()
        
        # Test with standard profile
        card = fsrs.schedule_new_card("user1")
        assert card.stability > 0
        assert card.difficulty > 0
        assert card.due_date > datetime.now()
        
        # Test with learning disability profile
        accessibility_profile = AccessibilityProfile(user_id="user2")
        accessibility_profile.add_impairment(ImpairmentType.COGNITIVE, "intellectual_disability", SeverityLevel.SEVERE)
        fsrs.register_cognitive_profile("user2", accessibility_profile)
        
        card_ld = fsrs.schedule_new_card("user2")
        assert card_ld.difficulty <= fsrs.get_cognitive_profile("user2").max_difficulty_ceiling
        
    def test_review_scheduling(self):
        """Test review scheduling with different outcomes"""
        fsrs = DisabilityAwareFSRS()
        
        # Create initial card
        card = fsrs.schedule_new_card("user1")
        original_stability = card.stability
        
        # Test successful review
        updated_card = fsrs.schedule_review("user1", card, ReviewOutcome.GOOD)
        assert updated_card.review_count == 1
        assert updated_card.stability >= original_stability
        assert updated_card.last_review is not None
        
        # Test failed review
        failed_card = fsrs.schedule_review("user1", card, ReviewOutcome.AGAIN)
        assert failed_card.lapses == 1
        assert failed_card.encouragement_needed
        
    def test_encouragement_reviews(self):
        """Test encouragement review functionality"""
        fsrs = DisabilityAwareFSRS()
        
        # Register learning disability profile
        accessibility_profile = AccessibilityProfile(user_id="user1")
        accessibility_profile.add_impairment(ImpairmentType.COGNITIVE, "dyslexia", SeverityLevel.MODERATE)
        fsrs.register_cognitive_profile("user1", accessibility_profile)
        
        # Create cards with lapses
        cards = []
        for i in range(3):
            card = fsrs.schedule_new_card("user1")
            card.lapses = 2
            card.last_review = datetime.now() - timedelta(days=2)
            cards.append(card)
            
        encouragement_cards = fsrs.get_encouragement_review_cards("user1", cards)
        assert len(encouragement_cards) == 3
        
    def test_encouragement_messages(self):
        """Test encouragement message generation"""
        fsrs = DisabilityAwareFSRS()
        
        card = CardState(
            due_date=datetime.now(),
            stability=1.0,
            difficulty=5.0
        )
        
        # Test different outcomes
        for outcome in [ReviewOutcome.AGAIN, ReviewOutcome.GOOD, ReviewOutcome.EASY]:
            message = fsrs.get_encouragement_message("user1", card, outcome)
            assert isinstance(message, str)
            assert len(message) > 0
            
    def test_difficulty_ceiling_adaptation(self):
        """Test adaptive difficulty ceiling"""
        fsrs = DisabilityAwareFSRS()
        
        # Start with standard profile ceiling (8.0)
        original_ceiling = 8.0
        
        # High success rate should increase ceiling
        fsrs.adapt_difficulty_ceiling("user1", 0.85)
        after_increase = fsrs.get_cognitive_profile("user1").max_difficulty_ceiling
        assert after_increase > original_ceiling
        
        # Low success rate should decrease ceiling from the increased value
        fsrs.adapt_difficulty_ceiling("user1", 0.55)
        after_decrease = fsrs.get_cognitive_profile("user1").max_difficulty_ceiling
        assert after_decrease < after_increase
        
    def test_session_config_generation(self):
        """Test review session configuration"""
        fsrs = DisabilityAwareFSRS()
        
        # Standard profile config
        config = fsrs.get_review_session_config("user1")
        assert "max_new_cards" in config
        assert "session_time_limit" in config
        
        # ADHD profile config (should be adjusted)
        accessibility_profile = AccessibilityProfile(user_id="user2")
        accessibility_profile.add_impairment(ImpairmentType.COGNITIVE, "adhd", SeverityLevel.MODERATE)
        fsrs.register_cognitive_profile("user2", accessibility_profile)
        
        adhd_config = fsrs.get_review_session_config("user2")
        assert adhd_config["max_new_cards"] < config["max_new_cards"]
        assert adhd_config["break_frequency"] < config["break_frequency"]
        
    def test_performance_report(self):
        """Test performance report generation"""
        fsrs = DisabilityAwareFSRS()
        
        # Create some test cards
        cards = []
        for i in range(5):
            card = fsrs.schedule_new_card("user1")
            card.review_count = 3
            card.lapses = 1 if i < 2 else 0  # 2 out of 5 have lapses
            cards.append(card)
            
        report = fsrs.generate_performance_report("user1", cards)
        
        assert report["total_cards"] == 5
        assert report["total_reviews"] == 15
        assert "success_rate" in report
        assert "recommendations" in report
        assert isinstance(report["recommendations"], list)


class TestIntegration:
    """Integration tests for both modules working together"""
    
    def test_accessibility_engine_fsrs_integration(self):
        """Test integration between accessibility engine and FSRS"""
        # Create accessibility engine
        accessibility_engine = AccessibilityEngine()
        
        # Create FSRS
        fsrs = DisabilityAwareFSRS()
        
        # Create user profile with dyslexia
        profile = accessibility_engine.create_profile("user1")
        profile.add_impairment(ImpairmentType.COGNITIVE, "dyslexia", SeverityLevel.MODERATE)
        profile.add_impairment(ImpairmentType.VISUAL, "low_vision", SeverityLevel.MILD)
        
        # Register profile with FSRS
        fsrs.register_cognitive_profile("user1", profile)
        
        # Get UI config from accessibility engine
        ui_config = accessibility_engine.get_ui_config("user1")
        
        # Get session config from FSRS
        session_config = fsrs.get_review_session_config("user1")
        
        # Verify both work together
        assert ui_config["dyslexia_friendly"].enabled
        assert ui_config["high_contrast"].enabled
        assert session_config["allow_hints"]  # Should be enabled for learning disabilities
        
        # Test content processing with simplified language - use words that will be simplified
        content = "I will demonstrate how to utilize this methodology."
        processed = accessibility_engine.process_content("user1", content)
        
        # Should be simplified (complex words should be replaced)
        assert "show" in processed or "use" in processed  # Some simplification occurred
        
        # Create and schedule a card
        card = fsrs.schedule_new_card("user1")
        cognitive_profile = fsrs.get_cognitive_profile("user1")
        
        # Difficulty should be limited for learning disability
        assert card.difficulty <= cognitive_profile.max_difficulty_ceiling


# Run the tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])