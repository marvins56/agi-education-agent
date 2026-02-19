"""
Import/Export - Content import and export functionality

This module provides capabilities for importing educational content from various sources
and exporting content for offline use, SMS delivery, and other platforms.
"""

import json
import csv
import logging
import zipfile
from abc import ABC, abstractmethod
from dataclasses import asdict
from datetime import datetime
from io import StringIO, BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
import re

from .library import ContentLibrary, ContentItem, ContentType, DifficultyLevel, ContentMetadata

logger = logging.getLogger(__name__)


class ImportFormat(ABC):
    """Abstract base class for import formats"""
    
    @abstractmethod
    def parse(self, data: Union[str, bytes]) -> List[Dict[str, Any]]:
        """Parse content from data"""
        pass
    
    @abstractmethod
    def validate(self, content: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate content structure"""
        pass


class JSONImportFormat(ImportFormat):
    """JSON format importer"""
    
    def parse(self, data: Union[str, bytes]) -> List[Dict[str, Any]]:
        """Parse JSON content"""
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        
        parsed = json.loads(data)
        
        # Handle both single objects and arrays
        if isinstance(parsed, list):
            return parsed
        else:
            return [parsed]
    
    def validate(self, content: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate JSON content structure"""
        errors = []
        required_fields = ['title', 'content_type', 'subject', 'grade', 'topic', 'content_data']
        
        for field in required_fields:
            if field not in content:
                errors.append(f"Missing required field: {field}")
        
        # Validate content_type
        if 'content_type' in content:
            try:
                ContentType(content['content_type'])
            except ValueError:
                errors.append(f"Invalid content_type: {content['content_type']}")
        
        return len(errors) == 0, errors


class CSVImportFormat(ImportFormat):
    """CSV format importer"""
    
    def parse(self, data: Union[str, bytes]) -> List[Dict[str, Any]]:
        """Parse CSV content"""
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        
        reader = csv.DictReader(StringIO(data))
        content_list = []
        
        for row in reader:
            # Convert CSV row to content structure
            content_data = {}
            metadata_fields = ['title', 'content_type', 'subject', 'grade', 'topic', 'difficulty', 'language', 'tags']
            
            for key, value in row.items():
                if key in metadata_fields:
                    continue
                content_data[key] = value
            
            content = {
                'title': row.get('title', ''),
                'content_type': row.get('content_type', 'lesson'),
                'subject': row.get('subject', ''),
                'grade': row.get('grade', ''),
                'topic': row.get('topic', ''),
                'difficulty': row.get('difficulty', 'intermediate'),
                'language': row.get('language', 'en'),
                'tags': row.get('tags', '').split(',') if row.get('tags') else [],
                'content_data': content_data
            }
            content_list.append(content)
        
        return content_list
    
    def validate(self, content: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate CSV content structure"""
        errors = []
        
        if not content.get('title'):
            errors.append("Title is required")
        if not content.get('subject'):
            errors.append("Subject is required")
        if not content.get('content_data'):
            errors.append("Content data is required")
        
        return len(errors) == 0, errors


class MarkdownImportFormat(ImportFormat):
    """Markdown format importer"""
    
    def parse(self, data: Union[str, bytes]) -> List[Dict[str, Any]]:
        """Parse Markdown content"""
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        
        # Extract metadata from front matter (if present)
        metadata = {}
        content_text = data
        
        if data.startswith('---'):
            parts = data.split('---', 2)
            if len(parts) >= 3:
                # Parse YAML front matter (simplified)
                front_matter = parts[1].strip()
                for line in front_matter.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()
                content_text = parts[2].strip()
        
        # Parse markdown structure
        content_data = self._parse_markdown_structure(content_text)
        
        content = {
            'title': metadata.get('title', 'Untitled'),
            'content_type': metadata.get('content_type', 'lesson'),
            'subject': metadata.get('subject', 'General'),
            'grade': metadata.get('grade', '1'),
            'topic': metadata.get('topic', 'General'),
            'difficulty': metadata.get('difficulty', 'intermediate'),
            'language': metadata.get('language', 'en'),
            'tags': metadata.get('tags', '').split(',') if metadata.get('tags') else [],
            'content_data': content_data
        }
        
        return [content]
    
    def validate(self, content: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate Markdown content"""
        errors = []
        
        if not content.get('title') or content.get('title') == 'Untitled':
            errors.append("Title should be specified in front matter")
        
        return len(errors) == 0, errors
    
    def _parse_markdown_structure(self, text: str) -> Dict[str, Any]:
        """Parse markdown into structured content"""
        content = {'raw_markdown': text}
        
        # Extract headings
        headings = re.findall(r'^#+\s+(.+)$', text, re.MULTILINE)
        if headings:
            content['headings'] = headings
        
        # Extract sections
        sections = re.split(r'^#+\s+', text, flags=re.MULTILINE)
        if len(sections) > 1:
            content['sections'] = [section.strip() for section in sections[1:]]
        
        return content


class ContentImporter:
    """Content importer supporting multiple formats"""
    
    def __init__(self, content_library: ContentLibrary):
        """
        Initialize content importer
        
        Args:
            content_library: Content library to import into
        """
        self.content_library = content_library
        self.formats = {
            'json': JSONImportFormat(),
            'csv': CSVImportFormat(),
            'markdown': MarkdownImportFormat(),
            'md': MarkdownImportFormat()
        }
    
    def import_from_file(self, 
                        file_path: Union[str, Path],
                        format_type: Optional[str] = None,
                        author: Optional[str] = None) -> Tuple[int, int, List[str]]:
        """
        Import content from file
        
        Args:
            file_path: Path to file to import
            format_type: Format type (json, csv, markdown) - auto-detected if None
            author: Author to assign to imported content
            
        Returns:
            Tuple of (successful_imports, failed_imports, error_messages)
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return 0, 1, [f"File not found: {file_path}"]
        
        # Auto-detect format if not specified
        if format_type is None:
            format_type = file_path.suffix.lstrip('.').lower()
        
        if format_type not in self.formats:
            return 0, 1, [f"Unsupported format: {format_type}"]
        
        try:
            # Read file
            if format_type == 'csv' or format_type in ['json', 'markdown', 'md']:
                data = file_path.read_text(encoding='utf-8')
            else:
                data = file_path.read_bytes()
            
            return self.import_from_data(data, format_type, author)
        
        except Exception as e:
            logger.error(f"Error importing from file {file_path}: {e}")
            return 0, 1, [f"Import error: {str(e)}"]
    
    def import_from_data(self,
                        data: Union[str, bytes],
                        format_type: str,
                        author: Optional[str] = None) -> Tuple[int, int, List[str]]:
        """
        Import content from raw data
        
        Args:
            data: Raw data to import
            format_type: Format type
            author: Author to assign to imported content
            
        Returns:
            Tuple of (successful_imports, failed_imports, error_messages)
        """
        if format_type not in self.formats:
            return 0, 1, [f"Unsupported format: {format_type}"]
        
        format_handler = self.formats[format_type]
        successful = 0
        failed = 0
        errors = []
        
        try:
            # Parse content
            content_list = format_handler.parse(data)
            
            for content in content_list:
                # Validate content
                is_valid, validation_errors = format_handler.validate(content)
                
                if not is_valid:
                    failed += 1
                    errors.extend(validation_errors)
                    continue
                
                try:
                    # Import into library
                    self._import_content_item(content, author)
                    successful += 1
                
                except Exception as e:
                    failed += 1
                    errors.append(f"Failed to import '{content.get('title', 'Unknown')}': {str(e)}")
        
        except Exception as e:
            logger.error(f"Error parsing content: {e}")
            return 0, 1, [f"Parse error: {str(e)}"]
        
        logger.info(f"Import completed: {successful} successful, {failed} failed")
        return successful, failed, errors
    
    def _import_content_item(self, content: Dict[str, Any], author: Optional[str]):
        """Import a single content item"""
        # Convert string difficulty to enum
        difficulty_str = content.get('difficulty', 'intermediate')
        try:
            difficulty = DifficultyLevel(difficulty_str)
        except ValueError:
            difficulty = DifficultyLevel.INTERMEDIATE
        
        # Convert string content type to enum
        content_type_str = content.get('content_type', 'lesson')
        try:
            content_type = ContentType(content_type_str)
        except ValueError:
            content_type = ContentType.LESSON
        
        # Add to library
        self.content_library.add_content(
            title=content['title'],
            content_type=content_type,
            subject=content['subject'],
            grade=content['grade'],
            topic=content['topic'],
            content_data=content['content_data'],
            difficulty=difficulty,
            language=content.get('language', 'en'),
            duration=content.get('duration'),
            tags=set(content.get('tags', [])),
            author=author
        )


class ExportFormat(ABC):
    """Abstract base class for export formats"""
    
    @abstractmethod
    def format_content(self, content_items: List[ContentItem]) -> Union[str, bytes]:
        """Format content items for export"""
        pass


class SMSExportFormat(ExportFormat):
    """Export format optimized for SMS delivery"""
    
    def __init__(self, max_length: int = 160):
        self.max_length = max_length
    
    def format_content(self, content_items: List[ContentItem]) -> str:
        """Format content for SMS delivery"""
        formatted_content = []
        
        for item in content_items:
            # Create SMS-friendly summary
            title = item.metadata.title
            topic = item.metadata.topic
            
            # Extract key points from content
            content_text = self._extract_text_from_content(item.content_data)
            key_points = self._extract_key_points(content_text, self.max_length - 50)
            
            sms_content = f"{topic}: {key_points}"
            
            # Truncate if too long
            if len(sms_content) > self.max_length:
                sms_content = sms_content[:self.max_length - 3] + "..."
            
            formatted_content.append(sms_content)
        
        return "\n---\n".join(formatted_content)
    
    def _extract_text_from_content(self, content_data: Dict[str, Any]) -> str:
        """Extract text from content data"""
        text_parts = []
        
        def extract_recursive(obj):
            if isinstance(obj, str):
                text_parts.append(obj)
            elif isinstance(obj, dict):
                for value in obj.values():
                    extract_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_recursive(item)
        
        extract_recursive(content_data)
        return " ".join(text_parts)
    
    def _extract_key_points(self, text: str, max_length: int) -> str:
        """Extract key points from text"""
        # Simple extraction - take first sentences up to max_length
        sentences = re.split(r'[.!?]+', text)
        result = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(result + sentence) < max_length:
                if result:
                    result += ". "
                result += sentence
            else:
                break
        
        return result


class USSDExportFormat(ExportFormat):
    """Export format for USSD delivery"""
    
    def format_content(self, content_items: List[ContentItem]) -> str:
        """Format content for USSD delivery"""
        ussd_menu = []
        
        for i, item in enumerate(content_items, 1):
            # Create USSD menu structure
            menu_item = f"{i}. {item.metadata.title}"
            ussd_menu.append(menu_item)
        
        menu_text = "Select lesson:\n" + "\n".join(ussd_menu)
        
        # Add content pages
        content_pages = []
        for i, item in enumerate(content_items, 1):
            page_text = f"Lesson {i}: {item.metadata.title}\n"
            content_text = self._extract_text_from_content(item.content_data)
            
            # Split into USSD-sized chunks (182 chars max)
            chunks = self._split_into_chunks(content_text, 150)
            for j, chunk in enumerate(chunks, 1):
                page_text += f"Page {j}: {chunk}\n"
            
            content_pages.append(page_text)
        
        return menu_text + "\n\n" + "\n---\n".join(content_pages)
    
    def _extract_text_from_content(self, content_data: Dict[str, Any]) -> str:
        """Extract text from content data"""
        # Similar to SMS format
        text_parts = []
        
        def extract_recursive(obj):
            if isinstance(obj, str):
                text_parts.append(obj)
            elif isinstance(obj, dict):
                for value in obj.values():
                    extract_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_recursive(item)
        
        extract_recursive(content_data)
        return " ".join(text_parts)
    
    def _split_into_chunks(self, text: str, chunk_size: int) -> List[str]:
        """Split text into USSD-friendly chunks"""
        words = text.split()
        chunks = []
        current_chunk = ""
        
        for word in words:
            if len(current_chunk + " " + word) <= chunk_size:
                if current_chunk:
                    current_chunk += " "
                current_chunk += word
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = word
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks


class OfflinePackExportFormat(ExportFormat):
    """Export format for offline lesson packs"""
    
    def format_content(self, content_items: List[ContentItem]) -> bytes:
        """Create downloadable offline pack"""
        # Create ZIP file in memory
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add metadata file
            metadata = {
                'pack_created': datetime.now().isoformat(),
                'content_count': len(content_items),
                'subjects': list(set(item.metadata.subject for item in content_items)),
                'grades': list(set(str(item.metadata.grade) for item in content_items))
            }
            zip_file.writestr('pack_info.json', json.dumps(metadata, indent=2))
            
            # Add each content item
            for item in content_items:
                filename = f"{item.metadata.content_id}.json"
                content_data = {
                    'metadata': item.metadata.to_dict(),
                    'content': item.content_data
                }
                zip_file.writestr(filename, json.dumps(content_data, indent=2))
            
            # Add index file
            index = {
                'contents': [
                    {
                        'id': item.metadata.content_id,
                        'title': item.metadata.title,
                        'type': item.metadata.content_type.value,
                        'subject': item.metadata.subject,
                        'grade': item.metadata.grade,
                        'topic': item.metadata.topic
                    }
                    for item in content_items
                ]
            }
            zip_file.writestr('index.json', json.dumps(index, indent=2))
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue()


class ContentExporter:
    """Content exporter supporting multiple formats"""
    
    def __init__(self, content_library: ContentLibrary):
        """
        Initialize content exporter
        
        Args:
            content_library: Content library to export from
        """
        self.content_library = content_library
        self.formats = {
            'sms': SMSExportFormat(),
            'ussd': USSDExportFormat(),
            'offline_pack': OfflinePackExportFormat(),
            'json': lambda items: json.dumps([asdict(item.metadata) for item in items], indent=2)
        }
    
    def export_content(self,
                      content_ids: List[str],
                      format_type: str,
                      output_path: Optional[Union[str, Path]] = None) -> Union[str, bytes]:
        """
        Export content in specified format
        
        Args:
            content_ids: List of content IDs to export
            format_type: Export format type
            output_path: Optional path to save exported content
            
        Returns:
            Exported content as string or bytes
        """
        if format_type not in self.formats:
            raise ValueError(f"Unsupported export format: {format_type}")
        
        # Get content items
        content_items = []
        for content_id in content_ids:
            item = self.content_library.get_content(content_id)
            if item:
                content_items.append(item)
            else:
                logger.warning(f"Content not found: {content_id}")
        
        if not content_items:
            raise ValueError("No content items found for export")
        
        # Format content
        formatter = self.formats[format_type]
        if callable(formatter):
            exported_content = formatter(content_items)
        else:
            exported_content = formatter.format_content(content_items)
        
        # Save to file if path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if isinstance(exported_content, bytes):
                output_path.write_bytes(exported_content)
            else:
                output_path.write_text(exported_content, encoding='utf-8')
            
            logger.info(f"Content exported to {output_path}")
        
        return exported_content
    
    def export_by_criteria(self,
                          format_type: str,
                          subject: Optional[str] = None,
                          grade: Optional[Union[int, str]] = None,
                          topic: Optional[str] = None,
                          content_type: Optional[ContentType] = None,
                          limit: Optional[int] = None,
                          output_path: Optional[Union[str, Path]] = None) -> Union[str, bytes]:
        """
        Export content matching criteria
        
        Args:
            format_type: Export format type
            subject: Subject filter
            grade: Grade filter
            topic: Topic filter
            content_type: Content type filter
            limit: Maximum number of items to export
            output_path: Optional path to save exported content
            
        Returns:
            Exported content
        """
        # Search for content
        content_items = self.content_library.search_content(
            subject=subject,
            grade=grade,
            topic=topic,
            content_type=content_type,
            limit=limit
        )
        
        if not content_items:
            raise ValueError("No content found matching criteria")
        
        # Get content IDs and export
        content_ids = [item.metadata.content_id for item in content_items]
        return self.export_content(content_ids, format_type, output_path)