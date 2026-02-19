"""
Mobile API optimization package for EduAGI.

This package provides mobile-specific optimizations including:
- API response compression and payload minimization
- Offline synchronization with conflict resolution
- Progressive Web App (PWA) support
- Device-specific adaptations for optimal mobile experience

Designed specifically for East African students accessing EduAGI via mobile devices.
"""

from .api_optimizer import MobileAPIOptimizer
from .offline_sync import OfflineSyncManager
from .pwa import PWAManager
from .device_adapter import DeviceAdapter

__all__ = [
    "MobileAPIOptimizer",
    "OfflineSyncManager", 
    "PWAManager",
    "DeviceAdapter"
]

__version__ = "1.0.0"