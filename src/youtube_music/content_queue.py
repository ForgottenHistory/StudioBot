"""Content Queue Manager

Maintains a queue of pre-generated ads and conversations for instant playback.
"""

import asyncio
import logging
from collections import deque
from typing import Optional, Dict, Any, Literal
from datetime import datetime
import random

logger = logging.getLogger(__name__)

ContentType = Literal["ad", "conversation"]

class ContentItem:
    """Represents a pre-generated content item"""
    def __init__(self, content_type: ContentType, data: Dict[str, Any]):
        self.content_type = content_type
        self.data = data
        self.created_at = datetime.now()
        self.audio_url = data.get('audio_url', '')
        self.content = data.get('content', '')

    def is_expired(self, max_age_minutes: int = 30) -> bool:
        """Check if content item is too old"""
        age = datetime.now() - self.created_at
        return age.total_seconds() > (max_age_minutes * 60)

class ContentQueue:
    """Manages pre-generated content queue for instant playback"""

    def __init__(self, content_generator, config=None):
        self.content_generator = content_generator
        self.config = config

        # Queue settings
        self.max_queue_size = config.get('content_queue.max_size', 4) if config else 4
        self.min_ads = config.get('content_queue.min_ads', 1) if config else 1
        self.min_conversations = config.get('content_queue.min_conversations', 1) if config else 1
        self.max_age_minutes = config.get('content_queue.max_age_minutes', 30) if config else 30

        # Queue storage
        self.queue = deque()
        self.generation_lock = asyncio.Lock()
        self.last_served_type = None

        # Background task
        self.refill_task = None
        self.is_running = False

        logger.info(f"📊 Content queue initialized (max_size: {self.max_queue_size}, min_ads: {self.min_ads}, min_conversations: {self.min_conversations})")

    async def start(self):
        """Start the content queue system"""
        if self.is_running:
            return

        self.is_running = True
        logger.info("🚀 Starting content queue system...")

        # Initial queue fill
        await self.fill_queue()

        # Start background refill task
        self.refill_task = asyncio.create_task(self._background_refill_loop())
        logger.info("✅ Content queue system started")

    async def stop(self):
        """Stop the content queue system"""
        self.is_running = False
        if self.refill_task:
            self.refill_task.cancel()
            try:
                await self.refill_task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 Content queue system stopped")

    async def get_next_content(self, track_info: Optional[Dict[str, Any]] = None) -> Optional[ContentItem]:
        """Get the next content item for immediate playback"""
        # Clean expired items first
        await self._remove_expired_items()

        if not self.queue:
            logger.warning("⚠️ Queue is empty! Generating content on demand...")
            return await self._generate_emergency_content(track_info)

        # Get next item (alternate types for variety)
        content_item = self._get_best_next_item()

        if content_item:
            self.queue.remove(content_item)
            self.last_served_type = content_item.content_type
            logger.info(f"📤 Served {content_item.content_type} from queue (queue size: {len(self.queue)})")

            # Trigger background refill
            asyncio.create_task(self._trigger_refill())

        return content_item

    def _get_best_next_item(self) -> Optional[ContentItem]:
        """Select the best next item based on variety and freshness"""
        if not self.queue:
            return None

        # Prefer different type than last served for variety
        if self.last_served_type:
            preferred_type = "conversation" if self.last_served_type == "ad" else "ad"
            for item in self.queue:
                if item.content_type == preferred_type:
                    return item

        # Fallback to any available item (prefer newer items)
        return max(self.queue, key=lambda x: x.created_at)

    async def fill_queue(self):
        """Fill the queue to meet minimum requirements"""
        async with self.generation_lock:
            await self._remove_expired_items()

            # Count current content by type
            ad_count = sum(1 for item in self.queue if item.content_type == "ad")
            conversation_count = sum(1 for item in self.queue if item.content_type == "conversation")

            logger.info(f"📊 Queue status: {ad_count} ads, {conversation_count} conversations")

            # Generate missing ads
            ads_needed = max(0, self.min_ads - ad_count)
            for i in range(ads_needed):
                if len(self.queue) >= self.max_queue_size:
                    break
                logger.info(f"🎬 Generating ad {i+1}/{ads_needed} for queue...")
                await self._generate_and_queue_ad()

            # Generate missing conversations
            conversations_needed = max(0, self.min_conversations - conversation_count)
            for i in range(conversations_needed):
                if len(self.queue) >= self.max_queue_size:
                    break
                logger.info(f"🎭 Generating conversation {i+1}/{conversations_needed} for queue...")
                await self._generate_and_queue_conversation()

            logger.info(f"✅ Queue filled: {len(self.queue)} items total")

    async def _generate_and_queue_ad(self):
        """Generate an ad and add it to the queue"""
        try:
            # Create fake track info for ad generation
            fake_track = {
                "title": f"Track {random.randint(1000, 9999)}",
                "artist": f"Artist {random.randint(100, 999)}"
            }

            ad_data = await self.content_generator.pre_generate_ad(fake_track)
            if ad_data:
                content_item = ContentItem("ad", ad_data)
                self.queue.append(content_item)
                logger.info(f"✅ Ad queued successfully")
            else:
                logger.error("❌ Failed to generate ad for queue")
        except Exception as e:
            logger.error(f"❌ Error generating ad for queue: {e}")

    async def _generate_and_queue_conversation(self):
        """Generate a conversation and add it to the queue"""
        try:
            # Create fake track info for conversation generation
            fake_track = {
                "title": f"Track {random.randint(1000, 9999)}",
                "artist": f"Artist {random.randint(100, 999)}"
            }

            conversation_data = await self.content_generator.pre_generate_conversation(fake_track)
            if conversation_data:
                content_item = ContentItem("conversation", conversation_data)
                self.queue.append(content_item)
                logger.info(f"✅ Conversation queued successfully")
            else:
                logger.error("❌ Failed to generate conversation for queue")
        except Exception as e:
            logger.error(f"❌ Error generating conversation for queue: {e}")

    async def _remove_expired_items(self):
        """Remove expired items from the queue"""
        initial_count = len(self.queue)
        self.queue = deque([item for item in self.queue if not item.is_expired(self.max_age_minutes)])
        removed_count = initial_count - len(self.queue)

        if removed_count > 0:
            logger.info(f"🗑️ Removed {removed_count} expired items from queue")

    async def _generate_emergency_content(self, track_info: Optional[Dict[str, Any]] = None) -> Optional[ContentItem]:
        """Generate content on demand when queue is empty"""
        try:
            logger.warning("🚨 Emergency content generation!")

            # Use provided track info or create fake one
            if not track_info:
                track_info = {
                    "title": "Emergency Track",
                    "artist": "Emergency Artist"
                }

            # Try to generate an ad first (usually faster)
            ad_data = await self.content_generator.pre_generate_ad(track_info)
            if ad_data:
                return ContentItem("ad", ad_data)

            logger.error("❌ Emergency content generation failed")
            return None
        except Exception as e:
            logger.error(f"❌ Emergency content generation error: {e}")
            return None

    async def _trigger_refill(self):
        """Trigger background refill if needed"""
        if not self.is_running:
            return

        # Check if we need to refill
        ad_count = sum(1 for item in self.queue if item.content_type == "ad")
        conversation_count = sum(1 for item in self.queue if item.content_type == "conversation")

        if ad_count < self.min_ads or conversation_count < self.min_conversations:
            asyncio.create_task(self.fill_queue())

    async def _background_refill_loop(self):
        """Background task to keep queue filled"""
        while self.is_running:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds

                if not self.is_running:
                    break

                await self._trigger_refill()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Background refill error: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        ad_count = sum(1 for item in self.queue if item.content_type == "ad")
        conversation_count = sum(1 for item in self.queue if item.content_type == "conversation")

        return {
            "total_items": len(self.queue),
            "ads": ad_count,
            "conversations": conversation_count,
            "is_running": self.is_running,
            "last_served_type": self.last_served_type,
            "queue_items": [
                {
                    "type": item.content_type,
                    "created_at": item.created_at.isoformat(),
                    "age_minutes": (datetime.now() - item.created_at).total_seconds() / 60
                }
                for item in self.queue
            ]
        }