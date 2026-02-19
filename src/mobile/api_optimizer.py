"""
Mobile API Optimizer for EduAGI.

Optimizes API responses for mobile devices with limited bandwidth and resources.
Includes compression, payload minimization, pagination, and bandwidth-aware responses.
"""

import gzip
import json
import time
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import brotli
import hashlib


@dataclass
class MobileRequest:
    """Represents a mobile API request with optimization hints."""
    fields: Optional[List[str]] = None
    compression: str = "gzip"  # gzip, brotli, none
    network_type: str = "4g"  # 2g, 3g, 4g, wifi
    battery_level: Optional[int] = None
    screen_size: str = "mobile"  # mobile, tablet, desktop
    offline_capable: bool = True
    lazy_load: bool = True


@dataclass  
class PaginationCursor:
    """Cursor-based pagination for mobile APIs."""
    cursor: str
    has_next: bool
    has_prev: bool
    total_estimate: Optional[int] = None
    page_size: int = 20


@dataclass
class BatchRequest:
    """Represents a batched API request."""
    requests: List[Dict[str, Any]]
    request_id: str
    timestamp: float


class MobileAPIOptimizer:
    """
    Optimizes API responses for mobile devices.
    
    Features:
    - Response compression (gzip/brotli)
    - Payload minimization 
    - Cursor-based pagination
    - Bandwidth-aware responses
    - Request batching
    - Cache optimization
    """

    def __init__(self):
        self.compression_threshold = 1024  # bytes
        self.network_profiles = {
            "2g": {"max_payload": 10240, "quality": "low"},    # 10KB
            "3g": {"max_payload": 51200, "quality": "medium"}, # 50KB  
            "4g": {"max_payload": 204800, "quality": "high"},  # 200KB
            "wifi": {"max_payload": 1048576, "quality": "high"} # 1MB
        }
        self.batch_requests = {}
        self.response_cache = {}

    def optimize_response(self, data: Dict[str, Any], request: MobileRequest) -> bytes:
        """
        Optimize API response for mobile consumption.
        
        Args:
            data: Raw response data
            request: Mobile request with optimization hints
            
        Returns:
            Optimized and compressed response bytes
        """
        # 1. Minimize payload based on requested fields
        if request.fields:
            data = self._filter_fields(data, request.fields)
            
        # 2. Apply network-aware optimizations
        data = self._apply_network_optimization(data, request.network_type)
        
        # 3. Add lazy loading hints
        if request.lazy_load:
            data = self._add_lazy_loading_hints(data)
            
        # 4. Apply battery-aware optimizations
        if request.battery_level and request.battery_level < 20:
            data = self._apply_battery_optimization(data)
            
        # 5. Serialize to JSON
        json_data = json.dumps(data, separators=(',', ':')).encode('utf-8')
        
        # 6. Apply compression
        return self._compress_response(json_data, request.compression)

    def _filter_fields(self, data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """Filter response to only include requested fields."""
        if isinstance(data, dict):
            filtered = {}
            for field in fields:
                if '.' in field:  # Nested field like 'user.name'
                    parts = field.split('.')
                    if parts[0] in data:
                        if parts[0] not in filtered:
                            filtered[parts[0]] = {}
                        if isinstance(data[parts[0]], dict) and parts[1] in data[parts[0]]:
                            filtered[parts[0]][parts[1]] = data[parts[0]][parts[1]]
                else:
                    if field in data:
                        filtered[field] = data[field]
            return filtered
        return data

    def _apply_network_optimization(self, data: Dict[str, Any], network_type: str) -> Dict[str, Any]:
        """Apply network-specific optimizations."""
        profile = self.network_profiles.get(network_type, self.network_profiles["4g"])
        
        # Adjust image quality/resolution hints
        if "images" in data:
            quality = profile["quality"] 
            if isinstance(data["images"], list):
                for img in data["images"]:
                    if isinstance(img, dict):
                        img["quality_hint"] = quality
                        if quality == "low":
                            img["max_width"] = 320
                        elif quality == "medium":
                            img["max_width"] = 640
                        else:
                            img["max_width"] = 1024

        # Limit text content for very slow networks
        if network_type == "2g" and "content" in data:
            if isinstance(data["content"], str) and len(data["content"]) > 500:
                data["content"] = data["content"][:500] + "..."
                data["truncated"] = True
                
        return data

    def _add_lazy_loading_hints(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add lazy loading hints for mobile clients."""
        # Mark heavy content for lazy loading
        if "lessons" in data and isinstance(data["lessons"], list):
            for lesson in data["lessons"]:
                if isinstance(lesson, dict):
                    if "video_url" in lesson:
                        lesson["lazy_load"] = True
                    if "attachments" in lesson:
                        lesson["attachments_lazy"] = True
                        
        # Add pagination hints
        data["_mobile_hints"] = {
            "lazy_load_enabled": True,
            "preload_next": False,
            "cache_duration": 300  # 5 minutes
        }
        
        return data

    def _apply_battery_optimization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize for low battery scenarios."""
        # Disable animations and heavy processing hints
        data["_mobile_hints"] = data.get("_mobile_hints", {})
        data["_mobile_hints"].update({
            "disable_animations": True,
            "reduce_polling": True,
            "minimal_ui": True
        })
        
        # Remove non-essential data
        if "analytics" in data:
            del data["analytics"]
        if "debug_info" in data:
            del data["debug_info"]
            
        return data

    def _compress_response(self, data: bytes, compression: str) -> bytes:
        """Compress response based on compression type."""
        if len(data) < self.compression_threshold:
            return data
            
        if compression == "gzip":
            return gzip.compress(data, compresslevel=6)
        elif compression == "brotli":
            return brotli.compress(data, quality=6)
        else:
            return data

    def create_pagination_cursor(self, items: List[Any], page_size: int = 20, 
                               current_offset: int = 0, total_count: Optional[int] = None) -> PaginationCursor:
        """Create cursor-based pagination for mobile."""
        # Create cursor from current position + timestamp
        cursor_data = f"{current_offset}_{int(time.time())}"
        cursor = hashlib.md5(cursor_data.encode()).hexdigest()[:16]
        
        has_next = len(items) >= page_size
        has_prev = current_offset > 0
        
        return PaginationCursor(
            cursor=cursor,
            has_next=has_next,
            has_prev=has_prev,
            total_estimate=total_count,
            page_size=page_size
        )

    def batch_requests(self, requests: List[Dict[str, Any]], timeout: int = 30) -> str:
        """
        Batch multiple API requests into a single request.
        
        Args:
            requests: List of API requests to batch
            timeout: Batch timeout in seconds
            
        Returns:
            Batch request ID
        """
        batch_id = hashlib.md5(f"{time.time()}_{len(requests)}".encode()).hexdigest()[:12]
        
        batch_request = BatchRequest(
            requests=requests,
            request_id=batch_id,
            timestamp=time.time()
        )
        
        self.batch_requests[batch_id] = batch_request
        return batch_id

    def get_batched_response(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get response for a batched request."""
        if batch_id not in self.batch_requests:
            return None
            
        batch = self.batch_requests[batch_id]
        
        # Simulate processing batched requests
        responses = []
        for req in batch.requests:
            # This would normally call the actual API endpoints
            responses.append({
                "request_id": req.get("id"),
                "status": "success",
                "data": {},  # Actual response data
                "processed_at": datetime.utcnow().isoformat()
            })
            
        # Clean up
        del self.batch_requests[batch_id]
        
        return {
            "batch_id": batch_id,
            "responses": responses,
            "processed_at": datetime.utcnow().isoformat()
        }

    def get_cache_headers(self, resource_type: str, user_id: Optional[str] = None) -> Dict[str, str]:
        """
        Generate appropriate cache headers for mobile apps.
        
        Args:
            resource_type: Type of resource (user, lessons, progress, etc.)
            user_id: User ID for user-specific caching
            
        Returns:
            Dict of HTTP cache headers
        """
        cache_profiles = {
            "static": {
                "Cache-Control": "public, max-age=86400, s-maxage=86400",  # 1 day
                "ETag": f'"{resource_type}-{int(time.time() // 3600)}"'
            },
            "user": {
                "Cache-Control": "private, max-age=300, must-revalidate",  # 5 minutes
                "ETag": f'"{user_id}-{resource_type}-{int(time.time() // 60)}"'
            },
            "dynamic": {
                "Cache-Control": "private, no-cache, must-revalidate",
                "ETag": f'"{resource_type}-{int(time.time())}"'
            },
            "lessons": {
                "Cache-Control": "public, max-age=3600, s-maxage=7200",  # 1-2 hours
                "ETag": f'"{resource_type}-{int(time.time() // 1800)}"'  # 30 min buckets
            }
        }
        
        profile = cache_profiles.get(resource_type, cache_profiles["dynamic"])
        
        # Add mobile-specific headers
        profile.update({
            "X-Mobile-Cache": "enabled",
            "X-Offline-TTL": "300",  # 5 minutes offline TTL
            "Vary": "Accept-Encoding, User-Agent"
        })
        
        return profile

    def cleanup_expired_batches(self, max_age: int = 300):
        """Clean up expired batch requests."""
        current_time = time.time()
        expired_batches = [
            batch_id for batch_id, batch in self.batch_requests.items()
            if current_time - batch.timestamp > max_age
        ]
        
        for batch_id in expired_batches:
            del self.batch_requests[batch_id]