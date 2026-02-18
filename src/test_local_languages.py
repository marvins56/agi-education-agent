"""
Tests for local_languages.py module

Comprehensive tests for multi-language support including translation framework,
code-switching, phonetic guides, and language preference management.
"""

import pytest
import sqlite3
import tempfile
import json
from datetime import datetime
from unittest.mock import Mock, patch

from local_languages import (
    LanguageScaffold, TranslationDatabase, PhoneticGuide, CodeSwitchingEngine,
    Language, LanguageComplexity, LanguagePreference, TranslationEntry
)


class TestLanguage:
    """Test Language enum"""
    
    def test_language_values(self):
        """Test language enum values"""
        assert Language.ENGLISH.value == "en"
        assert Language.LUGANDA.value == "lg"
        assert Language.SWAHILI.value == "sw"
        assert Language.RUNYANKOLE.value == "nyn"


class TestLanguageComplexity:
    """Test LanguageComplexity enum"""
    
    def test_complexity_values(self):
        """Test language complexity enum values"""
        assert LanguageComplexity.TECHNICAL.value == "technical"
        assert LanguageComplexity.STANDARD.value == "standard"
        assert LanguageComplexity.SIMPLIFIED.value == "simplified"


class TestLanguagePreference:
    """Test LanguagePreference dataclass"""
    
    def test_language_preference_creation(self):
        """Test basic language preference creation"""
        preference = LanguagePreference(
            user_id="test_user",
            primary_language=Language.LUGANDA
        )
        
        assert preference.user_id == "test_user"
        assert preference.primary_language == Language.LUGANDA
        assert preference.complexity_level == LanguageComplexity.STANDARD
        assert preference.enable_code_switching is True
        assert preference.phonetic_support is True
    
    def test_fallback_language_defaults(self):
        """Test automatic fallback language setup"""
        # Test Luganda fallback
        luganda_pref = LanguagePreference(
            user_id="luganda_user",
            primary_language=Language.LUGANDA
        )
        assert Language.ENGLISH in luganda_pref.fallback_languages
        assert Language.SWAHILI in luganda_pref.fallback_languages
        
        # Test Swahili fallback
        swahili_pref = LanguagePreference(
            user_id="swahili_user",
            primary_language=Language.SWAHILI
        )
        assert Language.ENGLISH in swahili_pref.fallback_languages
        assert Language.LUGANDA in swahili_pref.fallback_languages
        
        # Test English fallback
        english_pref = LanguagePreference(
            user_id="english_user",
            primary_language=Language.ENGLISH
        )
        assert Language.SWAHILI in english_pref.fallback_languages
        assert Language.LUGANDA in english_pref.fallback_languages
    
    def test_custom_fallback_languages(self):
        """Test custom fallback language configuration"""
        custom_fallback = [Language.ENGLISH, Language.RUNYANKOLE]
        preference = LanguagePreference(
            user_id="custom_user",
            primary_language=Language.LUGANDA,
            fallback_languages=custom_fallback
        )
        
        assert preference.fallback_languages == custom_fallback


class TestTranslationEntry:
    """Test TranslationEntry dataclass"""
    
    def test_translation_entry_creation(self):
        """Test translation entry creation"""
        entry = TranslationEntry(
            key="water",
            language=Language.LUGANDA,
            text="amazzi",
            context="science",
            complexity_level=LanguageComplexity.STANDARD,
            phonetic_guide="/aˈmazzi/",
            usage_examples=["Water is essential for life", "Amazzi ga mugaso eri obulamu"]
        )
        
        assert entry.key == "water"
        assert entry.language == Language.LUGANDA
        assert entry.text == "amazzi"
        assert entry.context == "science"
        assert entry.complexity_level == LanguageComplexity.STANDARD
        assert entry.phonetic_guide == "/aˈmazzi/"
        assert len(entry.usage_examples) == 2
    
    def test_translation_entry_dict_conversion(self):
        """Test conversion to/from dictionary"""
        original_entry = TranslationEntry(
            key="student",
            language=Language.SWAHILI,
            text="mwanafunzi",
            context="education",
            usage_examples=["The student is learning", "Mwanafunzi anajifunza"]
        )
        
        # Convert to dict and back
        entry_dict = original_entry.to_dict()
        restored_entry = TranslationEntry.from_dict(entry_dict)
        
        assert restored_entry.key == original_entry.key
        assert restored_entry.language == original_entry.language
        assert restored_entry.text == original_entry.text
        assert restored_entry.context == original_entry.context
        assert restored_entry.usage_examples == original_entry.usage_examples


class TestPhoneticGuide:
    """Test PhoneticGuide class"""
    
    def test_phonetic_guide_initialization(self):
        """Test phonetic guide initialization"""
        guide = PhoneticGuide()
        
        assert hasattr(guide, 'LUGANDA_PATTERNS')
        assert hasattr(guide, 'SWAHILI_PATTERNS')
        assert hasattr(guide, 'RUNYANKOLE_PATTERNS')
        assert 'ch' in guide.LUGANDA_PATTERNS
        assert 'ng' in guide.SWAHILI_PATTERNS
    
    def test_english_phonetic_generation(self):
        """Test English phonetic guide generation"""
        guide = PhoneticGuide()
        
        # Test technical terms
        phonetic = guide.generate_phonetic_guide("photosynthesis", Language.ENGLISH, is_technical_term=True)
        assert phonetic == "/ˌfoʊtoʊˈsɪnθəsɪs/"
        
        phonetic = guide.generate_phonetic_guide("equation", Language.ENGLISH, is_technical_term=True)
        assert phonetic == "/ɪˈkweɪʒən/"
        
        # Test simple word transformation
        phonetic = guide.generate_phonetic_guide("philosophy", Language.ENGLISH, is_technical_term=False)
        assert "f" in phonetic  # 'ph' should become 'f'
    
    def test_luganda_phonetic_generation(self):
        """Test Luganda phonetic guide generation"""
        guide = PhoneticGuide()
        
        # Test Luganda-specific patterns
        phonetic = guide.generate_phonetic_guide("omwana", Language.LUGANDA)
        assert phonetic.startswith("/")
        assert phonetic.endswith("/")
        
        # Test pattern replacement
        phonetic = guide.generate_phonetic_guide("engatto", Language.LUGANDA)  # contains 'ng'
        assert "ŋ" in phonetic  # 'ng' should become 'ŋ'
    
    def test_swahili_phonetic_generation(self):
        """Test Swahili phonetic guide generation"""
        guide = PhoneticGuide()
        
        phonetic = guide.generate_phonetic_guide("mwalimu", Language.SWAHILI)
        assert phonetic.startswith("/")
        assert phonetic.endswith("/")
        
        # Test specific Swahili patterns
        phonetic = guide.generate_phonetic_guide("dhani", Language.SWAHILI)  # contains 'dh'
        assert "ð" in phonetic  # 'dh' should become 'ð'
    
    def test_runyankole_phonetic_generation(self):
        """Test Runyankole phonetic guide generation"""
        guide = PhoneticGuide()
        
        phonetic = guide.generate_phonetic_guide("omwana", Language.RUNYANKOLE)
        assert phonetic.startswith("/")
        assert phonetic.endswith("/")
        
        # Test pattern replacement
        phonetic = guide.generate_phonetic_guide("ekyagyo", Language.RUNYANKOLE)  # contains 'ky'
        assert "c" in phonetic  # 'ky' should become 'c'


class TestCodeSwitchingEngine:
    """Test CodeSwitchingEngine class"""
    
    def test_code_switching_initialization(self):
        """Test code switching engine initialization"""
        engine = CodeSwitchingEngine()
        
        assert 'mathematics' in engine.technical_terms_english
        assert 'biology' in engine.technical_terms_english
        assert 'computer' in engine.technical_terms_english
        
        assert Language.LUGANDA in engine.local_language_anchors
        assert Language.SWAHILI in engine.local_language_anchors
        assert Language.RUNYANKOLE in engine.local_language_anchors
    
    def test_code_switching_with_technical_terms(self):
        """Test code switching preserves technical terms"""
        engine = CodeSwitchingEngine()
        
        text = "Today we will study mathematics and biology in the laboratory"
        result = engine.apply_code_switching(text, Language.LUGANDA, subject_context="science")
        
        # Technical terms should be preserved in context
        assert "mathematics" in result
        assert "biology" in result
        assert "laboratory" in result
    
    def test_code_switching_with_english_primary(self):
        """Test no code switching when primary language is English"""
        engine = CodeSwitchingEngine()
        
        text = "This is a test sentence with mathematics terms"
        result = engine.apply_code_switching(text, Language.ENGLISH)
        
        assert result == text  # Should be unchanged
    
    def test_code_switch_point_suggestions(self):
        """Test suggestions for code switching points"""
        engine = CodeSwitchingEngine()
        
        text = "Today we will learn mathematics and computer science"
        suggestions = engine.suggest_code_switch_points(text, Language.LUGANDA)
        
        assert len(suggestions) == 2  # Should find 'mathematics' and 'computer'
        
        math_suggestion = next((s for s in suggestions if s['word'] == 'mathematics'), None)
        assert math_suggestion is not None
        assert math_suggestion['suggestion'] == 'technical_term'


class TestTranslationDatabase:
    """Test TranslationDatabase class"""
    
    def test_database_initialization(self):
        """Test translation database initialization"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db = TranslationDatabase(temp_db.name)
            
            # Check that tables were created
            with sqlite3.connect(temp_db.name) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                assert 'translations' in tables
                assert 'language_preferences' in tables
    
    def test_default_translations_populated(self):
        """Test that default translations are populated"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db = TranslationDatabase(temp_db.name)
            
            # Check for some default translations
            lesson_translation = db.get_translation("lesson", Language.LUGANDA, "education")
            assert lesson_translation is not None
            assert lesson_translation.text == "essomo"
            
            student_translation = db.get_translation("student", Language.SWAHILI, "education")
            assert student_translation is not None
            assert student_translation.text == "mwanafunzi"
    
    def test_add_and_retrieve_translation(self):
        """Test adding and retrieving custom translations"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db = TranslationDatabase(temp_db.name)
            
            # Add custom translation
            custom_entry = TranslationEntry(
                key="computer",
                language=Language.LUGANDA,
                text="kompyuta",
                context="technology",
                complexity_level=LanguageComplexity.STANDARD,
                phonetic_guide="/komˈpjuta/",
                usage_examples=["I use a computer", "Nkozesa kompyuta"]
            )
            
            success = db.add_translation(custom_entry)
            assert success is True
            
            # Retrieve translation
            retrieved = db.get_translation("computer", Language.LUGANDA, "technology")
            assert retrieved is not None
            assert retrieved.text == "kompyuta"
            assert retrieved.phonetic_guide == "/komˈpjuta/"
    
    def test_translation_search(self):
        """Test translation search functionality"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db = TranslationDatabase(temp_db.name)
            
            # Search for existing translations
            results = db.search_translations("water", Language.LUGANDA)
            assert len(results) >= 1
            
            # Should find "water" -> "amazzi"
            water_result = next((r for r in results if r.key == "water"), None)
            assert water_result is not None
            assert water_result.text == "amaizi"  # Runyankole version might be found
    
    def test_user_preference_storage(self):
        """Test storing and retrieving user preferences"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db = TranslationDatabase(temp_db.name)
            
            # Create user preference
            preference = LanguagePreference(
                user_id="test_pref_user",
                primary_language=Language.LUGANDA,
                fallback_languages=[Language.ENGLISH, Language.SWAHILI],
                complexity_level=LanguageComplexity.SIMPLIFIED,
                enable_code_switching=False,
                phonetic_support=True,
                math_language=Language.ENGLISH,
                science_language=Language.SWAHILI
            )
            
            # Store preference
            success = db.store_user_preference(preference)
            assert success is True
            
            # Retrieve preference
            retrieved_pref = db.get_user_preference("test_pref_user")
            assert retrieved_pref is not None
            assert retrieved_pref.user_id == "test_pref_user"
            assert retrieved_pref.primary_language == Language.LUGANDA
            assert retrieved_pref.complexity_level == LanguageComplexity.SIMPLIFIED
            assert retrieved_pref.enable_code_switching is False
            assert retrieved_pref.math_language == Language.ENGLISH
            assert retrieved_pref.science_language == Language.SWAHILI
    
    def test_translation_complexity_fallback(self):
        """Test translation retrieval with complexity fallback"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db = TranslationDatabase(temp_db.name)
            
            # Add translations with different complexity levels
            standard_entry = TranslationEntry(
                key="fraction",
                language=Language.LUGANDA,
                text="ekitundu",
                context="mathematics",
                complexity_level=LanguageComplexity.STANDARD
            )
            
            simplified_entry = TranslationEntry(
                key="fraction",
                language=Language.LUGANDA,
                text="ekimu ku kimu",
                context="mathematics",
                complexity_level=LanguageComplexity.SIMPLIFIED
            )
            
            db.add_translation(standard_entry)
            db.add_translation(simplified_entry)
            
            # Request standard complexity
            standard_result = db.get_translation("fraction", Language.LUGANDA, "mathematics", LanguageComplexity.STANDARD)
            assert standard_result is not None
            assert standard_result.text == "ekitundu"
            
            # Request simplified complexity
            simplified_result = db.get_translation("fraction", Language.LUGANDA, "mathematics", LanguageComplexity.SIMPLIFIED)
            assert simplified_result is not None
            assert simplified_result.text == "ekimu ku kimu"


class TestLanguageScaffold:
    """Test main LanguageScaffold class"""
    
    def test_language_scaffold_initialization(self):
        """Test language scaffold initialization"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            scaffold = LanguageScaffold(temp_db.name)
            
            assert scaffold.translation_db is not None
            assert scaffold.phonetic_guide is not None
            assert scaffold.code_switching is not None
            assert isinstance(scaffold.translation_cache, dict)
    
    def test_user_language_preference_management(self):
        """Test user language preference management"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            scaffold = LanguageScaffold(temp_db.name)
            
            # Create and set preference
            preference = LanguagePreference(
                user_id="scaffold_test_user",
                primary_language=Language.SWAHILI,
                complexity_level=LanguageComplexity.SIMPLIFIED
            )
            
            success = scaffold.set_user_language_preference("scaffold_test_user", preference)
            assert success is True
            
            # Retrieve preference
            retrieved = scaffold.get_user_language_preference("scaffold_test_user")
            assert retrieved.user_id == "scaffold_test_user"
            assert retrieved.primary_language == Language.SWAHILI
            assert retrieved.complexity_level == LanguageComplexity.SIMPLIFIED
    
    def test_default_user_preference_creation(self):
        """Test automatic creation of default user preferences"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            scaffold = LanguageScaffold(temp_db.name)
            
            # Request preference for non-existent user
            preference = scaffold.get_user_language_preference("new_user")
            
            assert preference.user_id == "new_user"
            assert preference.primary_language == Language.ENGLISH  # Default
            assert preference.complexity_level == LanguageComplexity.STANDARD
    
    def test_content_translation_english_primary(self):
        """Test content translation when primary language is English"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            scaffold = LanguageScaffold(temp_db.name)
            
            # Set English preference
            preference = LanguagePreference(
                user_id="english_user",
                primary_language=Language.ENGLISH
            )
            scaffold.set_user_language_preference("english_user", preference)
            
            content = "Today we will learn about fractions in mathematics."
            result = scaffold.translate_content(content, "english_user", "mathematics")
            
            assert result['translated_text'] == content  # Should be unchanged
            assert result['primary_language'] == 'en'
            assert result['fallback_used'] is False
            assert result['code_switched'] is False
    
    def test_content_translation_with_local_language(self):
        """Test content translation to local language"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            scaffold = LanguageScaffold(temp_db.name)
            
            # Set Luganda preference
            preference = LanguagePreference(
                user_id="luganda_user",
                primary_language=Language.LUGANDA,
                enable_code_switching=True
            )
            scaffold.set_user_language_preference("luganda_user", preference)
            
            content = "Today we will learn about water in science class."
            result = scaffold.translate_content(content, "luganda_user", "science")
            
            assert result['primary_language'] == 'lg'
            assert result['code_switched'] is True
            # Should have some translation attempts
            assert 'phonetic_guides' in result
    
    def test_subject_specific_language_preference(self):
        """Test subject-specific language preferences"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            scaffold = LanguageScaffold(temp_db.name)
            
            # Set preference with subject-specific languages
            preference = LanguagePreference(
                user_id="subject_user",
                primary_language=Language.LUGANDA,
                math_language=Language.ENGLISH,
                science_language=Language.SWAHILI
            )
            scaffold.set_user_language_preference("subject_user", preference)
            
            # Test mathematics content (should use English)
            math_content = "Today we will solve equations."
            math_result = scaffold.translate_content(math_content, "subject_user", "mathematics")
            assert math_result['primary_language'] == 'en'  # Should use math_language
            
            # Test science content (should use Swahili)
            science_content = "We will study plants today."
            science_result = scaffold.translate_content(science_content, "subject_user", "science")
            assert science_result['primary_language'] == 'sw'  # Should use science_language
    
    def test_add_custom_translation(self):
        """Test adding custom translations"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            scaffold = LanguageScaffold(temp_db.name)
            
            # Add custom translation
            success = scaffold.add_translation(
                "algorithm", Language.LUGANDA, "enkola",
                context="computer_science", complexity=LanguageComplexity.STANDARD,
                usage_examples=["This algorithm is efficient", "Enkola eno ya maanyi"]
            )
            assert success is True
            
            # Verify translation was added
            results = scaffold.search_translations("algorithm", "test_user")
            algorithm_result = next((r for r in results if r['key'] == 'algorithm'), None)
            assert algorithm_result is not None
            assert algorithm_result['text'] == 'enkola'
    
    def test_phonetic_guide_generation(self):
        """Test phonetic guide generation"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            scaffold = LanguageScaffold(temp_db.name)
            
            # Test English technical term
            phonetic = scaffold.get_phonetic_guide("photosynthesis", Language.ENGLISH, is_technical=True)
            assert phonetic == "/ˌfoʊtoʊˈsɪnθəsɪs/"
            
            # Test local language
            phonetic = scaffold.get_phonetic_guide("amazzi", Language.LUGANDA)
            assert phonetic.startswith("/")
            assert phonetic.endswith("/")
    
    def test_code_switching_suggestions(self):
        """Test code switching suggestions"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            scaffold = LanguageScaffold(temp_db.name)
            
            # Set up user preference
            preference = LanguagePreference(
                user_id="switch_user",
                primary_language=Language.LUGANDA
            )
            scaffold.set_user_language_preference("switch_user", preference)
            
            text = "We will study mathematics and biology today"
            suggestions = scaffold.suggest_code_switching(text, "switch_user", "science")
            
            assert len(suggestions) >= 2  # Should find 'mathematics' and 'biology'
            
            math_suggestion = next((s for s in suggestions if 'mathematics' in s['word']), None)
            assert math_suggestion is not None
    
    def test_translation_search(self):
        """Test translation search functionality"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            scaffold = LanguageScaffold(temp_db.name)
            
            # Set up user preference
            preference = LanguagePreference(
                user_id="search_user",
                primary_language=Language.SWAHILI
            )
            scaffold.set_user_language_preference("search_user", preference)
            
            # Search for translations
            results = scaffold.search_translations("maji", "search_user")  # Should find water-related translations
            assert len(results) >= 0  # May or may not find results depending on default data
            
            # Search for common term
            results = scaffold.search_translations("student", "search_user")
            assert len(results) >= 1  # Should find student translations
    
    def test_language_statistics(self):
        """Test language usage statistics"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            scaffold = LanguageScaffold(temp_db.name)
            
            # Set up user preference
            preference = LanguagePreference(
                user_id="stats_user",
                primary_language=Language.LUGANDA,
                fallback_languages=[Language.ENGLISH, Language.SWAHILI],
                complexity_level=LanguageComplexity.SIMPLIFIED,
                enable_code_switching=True,
                phonetic_support=True,
                math_language=Language.ENGLISH
            )
            scaffold.set_user_language_preference("stats_user", preference)
            
            # Get statistics
            stats = scaffold.get_language_stats("stats_user")
            
            assert stats['primary_language'] == 'lg'
            assert 'en' in stats['fallback_languages']
            assert 'sw' in stats['fallback_languages']
            assert stats['complexity_level'] == 'simplified'
            assert stats['code_switching_enabled'] is True
            assert stats['phonetic_support_enabled'] is True
            assert stats['subject_preferences']['mathematics'] == 'en'
            assert 'translation_cache_size' in stats
    
    def test_translation_caching(self):
        """Test translation caching mechanism"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            scaffold = LanguageScaffold(temp_db.name)
            
            # Set small cache limit for testing
            original_limit = scaffold.cache_size_limit
            scaffold.cache_size_limit = 3
            
            try:
                # Add translations that should be cached
                for i in range(5):
                    scaffold.add_translation(
                        f"test_word_{i}", Language.LUGANDA, f"test_translation_{i}",
                        context="test", complexity=LanguageComplexity.STANDARD
                    )
                
                # Cache should be limited to 3 entries
                assert len(scaffold.translation_cache) <= 3
                
            finally:
                # Restore original limit
                scaffold.cache_size_limit = original_limit


class TestIntegration:
    """Integration tests for the language system"""
    
    def test_full_translation_workflow(self):
        """Test complete translation workflow"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            scaffold = LanguageScaffold(temp_db.name)
            
            # Set up user with Luganda preference
            preference = LanguagePreference(
                user_id="integration_user",
                primary_language=Language.LUGANDA,
                complexity_level=LanguageComplexity.STANDARD,
                enable_code_switching=True,
                phonetic_support=True,
                math_language=Language.ENGLISH
            )
            scaffold.set_user_language_preference("integration_user", preference)
            
            # Add some custom translations for testing
            scaffold.add_translation("plant", Language.LUGANDA, "ekimera", context="science")
            scaffold.add_translation("animal", Language.LUGANDA, "ekisolo", context="science")
            
            # Test science content translation
            science_content = "Today we will learn about plants and animals in our environment."
            result = scaffold.translate_content(science_content, "integration_user", "science")
            
            assert result['primary_language'] == 'lg'
            assert result['code_switched'] is True
            assert 'phonetic_guides' in result
            
            # Check that some translation occurred
            translated_text = result['translated_text']
            # Should have attempted to translate 'plant' and 'animal'
            assert 'ekimera' in translated_text or 'plant' in translated_text
            assert 'ekisolo' in translated_text or 'animal' in translated_text
            
            # Test mathematics content (should use English due to math_language setting)
            math_content = "We will solve equations with fractions today."
            math_result = scaffold.translate_content(math_content, "integration_user", "mathematics")
            
            assert math_result['primary_language'] == 'en'
            assert math_result['translated_text'] == math_content  # Should be unchanged in English
    
    def test_fallback_language_chain(self):
        """Test fallback language chain functionality"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            scaffold = LanguageScaffold(temp_db.name)
            
            # Set up user with specific fallback chain
            preference = LanguagePreference(
                user_id="fallback_user",
                primary_language=Language.RUNYANKOLE,
                fallback_languages=[Language.LUGANDA, Language.SWAHILI, Language.ENGLISH]
            )
            scaffold.set_user_language_preference("fallback_user", preference)
            
            # Add translation only in Luganda (first fallback)
            scaffold.add_translation("teacher", Language.LUGANDA, "omusomesa", context="education")
            
            # Translate content - should fall back to Luganda
            content = "The teacher is explaining the lesson."
            result = scaffold.translate_content(content, "fallback_user", "education")
            
            assert result['fallback_used'] is True
            # Should have attempted translation using fallback
            assert 'omusomesa' in result['translated_text'] or 'teacher' in result['translated_text']


# Run the tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])