"""
Accessibility Engine - Core accessibility service for inclusive learning

This module provides comprehensive accessibility features for educational AI,
including profiles for different disabilities, adaptive interfaces, and
automatic detection of accessibility needs.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import re
import time
import logging

logger = logging.getLogger(__name__)


class SeverityLevel(Enum):
    """Severity levels for disabilities"""
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class ImpairmentType(Enum):
    """Types of impairments supported"""
    VISUAL = "visual"
    HEARING = "hearing"
    COGNITIVE = "cognitive"
    MOTOR = "motor"


@dataclass
class AccessibilityProfile:
    """
    Stores user's accessibility needs and preferences
    """
    user_id: str
    visual_impairments: Dict[str, SeverityLevel] = field(default_factory=dict)
    hearing_impairments: Dict[str, SeverityLevel] = field(default_factory=dict)
    cognitive_impairments: Dict[str, SeverityLevel] = field(default_factory=dict)
    motor_impairments: Dict[str, SeverityLevel] = field(default_factory=dict)
    
    # Preferences
    preferred_interaction_mode: str = "standard"
    requires_voice_only: bool = False
    needs_simplified_language: bool = False
    requires_patience_mode: bool = False
    
    # Auto-detected patterns
    slow_typing_pattern: bool = False
    frequent_errors_pattern: bool = False
    long_response_times: bool = False
    
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def add_impairment(self, impairment_type: ImpairmentType, 
                      condition: str, severity: SeverityLevel):
        """Add an impairment to the profile"""
        if impairment_type == ImpairmentType.VISUAL:
            self.visual_impairments[condition] = severity
        elif impairment_type == ImpairmentType.HEARING:
            self.hearing_impairments[condition] = severity
        elif impairment_type == ImpairmentType.COGNITIVE:
            self.cognitive_impairments[condition] = severity
        elif impairment_type == ImpairmentType.MOTOR:
            self.motor_impairments[condition] = severity
        
        self.updated_at = time.time()
        self._update_preferences()

    def _update_preferences(self):
        """Update preferences based on impairments"""
        # Voice-only mode for severe visual impairments
        if any(severity == SeverityLevel.SEVERE 
               for severity in self.visual_impairments.values()):
            self.requires_voice_only = True
            
        # Simplified language for cognitive impairments
        if any(severity in [SeverityLevel.MODERATE, SeverityLevel.SEVERE]
               for severity in self.cognitive_impairments.values()):
            self.needs_simplified_language = True
            
        # Patience mode for motor or cognitive impairments
        if (any(severity != SeverityLevel.MILD 
                for severity in self.motor_impairments.values()) or
            any(severity != SeverityLevel.MILD 
                for severity in self.cognitive_impairments.values())):
            self.requires_patience_mode = True


@dataclass
class SpeechConfig:
    """Configuration for speech synthesis"""
    rate: float = 1.0  # Speech rate (0.5 to 2.0)
    pitch: float = 1.0  # Pitch adjustment (0.5 to 2.0)
    pause_duration: float = 0.5  # Pause between sentences (seconds)
    voice_id: Optional[str] = None  # Specific voice to use
    use_ssml: bool = True  # Use Speech Synthesis Markup Language


@dataclass 
class HighContrastConfig:
    """Configuration for high contrast mode"""
    enabled: bool = False
    background_color: str = "#000000"
    text_color: str = "#FFFFFF"
    highlight_color: str = "#FFFF00"
    contrast_ratio: float = 7.0  # WCAG AA compliant


@dataclass
class DyslexiaFriendlyConfig:
    """Configuration for dyslexia-friendly formatting"""
    enabled: bool = False
    font_family: str = "OpenDyslexic"
    line_spacing: float = 1.5
    character_spacing: float = 0.12
    word_spacing: float = 0.16
    use_larger_font: bool = True
    avoid_justified_text: bool = True


class VoiceOnlyMode:
    """
    Complete learning flow without visual UI for blind students
    """
    
    def __init__(self, speech_config: SpeechConfig = None):
        self.speech_config = speech_config or SpeechConfig()
        self.conversation_history: List[Dict[str, Any]] = []
        self.current_lesson_state = {}
        
    def start_lesson(self, lesson_content: str) -> str:
        """Start a lesson in voice-only mode"""
        intro = self._generate_voice_intro(lesson_content)
        self.conversation_history.append({
            "type": "lesson_start",
            "content": intro,
            "timestamp": time.time()
        })
        return intro
        
    def present_content(self, content: str, content_type: str = "text") -> str:
        """Present content optimized for voice"""
        voice_content = self._adapt_content_for_voice(content, content_type)
        
        self.conversation_history.append({
            "type": "content_presentation", 
            "original": content,
            "voice_adapted": voice_content,
            "timestamp": time.time()
        })
        
        return voice_content
        
    def handle_user_response(self, user_input: str) -> str:
        """Process user response and provide voice feedback"""
        response = self._generate_voice_response(user_input)
        
        self.conversation_history.append({
            "type": "user_interaction",
            "user_input": user_input,
            "system_response": response,
            "timestamp": time.time()
        })
        
        return response
        
    def _generate_voice_intro(self, lesson_content: str) -> str:
        """Generate voice-optimized lesson introduction"""
        return (f"Welcome to today's lesson. "
                f"I'll guide you through the material step by step. "
                f"You can ask questions anytime by simply speaking. "
                f"Let's begin.")
                
    def _adapt_content_for_voice(self, content: str, content_type: str) -> str:
        """Adapt visual content for voice presentation"""
        if content_type == "math":
            return self._math_to_speech(content)
        elif content_type == "diagram":
            return self._diagram_to_speech(content)
        else:
            # Add natural pauses and clarifications
            adapted = content.replace(". ", ". <pause> ")
            adapted = re.sub(r'\b(\d+)\b', r'the number \1', adapted)
            return adapted
            
    def _math_to_speech(self, math_content: str) -> str:
        """Convert mathematical notation to speech"""
        # Basic math-to-speech conversion
        speech = math_content
        speech = speech.replace("+", "plus")
        speech = speech.replace("-", "minus")
        speech = speech.replace("*", "times")
        speech = speech.replace("/", "divided by")
        speech = speech.replace("=", "equals")
        speech = speech.replace("²", "squared")
        speech = speech.replace("³", "cubed")
        return speech
        
    def _diagram_to_speech(self, diagram_description: str) -> str:
        """Convert diagram descriptions to speech"""
        return f"Let me describe this diagram for you: {diagram_description}"
        
    def _generate_voice_response(self, user_input: str) -> str:
        """Generate appropriate voice response"""
        return f"I understand you said: {user_input}. Let me help you with that."


class SimplifiedLanguageProcessor:
    """
    Auto-simplify explanations for cognitive disabilities
    """
    
    COMPLEX_WORDS = {
        "demonstrate": "show",
        "utilize": "use",
        "consequently": "so",
        "furthermore": "also",
        "nevertheless": "but",
        "approximately": "about",
        "sufficient": "enough",
        "acquire": "get",
        "assistance": "help",
        "comprehend": "understand"
    }
    
    def __init__(self, max_sentence_length: int = 15):
        self.max_sentence_length = max_sentence_length
        
    def simplify_text(self, text: str) -> str:
        """Simplify text for easier understanding"""
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        simplified_sentences = []
        
        for sentence in sentences:
            if sentence.strip():
                simplified = self._simplify_sentence(sentence.strip())
                simplified_sentences.extend(simplified)
                
        return '. '.join(simplified_sentences) + '.'
        
    def _simplify_sentence(self, sentence: str) -> List[str]:
        """Simplify a single sentence"""
        # Replace complex words
        words = sentence.split()
        simplified_words = []
        
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word.lower())
            if clean_word in self.COMPLEX_WORDS:
                replacement = self.COMPLEX_WORDS[clean_word]
                # Maintain original capitalization pattern
                if word[0].isupper():
                    replacement = replacement.capitalize()
                simplified_words.append(replacement)
            else:
                simplified_words.append(word)
                
        simplified_sentence = ' '.join(simplified_words)
        
        # Split long sentences
        if len(simplified_words) > self.max_sentence_length:
            return self._split_long_sentence(simplified_sentence)
        
        return [simplified_sentence]
        
    def _split_long_sentence(self, sentence: str) -> List[str]:
        """Split long sentences into shorter ones"""
        # Simple splitting on conjunctions
        conjunctions = [' and ', ' but ', ' so ', ' because ', ' when ', ' if ']
        
        for conjunction in conjunctions:
            if conjunction in sentence:
                parts = sentence.split(conjunction, 1)
                if len(parts) == 2:
                    return [parts[0].strip(), parts[1].strip()]
                    
        # If no conjunctions, split at commas
        if ', ' in sentence:
            parts = sentence.split(', ', 1)
            return [parts[0].strip(), parts[1].strip()]
            
        return [sentence]
        
    def add_examples(self, concept: str, examples: List[str] = None) -> str:
        """Add examples to explain concepts"""
        if examples is None:
            examples = self._generate_examples(concept)
            
        example_text = f"For example: {'. For example: '.join(examples)}"
        return f"{concept}. {example_text}"
        
    def _generate_examples(self, concept: str) -> List[str]:
        """Generate simple examples for concepts"""
        # This would integrate with the main AI system
        return [f"Think of {concept} like..."]


class PatienceMode:
    """
    Configurable response timeouts with no time pressure and encouraging feedback
    """
    
    def __init__(self, 
                 base_timeout: float = 60.0,
                 encouragement_interval: float = 30.0):
        self.base_timeout = base_timeout
        self.encouragement_interval = encouragement_interval
        self.user_response_times: List[float] = []
        
    def get_adaptive_timeout(self, user_id: str) -> float:
        """Get adaptive timeout based on user's historical response times"""
        if not self.user_response_times:
            return self.base_timeout
            
        avg_time = sum(self.user_response_times[-10:]) / len(self.user_response_times[-10:])
        # Allow 3x average time, minimum base_timeout
        return max(self.base_timeout, avg_time * 3)
        
    def record_response_time(self, response_time: float):
        """Record user response time for adaptive timeout calculation"""
        self.user_response_times.append(response_time)
        # Keep only last 50 response times
        if len(self.user_response_times) > 50:
            self.user_response_times.pop(0)
            
    def get_encouragement_message(self, wait_time: float) -> str:
        """Get encouraging message based on wait time"""
        if wait_time < 15:
            return None
        elif wait_time < 30:
            return "Take your time. I'm here when you're ready."
        elif wait_time < 60:
            return "No rush at all. Think it through."
        else:
            return "You're doing great. Take all the time you need."


class AccessibilityDetector:
    """
    Auto-detection of accessibility needs from interaction patterns
    """
    
    def __init__(self):
        self.typing_speeds: Dict[str, List[float]] = {}
        self.error_counts: Dict[str, int] = {}
        self.response_times: Dict[str, List[float]] = {}
        
    def analyze_typing_pattern(self, user_id: str, 
                             text_length: int, 
                             typing_time: float) -> bool:
        """Analyze if user has slow typing pattern"""
        if user_id not in self.typing_speeds:
            self.typing_speeds[user_id] = []
            
        wpm = (text_length / 5) / (typing_time / 60)  # Words per minute
        self.typing_speeds[user_id].append(wpm)
        
        # Keep only recent measurements
        if len(self.typing_speeds[user_id]) > 20:
            self.typing_speeds[user_id].pop(0)
            
        # Suggest voice if consistently slow (< 20 WPM)
        if len(self.typing_speeds[user_id]) >= 5:
            avg_wpm = sum(self.typing_speeds[user_id]) / len(self.typing_speeds[user_id])
            return avg_wpm < 20
            
        return False
        
    def analyze_error_pattern(self, user_id: str, has_error: bool) -> bool:
        """Analyze if user makes frequent errors suggesting simplified mode"""
        if user_id not in self.error_counts:
            self.error_counts[user_id] = 0
            
        if has_error:
            self.error_counts[user_id] += 1
            
        # Suggest simplified mode if error rate > 30%
        total_interactions = sum(1 for _ in self.response_times.get(user_id, []))
        if total_interactions >= 10:
            error_rate = self.error_counts[user_id] / total_interactions
            return error_rate > 0.3
            
        return False
        
    def suggest_accommodations(self, user_id: str) -> List[str]:
        """Suggest accessibility accommodations based on patterns"""
        suggestions = []
        
        if self.analyze_typing_pattern(user_id, 0, 0):  # Check existing data
            suggestions.append("voice_input")
            
        if self.analyze_error_pattern(user_id, False):  # Check existing data
            suggestions.append("simplified_language")
            
        # Check response times for patience mode
        if user_id in self.response_times:
            avg_response_time = (sum(self.response_times[user_id]) / 
                               len(self.response_times[user_id]))
            if avg_response_time > 45:  # 45 seconds
                suggestions.append("patience_mode")
                
        return suggestions


class AccessibilityEngine:
    """
    Main accessibility engine that coordinates all accessibility features
    """
    
    def __init__(self):
        self.profiles: Dict[str, AccessibilityProfile] = {}
        self.voice_only_sessions: Dict[str, VoiceOnlyMode] = {}
        self.language_processor = SimplifiedLanguageProcessor()
        self.patience_mode = PatienceMode()
        self.detector = AccessibilityDetector()
        
    def create_profile(self, user_id: str) -> AccessibilityProfile:
        """Create new accessibility profile for user"""
        profile = AccessibilityProfile(user_id=user_id)
        self.profiles[user_id] = profile
        return profile
        
    def get_profile(self, user_id: str) -> Optional[AccessibilityProfile]:
        """Get accessibility profile for user"""
        return self.profiles.get(user_id)
        
    def start_voice_only_session(self, user_id: str, 
                                speech_config: SpeechConfig = None) -> VoiceOnlyMode:
        """Start voice-only learning session"""
        voice_session = VoiceOnlyMode(speech_config)
        self.voice_only_sessions[user_id] = voice_session
        return voice_session
        
    def process_content(self, user_id: str, content: str, 
                       content_type: str = "text") -> str:
        """Process content based on user's accessibility needs"""
        profile = self.get_profile(user_id)
        if not profile:
            return content
            
        processed_content = content
        
        # Apply simplification if needed
        if profile.needs_simplified_language:
            processed_content = self.language_processor.simplify_text(processed_content)
            
        # Handle voice-only mode
        if profile.requires_voice_only and user_id in self.voice_only_sessions:
            processed_content = self.voice_only_sessions[user_id].present_content(
                processed_content, content_type)
                
        return processed_content
        
    def get_ui_config(self, user_id: str) -> Dict[str, Any]:
        """Get UI configuration based on accessibility profile"""
        profile = self.get_profile(user_id)
        if not profile:
            return {}
            
        config = {}
        
        # High contrast settings
        if any("blindness" in imp or "low_vision" in imp 
               for imp in profile.visual_impairments):
            config["high_contrast"] = HighContrastConfig(enabled=True)
            
        # Dyslexia-friendly settings
        if "dyslexia" in profile.cognitive_impairments:
            config["dyslexia_friendly"] = DyslexiaFriendlyConfig(enabled=True)
            
        # Speech configuration
        if profile.requires_voice_only or any(profile.hearing_impairments.values()):
            config["speech"] = SpeechConfig(rate=0.8)  # Slower for better comprehension
            
        return config
        
    def analyze_interaction(self, user_id: str, interaction_data: Dict[str, Any]):
        """Analyze user interaction for accessibility patterns"""
        # Record typing patterns
        if "typing_time" in interaction_data and "text_length" in interaction_data:
            slow_typing = self.detector.analyze_typing_pattern(
                user_id, 
                interaction_data["text_length"],
                interaction_data["typing_time"]
            )
            
            if slow_typing:
                logger.info(f"Detected slow typing for user {user_id}")
                
        # Record error patterns
        if "has_error" in interaction_data:
            frequent_errors = self.detector.analyze_error_pattern(
                user_id, 
                interaction_data["has_error"]
            )
            
            if frequent_errors:
                logger.info(f"Detected frequent errors for user {user_id}")
                
        # Get suggestions and update profile
        suggestions = self.detector.suggest_accommodations(user_id)
        if suggestions:
            self._apply_suggestions(user_id, suggestions)
            
    def _apply_suggestions(self, user_id: str, suggestions: List[str]):
        """Apply accessibility suggestions to user profile"""
        profile = self.get_profile(user_id)
        if not profile:
            profile = self.create_profile(user_id)
            
        for suggestion in suggestions:
            if suggestion == "voice_input":
                profile.requires_voice_only = True
                logger.info(f"Enabled voice-only mode for user {user_id}")
            elif suggestion == "simplified_language":
                profile.needs_simplified_language = True
                logger.info(f"Enabled simplified language for user {user_id}")
            elif suggestion == "patience_mode":
                profile.requires_patience_mode = True
                logger.info(f"Enabled patience mode for user {user_id}")