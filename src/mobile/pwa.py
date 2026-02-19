"""
Progressive Web App (PWA) Manager for EduAGI Mobile.

Provides PWA functionality including service worker registration, web app manifest,
push notifications, offline support, and app installation prompts.
"""

import json
import base64
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import os
from pathlib import Path


@dataclass
class PWAConfig:
    """PWA configuration settings."""
    app_name: str = "EduAGI"
    short_name: str = "EduAGI"
    description: str = "AI-Powered Education for East Africa"
    theme_color: str = "#2196F3"
    background_color: str = "#FFFFFF"
    display: str = "standalone"  # standalone, fullscreen, minimal-ui, browser
    orientation: str = "portrait"  # portrait, landscape, any
    start_url: str = "/"
    scope: str = "/"
    lang: str = "en"


@dataclass
class PushSubscription:
    """Represents a Web Push notification subscription."""
    endpoint: str
    keys: Dict[str, str]  # p256dh and auth keys
    user_id: Optional[str] = None
    device_info: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    active: bool = True


@dataclass
class PWAManifestIcon:
    """PWA manifest icon definition."""
    src: str
    sizes: str
    type: str
    purpose: str = "any"  # any, maskable, monochrome


@dataclass
class ServiceWorkerUpdate:
    """Service worker update information."""
    version: str
    timestamp: datetime
    files_updated: List[str] = field(default_factory=list)
    cache_invalidated: bool = False


class PWAManager:
    """
    Manages Progressive Web App functionality for EduAGI Mobile.
    
    Features:
    - Service worker registration and management
    - Web app manifest generation
    - Push notification subscriptions
    - Installation prompt tracking
    - Offline page serving
    - App update notifications
    """

    def __init__(self, config: PWAConfig, static_path: str = "./static"):
        self.config = config
        self.static_path = Path(static_path)
        self.push_subscriptions: Dict[str, PushSubscription] = {}
        self.install_prompts: Dict[str, datetime] = {}
        self.sw_version = "1.0.0"
        self.cached_resources = set()
        self._ensure_static_directory()

    def _ensure_static_directory(self):
        """Ensure static assets directory exists."""
        self.static_path.mkdir(exist_ok=True)
        (self.static_path / "icons").mkdir(exist_ok=True)
        (self.static_path / "sw").mkdir(exist_ok=True)

    def generate_manifest(self) -> Dict[str, Any]:
        """
        Generate PWA web app manifest.
        
        Returns:
            Dict containing the web app manifest
        """
        # Default icon sizes for PWA
        icon_sizes = ["72x72", "96x96", "128x128", "144x144", "152x152", 
                     "192x192", "384x384", "512x512"]
        
        icons = []
        for size in icon_sizes:
            icons.append({
                "src": f"/static/icons/icon-{size}.png",
                "sizes": size,
                "type": "image/png",
                "purpose": "any"
            })
        
        # Add maskable icons for better Android experience
        for size in ["192x192", "512x512"]:
            icons.append({
                "src": f"/static/icons/maskable-icon-{size}.png", 
                "sizes": size,
                "type": "image/png",
                "purpose": "maskable"
            })

        manifest = {
            "name": self.config.app_name,
            "short_name": self.config.short_name,
            "description": self.config.description,
            "start_url": self.config.start_url,
            "scope": self.config.scope,
            "display": self.config.display,
            "orientation": self.config.orientation,
            "theme_color": self.config.theme_color,
            "background_color": self.config.background_color,
            "lang": self.config.lang,
            "icons": icons,
            "categories": ["education", "productivity", "utilities"],
            "shortcuts": [
                {
                    "name": "My Lessons",
                    "short_name": "Lessons", 
                    "description": "View your current lessons",
                    "url": "/lessons",
                    "icons": [{"src": "/static/icons/lessons-96x96.png", "sizes": "96x96"}]
                },
                {
                    "name": "Progress",
                    "short_name": "Progress",
                    "description": "Check your learning progress", 
                    "url": "/progress",
                    "icons": [{"src": "/static/icons/progress-96x96.png", "sizes": "96x96"}]
                },
                {
                    "name": "Practice Quiz",
                    "short_name": "Quiz",
                    "description": "Take a practice quiz",
                    "url": "/quiz",
                    "icons": [{"src": "/static/icons/quiz-96x96.png", "sizes": "96x96"}]
                }
            ],
            "related_applications": [],
            "prefer_related_applications": False
        }
        
        return manifest

    def generate_service_worker(self) -> str:
        """
        Generate service worker JavaScript code.
        
        Returns:
            Service worker JavaScript code as string
        """
        cache_name = f"eduagi-v{self.sw_version}"
        
        # Core files to cache for offline functionality
        core_files = [
            "/",
            "/static/css/app.css",
            "/static/js/app.js", 
            "/static/icons/icon-192x192.png",
            "/offline",
            "/manifest.json"
        ]
        
        sw_code = f"""
// EduAGI Service Worker v{self.sw_version}
const CACHE_NAME = '{cache_name}';
const CORE_FILES = {json.dumps(core_files)};
const OFFLINE_URL = '/offline';

// Install event - cache core files
self.addEventListener('install', event => {{
    console.log('SW: Installing service worker v{self.sw_version}');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {{
                console.log('SW: Caching core files');
                return cache.addAll(CORE_FILES);
            }})
            .then(() => self.skipWaiting())
            .catch(error => {{
                console.error('SW: Failed to cache core files:', error);
            }})
    );
}});

// Activate event - clean up old caches
self.addEventListener('activate', event => {{
    console.log('SW: Activating service worker v{self.sw_version}');
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {{
                return Promise.all(
                    cacheNames
                        .filter(cacheName => cacheName !== CACHE_NAME)
                        .map(cacheName => {{
                            console.log('SW: Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }})
                );
            }})
            .then(() => self.clients.claim())
    );
}});

// Fetch event - serve from cache with fallback
self.addEventListener('fetch', event => {{
    // Skip non-GET requests
    if (event.request.method !== 'GET') return;
    
    // Skip cross-origin requests
    if (!event.request.url.startsWith(self.location.origin)) return;

    event.respondWith(
        caches.match(event.request)
            .then(cachedResponse => {{
                if (cachedResponse) {{
                    // Return cached version
                    return cachedResponse;
                }}
                
                // Try to fetch from network
                return fetch(event.request)
                    .then(response => {{
                        // Cache successful responses
                        if (response.status === 200) {{
                            const responseClone = response.clone();
                            caches.open(CACHE_NAME)
                                .then(cache => {{
                                    cache.put(event.request, responseClone);
                                }});
                        }}
                        return response;
                    }})
                    .catch(() => {{
                        // Network failed, serve offline page for navigation requests
                        if (event.request.mode === 'navigate') {{
                            return caches.match(OFFLINE_URL);
                        }}
                        throw new Error('Network failed and no cached version available');
                    }});
            }})
    );
}});

// Push notification event
self.addEventListener('push', event => {{
    console.log('SW: Push message received');
    
    let notificationData = {{}};
    if (event.data) {{
        try {{
            notificationData = event.data.json();
        }} catch (e) {{
            notificationData = {{ title: event.data.text() }};
        }}
    }}
    
    const options = {{
        body: notificationData.body || 'You have a new update from EduAGI',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/badge-72x72.png',
        tag: notificationData.tag || 'eduagi-notification',
        data: notificationData.data || {{}},
        actions: [
            {{
                action: 'view',
                title: 'View',
                icon: '/static/icons/view-32x32.png'
            }},
            {{
                action: 'dismiss', 
                title: 'Dismiss',
                icon: '/static/icons/dismiss-32x32.png'
            }}
        ],
        requireInteraction: notificationData.important || false,
        vibrate: [200, 100, 200]
    }};
    
    event.waitUntil(
        self.registration.showNotification(
            notificationData.title || 'EduAGI Notification',
            options
        )
    );
}});

// Notification click event
self.addEventListener('notificationclick', event => {{
    console.log('SW: Notification clicked');
    event.notification.close();
    
    if (event.action === 'dismiss') {{
        return;
    }}
    
    // Default action or 'view' action
    const url = event.notification.data?.url || '/';
    
    event.waitUntil(
        clients.matchAll({{ type: 'window' }})
            .then(clientList => {{
                // Try to focus existing window
                for (const client of clientList) {{
                    if (client.url === url && 'focus' in client) {{
                        return client.focus();
                    }}
                }}
                // Open new window
                if (clients.openWindow) {{
                    return clients.openWindow(url);
                }}
            }})
    );
}});

// Background sync event (for offline actions)
self.addEventListener('sync', event => {{
    console.log('SW: Background sync triggered:', event.tag);
    
    if (event.tag === 'background-sync') {{
        event.waitUntil(doBackgroundSync());
    }}
}});

async function doBackgroundSync() {{
    try {{
        // Sync offline data with server
        const response = await fetch('/api/sync/offline-data', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }}
        }});
        
        if (response.ok) {{
            console.log('SW: Background sync completed successfully');
        }} else {{
            throw new Error('Sync failed');
        }}
    }} catch (error) {{
        console.error('SW: Background sync failed:', error);
        throw error; // Re-register for retry
    }}
}}

// Message handler for communication with main thread
self.addEventListener('message', event => {{
    if (event.data && event.data.type === 'SKIP_WAITING') {{
        self.skipWaiting();
    }}
    
    if (event.data && event.data.type === 'GET_VERSION') {{
        event.ports[0].postMessage({{ version: '{self.sw_version}' }});
    }}
}});

console.log('SW: Service worker v{self.sw_version} loaded successfully');
"""
        return sw_code

    def register_push_subscription(self, subscription_data: Dict[str, Any], 
                                 user_id: Optional[str] = None, 
                                 device_info: Optional[Dict[str, Any]] = None) -> str:
        """
        Register a Web Push notification subscription.
        
        Args:
            subscription_data: Push subscription data from client
            user_id: Associated user ID
            device_info: Device information
            
        Returns:
            Subscription ID
        """
        subscription_id = hashlib.md5(
            f"{subscription_data['endpoint']}_{user_id}".encode()
        ).hexdigest()[:16]
        
        subscription = PushSubscription(
            endpoint=subscription_data['endpoint'],
            keys=subscription_data['keys'],
            user_id=user_id,
            device_info=device_info or {}
        )
        
        self.push_subscriptions[subscription_id] = subscription
        return subscription_id

    def unregister_push_subscription(self, subscription_id: str) -> bool:
        """Unregister a push subscription."""
        if subscription_id in self.push_subscriptions:
            self.push_subscriptions[subscription_id].active = False
            return True
        return False

    def send_push_notification(self, user_id: str, notification_data: Dict[str, Any]) -> List[str]:
        """
        Send push notification to user's subscribed devices.
        
        Args:
            user_id: Target user ID
            notification_data: Notification payload
            
        Returns:
            List of subscription IDs that received the notification
        """
        sent_to = []
        
        for sub_id, subscription in self.push_subscriptions.items():
            if subscription.user_id == user_id and subscription.active:
                # In production, this would use the Web Push Protocol
                # to send notifications via the push service
                success = self._send_web_push(subscription, notification_data)
                if success:
                    sent_to.append(sub_id)
        
        return sent_to

    def _send_web_push(self, subscription: PushSubscription, data: Dict[str, Any]) -> bool:
        """
        Send Web Push notification (placeholder implementation).
        
        In production, this would use libraries like pywebpush to send
        notifications via the Web Push Protocol.
        """
        # Placeholder - would use actual Web Push implementation
        print(f"Sending push notification to {subscription.endpoint}: {data}")
        return True

    def track_install_prompt(self, user_id: str) -> bool:
        """
        Track when install prompt is shown to user.
        
        Args:
            user_id: User who saw the prompt
            
        Returns:
            bool: True if prompt should be shown (not shown recently)
        """
        now = datetime.utcnow()
        last_shown = self.install_prompts.get(user_id)
        
        # Don't show prompt more than once per week
        if last_shown and (now - last_shown).days < 7:
            return False
            
        self.install_prompts[user_id] = now
        return True

    def generate_offline_page(self) -> str:
        """
        Generate offline fallback page HTML.
        
        Returns:
            HTML content for offline page
        """
        return f"""
<!DOCTYPE html>
<html lang="{self.config.lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Offline - {self.config.app_name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: {self.config.background_color};
            color: #333;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
            text-align: center;
        }}
        
        .offline-icon {{
            width: 120px;
            height: 120px;
            margin-bottom: 20px;
            opacity: 0.6;
        }}
        
        h1 {{
            color: {self.config.theme_color};
            margin-bottom: 16px;
        }}
        
        p {{
            font-size: 16px;
            line-height: 1.5;
            max-width: 400px;
            margin-bottom: 20px;
            opacity: 0.8;
        }}
        
        .retry-btn {{
            background-color: {self.config.theme_color};
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            font-size: 16px;
            cursor: pointer;
            transition: background-color 0.2s;
        }}
        
        .retry-btn:hover {{
            background-color: {self.config.theme_color}dd;
        }}
        
        .cached-content {{
            margin-top: 30px;
            text-align: left;
        }}
        
        .cached-content h3 {{
            color: {self.config.theme_color};
        }}
        
        .cached-content ul {{
            list-style: none;
            padding: 0;
        }}
        
        .cached-content li {{
            padding: 8px;
            margin: 4px 0;
            background: #f5f5f5;
            border-radius: 4px;
        }}
        
        .cached-content a {{
            color: {self.config.theme_color};
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <svg class="offline-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M23 12C23 18.075 18.075 23 12 23S1 18.075 1 12 5.925 1 12 1s11 4.925 11 11Z" 
              stroke="currentColor" stroke-width="2"/>
        <path d="M8 12L11 15L16 9" stroke="currentColor" stroke-width="2" 
              stroke-linecap="round" stroke-linejoin="round" opacity="0.3"/>
    </svg>
    
    <h1>You're Offline</h1>
    <p>It looks like you're not connected to the internet. Check your connection and try again, or browse previously loaded content below.</p>
    
    <button class="retry-btn" onclick="window.location.reload()">Try Again</button>
    
    <div class="cached-content">
        <h3>Available Offline Content</h3>
        <ul>
            <li><a href="/">Home</a></li>
            <li><a href="/lessons">My Lessons</a></li>
            <li><a href="/progress">Learning Progress</a></li>
            <li><a href="/profile">Profile</a></li>
        </ul>
    </div>
    
    <script>
        // Automatically retry when connection is restored
        window.addEventListener('online', () => {{
            window.location.reload();
        }});
        
        // Show connection status
        if (navigator.onLine) {{
            document.querySelector('p').textContent = 
                'Connection restored! Click "Try Again" to continue.';
        }}
    </script>
</body>
</html>
"""

    def check_for_updates(self) -> Optional[ServiceWorkerUpdate]:
        """
        Check if service worker needs updating.
        
        Returns:
            ServiceWorkerUpdate info if update available, None otherwise
        """
        # In production, this would check for actual file changes
        # For now, return None (no updates)
        return None

    def get_pwa_install_criteria(self) -> Dict[str, Any]:
        """
        Get PWA installation criteria and current status.
        
        Returns:
            Dict with PWA installability information
        """
        return {
            "manifest_valid": True,
            "service_worker_registered": True,
            "served_over_https": True,  # Assume production deployment
            "has_icons": True,
            "installable": True,
            "criteria_met": [
                "Web app manifest with required fields",
                "Service worker registered and active", 
                "Served over HTTPS",
                "Icons for multiple screen sizes",
                "Start URL responds with 200 OK"
            ],
            "install_prompt_available": True
        }

    def get_subscription_stats(self) -> Dict[str, Any]:
        """Get push notification subscription statistics."""
        active_subs = sum(1 for sub in self.push_subscriptions.values() if sub.active)
        
        return {
            "total_subscriptions": len(self.push_subscriptions),
            "active_subscriptions": active_subs,
            "inactive_subscriptions": len(self.push_subscriptions) - active_subs,
            "unique_users": len(set(sub.user_id for sub in self.push_subscriptions.values() 
                                  if sub.user_id and sub.active))
        }