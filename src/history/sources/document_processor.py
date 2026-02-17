"""Document processing system for primary sources."""
import asyncio
import logging
import re
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import base64
import mimetypes

from src.history.schemas import PrimarySource, SourceType, HistoricalPeriod

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Processes different types of historical documents and media."""
    
    def __init__(self):
        # Supported file formats
        self.supported_formats = {
            "text": [".txt", ".doc", ".docx", ".pdf", ".rtf"],
            "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"],
            "audio": [".mp3", ".wav", ".ogg", ".m4a"],
            "video": [".mp4", ".avi", ".mov", ".wmv", ".flv"]
        }
        
        # Source type mappings
        self.source_type_mappings = self._initialize_source_type_mappings()
        
        # OCR and transcription services (placeholder for actual services)
        self.ocr_enabled = False
        self.transcription_enabled = False
    
    def _initialize_source_type_mappings(self) -> Dict[str, SourceType]:
        """Initialize mappings from file types to source types."""
        return {
            "letter": SourceType.LETTER,
            "diary": SourceType.DIARY,
            "speech": SourceType.SPEECH,
            "treaty": SourceType.TREATY,
            "newspaper": SourceType.NEWSPAPER,
            "photograph": SourceType.PHOTOGRAPH,
            "artwork": SourceType.ARTWORK,
            "artifact": SourceType.ARTIFACT,
            "memoir": SourceType.MEMOIR,
            "document": SourceType.DOCUMENT,
            "government": SourceType.GOVERNMENT_RECORD,
            "oral": SourceType.ORAL_HISTORY
        }
    
    async def process_document(
        self,
        file_path: Optional[str] = None,
        file_content: Optional[bytes] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source_hints: Optional[Dict[str, Any]] = None
    ) -> PrimarySource:
        """Process a document and create a PrimarySource object."""
        
        if not file_path and not file_content:
            raise ValueError("Either file_path or file_content must be provided")
        
        # Initialize metadata
        if metadata is None:
            metadata = {}
        
        if source_hints is None:
            source_hints = {}
        
        logger.info(f"Processing document: {file_path or 'content-based'}")
        
        # Determine file type and format
        file_info = await self._analyze_file_format(file_path, file_content)
        
        # Extract content based on file type
        extracted_content = await self._extract_content(
            file_path, file_content, file_info
        )
        
        # Determine source type
        source_type = self._determine_source_type(
            file_info, extracted_content, source_hints, metadata
        )
        
        # Extract metadata from content and filename
        extracted_metadata = await self._extract_metadata(
            extracted_content, file_info, metadata
        )
        
        # Create PrimarySource object
        primary_source = await self._create_primary_source(
            extracted_content,
            source_type,
            extracted_metadata,
            file_info
        )
        
        logger.info(f"Successfully processed document: {primary_source.title}")
        return primary_source
    
    async def _analyze_file_format(
        self,
        file_path: Optional[str],
        file_content: Optional[bytes]
    ) -> Dict[str, Any]:
        """Analyze file format and properties."""
        
        file_info = {
            "format": "unknown",
            "extension": "",
            "mime_type": "",
            "size": 0,
            "filename": ""
        }
        
        if file_path:
            path = Path(file_path)
            file_info["filename"] = path.name
            file_info["extension"] = path.suffix.lower()
            
            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            file_info["mime_type"] = mime_type or "application/octet-stream"
        
        if file_content:
            file_info["size"] = len(file_content)
            
            # Determine format from content if path not available
            if not file_path:
                file_info["format"] = self._detect_format_from_content(file_content)
        
        # Categorize format
        extension = file_info["extension"]
        for format_category, extensions in self.supported_formats.items():
            if extension in extensions:
                file_info["format"] = format_category
                break
        
        return file_info
    
    def _detect_format_from_content(self, content: bytes) -> str:
        """Detect file format from content bytes."""
        
        # Common file signatures
        signatures = {
            b'\xFF\xD8\xFF': "image",  # JPEG
            b'\x89PNG\r\n\x1A\n': "image",  # PNG
            b'GIF87a': "image",  # GIF87a
            b'GIF89a': "image",  # GIF89a
            b'%PDF': "text",  # PDF
            b'\x50\x4B\x03\x04': "text",  # ZIP-based (DOCX, etc.)
        }
        
        for signature, format_type in signatures.items():
            if content.startswith(signature):
                return format_type
        
        # Try to decode as text
        try:
            content.decode('utf-8')
            return "text"
        except UnicodeDecodeError:
            pass
        
        return "unknown"
    
    async def _extract_content(
        self,
        file_path: Optional[str],
        file_content: Optional[bytes],
        file_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract content from the file based on its format."""
        
        extracted = {
            "text": None,
            "image_data": None,
            "audio_data": None,
            "video_data": None,
            "raw_content": None
        }
        
        format_type = file_info["format"]
        
        try:
            if format_type == "text":
                extracted["text"] = await self._extract_text_content(
                    file_path, file_content, file_info
                )
            
            elif format_type == "image":
                extracted["image_data"] = await self._process_image_content(
                    file_path, file_content, file_info
                )
                # Attempt OCR if enabled
                if self.ocr_enabled:
                    extracted["text"] = await self._perform_ocr(
                        file_path, file_content
                    )
            
            elif format_type == "audio":
                extracted["audio_data"] = await self._process_audio_content(
                    file_path, file_content, file_info
                )
                # Attempt transcription if enabled
                if self.transcription_enabled:
                    extracted["text"] = await self._transcribe_audio(
                        file_path, file_content
                    )
            
            elif format_type == "video":
                extracted["video_data"] = await self._process_video_content(
                    file_path, file_content, file_info
                )
            
            # Store raw content for unknown formats
            if file_content:
                extracted["raw_content"] = base64.b64encode(file_content).decode()
            
        except Exception as e:
            logger.error(f"Error extracting content: {e}")
            extracted["error"] = str(e)
        
        return extracted
    
    async def _extract_text_content(
        self,
        file_path: Optional[str],
        file_content: Optional[bytes],
        file_info: Dict[str, Any]
    ) -> str:
        """Extract text content from text files."""
        
        text_content = ""
        
        try:
            if file_content:
                # Try different encodings
                encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
                for encoding in encodings:
                    try:
                        text_content = file_content.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
            
            elif file_path:
                # Read from file
                encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
                for encoding in encodings:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            text_content = f.read()
                        break
                    except (UnicodeDecodeError, FileNotFoundError):
                        continue
            
            # Handle specific formats
            extension = file_info.get("extension", "")
            if extension == ".pdf":
                text_content = await self._extract_pdf_text(file_path, file_content)
            elif extension in [".doc", ".docx"]:
                text_content = await self._extract_word_text(file_path, file_content)
            
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            text_content = f"Error extracting text: {e}"
        
        return text_content
    
    async def _extract_pdf_text(
        self,
        file_path: Optional[str],
        file_content: Optional[bytes]
    ) -> str:
        """Extract text from PDF files."""
        
        # Placeholder for PDF text extraction
        # In a real implementation, you would use libraries like PyPDF2 or pdfplumber
        logger.info("PDF text extraction not implemented - using placeholder")
        return "PDF text content would be extracted here"
    
    async def _extract_word_text(
        self,
        file_path: Optional[str],
        file_content: Optional[bytes]
    ) -> str:
        """Extract text from Word documents."""
        
        # Placeholder for Word document text extraction
        # In a real implementation, you would use libraries like python-docx
        logger.info("Word document extraction not implemented - using placeholder")
        return "Word document text content would be extracted here"
    
    async def _process_image_content(
        self,
        file_path: Optional[str],
        file_content: Optional[bytes],
        file_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process image content and extract metadata."""
        
        image_data = {
            "width": None,
            "height": None,
            "color_mode": None,
            "format": file_info.get("extension", "").upper(),
            "description": "",
            "base64_data": None
        }
        
        try:
            if file_content:
                image_data["base64_data"] = base64.b64encode(file_content).decode()
                # Placeholder for image analysis
                image_data["description"] = "Historical photograph or artwork"
            
            # In a real implementation, you would use libraries like Pillow
            # to extract actual image metadata and perform analysis
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            image_data["error"] = str(e)
        
        return image_data
    
    async def _process_audio_content(
        self,
        file_path: Optional[str],
        file_content: Optional[bytes],
        file_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process audio content."""
        
        audio_data = {
            "duration": None,
            "format": file_info.get("extension", "").upper(),
            "sample_rate": None,
            "channels": None,
            "description": "Historical audio recording",
            "base64_data": None
        }
        
        try:
            if file_content:
                audio_data["base64_data"] = base64.b64encode(file_content).decode()
            
            # Placeholder for audio analysis
            # In a real implementation, you would use libraries like librosa or pydub
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            audio_data["error"] = str(e)
        
        return audio_data
    
    async def _process_video_content(
        self,
        file_path: Optional[str],
        file_content: Optional[bytes],
        file_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process video content."""
        
        video_data = {
            "duration": None,
            "width": None,
            "height": None,
            "framerate": None,
            "format": file_info.get("extension", "").upper(),
            "description": "Historical video recording",
            "base64_data": None
        }
        
        try:
            if file_content:
                # For large video files, you might want to store only metadata
                # and save the actual file separately
                video_data["size"] = len(file_content)
            
            # Placeholder for video analysis
            # In a real implementation, you would use libraries like OpenCV or ffmpeg
            
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            video_data["error"] = str(e)
        
        return video_data
    
    async def _perform_ocr(
        self,
        file_path: Optional[str],
        file_content: Optional[bytes]
    ) -> str:
        """Perform OCR on image content."""
        
        # Placeholder for OCR functionality
        # In a real implementation, you would use libraries like Tesseract or cloud OCR services
        logger.info("OCR not implemented - using placeholder")
        return "OCR text would be extracted from the image here"
    
    async def _transcribe_audio(
        self,
        file_path: Optional[str],
        file_content: Optional[bytes]
    ) -> str:
        """Transcribe audio content to text."""
        
        # Placeholder for audio transcription
        # In a real implementation, you would use services like Whisper, Google Speech-to-Text, etc.
        logger.info("Audio transcription not implemented - using placeholder")
        return "Audio transcription would be generated here"
    
    def _determine_source_type(
        self,
        file_info: Dict[str, Any],
        extracted_content: Dict[str, Any],
        source_hints: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> SourceType:
        """Determine the source type from various indicators."""
        
        # Check explicit hints first
        if "source_type" in source_hints:
            hint_type = source_hints["source_type"].lower()
            for key, source_type in self.source_type_mappings.items():
                if key in hint_type:
                    return source_type
        
        # Check filename for clues
        filename = file_info.get("filename", "").lower()
        for key, source_type in self.source_type_mappings.items():
            if key in filename:
                return source_type
        
        # Check content for clues
        text_content = extracted_content.get("text", "") or ""
        text_lower = text_content.lower()
        
        # Specific patterns for different source types
        if any(phrase in text_lower for phrase in ["dear", "sincerely", "yours truly", "my dear"]):
            return SourceType.LETTER
        elif any(phrase in text_lower for phrase in ["diary", "today i", "this morning"]):
            return SourceType.DIARY
        elif any(phrase in text_lower for phrase in ["ladies and gentlemen", "my fellow", "today i speak"]):
            return SourceType.SPEECH
        elif any(phrase in text_lower for phrase in ["treaty", "agreement", "shall be", "article"]):
            return SourceType.TREATY
        elif any(phrase in text_lower for phrase in ["newspaper", "daily", "times", "herald", "post"]):
            return SourceType.NEWSPAPER
        elif any(phrase in text_lower for phrase in ["memoir", "i remember", "looking back", "my life"]):
            return SourceType.MEMOIR
        elif "government" in text_lower or "official" in text_lower:
            return SourceType.GOVERNMENT_RECORD
        
        # Default based on file format
        format_type = file_info.get("format", "unknown")
        if format_type == "image":
            return SourceType.PHOTOGRAPH
        elif format_type == "audio":
            return SourceType.ORAL_HISTORY
        else:
            return SourceType.DOCUMENT
    
    async def _extract_metadata(
        self,
        extracted_content: Dict[str, Any],
        file_info: Dict[str, Any],
        provided_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract and compile metadata from various sources."""
        
        metadata = provided_metadata.copy()
        
        # Extract dates from content
        if not metadata.get("date_created"):
            metadata["date_created"] = await self._extract_date_from_content(
                extracted_content.get("text", "")
            )
        
        # Extract author from content
        if not metadata.get("author"):
            metadata["author"] = await self._extract_author_from_content(
                extracted_content.get("text", "")
            )
        
        # Extract title
        if not metadata.get("title"):
            metadata["title"] = self._generate_title(
                extracted_content, file_info, metadata
            )
        
        # Extract location references
        if not metadata.get("origin_location"):
            metadata["origin_location"] = await self._extract_location_from_content(
                extracted_content.get("text", "")
            )
        
        # Determine historical period
        if not metadata.get("historical_period"):
            metadata["historical_period"] = self._determine_historical_period(
                metadata.get("date_created")
            )
        
        # Generate description
        if not metadata.get("description"):
            metadata["description"] = self._generate_description(
                extracted_content, file_info, metadata
            )
        
        return metadata
    
    async def _extract_date_from_content(self, text: str) -> Optional[str]:
        """Extract date information from text content."""
        
        if not text:
            return None
        
        # Common date patterns
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b',  # MM/DD/YYYY or DD/MM/YYYY
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',  # YYYY/MM/DD
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
            r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b',
            r'\b\d{4}\b'  # Just year
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return None
    
    async def _extract_author_from_content(self, text: str) -> Optional[str]:
        """Extract author information from text content."""
        
        if not text:
            return None
        
        # Common author patterns
        author_patterns = [
            r'(?:signed|by|from|author|written by)[\s:]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # Name at beginning
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*$'  # Name at end
        ]
        
        for pattern in author_patterns:
            matches = re.findall(pattern, text[:500], re.MULTILINE)  # Check first 500 chars
            if matches:
                return matches[0].strip()
        
        return None
    
    async def _extract_location_from_content(self, text: str) -> Optional[str]:
        """Extract location information from text content."""
        
        if not text:
            return None
        
        # Common location patterns
        location_patterns = [
            r'\b(?:in|at|from)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s*([A-Z][a-z]+)?\b',
            r'\b([A-Z][a-z]+),\s*([A-Z][A-Z])\b',  # City, STATE
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s+(?:England|France|Germany|Italy|Spain|Russia|China|Japan|India)\b'
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, text[:1000], re.IGNORECASE)
            if matches:
                if isinstance(matches[0], tuple):
                    return ", ".join(filter(None, matches[0]))
                return matches[0]
        
        return None
    
    def _determine_historical_period(self, date_str: Optional[str]) -> HistoricalPeriod:
        """Determine historical period from date."""
        
        if not date_str:
            return HistoricalPeriod.CONTEMPORARY
        
        # Extract year
        year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
        if not year_match:
            return HistoricalPeriod.CONTEMPORARY
        
        year = int(year_match.group())
        
        # Map year to historical period
        if year < 1500:
            return HistoricalPeriod.MEDIEVAL
        elif year < 1700:
            return HistoricalPeriod.RENAISSANCE
        elif year < 1850:
            return HistoricalPeriod.EARLY_MODERN
        elif year < 1920:
            return HistoricalPeriod.INDUSTRIAL_AGE
        elif year < 1990:
            return HistoricalPeriod.MODERN_ERA
        else:
            return HistoricalPeriod.CONTEMPORARY
    
    def _generate_title(
        self,
        extracted_content: Dict[str, Any],
        file_info: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> str:
        """Generate a title for the source."""
        
        # Use filename if available
        filename = file_info.get("filename", "")
        if filename:
            # Clean up filename
            title = Path(filename).stem
            title = re.sub(r'[_-]', ' ', title)
            title = title.replace('.', ' ').strip()
            if title:
                return title.title()
        
        # Use first line of text content
        text = extracted_content.get("text", "")
        if text:
            first_line = text.split('\n')[0].strip()
            if first_line and len(first_line) < 100:
                return first_line[:50] + "..." if len(first_line) > 50 else first_line
        
        # Default titles based on source type
        source_type = metadata.get("source_type", "document")
        author = metadata.get("author", "Unknown Author")
        date = metadata.get("date_created", "Undated")
        
        return f"{source_type.title()} by {author} ({date})"
    
    def _generate_description(
        self,
        extracted_content: Dict[str, Any],
        file_info: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> str:
        """Generate a description for the source."""
        
        format_type = file_info.get("format", "unknown")
        source_type = metadata.get("source_type", "document")
        author = metadata.get("author", "Unknown")
        date = metadata.get("date_created", "Undated")
        
        # Base description
        if format_type == "text":
            text = extracted_content.get("text", "")
            if text:
                # Use first paragraph as description
                paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
                if paragraphs:
                    first_paragraph = paragraphs[0]
                    if len(first_paragraph) > 200:
                        return first_paragraph[:200] + "..."
                    return first_paragraph
        
        # Fallback description
        description_parts = []
        
        if source_type:
            description_parts.append(f"{source_type.title()}")
        
        if author and author != "Unknown":
            description_parts.append(f"by {author}")
        
        if date and date != "Undated":
            description_parts.append(f"from {date}")
        
        base_description = " ".join(description_parts)
        
        if format_type == "image":
            return f"Historical image: {base_description}"
        elif format_type == "audio":
            return f"Historical audio recording: {base_description}"
        elif format_type == "video":
            return f"Historical video recording: {base_description}"
        else:
            return f"Historical document: {base_description}"
    
    async def _create_primary_source(
        self,
        extracted_content: Dict[str, Any],
        source_type: SourceType,
        metadata: Dict[str, Any],
        file_info: Dict[str, Any]
    ) -> PrimarySource:
        """Create a PrimarySource object from processed data."""
        
        # Generate unique ID
        import uuid
        source_id = str(uuid.uuid4())
        
        # Create the primary source
        primary_source = PrimarySource(
            source_id=source_id,
            title=metadata.get("title", "Untitled Document"),
            description=metadata.get("description", "Historical document"),
            source_type=source_type,
            
            # Content
            content=extracted_content.get("text"),
            image_url=metadata.get("image_url"),
            document_url=metadata.get("document_url"),
            
            # Historical context
            date_created=metadata.get("date_created", "Undated"),
            author=metadata.get("author"),
            origin_location=metadata.get("origin_location"),
            historical_period=metadata.get("historical_period", HistoricalPeriod.CONTEMPORARY),
            
            # Analysis framework (filled in later by analysis tools)
            intended_audience=metadata.get("intended_audience"),
            purpose=metadata.get("purpose"),
            biases=[],
            limitations=[],
            
            # Educational metadata
            complexity_level=self._calculate_complexity_level(extracted_content, metadata),
            key_concepts=metadata.get("key_concepts", []),
            discussion_questions=[],
            
            # Authenticity
            authenticity_verified=False,
            reliability_score=None
        )
        
        return primary_source
    
    def _calculate_complexity_level(
        self,
        extracted_content: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> float:
        """Calculate complexity level of the source."""
        
        base_complexity = 0.5
        
        text = extracted_content.get("text", "")
        if text:
            # Text length factor
            length_factor = min(len(text) / 5000, 1.0) * 0.2
            
            # Vocabulary complexity (simple measure)
            words = text.split()
            if words:
                avg_word_length = sum(len(word) for word in words) / len(words)
                vocab_factor = min(avg_word_length / 6, 1.0) * 0.2
            else:
                vocab_factor = 0
            
            # Sentence complexity
            sentences = re.split(r'[.!?]+', text)
            if sentences:
                avg_sentence_length = sum(len(s.split()) for s in sentences if s.strip()) / len([s for s in sentences if s.strip()])
                sentence_factor = min(avg_sentence_length / 20, 1.0) * 0.1
            else:
                sentence_factor = 0
            
            base_complexity += length_factor + vocab_factor + sentence_factor
        
        # Historical distance factor
        date_str = metadata.get("date_created", "")
        if date_str:
            year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
            if year_match:
                year = int(year_match.group())
                years_ago = 2024 - year
                historical_distance_factor = min(years_ago / 100, 1.0) * 0.1
                base_complexity += historical_distance_factor
        
        return min(1.0, base_complexity)

    async def batch_process_documents(
        self,
        file_paths: List[str],
        batch_metadata: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> List[PrimarySource]:
        """Process multiple documents in batch."""
        
        if batch_metadata is None:
            batch_metadata = {}
        
        processed_sources = []
        
        for file_path in file_paths:
            try:
                metadata = batch_metadata.get(file_path, {})
                source = await self.process_document(
                    file_path=file_path,
                    metadata=metadata
                )
                processed_sources.append(source)
                
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                continue
        
        logger.info(f"Successfully processed {len(processed_sources)} out of {len(file_paths)} documents")
        return processed_sources