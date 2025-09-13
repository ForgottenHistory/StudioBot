"""Dynamic Content Generator

Handles generating ads and conversations using OpenRouter API.
"""

import random
import requests
from typing import Optional

from src.content.content_manager import Topic, Personality, ContentManager


class DynamicContentGenerator:
    def __init__(self, openrouter_api_key: str, content_manager: ContentManager, config=None):
        self.openrouter_api_key = openrouter_api_key
        self.content_manager = content_manager
        self.config = config

        # Get content generation settings from config
        if self.config:
            self.max_tokens = self.config.get('content.max_tokens', 300)
            self.temperature = self.config.get('content.temperature', 0.7)
            self.model = self.config.get('content.model', 'moonshotai/kimi-k2-0905')
        else:
            self.max_tokens = 300
            self.temperature = 0.7
            self.model = 'moonshotai/kimi-k2-0905'

    def generate_themed_ad(self, topic: Topic = None) -> str:
        """Generate an ad for a specific topic using OpenRouter"""
        if not topic:
            topic = self.content_manager.get_random_topic()

        # Create enhanced prompt with topic details
        products_list = ', '.join(topic.products[:3])  # Use first 3 products as examples

        prompt = f"""Create a satirical GTA-style radio advertisement about {topic.theme}.

Theme: {topic.description}
Example products: {products_list}

Make it absurd and funny, like something from Vice City radio. Keep it under 60 words. Include:
- A ridiculous product or service related to {topic.theme}
- Over-the-top marketing claims
- Absurd side effects or disclaimers
- Corporate name that sounds professional but fake

Make it sound like a real radio ad but completely ridiculous. No special characters, just plain text."""

        return self._call_openrouter_api(prompt)

    def generate_conversation_content(self, personality1: Personality, personality2: Personality, topic: Topic = None) -> str:
        """Generate conversation content between two personalities"""
        if not topic:
            topic = self.content_manager.get_random_topic()

        # Generate random radio intro/outro templates
        radio_intros = [
            "Welcome back to the show, folks.",
            "And we're back with more madness.",
            "You're listening to the late night express.",
            "Once again, welcome to our little corner of chaos.",
            "We're back on the airwaves with more insanity."
        ]

        radio_outros = [
            "Well folks, that's all the time we have for that particular brand of crazy.",
            "And that's another segment that'll haunt my dreams. We'll be right back.",
            "Ladies and gentlemen, I need a drink. More after this commercial break.",
            "That's enough of that madness for now. Stay tuned for more chaos.",
            "Well, that happened. We'll return with more questionable content shortly."
        ]

        # Create conversation prompt with mandatory radio formatting
        prompt = f"""Create a short radio show conversation between a HOST and GUEST about {topic.theme}.

HOST: {personality1.name}
- Role: {personality1.role}
- Style: {personality1.speaking_style}
- Personality: {', '.join(personality1.personality_traits[:3])}

GUEST: {personality2.name}
- Role: {personality2.role}
- Style: {personality2.speaking_style}
- Personality: {', '.join(personality2.personality_traits[:3])}

Topic: {topic.description}

MANDATORY FORMAT - You MUST follow this structure:

1. HOST introduces the segment with: "{random.choice(radio_intros)} We've got [GUEST NAME] here to talk about [TOPIC]."
2. 4-6 lines of back-and-forth dialogue about the topic
3. HOST concludes with: "{random.choice(radio_outros)}"

RULES:
- Keep each line under 15 words for radio pacing
- Host is professional but skeptical
- Guest is enthusiastic about their crazy idea
- Make the topic discussion absurd and funny
- Each line should be: "Character Name: dialogue"

Example structure:
{personality1.name}: Welcome back to the show, folks. We've got {personality2.name} here to talk about {topic.theme.lower()}.
{personality2.name}: Thanks for having me! I've got this amazing new invention!
{personality1.name}: Of course you do. What is it this time?
{personality2.name}: It's a combination toaster and alarm clock!
{personality1.name}: Because those two things obviously belong together.
{personality2.name}: Exactly! Wake up to fresh toast every morning!
{personality1.name}: That's enough of that madness for now. Stay tuned for more chaos."""

        return self._call_openrouter_api(prompt)

    def _call_openrouter_api(self, prompt: str) -> str:
        """Call OpenRouter API with the given prompt"""
        if not self.openrouter_api_key:
            return "Sorry folks, we're having technical difficulties with our content generation system!"

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"[CONTENT] OpenRouter API error: {e}")
            return f"Well folks, looks like our content generator is having a coffee break. Technical difficulties!"