"""Radio Content Scheduler

Handles automatic content generation on timed intervals.
"""

import time
import random
import threading
from datetime import datetime
from typing import Optional

from src.content.content_generator import DynamicContentGenerator


class RadioScheduler:
    def __init__(self, content_generator: DynamicContentGenerator, radio_server=None, config=None):
        self.content_generator = content_generator
        self.radio_server = radio_server
        self.is_running = False
        self.schedule_thread = None

        # Schedule configuration from config or defaults
        if config:
            self.ad_interval = config.get('ad_interval', 120)
            self.conversation_interval = config.get('conversation_interval', 300)
            self.auto_start = config.get('auto_start', False)
        else:
            self.ad_interval = 120  # Generate ad every 2 minutes
            self.conversation_interval = 300  # Generate conversation every 5 minutes
            self.auto_start = False

        self.last_ad_time = 0
        self.last_conversation_time = 0

        # Auto-start if configured
        if self.auto_start:
            self.start_scheduler()

    def start_scheduler(self):
        """Start the automatic content generation scheduler"""
        if self.is_running:
            return

        self.is_running = True
        self.schedule_thread = threading.Thread(target=self._schedule_loop, daemon=True)
        self.schedule_thread.start()
        print("[SCHEDULER] Started automatic content generation")

    def stop_scheduler(self):
        """Stop the scheduler"""
        self.is_running = False
        if self.schedule_thread:
            self.schedule_thread.join(timeout=5)
        print("[SCHEDULER] Stopped")

    def _schedule_loop(self):
        """Main scheduler loop"""
        while self.is_running:
            current_time = time.time()

            # Check if it's time to generate an ad
            if current_time - self.last_ad_time >= self.ad_interval:
                self._generate_scheduled_ad()
                self.last_ad_time = current_time

            # Check if it's time to generate a conversation
            if current_time - self.last_conversation_time >= self.conversation_interval:
                self._generate_scheduled_conversation()
                self.last_conversation_time = current_time

            time.sleep(10)  # Check every 10 seconds

    def _generate_scheduled_ad(self):
        """Generate and announce a new ad"""
        try:
            topic = self.content_generator.content_manager.get_random_topic()
            ad_content = self.content_generator.generate_themed_ad(topic)

            print(f"[SCHEDULER] Generated ad for {topic.theme}: {ad_content[:50]}...")

            # Log using radio server logging system
            if self.radio_server and hasattr(self.radio_server, 'log_generation'):
                self.radio_server.log_generation(
                    "scheduled_ad",
                    ad_content,
                    topic=topic.theme,
                    request_type="scheduler_automatic"
                )

        except Exception as e:
            print(f"[SCHEDULER] Error generating scheduled ad: {e}")

    def _generate_scheduled_conversation(self):
        """Generate and announce a new conversation"""
        try:
            # Get host and a random guest
            cm = self.content_generator.content_manager
            host = None
            guest = None

            # Try to get a main host
            for p in cm.personalities.values():
                if p.role == 'main_host':
                    host = p
                    break

            if not host:
                host = cm.get_random_personality()

            # Get a different personality for guest
            available_guests = [p for p in cm.personalities.values() if p.name != host.name]
            if available_guests:
                guest = random.choice(available_guests)
            else:
                return  # Can't have conversation with one person

            topic = cm.get_random_topic()
            conversation_content = self.content_generator.generate_conversation_content(host, guest, topic)

            print(f"[SCHEDULER] Generated conversation: {host.name} & {guest.name} about {topic.theme}")

            # Log using radio server logging system
            if self.radio_server and hasattr(self.radio_server, 'log_generation'):
                self.radio_server.log_generation(
                    "scheduled_conversation",
                    conversation_content,
                    host=host.name,
                    guest=guest.name,
                    topic=topic.theme,
                    request_type="scheduler_automatic"
                )

        except Exception as e:
            print(f"[SCHEDULER] Error generating scheduled conversation: {e}")

    def get_status(self):
        """Get scheduler status information"""
        return {
            "running": self.is_running,
            "ad_interval": self.ad_interval,
            "conversation_interval": self.conversation_interval,
            "last_ad_time": self.last_ad_time,
            "last_conversation_time": self.last_conversation_time
        }