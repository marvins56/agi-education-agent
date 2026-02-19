"""
Tests for the mobile package.

Tests mobile API optimization, offline synchronization, PWA features, 
and device adaptation functionality.
"""

import pytest
import json
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile
import os

# Import the mobile package classes
import sys
sys.path.append(str(Path(__file__).parent.parent / "src"))

from mobile.api_optimizer import (
    MobileAPIOptimizer, MobileRequest, PaginationCursor, BatchRequest
)
from mobile.offline_sync import (
    OfflineSyncManager, SyncEntity, SyncStatus, SyncPriority, ConflictResolution
)
from mobile.pwa import (
    PWAManager, PWAConfig, PushSubscription, ServiceWorkerUpdate
)
from mobile.device_adapter import (
    DeviceAdapter, DeviceCapabilities, AdaptationSettings, 
    DeviceType, NetworkQuality, InputMethod
)


class TestMobileAPIOptimizer:
    """Test the MobileAPIOptimizer class."""

    def setup_method(self):
        self.optimizer = MobileAPIOptimizer()

    def test_optimize_response_basic(self):
        """Test basic response optimization."""
        data = {"user": {"name": "John", "email": "john@test.com"}, "lessons": [1, 2, 3]}
        request = MobileRequest(
            fields=["user.name", "lessons"],
            compression="gzip",
            network_type="3g"
        )
        
        result = self.optimizer.optimize_response(data, request)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_field_filtering(self):
        """Test payload minimization by field filtering."""
        data = {
            "user": {"name": "John", "email": "john@test.com", "secret": "hidden"},
            "lessons": [1, 2, 3],
            "analytics": {"views": 100}
        }
        
        filtered = self.optimizer._filter_fields(data, ["user.name", "lessons"])
        
        assert "user" in filtered
        assert "name" in filtered["user"]
        assert "email" not in filtered["user"]
        assert "lessons" in filtered
        assert "analytics" not in filtered

    def test_network_optimization(self):
        """Test network-specific optimizations."""
        data = {
            "images": [{"url": "test.jpg"}, {"url": "test2.jpg"}],
            "content": "A" * 1000  # Long content
        }
        
        # Test 2G optimization
        optimized = self.optimizer._apply_network_optimization(data, "2g")
        assert "truncated" in optimized
        assert len(optimized["content"]) <= 503  # 500 + "..."
        
        for img in optimized["images"]:
            assert img["quality_hint"] == "low"
            assert img["max_width"] == 320

    def test_battery_optimization(self):
        """Test battery-aware optimizations."""
        data = {
            "content": "test",
            "analytics": {"data": "removed"},
            "debug_info": {"logs": "removed"}
        }
        
        optimized = self.optimizer._apply_battery_optimization(data)
        
        assert "_mobile_hints" in optimized
        assert optimized["_mobile_hints"]["disable_animations"] is True
        assert "analytics" not in optimized
        assert "debug_info" not in optimized

    def test_pagination_cursor(self):
        """Test cursor-based pagination."""
        items = list(range(25))  # 25 items
        cursor = self.optimizer.create_pagination_cursor(items, page_size=20, current_offset=0)
        
        assert isinstance(cursor, PaginationCursor)
        assert cursor.has_next is True
        assert cursor.has_prev is False
        assert cursor.page_size == 20
        assert len(cursor.cursor) == 16  # MD5 hash truncated

    def test_request_batching(self):
        """Test request batching functionality."""
        requests = [
            {"id": "req1", "endpoint": "/api/user"},
            {"id": "req2", "endpoint": "/api/lessons"}
        ]
        
        batch_id = self.optimizer.batch_requests(requests)
        assert batch_id in self.optimizer.batch_requests
        
        response = self.optimizer.get_batched_response(batch_id)
        assert response is not None
        assert response["batch_id"] == batch_id
        assert len(response["responses"]) == 2

    def test_cache_headers(self):
        """Test cache header generation."""
        # Test static resource headers
        headers = self.optimizer.get_cache_headers("static")
        assert "Cache-Control" in headers
        assert "public" in headers["Cache-Control"]
        assert "ETag" in headers
        
        # Test user-specific headers
        headers = self.optimizer.get_cache_headers("user", "user123")
        assert "private" in headers["Cache-Control"]
        assert "user123" in headers["ETag"]


class TestOfflineSyncManager:
    """Test the OfflineSyncManager class."""

    def setup_method(self):
        # Use temporary database for testing
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_sync.db")
        self.sync_manager = OfflineSyncManager(storage_path=self.db_path, max_storage_mb=10)

    def teardown_method(self):
        """Clean up temporary files."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
        os.rmdir(self.temp_dir)

    @pytest.mark.asyncio
    async def test_add_entity(self):
        """Test adding entities to sync queue."""
        entity = SyncEntity(
            entity_id="test_entity_1",
            entity_type="user_progress",
            data={"progress": 75, "lesson_id": "lesson_1"},
            priority=SyncPriority.CRITICAL,
            last_modified=datetime.utcnow()
        )
        
        await self.sync_manager.add_entity(entity)
        
        assert "test_entity_1" in self.sync_manager.entity_states
        assert len(self.sync_manager.sync_queue[SyncPriority.CRITICAL]) == 1

    @pytest.mark.asyncio
    async def test_delta_changes(self):
        """Test getting delta changes since timestamp."""
        # Add some test entities
        base_time = datetime.utcnow()
        
        entity1 = SyncEntity(
            entity_id="entity_1",
            entity_type="lesson",
            data={"completed": True},
            priority=SyncPriority.HIGH,
            last_modified=base_time - timedelta(minutes=10)
        )
        
        entity2 = SyncEntity(
            entity_id="entity_2", 
            entity_type="lesson",
            data={"completed": False},
            priority=SyncPriority.HIGH,
            last_modified=base_time + timedelta(minutes=5)
        )
        
        await self.sync_manager.add_entity(entity1)
        await self.sync_manager.add_entity(entity2)
        
        # Get changes since base_time
        changes = await self.sync_manager.get_delta_changes("lesson", base_time)
        
        assert len(changes) == 1  # Only entity2 should be returned
        assert changes[0].entity_id == "entity_2"

    def test_merge_entity_data(self):
        """Test data merging for conflict resolution."""
        local_data = {
            "progress": 60,
            "scores": [80, 90],
            "notes": "Local notes",
            "completed_lessons": ["lesson1", "lesson2"]
        }
        
        remote_data = {
            "progress": 75,  # Higher progress (should win)
            "scores": [85, 95, 100],  # Additional scores
            "notes": "",  # Empty (local should win)
            "completed_lessons": ["lesson2", "lesson3"]  # Different lessons
        }
        
        merged = self.sync_manager._merge_entity_data(local_data, remote_data)
        
        assert merged["progress"] == 75  # Max value
        assert merged["notes"] == "Local notes"  # Non-empty local value
        assert set(merged["scores"]) == {80, 90, 85, 95, 100}  # Merged arrays
        assert set(merged["completed_lessons"]) == {"lesson1", "lesson2", "lesson3"}

    def test_sync_status_tracking(self):
        """Test sync status tracking by entity type."""
        # This would normally require database interaction
        # For now, test the method exists and returns correct structure
        status = self.sync_manager.get_sync_status_by_type("user_progress")
        
        assert isinstance(status, dict)
        for sync_status in SyncStatus:
            assert sync_status in status

    def test_storage_info(self):
        """Test storage quota and usage tracking."""
        info = self.sync_manager.get_storage_info()
        
        assert "current_size_bytes" in info
        assert "max_size_bytes" in info
        assert "usage_percent" in info
        assert "entities_count" in info


class TestPWAManager:
    """Test the PWAManager class."""

    def setup_method(self):
        config = PWAConfig(
            app_name="Test EduAGI",
            short_name="TestEdu",
            theme_color="#FF5722"
        )
        self.temp_dir = tempfile.mkdtemp()
        self.pwa_manager = PWAManager(config, static_path=self.temp_dir)

    def teardown_method(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_generate_manifest(self):
        """Test PWA manifest generation."""
        manifest = self.pwa_manager.generate_manifest()
        
        assert manifest["name"] == "Test EduAGI"
        assert manifest["short_name"] == "TestEdu"
        assert manifest["theme_color"] == "#FF5722"
        assert manifest["display"] == "standalone"
        assert len(manifest["icons"]) > 0
        assert len(manifest["shortcuts"]) == 3

    def test_generate_service_worker(self):
        """Test service worker code generation."""
        sw_code = self.pwa_manager.generate_service_worker()
        
        assert "EduAGI Service Worker" in sw_code
        assert "install" in sw_code
        assert "activate" in sw_code
        assert "fetch" in sw_code
        assert "push" in sw_code
        assert f"v{self.pwa_manager.sw_version}" in sw_code

    def test_push_subscription_management(self):
        """Test push notification subscription management."""
        subscription_data = {
            "endpoint": "https://fcm.googleapis.com/fcm/send/test123",
            "keys": {
                "p256dh": "test_p256dh_key",
                "auth": "test_auth_key"
            }
        }
        
        sub_id = self.pwa_manager.register_push_subscription(
            subscription_data, user_id="user123"
        )
        
        assert sub_id in self.pwa_manager.push_subscriptions
        assert self.pwa_manager.push_subscriptions[sub_id].user_id == "user123"
        
        # Test unregistration
        success = self.pwa_manager.unregister_push_subscription(sub_id)
        assert success is True
        assert self.pwa_manager.push_subscriptions[sub_id].active is False

    def test_install_prompt_tracking(self):
        """Test install prompt tracking."""
        # First prompt should be allowed
        should_show = self.pwa_manager.track_install_prompt("user123")
        assert should_show is True
        
        # Second prompt within 7 days should be blocked
        should_show = self.pwa_manager.track_install_prompt("user123")
        assert should_show is False

    def test_offline_page_generation(self):
        """Test offline fallback page generation."""
        offline_html = self.pwa_manager.generate_offline_page()
        
        assert "<!DOCTYPE html>" in offline_html
        assert "You're Offline" in offline_html
        assert self.pwa_manager.config.app_name in offline_html
        assert self.pwa_manager.config.theme_color in offline_html

    def test_pwa_install_criteria(self):
        """Test PWA installability criteria check."""
        criteria = self.pwa_manager.get_pwa_install_criteria()
        
        assert criteria["manifest_valid"] is True
        assert criteria["service_worker_registered"] is True
        assert criteria["installable"] is True
        assert len(criteria["criteria_met"]) > 0

    def test_subscription_stats(self):
        """Test push subscription statistics."""
        # Add some test subscriptions
        for i in range(3):
            sub_data = {
                "endpoint": f"https://test.com/endpoint{i}",
                "keys": {"p256dh": "key", "auth": "auth"}
            }
            self.pwa_manager.register_push_subscription(sub_data, user_id=f"user{i}")
        
        stats = self.pwa_manager.get_subscription_stats()
        
        assert stats["total_subscriptions"] == 3
        assert stats["active_subscriptions"] == 3
        assert stats["unique_users"] == 3


class TestDeviceAdapter:
    """Test the DeviceAdapter class."""

    def setup_method(self):
        self.adapter = DeviceAdapter()

    def test_detect_device_capabilities_mobile(self):
        """Test device capability detection for mobile."""
        headers = {
            "user-agent": "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 Chrome/91.0",
            "connection-type": "cellular",
            "ect": "3g",
            "save-data": "on"
        }
        
        client_hints = {
            "viewport-width": 375,
            "viewport-height": 812,
            "dpr": 2.0,
            "device-memory": 3
        }
        
        caps = self.adapter.detect_device_capabilities(headers, client_hints)
        
        assert caps.screen_width == 375
        assert caps.device_pixel_ratio == 2.0
        assert caps.network_type == NetworkQuality.FAST_3G
        assert caps.data_saver_enabled is True
        assert caps.has_touch is True
        assert caps.os_name == "android"
        assert caps.browser_name == "chrome"

    def test_device_type_detection(self):
        """Test device type classification."""
        # Mobile
        mobile_caps = DeviceCapabilities(screen_width=375)
        assert self.adapter.determine_device_type(mobile_caps) == DeviceType.MOBILE
        
        # Tablet  
        tablet_caps = DeviceCapabilities(screen_width=768)
        assert self.adapter.determine_device_type(tablet_caps) == DeviceType.TABLET
        
        # Desktop
        desktop_caps = DeviceCapabilities(screen_width=1200)
        assert self.adapter.determine_device_type(desktop_caps) == DeviceType.DESKTOP

    def test_generate_adaptations_low_end(self):
        """Test adaptation generation for low-end devices."""
        caps = DeviceCapabilities(
            screen_width=360,
            memory_gb=1.5,
            battery_level=15,
            network_type=NetworkQuality.SLOW_3G,
            data_saver_enabled=True
        )
        
        settings = self.adapter.generate_adaptations(caps)
        
        # Should apply low-end device profile
        assert settings.layout_density == "compact"
        assert settings.animation_level == "none"  # Due to low battery
        assert settings.image_quality == "low"
        assert settings.max_concurrent_requests <= 2
        assert settings.prefetch_enabled is False

    def test_generate_adaptations_high_end(self):
        """Test adaptation generation for high-end devices."""
        caps = DeviceCapabilities(
            screen_width=1024,
            memory_gb=8,
            battery_level=80,
            network_type=NetworkQuality.WIFI,
            data_saver_enabled=False
        )
        
        settings = self.adapter.generate_adaptations(caps)
        
        # Should apply high-end optimizations
        assert settings.layout_density == "spacious"
        assert settings.image_quality == "high"
        assert settings.max_concurrent_requests >= 4
        assert settings.prefetch_enabled is True

    def test_layout_hints_generation(self):
        """Test UI layout hints generation."""
        caps = DeviceCapabilities(
            screen_width=375,
            screen_height=812,
            has_touch=True,
            has_mouse=False
        )
        
        settings = AdaptationSettings(
            layout_density="normal",
            font_size="large"
        )
        
        hints = self.adapter.get_layout_hints(caps, settings)
        
        assert hints["device_type"] == "mobile"
        assert hints["layout"]["grid_columns"] == 1
        assert hints["layout"]["sidebar_collapsed"] is True
        assert hints["controls"]["touch_targets_min"] == 44
        assert hints["typography"]["font_size"] == "large"

    def test_performance_budget(self):
        """Test performance budget calculation."""
        # Low-end device
        low_end_caps = DeviceCapabilities(
            memory_gb=1,
            network_type=NetworkQuality.SLOW_2G
        )
        
        settings = AdaptationSettings()
        budget = self.adapter.get_performance_budget(low_end_caps, settings)
        
        # Should have restrictive budget
        assert budget["max_bundle_size_kb"] <= 150
        assert budget["max_image_size_kb"] <= 100
        assert budget["max_load_time_ms"] >= 5000

    def test_feature_enablement(self):
        """Test feature enablement based on capabilities."""
        # Device with microphone and WebRTC support
        caps = DeviceCapabilities(
            has_microphone=True,
            supports_webrtc=True,
            supports_push_notifications=True,
            network_type=NetworkQuality.FAST_4G
        )
        
        settings = AdaptationSettings()
        
        assert self.adapter.should_enable_feature("voice_input", caps, settings) is True
        assert self.adapter.should_enable_feature("push_notifications", caps, settings) is True
        assert self.adapter.should_enable_feature("high_quality_images", caps, settings) is True
        
        # Device without capabilities
        limited_caps = DeviceCapabilities(
            has_microphone=False,
            network_type=NetworkQuality.SLOW_2G
        )
        
        assert self.adapter.should_enable_feature("voice_input", limited_caps, settings) is False
        assert self.adapter.should_enable_feature("video_lessons", limited_caps, settings) is False

    def test_content_optimization_hints(self):
        """Test content optimization hints."""
        caps = DeviceCapabilities(
            browser_name="chrome",
            network_type=NetworkQuality.WIFI
        )
        
        settings = AdaptationSettings(
            image_quality="high",
            lazy_loading=False,
            content_compression=True
        )
        
        hints = self.adapter.get_content_optimization_hints(caps, settings)
        
        assert hints["image_format"] == "webp"
        assert hints["image_quality"] == "high"
        assert hints["lazy_load_threshold"] == 0  # Lazy loading disabled
        assert hints["compression_enabled"] is True
        assert hints["cdn_region"] == "africa-east"


# Integration tests
class TestMobilePackageIntegration:
    """Integration tests for the mobile package."""

    @pytest.mark.asyncio
    async def test_end_to_end_mobile_optimization(self):
        """Test end-to-end mobile optimization flow."""
        # 1. Detect device capabilities
        adapter = DeviceAdapter()
        headers = {
            "user-agent": "Mozilla/5.0 (Linux; Android 9; Tecno Camon 12) Chrome/91.0",
            "connection-type": "cellular",
            "ect": "3g"
        }
        
        caps = adapter.detect_device_capabilities(headers)
        settings = adapter.generate_adaptations(caps)
        
        # 2. Optimize API response based on capabilities
        optimizer = MobileAPIOptimizer()
        
        test_data = {
            "user": {"name": "Amara", "progress": 65},
            "lessons": [
                {"id": 1, "title": "Math Basics", "video_url": "video1.mp4"},
                {"id": 2, "title": "Science Intro", "video_url": "video2.mp4"}
            ],
            "images": [{"url": "lesson1.jpg"}, {"url": "lesson2.jpg"}]
        }
        
        mobile_request = MobileRequest(
            fields=["user.name", "user.progress", "lessons"],
            network_type=caps.network_type.value,
            lazy_load=True
        )
        
        optimized_response = optimizer.optimize_response(test_data, mobile_request)
        
        # Response should be optimized
        assert isinstance(optimized_response, bytes)
        assert len(optimized_response) > 0
        
        # 3. Test offline sync preparation
        sync_manager = OfflineSyncManager()
        
        sync_entity = SyncEntity(
            entity_id="user_progress_amara",
            entity_type="user_progress", 
            data={"progress": 65, "last_lesson": 1},
            priority=SyncPriority.CRITICAL,
            last_modified=datetime.utcnow()
        )
        
        await sync_manager.add_entity(sync_entity)
        
        # Entity should be queued for sync
        assert len(sync_manager.sync_queue[SyncPriority.CRITICAL]) == 1
        
        # 4. Test PWA configuration
        pwa_manager = PWAManager(PWAConfig())
        manifest = pwa_manager.generate_manifest()
        sw_code = pwa_manager.generate_service_worker()
        
        # PWA assets should be generated
        assert "name" in manifest
        assert "install" in sw_code
        
        print("✅ End-to-end mobile optimization test passed!")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])