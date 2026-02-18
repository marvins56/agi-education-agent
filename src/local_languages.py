"""
Local Languages System - Multi-language support for East African education

This module provides comprehensive language scaffolding including translation framework,
code-switching support, phonetic pronunciation guides, and language preference management
for Luganda, Swahili, Runyankole, and English in educational contexts.
"""

import json
import re
import sqlite3
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set, Union
from enum import Enum
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class Language(Enum):
    """Supported languages"""
    ENGLISH = "en"
    LUGANDA = "lg"
    SWAHILI = "sw"
    RUNYANKOLE = "nyn"
    

class LanguageComplexity(Enum):
    """Language complexity levels for fallback"""
    TECHNICAL = "technical"  # Full technical vocabulary
    STANDARD = "standard"   # Standard vocabulary
    SIMPLIFIED = "simplified"  # Simplified vocabulary and grammar


@dataclass
class LanguagePreference:
    """User language preference settings"""
    user_id: str
    primary_language: Language
    fallback_languages: List[Language] = field(default_factory=list)
    complexity_level: LanguageComplexity = LanguageComplexity.STANDARD
    enable_code_switching: bool = True
    phonetic_support: bool = True
    
    # Subject-specific preferences
    math_language: Optional[Language] = None
    science_language: Optional[Language] = None
    
    def __post_init__(self):
        """Set up default fallback chain"""
        if not self.fallback_languages:
            if self.primary_language == Language.LUGANDA:
                self.fallback_languages = [Language.ENGLISH, Language.SWAHILI]
            elif self.primary_language == Language.RUNYANKOLE:
                self.fallback_languages = [Language.ENGLISH, Language.SWAHILI]
            elif self.primary_language == Language.SWAHILI:
                self.fallback_languages = [Language.ENGLISH, Language.LUGANDA]
            else:  # English
                self.fallback_languages = [Language.SWAHILI, Language.LUGANDA]


@dataclass
class TranslationEntry:
    """Individual translation entry"""
    key: str
    language: Language
    text: str
    context: str = ""  # Educational context (math, science, etc.)
    complexity_level: LanguageComplexity = LanguageComplexity.STANDARD
    phonetic_guide: Optional[str] = None
    usage_examples: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            'key': self.key,
            'language': self.language.value,
            'text': self.text,
            'context': self.context,
            'complexity_level': self.complexity_level.value,
            'phonetic_guide': self.phonetic_guide,
            'usage_examples': json.dumps(self.usage_examples)
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TranslationEntry':
        """Create from dictionary from storage"""
        return cls(
            key=data['key'],
            language=Language(data['language']),
            text=data['text'],
            context=data.get('context', ''),
            complexity_level=LanguageComplexity(data.get('complexity_level', 'standard')),
            phonetic_guide=data.get('phonetic_guide'),
            usage_examples=json.loads(data.get('usage_examples', '[]'))
        )


class PhoneticGuide:
    """Generates phonetic pronunciation guides for technical terms"""
    
    # Common East African phonetic patterns
    LUGANDA_PATTERNS = {
        'ch': 'ʧ',    # as in chair
        'gg': 'ɡː',   # long g
        'ng': 'ŋ',    # as in sing
        'ny': 'ɲ',    # as in canyon
        'nw': 'nʷ',   # n with w sound
    }
    
    SWAHILI_PATTERNS = {
        'ch': 'ʧ',
        'dh': 'ð',    # as in this
        'gh': 'ɣ',    # voiced velar fricative
        'kh': 'x',    # voiceless velar fricative
        'ng': 'ŋ',
        'ny': 'ɲ',
        'th': 'θ',    # as in think
    }
    
    RUNYANKOLE_PATTERNS = {
        'gy': 'ɟ',    # palatalized g
        'ky': 'c',    # palatalized k
        'ny': 'ɲ',
        'rw': 'rʷ',   # r with w sound
        'ry': 'rʲ',   # palatalized r
    }
    
    def __init__(self):
        self.english_stress_patterns = self._load_english_stress_patterns()
    
    def generate_phonetic_guide(self, word: str, language: Language, 
                               is_technical_term: bool = False) -> str:
        """Generate phonetic guide for a word in the specified language"""
        
        if language == Language.ENGLISH:
            return self._generate_english_phonetics(word, is_technical_term)
        elif language == Language.LUGANDA:
            return self._generate_luganda_phonetics(word)
        elif language == Language.SWAHILI:
            return self._generate_swahili_phonetics(word)
        elif language == Language.RUNYANKOLE:
            return self._generate_runyankole_phonetics(word)
        
        return f"/{word}/"  # Fallback
    
    def _generate_english_phonetics(self, word: str, is_technical: bool) -> str:
        """Generate phonetics for English words, especially technical terms"""
        word_lower = word.lower()
        
        # Common technical term pronunciations
        technical_pronunciations = {
            'equation': '/ɪˈkweɪʒən/',
            'algorithm': '/ˈælɡərɪðəm/',
            'photosynthesis': '/ˌfoʊtoʊˈsɪnθəsɪs/',
            'chromosome': '/ˈkroʊməsoʊm/',
            'hypothesis': '/haɪˈpɑːθəsɪs/',
            'microscope': '/ˈmaɪkrəskoʊp/',
            'diameter': '/daɪˈæmətər/',
            'circumference': '/sərˈkʌmfərəns/',
            'numerator': '/ˈnuːməreɪtər/',
            'denominator': '/dɪˈnɑːməneɪtər/',
        }
        
        if is_technical and word_lower in technical_pronunciations:
            return technical_pronunciations[word_lower]
        
        # Simple English phonetic approximation
        phonetic = word_lower
        phonetic = re.sub(r'ph', 'f', phonetic)
        phonetic = re.sub(r'th', 'θ', phonetic)
        phonetic = re.sub(r'sh', 'ʃ', phonetic)
        phonetic = re.sub(r'ch', 'ʧ', phonetic)
        phonetic = re.sub(r'ng', 'ŋ', phonetic)
        
        return f'/{phonetic}/'
    
    def _generate_luganda_phonetics(self, word: str) -> str:
        """Generate phonetics for Luganda words"""
        phonetic = word.lower()
        
        for pattern, replacement in self.LUGANDA_PATTERNS.items():
            phonetic = phonetic.replace(pattern, replacement)
        
        return f'/{phonetic}/'
    
    def _generate_swahili_phonetics(self, word: str) -> str:
        """Generate phonetics for Swahili words"""
        phonetic = word.lower()
        
        for pattern, replacement in self.SWAHILI_PATTERNS.items():
            phonetic = phonetic.replace(pattern, replacement)
        
        return f'/{phonetic}/'
    
    def _generate_runyankole_phonetics(self, word: str) -> str:
        """Generate phonetics for Runyankole words"""
        phonetic = word.lower()
        
        for pattern, replacement in self.RUNYANKOLE_PATTERNS.items():
            phonetic = phonetic.replace(pattern, replacement)
        
        return f'/{phonetic}/'
    
    def _load_english_stress_patterns(self) -> dict:
        """Load common English stress patterns"""
        # This would typically load from a file or database
        return {
            'mathematics': 'math-e-MAT-ics',
            'biology': 'bi-OL-o-gy',
            'chemistry': 'CHEM-is-try',
            'physics': 'PHYS-ics',
        }


class CodeSwitchingEngine:
    """Handles natural code-switching between languages in educational content"""
    
    def __init__(self):
        # Common code-switching patterns in East African education
        self.technical_terms_english = {
            'mathematics', 'algebra', 'geometry', 'calculus', 'equation',
            'biology', 'chemistry', 'physics', 'science', 'experiment',
            'computer', 'technology', 'internet', 'software', 'hardware'
        }
        
        # Words that naturally stay in local language
        self.local_language_anchors = {
            Language.LUGANDA: {'omwana', 'abasomesa', 'essomero', 'okusoma'},
            Language.SWAHILI: {'mtoto', 'walimu', 'shule', 'kusoma'},
            Language.RUNYANKOLE: {'omwana', 'abarimu', 'eshomero', 'okusoma'}
        }
    
    def apply_code_switching(self, text: str, primary_language: Language, 
                           subject_context: str = None) -> str:
        """Apply natural code-switching patterns to text"""
        
        if primary_language == Language.ENGLISH:
            return text  # No code-switching needed
        
        # Split text into words
        words = text.split()
        processed_words = []
        
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word.lower())
            
            # Keep technical terms in English
            if clean_word in self.technical_terms_english:
                if subject_context in ['mathematics', 'science', 'computer_science']:
                    processed_words.append(word)  # Keep in English
                    continue
            
            # Check if word should stay in local language
            local_anchors = self.local_language_anchors.get(primary_language, set())
            if clean_word in local_anchors:
                processed_words.append(word)  # Keep in local language
                continue
            
            processed_words.append(word)
        
        return ' '.join(processed_words)
    
    def suggest_code_switch_points(self, text: str, primary_language: Language) -> List[dict]:
        """Suggest appropriate points for code-switching"""
        suggestions = []
        
        # Find technical terms that could benefit from explanation
        words = text.split()
        for i, word in enumerate(words):
            clean_word = re.sub(r'[^\w]', '', word.lower())
            
            if clean_word in self.technical_terms_english:
                suggestions.append({
                    'position': i,
                    'word': word,
                    'suggestion': 'technical_term',
                    'explanation': f'Consider explaining "{word}" in {primary_language.value}'
                })
        
        return suggestions


class TranslationDatabase:
    """SQLite-based translation database for offline use"""
    
    def __init__(self, db_path: str = "translations.db"):
        self.db_path = db_path
        self.conn_lock = threading.Lock()
        self._init_database()
        self._populate_default_translations()
    
    def _init_database(self):
        """Initialize translation database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS translations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL,
                    language TEXT NOT NULL,
                    text TEXT NOT NULL,
                    context TEXT DEFAULT '',
                    complexity_level TEXT DEFAULT 'standard',
                    phonetic_guide TEXT,
                    usage_examples TEXT DEFAULT '[]',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(key, language, context, complexity_level)
                );
                
                CREATE TABLE IF NOT EXISTS language_preferences (
                    user_id TEXT PRIMARY KEY,
                    primary_language TEXT NOT NULL,
                    fallback_languages TEXT NOT NULL,
                    complexity_level TEXT DEFAULT 'standard',
                    enable_code_switching BOOLEAN DEFAULT TRUE,
                    phonetic_support BOOLEAN DEFAULT TRUE,
                    math_language TEXT,
                    science_language TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_translations_key ON translations(key);
                CREATE INDEX IF NOT EXISTS idx_translations_lang ON translations(language);
                CREATE INDEX IF NOT EXISTS idx_translations_context ON translations(context);
            """)
    
    def _populate_default_translations(self):
        """Populate database with essential educational translations"""
        default_translations = [
            # Basic educational terms
            ('lesson', 'lg', 'essomo', 'education', 'standard'),
            ('lesson', 'sw', 'somo', 'education', 'standard'),
            ('lesson', 'nyn', 'eshomo', 'education', 'standard'),
            
            ('student', 'lg', 'omuyizi', 'education', 'standard'),
            ('student', 'sw', 'mwanafunzi', 'education', 'standard'),
            ('student', 'nyn', 'omuyizi', 'education', 'standard'),
            
            ('teacher', 'lg', 'omusomesa', 'education', 'standard'),
            ('teacher', 'sw', 'mwalimu', 'education', 'standard'),
            ('teacher', 'nyn', 'omwarimu', 'education', 'standard'),
            
            # Mathematics terms
            ('number', 'lg', 'ennamba', 'mathematics', 'standard'),
            ('number', 'sw', 'nambari', 'mathematics', 'standard'),
            ('number', 'nyn', 'ennamba', 'mathematics', 'standard'),
            
            ('addition', 'lg', 'okugattako', 'mathematics', 'standard'),
            ('addition', 'sw', 'kuongeza', 'mathematics', 'standard'),
            ('addition', 'nyn', 'okugattako', 'mathematics', 'standard'),
            
            ('subtraction', 'lg', 'okuggyako', 'mathematics', 'standard'),
            ('subtraction', 'sw', 'kutoa', 'mathematics', 'standard'),
            ('subtraction', 'nyn', 'okuggyako', 'mathematics', 'standard'),
            
            # Science terms
            ('water', 'lg', 'amazzi', 'science', 'standard'),
            ('water', 'sw', 'maji', 'science', 'standard'),
            ('water', 'nyn', 'amaizi', 'science', 'standard'),
            
            ('plant', 'lg', 'ekimera', 'science', 'standard'),
            ('plant', 'sw', 'mmea', 'science', 'standard'),
            ('plant', 'nyn', 'ekimera', 'science', 'standard'),
            
            ('animal', 'lg', 'ekisolo', 'science', 'standard'),
            ('animal', 'sw', 'mnyama', 'science', 'standard'),
            ('animal', 'nyn', 'ekinyamaishwa', 'science', 'standard'),
            
            # Common classroom phrases
            ('good morning', 'lg', 'wasuze otya', 'classroom', 'standard'),
            ('good morning', 'sw', 'habari za asubuhi', 'classroom', 'standard'),
            ('good morning', 'nyn', 'oraire ota', 'classroom', 'standard'),
            
            ('thank you', 'lg', 'webale', 'classroom', 'standard'),
            ('thank you', 'sw', 'asante', 'classroom', 'standard'),
            ('thank you', 'nyn', 'webale', 'classroom', 'standard'),
            
            ('excuse me', 'lg', 'nsonyiwa', 'classroom', 'standard'),
            ('excuse me', 'sw', 'samahani', 'classroom', 'standard'),
            ('excuse me', 'nyn', 'nsonyiwa', 'classroom', 'standard'),
            
            # Technical terms with simplified versions
            ('fraction', 'lg', 'ekitundu', 'mathematics', 'standard'),
            ('fraction', 'sw', 'sehemu', 'mathematics', 'standard'),
            ('fraction', 'nyn', 'akashwekati', 'mathematics', 'standard'),
            
            ('fraction', 'lg', 'ekimu ku kimu', 'mathematics', 'simplified'),
            ('fraction', 'sw', 'sehemu moja', 'mathematics', 'simplified'),
            ('fraction', 'nyn', 'akamu kanini', 'mathematics', 'simplified'),
        ]
        
        # Insert default translations if they don't exist
        try:
            with self.conn_lock:
                with sqlite3.connect(self.db_path) as conn:
                    for key, lang, text, context, complexity in default_translations:
                        conn.execute("""
                            INSERT OR IGNORE INTO translations 
                            (key, language, text, context, complexity_level)
                            VALUES (?, ?, ?, ?, ?)
                        """, (key, lang, text, context, complexity))
                        
            logger.info("Populated default translations")
        except Exception as e:
            logger.error(f"Failed to populate default translations: {e}")
    
    def add_translation(self, entry: TranslationEntry) -> bool:
        """Add or update a translation entry"""
        try:
            with self.conn_lock:
                with sqlite3.connect(self.db_path) as conn:
                    data = entry.to_dict()
                    conn.execute("""
                        INSERT OR REPLACE INTO translations
                        (key, language, text, context, complexity_level, 
                         phonetic_guide, usage_examples, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (
                        data['key'], data['language'], data['text'], data['context'],
                        data['complexity_level'], data['phonetic_guide'], data['usage_examples']
                    ))
            return True
        except Exception as e:
            logger.error(f"Failed to add translation: {e}")
            return False
    
    def get_translation(self, key: str, language: Language,
                       context: str = '', complexity: LanguageComplexity = None) -> Optional[TranslationEntry]:
        """Get translation for a key in specified language"""
        try:
            with self.conn_lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    
                    # Try exact match first
                    if complexity:
                        query = """
                            SELECT * FROM translations 
                            WHERE key = ? AND language = ? AND context = ? AND complexity_level = ?
                        """
                        params = (key, language.value, context, complexity.value)
                    else:
                        query = """
                            SELECT * FROM translations 
                            WHERE key = ? AND language = ? AND context = ?
                            ORDER BY complexity_level DESC LIMIT 1
                        """
                        params = (key, language.value, context)
                    
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    row = cursor.fetchone()
                    
                    if row:
                        return TranslationEntry.from_dict(dict(row))
                    
                    # Fallback: try without context
                    if context:
                        cursor.execute("""
                            SELECT * FROM translations 
                            WHERE key = ? AND language = ?
                            ORDER BY complexity_level DESC LIMIT 1
                        """, (key, language.value))
                        row = cursor.fetchone()
                        
                        if row:
                            return TranslationEntry.from_dict(dict(row))
                            
        except Exception as e:
            logger.error(f"Failed to get translation: {e}")
        
        return None
    
    def search_translations(self, query: str, language: Language = None,
                          context: str = None, limit: int = 10) -> List[TranslationEntry]:
        """Search for translations matching query"""
        translations = []
        try:
            with self.conn_lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    
                    sql_query = "SELECT * FROM translations WHERE (key LIKE ? OR text LIKE ?)"
                    params = [f"%{query}%", f"%{query}%"]
                    
                    if language:
                        sql_query += " AND language = ?"
                        params.append(language.value)
                    
                    if context:
                        sql_query += " AND context = ?"
                        params.append(context)
                    
                    sql_query += " ORDER BY key ASC LIMIT ?"
                    params.append(limit)
                    
                    cursor = conn.cursor()
                    cursor.execute(sql_query, params)
                    
                    for row in cursor.fetchall():
                        translations.append(TranslationEntry.from_dict(dict(row)))
                        
        except Exception as e:
            logger.error(f"Failed to search translations: {e}")
        
        return translations
    
    def store_user_preference(self, preference: LanguagePreference) -> bool:
        """Store user language preference"""
        try:
            with self.conn_lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO language_preferences
                        (user_id, primary_language, fallback_languages, complexity_level,
                         enable_code_switching, phonetic_support, math_language, science_language, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (
                        preference.user_id,
                        preference.primary_language.value,
                        json.dumps([lang.value for lang in preference.fallback_languages]),
                        preference.complexity_level.value,
                        preference.enable_code_switching,
                        preference.phonetic_support,
                        preference.math_language.value if preference.math_language else None,
                        preference.science_language.value if preference.science_language else None
                    ))
            return True
        except Exception as e:
            logger.error(f"Failed to store user preference: {e}")
            return False
    
    def get_user_preference(self, user_id: str) -> Optional[LanguagePreference]:
        """Get user language preference"""
        try:
            with self.conn_lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT * FROM language_preferences WHERE user_id = ?
                    """, (user_id,))
                    row = cursor.fetchone()
                    
                    if row:
                        data = dict(row)
                        return LanguagePreference(
                            user_id=data['user_id'],
                            primary_language=Language(data['primary_language']),
                            fallback_languages=[Language(lang) for lang in json.loads(data['fallback_languages'])],
                            complexity_level=LanguageComplexity(data['complexity_level']),
                            enable_code_switching=bool(data['enable_code_switching']),
                            phonetic_support=bool(data['phonetic_support']),
                            math_language=Language(data['math_language']) if data['math_language'] else None,
                            science_language=Language(data['science_language']) if data['science_language'] else None
                        )
                        
        except Exception as e:
            logger.error(f"Failed to get user preference: {e}")
        
        return None


class LanguageScaffold:
    """Main language scaffolding system that provides contextual translation and support"""
    
    def __init__(self, db_path: str = "translations.db"):
        self.translation_db = TranslationDatabase(db_path)
        self.phonetic_guide = PhoneticGuide()
        self.code_switching = CodeSwitchingEngine()
        
        # Cache for frequently used translations
        self.translation_cache: Dict[str, TranslationEntry] = {}
        self.cache_size_limit = 1000
    
    def set_user_language_preference(self, user_id: str, preference: LanguagePreference) -> bool:
        """Set language preference for a user"""
        return self.translation_db.store_user_preference(preference)
    
    def get_user_language_preference(self, user_id: str) -> LanguagePreference:
        """Get language preference for user, with sensible defaults"""
        preference = self.translation_db.get_user_preference(user_id)
        
        if preference is None:
            # Create default preference
            preference = LanguagePreference(
                user_id=user_id,
                primary_language=Language.ENGLISH,  # Default to English
                complexity_level=LanguageComplexity.STANDARD
            )
            self.translation_db.store_user_preference(preference)
        
        return preference
    
    def translate_content(self, content: str, user_id: str, 
                         subject_context: str = None) -> dict:
        """Translate educational content based on user preferences
        
        Returns:
            Dict with translated content and metadata
        """
        preference = self.get_user_language_preference(user_id)
        
        if preference.primary_language == Language.ENGLISH:
            return {
                'translated_text': content,
                'primary_language': 'en',
                'fallback_used': False,
                'code_switched': False,
                'phonetic_guides': {},
                'untranslated_terms': []
            }
        
        # Determine target language based on subject context
        target_language = preference.primary_language
        if subject_context == 'mathematics' and preference.math_language:
            target_language = preference.math_language
        elif subject_context == 'science' and preference.science_language:
            target_language = preference.science_language
        
        # Process the content
        translated_text, metadata = self._translate_text(
            content, target_language, preference, subject_context
        )
        
        # Apply code-switching if enabled
        if preference.enable_code_switching:
            translated_text = self.code_switching.apply_code_switching(
                translated_text, target_language, subject_context
            )
            metadata['code_switched'] = True
        
        return {
            'translated_text': translated_text,
            'primary_language': target_language.value,
            'fallback_used': metadata.get('fallback_used', False),
            'code_switched': metadata.get('code_switched', False),
            'phonetic_guides': metadata.get('phonetic_guides', {}),
            'untranslated_terms': metadata.get('untranslated_terms', [])
        }
    
    def _translate_text(self, text: str, target_language: Language,
                       preference: LanguagePreference, context: str = None) -> Tuple[str, dict]:
        """Translate text using fallback chain if needed"""
        
        # Split text into words and handle translation
        words = self._tokenize_text(text)
        translated_words = []
        untranslated_terms = []
        phonetic_guides = {}
        fallback_used = False
        
        for word_info in words:
            if word_info['type'] == 'word':
                word = word_info['content']
                translated_word, used_fallback, phonetic = self._translate_word(
                    word, target_language, preference, context
                )
                
                translated_words.append(translated_word)
                
                if used_fallback:
                    fallback_used = True
                
                if phonetic and preference.phonetic_support:
                    phonetic_guides[word] = phonetic
                
                if translated_word == word:  # No translation found
                    untranslated_terms.append(word)
            else:
                # Keep punctuation and whitespace as-is
                translated_words.append(word_info['content'])
        
        translated_text = ''.join(translated_words)
        
        metadata = {
            'fallback_used': fallback_used,
            'phonetic_guides': phonetic_guides,
            'untranslated_terms': untranslated_terms
        }
        
        return translated_text, metadata
    
    def _tokenize_text(self, text: str) -> List[dict]:
        """Tokenize text into words and non-word elements"""
        tokens = []
        current_word = ""
        
        for char in text:
            if char.isalnum():
                current_word += char
            else:
                if current_word:
                    tokens.append({'type': 'word', 'content': current_word})
                    current_word = ""
                tokens.append({'type': 'punct', 'content': char})
        
        if current_word:
            tokens.append({'type': 'word', 'content': current_word})
        
        return tokens
    
    def _translate_word(self, word: str, target_language: Language,
                       preference: LanguagePreference, context: str = None) -> Tuple[str, bool, Optional[str]]:
        """Translate a single word using fallback chain"""
        
        # Try cache first
        cache_key = f"{word}:{target_language.value}:{context}:{preference.complexity_level.value}"
        if cache_key in self.translation_cache:
            entry = self.translation_cache[cache_key]
            phonetic = self.phonetic_guide.generate_phonetic_guide(
                entry.text, target_language, self._is_technical_term(word, context)
            )
            return entry.text, False, phonetic
        
        # Try direct translation
        translation = self.translation_db.get_translation(
            word.lower(), target_language, context or '', preference.complexity_level
        )
        
        if translation:
            self._cache_translation(cache_key, translation)
            phonetic = self.phonetic_guide.generate_phonetic_guide(
                translation.text, target_language, self._is_technical_term(word, context)
            )
            return translation.text, False, phonetic
        
        # Try fallback languages
        for fallback_lang in preference.fallback_languages:
            translation = self.translation_db.get_translation(
                word.lower(), fallback_lang, context or '', preference.complexity_level
            )
            
            if translation:
                self._cache_translation(cache_key, translation)
                phonetic = self.phonetic_guide.generate_phonetic_guide(
                    translation.text, fallback_lang, self._is_technical_term(word, context)
                )
                return translation.text, True, phonetic
        
        # Try simplified complexity level
        if preference.complexity_level != LanguageComplexity.SIMPLIFIED:
            simplified_translation = self.translation_db.get_translation(
                word.lower(), target_language, context or '', LanguageComplexity.SIMPLIFIED
            )
            
            if simplified_translation:
                self._cache_translation(cache_key, simplified_translation)
                phonetic = self.phonetic_guide.generate_phonetic_guide(
                    simplified_translation.text, target_language, self._is_technical_term(word, context)
                )
                return simplified_translation.text, False, phonetic
        
        # No translation found - return original word
        # Generate phonetic guide for English word
        phonetic = self.phonetic_guide.generate_phonetic_guide(
            word, Language.ENGLISH, self._is_technical_term(word, context)
        )
        return word, True, phonetic
    
    def _is_technical_term(self, word: str, context: str) -> bool:
        """Check if word is likely a technical term"""
        technical_contexts = {'mathematics', 'science', 'computer_science', 'physics', 'chemistry', 'biology'}
        return context in technical_contexts or word.lower() in self.code_switching.technical_terms_english
    
    def _cache_translation(self, cache_key: str, translation: TranslationEntry):
        """Cache translation entry"""
        if len(self.translation_cache) >= self.cache_size_limit:
            # Remove oldest entries (simple FIFO)
            oldest_key = next(iter(self.translation_cache))
            del self.translation_cache[oldest_key]
        
        self.translation_cache[cache_key] = translation
    
    def add_translation(self, key: str, language: Language, text: str,
                       context: str = '', complexity: LanguageComplexity = LanguageComplexity.STANDARD,
                       usage_examples: List[str] = None) -> bool:
        """Add a new translation to the database"""
        
        # Generate phonetic guide
        phonetic_guide = self.phonetic_guide.generate_phonetic_guide(
            text, language, context in ['mathematics', 'science']
        )
        
        entry = TranslationEntry(
            key=key.lower(),
            language=language,
            text=text,
            context=context,
            complexity_level=complexity,
            phonetic_guide=phonetic_guide,
            usage_examples=usage_examples or []
        )
        
        return self.translation_db.add_translation(entry)
    
    def get_phonetic_guide(self, word: str, language: Language, is_technical: bool = False) -> str:
        """Get phonetic pronunciation guide for a word"""
        return self.phonetic_guide.generate_phonetic_guide(word, language, is_technical)
    
    def suggest_code_switching(self, text: str, user_id: str, subject_context: str = None) -> List[dict]:
        """Suggest code-switching opportunities in text"""
        preference = self.get_user_language_preference(user_id)
        return self.code_switching.suggest_code_switch_points(text, preference.primary_language)
    
    def search_translations(self, query: str, user_id: str, limit: int = 10) -> List[dict]:
        """Search for translations matching query"""
        preference = self.get_user_language_preference(user_id)
        translations = self.translation_db.search_translations(
            query, preference.primary_language, limit=limit
        )
        
        results = []
        for translation in translations:
            results.append({
                'key': translation.key,
                'text': translation.text,
                'context': translation.context,
                'complexity': translation.complexity_level.value,
                'phonetic_guide': translation.phonetic_guide,
                'usage_examples': translation.usage_examples
            })
        
        return results
    
    def get_language_stats(self, user_id: str) -> dict:
        """Get language usage statistics for user"""
        preference = self.get_user_language_preference(user_id)
        
        # This would typically query usage logs
        return {
            'primary_language': preference.primary_language.value,
            'fallback_languages': [lang.value for lang in preference.fallback_languages],
            'complexity_level': preference.complexity_level.value,
            'code_switching_enabled': preference.enable_code_switching,
            'phonetic_support_enabled': preference.phonetic_support,
            'subject_preferences': {
                'mathematics': preference.math_language.value if preference.math_language else None,
                'science': preference.science_language.value if preference.science_language else None
            },
            'translation_cache_size': len(self.translation_cache)
        }


# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize language scaffold
    language_system = LanguageScaffold()
    
    # Set up user language preference
    user_preference = LanguagePreference(
        user_id="student_123",
        primary_language=Language.LUGANDA,
        fallback_languages=[Language.ENGLISH, Language.SWAHILI],
        complexity_level=LanguageComplexity.STANDARD,
        enable_code_switching=True,
        phonetic_support=True,
        math_language=Language.ENGLISH  # Keep math in English
    )
    
    language_system.set_user_language_preference("student_123", user_preference)
    
    # Add some custom translations
    language_system.add_translation(
        "photosynthesis", Language.LUGANDA, "okukola emmere mu kimera",
        context="science", complexity=LanguageComplexity.STANDARD,
        usage_examples=["Plants use photosynthesis to make food"]
    )
    
    # Translate educational content
    english_content = "Today we will learn about fractions. A fraction represents part of a whole number."
    
    translated_result = language_system.translate_content(
        english_content, "student_123", subject_context="mathematics"
    )
    
    print("Translation Result:")
    print(f"Original: {english_content}")
    print(f"Translated: {translated_result['translated_text']}")
    print(f"Language: {translated_result['primary_language']}")
    print(f"Code-switched: {translated_result['code_switched']}")
    print(f"Phonetic guides: {translated_result['phonetic_guides']}")
    print(f"Untranslated terms: {translated_result['untranslated_terms']}")
    
    # Get phonetic guide for technical term
    phonetic = language_system.get_phonetic_guide("photosynthesis", Language.ENGLISH, is_technical=True)
    print(f"\nPhotosynthesis pronunciation: {phonetic}")
    
    # Search translations
    search_results = language_system.search_translations("water", "student_123")
    print(f"\nSearch results for 'water': {search_results}")
    
    # Get language statistics
    stats = language_system.get_language_stats("student_123")
    print(f"\nLanguage statistics: {stats}")