"""Content Management System

Handles loading and managing topics and personalities from files.
"""

import os
import random
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Any


@dataclass
class Topic:
    theme: str
    description: str
    keywords: List[str]
    products: List[str]


@dataclass
class Personality:
    name: str
    role: str
    voice: str
    description: str
    personality_traits: List[str]
    catchphrases: List[str]
    speaking_style: str
    extra_data: Dict[str, Any]


class ContentManager:
    def __init__(self, content_dir="content"):
        self.content_dir = Path(content_dir)
        self.topics: Dict[str, Topic] = {}
        self.personalities: Dict[str, Personality] = {}

        self.load_all_content()

    def load_all_content(self):
        """Load all topics and personalities from files"""
        self.load_topics()
        self.load_personalities()
        print(f"[CONTENT] Loaded {len(self.topics)} topics, {len(self.personalities)} personalities")

    def load_topics(self):
        """Load topic files"""
        topics_dir = self.content_dir / "topics"
        if not topics_dir.exists():
            print("[CONTENT] Topics directory not found")
            return

        for topic_file in topics_dir.glob("*.txt"):
            try:
                topic_data = self.parse_content_file(topic_file)
                topic = Topic(
                    theme=topic_data.get('theme', topic_file.stem),
                    description=topic_data.get('description', ''),
                    keywords=self.parse_list(topic_data.get('keywords', '')),
                    products=self.parse_list(topic_data.get('products', ''))
                )
                self.topics[topic.theme] = topic
                print(f"[CONTENT] Loaded topic: {topic.theme}")
            except Exception as e:
                print(f"[CONTENT] Error loading topic {topic_file}: {e}")

    def load_personalities(self):
        """Load personality files"""
        personalities_dir = self.content_dir / "personalities"
        if not personalities_dir.exists():
            print("[CONTENT] Personalities directory not found")
            return

        for personality_file in personalities_dir.glob("*.txt"):
            try:
                personality_data = self.parse_content_file(personality_file)

                # Extract extra data (anything not in standard fields)
                standard_fields = {'name', 'role', 'voice', 'description', 'personality_traits', 'catchphrases', 'speaking_style'}
                extra_data = {k: v for k, v in personality_data.items() if k not in standard_fields}

                # Parse voice settings if present
                voice_settings = {}
                if 'voice_settings' in personality_data:
                    voice_settings_text = personality_data['voice_settings']
                    voice_settings = self.parse_voice_settings(voice_settings_text)

                personality = Personality(
                    name=personality_data.get('name', personality_file.stem.replace('_', ' ').title()),
                    role=personality_data.get('role', 'guest'),
                    voice=personality_data.get('voice', 'announcer'),
                    description=personality_data.get('description', ''),
                    personality_traits=self.parse_list(personality_data.get('personality_traits', '')),
                    catchphrases=self.parse_list(personality_data.get('catchphrases', '')),
                    speaking_style=personality_data.get('speaking_style', ''),
                    extra_data={**extra_data, 'voice_settings': voice_settings}
                )
                self.personalities[personality.name.lower().replace(' ', '_')] = personality
                print(f"[CONTENT] Loaded personality: {personality.name}")
            except Exception as e:
                print(f"[CONTENT] Error loading personality {personality_file}: {e}")

    def parse_content_file(self, file_path: Path) -> Dict[str, str]:
        """Parse a content file with key: value format"""
        data = {}
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        current_key = None
        current_value = []

        for line in lines:
            line = line.rstrip()
            if not line:
                continue

            if ':' in line and not line.startswith('-') and not line.startswith(' '):
                # Save previous key-value pair
                if current_key:
                    data[current_key] = '\n'.join(current_value).strip()

                # Start new key-value pair
                key, value = line.split(':', 1)
                current_key = key.strip()
                current_value = [value.strip()] if value.strip() else []
            else:
                # Continue current value
                if current_key:
                    current_value.append(line)

        # Save final key-value pair
        if current_key:
            data[current_key] = '\n'.join(current_value).strip()

        return data

    def parse_list(self, text: str) -> List[str]:
        """Parse a list from text (either newlines with - or comma-separated)"""
        if not text:
            return []

        # Handle bulleted lists
        if '\n-' in text or text.startswith('-'):
            items = []
            for line in text.split('\n'):
                line = line.strip()
                if line.startswith('-'):
                    items.append(line[1:].strip())
            return items

        # Handle comma-separated
        if ',' in text:
            return [item.strip() for item in text.split(',') if item.strip()]

        # Single item or newline-separated
        return [item.strip() for item in text.split('\n') if item.strip()]

    def parse_voice_settings(self, text: str) -> Dict[str, Any]:
        """Parse voice settings from text"""
        settings = {}
        if not text:
            return settings

        for line in text.split('\n'):
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                # Convert numeric values
                if key in ['exaggeration', 'temperature', 'cfg_weight']:
                    try:
                        settings[key] = float(value)
                    except ValueError:
                        settings[key] = value
                else:
                    settings[key] = value

        return settings

    def get_random_topic(self) -> Topic:
        """Get a random topic"""
        return random.choice(list(self.topics.values()))

    def get_random_personality(self, role: str = None) -> Personality:
        """Get a random personality, optionally filtered by role"""
        personalities = list(self.personalities.values())
        if role:
            personalities = [p for p in personalities if p.role == role]
        return random.choice(personalities) if personalities else None