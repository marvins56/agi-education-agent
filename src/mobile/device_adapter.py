"""
Device Adapter for EduAGI Mobile.

Adapts the user experience based on device capabilities including screen size,
battery level, network quality, storage, and input methods for optimal mobile experience.
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re


class DeviceType(Enum):
    MOBILE = "mobile"
    TABLET = "tablet"
    DESKTOP = "desktop"
    UNKNOWN = "unknown"


class NetworkQuality(Enum):
    OFFLINE = "offline"
    SLOW_2G = "slow-2g"
    SLOW_3G = "slow-3g"
    FAST_3G = "fast-3g"
    FAST_4G = "fast-4g"
    WIFI = "wifi"
    UNKNOWN = "unknown"


class InputMethod(Enum):
    TOUCH = "touch"
    MOUSE = "mouse"
    KEYBOARD = "keyboard"
    HYBRID = "hybrid"


@dataclass
class DeviceCapabilities:
    """Device capabilities and constraints."""
    # Screen properties
    screen_width: int = 0
    screen_height: int = 0
    device_pixel_ratio: float = 1.0
    orientation: str = "portrait"  # portrait, landscape
    
    # Performance indicators
    battery_level: Optional[int] = None
    battery_charging: Optional[bool] = None
    memory_gb: Optional[float] = None
    cpu_cores: Optional[int] = None
    
    # Network capabilities
    network_type: NetworkQuality = NetworkQuality.UNKNOWN
    connection_speed: Optional[float] = None  # Mbps
    data_saver_enabled: bool = False
    
    # Storage
    storage_quota_mb: Optional[float] = None
    storage_used_mb: Optional[float] = None
    
    # Input/Output capabilities
    has_touch: bool = False
    has_keyboard: bool = False
    has_mouse: bool = False
    has_camera: bool = False
    has_microphone: bool = False
    has_speakers: bool = True
    has_vibration: bool = False
    
    # Software capabilities
    supports_webgl: bool = False
    supports_webrtc: bool = False
    supports_service_worker: bool = False
    supports_push_notifications: bool = False
    
    # Browser/OS info
    user_agent: str = ""
    platform: str = ""
    browser_name: str = ""
    os_name: str = ""
    device_model: str = ""
    
    # Accessibility
    prefers_reduced_motion: bool = False
    high_contrast_mode: bool = False
    font_scale: float = 1.0


@dataclass
class AdaptationSettings:
    """Settings for adapting the experience."""
    # UI adaptations
    layout_density: str = "normal"  # compact, normal, spacious
    font_size: str = "normal"  # small, normal, large
    button_size: str = "normal"  # small, normal, large
    animation_level: str = "normal"  # none, reduced, normal, enhanced
    
    # Content adaptations
    image_quality: str = "auto"  # low, medium, high, auto
    video_quality: str = "auto"  # 240p, 360p, 480p, 720p, auto
    lazy_loading: bool = True
    content_compression: bool = True
    
    # Feature toggles
    enable_offline_mode: bool = True
    enable_notifications: bool = True
    enable_background_sync: bool = True
    enable_voice_features: bool = True
    
    # Performance settings
    max_concurrent_requests: int = 4
    cache_size_mb: int = 50
    prefetch_enabled: bool = True
    
    # Accessibility
    keyboard_navigation: bool = False
    screen_reader_optimized: bool = False


class DeviceAdapter:
    """
    Adapts EduAGI experience based on device capabilities and constraints.
    
    Features:
    - Screen size detection and layout adaptation
    - Battery level awareness
    - Network quality detection and optimization
    - Storage availability management
    - Input method detection
    - Camera/microphone capability detection
    - Accessibility adaptations
    """

    def __init__(self):
        self.device_profiles = {
            # Low-end mobile devices (common in East Africa)
            "low_end_mobile": {
                "screen_width_max": 400,
                "memory_max_gb": 2,
                "cpu_cores_max": 4,
                "adaptations": {
                    "layout_density": "compact",
                    "animation_level": "reduced",
                    "image_quality": "low",
                    "max_concurrent_requests": 2,
                    "cache_size_mb": 25
                }
            },
            # Mid-range mobile devices
            "mid_range_mobile": {
                "screen_width_max": 500,
                "memory_max_gb": 4,
                "cpu_cores_max": 8,
                "adaptations": {
                    "layout_density": "normal",
                    "animation_level": "normal",
                    "image_quality": "medium",
                    "max_concurrent_requests": 3,
                    "cache_size_mb": 40
                }
            },
            # High-end mobile and tablets
            "high_end_mobile": {
                "screen_width_max": 1200,
                "memory_max_gb": 8,
                "adaptations": {
                    "layout_density": "spacious",
                    "animation_level": "enhanced",
                    "image_quality": "high",
                    "max_concurrent_requests": 6,
                    "cache_size_mb": 100
                }
            }
        }
        
        self.network_profiles = {
            NetworkQuality.SLOW_2G: {
                "image_quality": "low",
                "video_quality": "240p",
                "lazy_loading": True,
                "prefetch_enabled": False,
                "max_concurrent_requests": 1
            },
            NetworkQuality.SLOW_3G: {
                "image_quality": "low",
                "video_quality": "360p", 
                "lazy_loading": True,
                "prefetch_enabled": False,
                "max_concurrent_requests": 2
            },
            NetworkQuality.FAST_3G: {
                "image_quality": "medium",
                "video_quality": "480p",
                "lazy_loading": True,
                "prefetch_enabled": True,
                "max_concurrent_requests": 3
            },
            NetworkQuality.FAST_4G: {
                "image_quality": "high",
                "video_quality": "720p",
                "lazy_loading": False,
                "prefetch_enabled": True,
                "max_concurrent_requests": 4
            },
            NetworkQuality.WIFI: {
                "image_quality": "high",
                "video_quality": "auto",
                "lazy_loading": False, 
                "prefetch_enabled": True,
                "max_concurrent_requests": 6
            }
        }

    def detect_device_capabilities(self, request_headers: Dict[str, str], 
                                 client_hints: Optional[Dict[str, Any]] = None) -> DeviceCapabilities:
        """
        Detect device capabilities from HTTP headers and client hints.
        
        Args:
            request_headers: HTTP request headers
            client_hints: Client hints data (if available)
            
        Returns:
            DeviceCapabilities object
        """
        caps = DeviceCapabilities()
        
        # Parse User-Agent
        user_agent = request_headers.get('user-agent', '').lower()
        caps.user_agent = user_agent
        caps.browser_name, caps.os_name, caps.device_model = self._parse_user_agent(user_agent)
        
        # Screen size from client hints or viewport
        if client_hints:
            caps.screen_width = client_hints.get('viewport-width', 0)
            caps.screen_height = client_hints.get('viewport-height', 0)
            caps.device_pixel_ratio = client_hints.get('dpr', 1.0)
            caps.memory_gb = client_hints.get('device-memory', None)
        
        # Network information
        connection_type = request_headers.get('connection-type', '').lower()
        effective_type = request_headers.get('ect', '').lower()  # Effective Connection Type
        
        if 'wifi' in connection_type:
            caps.network_type = NetworkQuality.WIFI
        elif effective_type:
            network_mapping = {
                'slow-2g': NetworkQuality.SLOW_2G,
                '2g': NetworkQuality.SLOW_3G,
                '3g': NetworkQuality.FAST_3G,
                '4g': NetworkQuality.FAST_4G
            }
            caps.network_type = network_mapping.get(effective_type, NetworkQuality.UNKNOWN)
        
        # Data saver
        caps.data_saver_enabled = request_headers.get('save-data', '').lower() == 'on'
        
        # Touch capabilities
        caps.has_touch = 'mobile' in user_agent or 'touch' in user_agent
        
        # Basic feature detection from UA
        caps.has_camera = 'mobile' in user_agent or 'tablet' in user_agent
        caps.has_microphone = caps.has_camera
        caps.has_vibration = 'mobile' in user_agent
        
        # Accessibility preferences
        caps.prefers_reduced_motion = request_headers.get('prefers-reduced-motion') == 'reduce'
        caps.high_contrast_mode = request_headers.get('prefers-contrast') == 'high'
        
        return caps

    def _parse_user_agent(self, user_agent: str) -> Tuple[str, str, str]:
        """
        Parse browser, OS, and device from User-Agent string.
        
        Returns:
            Tuple of (browser_name, os_name, device_model)
        """
        browser_name = "unknown"
        os_name = "unknown" 
        device_model = "unknown"
        
        # Browser detection
        if 'chrome' in user_agent and 'edge' not in user_agent:
            browser_name = "chrome"
        elif 'firefox' in user_agent:
            browser_name = "firefox"
        elif 'safari' in user_agent and 'chrome' not in user_agent:
            browser_name = "safari"
        elif 'edge' in user_agent:
            browser_name = "edge"
        elif 'opera' in user_agent:
            browser_name = "opera"
            
        # OS detection
        if 'android' in user_agent:
            os_name = "android"
        elif 'iphone' in user_agent or 'ipad' in user_agent:
            os_name = "ios"
        elif 'windows' in user_agent:
            os_name = "windows"
        elif 'macintosh' in user_agent or 'mac os' in user_agent:
            os_name = "macos"
        elif 'linux' in user_agent:
            os_name = "linux"
            
        # Basic device model extraction
        device_patterns = [
            r'iphone[^;]*',
            r'ipad[^;]*', 
            r'samsung[^;]*',
            r'huawei[^;]*',
            r'xiaomi[^;]*',
            r'oppo[^;]*',
            r'vivo[^;]*',
            r'tecno[^;)*',
            r'infinix[^;]*'
        ]
        
        for pattern in device_patterns:
            match = re.search(pattern, user_agent)
            if match:
                device_model = match.group(0).strip()
                break
        
        return browser_name, os_name, device_model

    def determine_device_type(self, capabilities: DeviceCapabilities) -> DeviceType:
        """Determine device type based on capabilities."""
        if capabilities.screen_width == 0:
            return DeviceType.UNKNOWN
            
        if capabilities.screen_width < 768:
            return DeviceType.MOBILE
        elif capabilities.screen_width < 1024:
            return DeviceType.TABLET
        else:
            return DeviceType.DESKTOP

    def generate_adaptations(self, capabilities: DeviceCapabilities) -> AdaptationSettings:
        """
        Generate optimal adaptation settings for device.
        
        Args:
            capabilities: Device capabilities
            
        Returns:
            AdaptationSettings with optimized configuration
        """
        settings = AdaptationSettings()
        
        # Apply device profile adaptations
        device_profile = self._get_device_profile(capabilities)
        if device_profile and "adaptations" in device_profile:
            adaptations = device_profile["adaptations"]
            for key, value in adaptations.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
        
        # Apply network-specific adaptations
        network_profile = self.network_profiles.get(capabilities.network_type, {})
        for key, value in network_profile.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        
        # Battery-aware adaptations
        if capabilities.battery_level is not None and capabilities.battery_level < 20:
            settings.animation_level = "none"
            settings.image_quality = "low" 
            settings.prefetch_enabled = False
            settings.max_concurrent_requests = 2
            settings.enable_background_sync = False
        
        # Data saver adaptations
        if capabilities.data_saver_enabled:
            settings.image_quality = "low"
            settings.video_quality = "240p"
            settings.lazy_loading = True
            settings.content_compression = True
            settings.prefetch_enabled = False
        
        # Accessibility adaptations
        if capabilities.prefers_reduced_motion:
            settings.animation_level = "none"
            
        if capabilities.high_contrast_mode:
            settings.font_size = "large"
            settings.button_size = "large"
        
        # Touch-based adaptations
        if capabilities.has_touch and not capabilities.has_mouse:
            settings.button_size = "large"
            settings.layout_density = "spacious"
        
        # Input method adaptations
        input_method = self._detect_primary_input_method(capabilities)
        if input_method == InputMethod.TOUCH:
            settings.keyboard_navigation = False
        elif input_method == InputMethod.KEYBOARD:
            settings.keyboard_navigation = True
            settings.screen_reader_optimized = True
        
        return settings

    def _get_device_profile(self, capabilities: DeviceCapabilities) -> Optional[Dict[str, Any]]:
        """Get the best matching device profile."""
        for profile_name, profile in self.device_profiles.items():
            if (capabilities.screen_width <= profile.get("screen_width_max", float('inf')) and
                (capabilities.memory_gb is None or 
                 capabilities.memory_gb <= profile.get("memory_max_gb", float('inf'))) and
                (capabilities.cpu_cores is None or
                 capabilities.cpu_cores <= profile.get("cpu_cores_max", float('inf')))):
                return profile
        return None

    def _detect_primary_input_method(self, capabilities: DeviceCapabilities) -> InputMethod:
        """Detect the primary input method for the device."""
        if capabilities.has_touch and not capabilities.has_mouse:
            return InputMethod.TOUCH
        elif capabilities.has_mouse and not capabilities.has_touch:
            return InputMethod.MOUSE
        elif capabilities.has_keyboard and not capabilities.has_touch:
            return InputMethod.KEYBOARD
        else:
            return InputMethod.HYBRID

    def get_layout_hints(self, capabilities: DeviceCapabilities, 
                        settings: AdaptationSettings) -> Dict[str, Any]:
        """
        Generate layout hints for the UI framework.
        
        Args:
            capabilities: Device capabilities
            settings: Adaptation settings
            
        Returns:
            Layout hints for responsive design
        """
        device_type = self.determine_device_type(capabilities)
        
        hints = {
            "device_type": device_type.value,
            "screen_size": {
                "width": capabilities.screen_width,
                "height": capabilities.screen_height,
                "pixel_ratio": capabilities.device_pixel_ratio
            },
            "layout": {
                "density": settings.layout_density,
                "orientation": capabilities.orientation,
                "grid_columns": self._get_grid_columns(device_type),
                "sidebar_collapsed": device_type == DeviceType.MOBILE
            },
            "typography": {
                "font_size": settings.font_size,
                "line_height": 1.6 if settings.font_size == "large" else 1.4,
                "scale_factor": capabilities.font_scale
            },
            "controls": {
                "button_size": settings.button_size,
                "touch_targets_min": 44 if capabilities.has_touch else 24,
                "hover_effects": capabilities.has_mouse
            },
            "animations": {
                "level": settings.animation_level,
                "duration_scale": 0.5 if settings.animation_level == "reduced" else 1.0,
                "enabled": settings.animation_level != "none"
            }
        }
        
        return hints

    def _get_grid_columns(self, device_type: DeviceType) -> int:
        """Get appropriate grid column count for device type."""
        if device_type == DeviceType.MOBILE:
            return 1
        elif device_type == DeviceType.TABLET:
            return 2
        else:
            return 3

    def get_performance_budget(self, capabilities: DeviceCapabilities,
                             settings: AdaptationSettings) -> Dict[str, Any]:
        """
        Calculate performance budgets for the device.
        
        Returns:
            Performance limits and targets
        """
        # Base budget for modern devices
        budget = {
            "max_bundle_size_kb": 300,
            "max_image_size_kb": 200,
            "max_fonts_kb": 100,
            "max_render_time_ms": 16,  # 60fps
            "max_load_time_ms": 3000
        }
        
        # Adjust for device capabilities
        if capabilities.memory_gb and capabilities.memory_gb < 2:
            budget["max_bundle_size_kb"] = 150
            budget["max_image_size_kb"] = 100
            budget["max_fonts_kb"] = 50
            
        if capabilities.network_type in [NetworkQuality.SLOW_2G, NetworkQuality.SLOW_3G]:
            budget["max_bundle_size_kb"] //= 2
            budget["max_image_size_kb"] //= 2
            budget["max_load_time_ms"] = 10000
            
        if capabilities.battery_level and capabilities.battery_level < 20:
            budget["max_render_time_ms"] = 33  # 30fps to save battery
            
        return budget

    def should_enable_feature(self, feature_name: str, capabilities: DeviceCapabilities,
                            settings: AdaptationSettings) -> bool:
        """
        Determine if a feature should be enabled based on device capabilities.
        
        Args:
            feature_name: Name of the feature to check
            capabilities: Device capabilities
            settings: Current adaptation settings
            
        Returns:
            bool: Whether the feature should be enabled
        """
        feature_requirements = {
            "voice_input": capabilities.has_microphone and capabilities.supports_webrtc,
            "camera_upload": capabilities.has_camera,
            "push_notifications": capabilities.supports_push_notifications,
            "offline_mode": capabilities.supports_service_worker,
            "background_sync": capabilities.supports_service_worker and settings.enable_background_sync,
            "vibration_feedback": capabilities.has_vibration,
            "high_quality_images": capabilities.network_type in [NetworkQuality.FAST_4G, NetworkQuality.WIFI],
            "video_lessons": capabilities.network_type != NetworkQuality.SLOW_2G,
            "real_time_features": capabilities.network_type in [NetworkQuality.FAST_4G, NetworkQuality.WIFI],
            "advanced_animations": settings.animation_level in ["normal", "enhanced"],
            "predictive_prefetch": settings.prefetch_enabled and capabilities.network_type != NetworkQuality.SLOW_2G
        }
        
        return feature_requirements.get(feature_name, True)

    def get_content_optimization_hints(self, capabilities: DeviceCapabilities,
                                     settings: AdaptationSettings) -> Dict[str, Any]:
        """Get hints for optimizing content delivery."""
        return {
            "image_format": "webp" if capabilities.browser_name in ["chrome", "firefox"] else "jpeg",
            "image_quality": settings.image_quality,
            "lazy_load_threshold": 200 if settings.lazy_loading else 0,
            "compression_enabled": settings.content_compression,
            "cdn_region": "africa-east",  # Optimize for East African users
            "cache_duration": {
                "static": 86400,  # 1 day
                "dynamic": 300 if capabilities.network_type == NetworkQuality.WIFI else 900,  # 5-15 min
                "user_content": 60  # 1 minute
            }
        }