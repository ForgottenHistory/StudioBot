"""Dynamic Content Generator

Handles generating ads and conversations using OpenRouter API.
"""

import random
import requests
from typing import Optional

from src.content.content_manager import Topic, Personality, ContentManager
from src.content.template_engine import TemplateEngine


class DynamicContentGenerator:
    def __init__(self, openrouter_api_key: str, content_manager: ContentManager, config=None):
        self.openrouter_api_key = openrouter_api_key
        self.content_manager = content_manager
        self.config = config

        # Initialize template engine
        content_dir = config.get('paths.content_dir', 'content') if config else 'content'
        self.template_engine = TemplateEngine(content_dir)

        # Get content generation settings from config
        if self.config:
            self.max_tokens = self.config.get('content.max_tokens', 800)  # Increased for conversations
            self.temperature = self.config.get('content.temperature', 0.7)
            self.model = self.config.get('content.model', 'moonshotai/kimi-k2-0905')
        else:
            self.max_tokens = 800
            self.temperature = 0.7
            self.model = 'moonshotai/kimi-k2-0905'

    def generate_themed_ad(self, topic: Topic = None) -> str:
        """Generate an ad for a specific topic using OpenRouter"""
        if not topic:
            topic = self.content_manager.get_random_topic()

        print(f"[CONTENT] === GENERATING THEMED ADVERTISEMENT ===")
        print(f"[CONTENT] Topic: {topic.theme}")

        # Create enhanced prompt with topic details
        products_list = ', '.join(topic.products[:3])  # Use first 3 products as examples

        prompt = f"""Create a HILARIOUS satirical GTA-style radio advertisement about {topic.theme}.

Theme: {topic.description}
Example products: {products_list}

COMEDY STRUCTURE:
1. HOOK - Grab attention with specific problem
2. SOLUTION - Introduce ridiculous product with specific name
3. ESCALATION - Add absurd features/benefits with specific numbers
4. DISCLAIMER - Rapid-fire funny side effects or warnings

COMEDY RULES:
- ONE specific product with exact name (not "amazing device")
- SPECIFIC numbers, prices, percentages for absurdity
- ESCALATING claims that get more ridiculous
- PHYSICAL comedy elements (visual absurdity)
- CORPORATE doublespeak mixed with obvious lies
- FAST PACING like real ads but increasingly unhinged

LENGTH: 50-70 words max for radio timing

EXAMPLE GOOD STRUCTURE:
"Tired of regular furniture? Try MegaCorp's Exploding Couch! Guaranteed to launch you 15 feet in the air every time you sit down! Now with optional parachute attachment for only $299.99 extra! Warning: Not responsible for ceiling damage, broken bones, or sudden understanding of physics. MegaCorp - Because safety is optional!"

Focus on ONE product, make each claim more absurd than the last, end with darkly funny disclaimer."""

        ad_content = self._call_openrouter_api(prompt)
        return self._clean_formatting(ad_content)

    def generate_conversation_content(self, personality1: Personality, personality2: Personality, topic: Topic = None) -> str:
        """Generate conversation content between two personalities"""
        if not topic:
            topic = self.content_manager.get_random_topic()

        print(f"[CONTENT] === GENERATING CONVERSATION ===")
        print(f"[CONTENT] Host: {personality1.name} ({personality1.role})")
        print(f"[CONTENT] Guest: {personality2.name} ({personality2.role})")
        print(f"[CONTENT] Topic: {topic.theme}")

        # Character-specific comedy rules are generated dynamically

        # Use template engine to generate conversation prompt
        # Suggest appropriate conversation style based on topic and personalities
        suggested_style = self.template_engine.suggest_style_for_topic(topic)

        # Optionally override with random style for variety (20% chance)
        if random.random() < 0.2:
            suggested_style = self.template_engine.get_random_conversation_style([suggested_style])

        print(f"[CONTENT] Using conversation style: {suggested_style}")

        # Generate prompt using template engine
        prompt = self.template_engine.render_conversation_prompt(
            suggested_style,
            personality1,  # host
            personality2,  # guest
            topic
        )

        # Generate the conversation content
        conversation_content = self._call_openrouter_api(prompt)

        # Clean up any formatting that slipped through
        conversation_content = self._clean_formatting(conversation_content)

        # Store the conversation style for logging (accessible to API routes)
        self.last_conversation_style = self.template_engine.get_style_info(suggested_style)

        return conversation_content

    def _get_character_comedy_rules(self, personality):
        """Get character-specific comedy rules based on personality traits and role"""
        rules = []

        # Base rules from role
        role_rules = {
            'expert_guest': [
                "- Use authoritative language but with completely wrong information",
                "- Make up statistics and scientific terms on the spot",
                "- Claim expertise in unrelated fields",
                "- Get defensive when questioned on details"
            ],
            'frequent_caller': [
                "- Be infectiously enthusiastic about obviously bad ideas",
                "- Reference family/friends in business schemes",
                "- Dismiss practical concerns with folksy wisdom",
                "- Use colloquial speech patterns and local expressions"
            ],
            'radio_host': [
                "- Use professional radio voice with increasing exasperation",
                "- Point out logical flaws through dry sarcasm",
                "- Make callbacks to earlier absurd claims",
                "- Maintain professional composure despite chaos"
            ]
        }

        # Add role-based rules
        if personality.role in role_rules:
            rules.extend(role_rules[personality.role])

        # Add trait-based rules
        trait_keywords = {
            'scientific': "- Overuse technical terminology incorrectly",
            'statistics': "- Quote specific but obviously fake numbers",
            'contradicts': "- Contradict previous statements casually",
            'defensive': "- React defensively to any skepticism",
            'upbeat': "- Maintain unrealistic optimism about terrible ideas",
            'pidgin': "- Mix regional dialect naturally into speech",
            'safety': "- Dismiss all safety concerns with cultural sayings",
            'sarcasm': "- Respond with increasingly dry sarcasm",
            'skeptical': "- Question the logic of every claim made",
            'professional': "- Maintain radio professionalism despite chaos"
        }

        # Check personality traits for relevant keywords
        all_traits = ' '.join(personality.personality_traits).lower()
        for keyword, rule in trait_keywords.items():
            if keyword in all_traits:
                rules.append(rule)

        # Add speaking style rules
        if personality.speaking_style:
            style_lower = personality.speaking_style.lower()
            if 'authoritative' in style_lower:
                rules.append("- Speak as if everything you say is established fact")
            if 'wrong' in style_lower or 'incorrect' in style_lower:
                rules.append("- Be confidently incorrect about basic concepts")
            if 'pidgin' in style_lower or 'rapid-fire' in style_lower:
                rules.append("- Use energetic, fast-paced speech patterns")
            if 'sarcastic' in style_lower or 'dry' in style_lower:
                rules.append("- Deliver responses with deadpan timing")

        # Fallback if no specific rules found
        if not rules:
            rules = [
                "- Stay true to established personality traits",
                "- Use natural speaking patterns for your role",
                "- Escalate absurdity with each response",
                "- React authentically to other character's claims"
            ]

        return '\n'.join(rules)

    def _get_random_conversation_style(self, personality, topic):
        """Generate random conversation style based on personality and topic"""
        import random

        # Base conversation styles that work for any character
        base_styles = [
            {
                "type": "invention_pitch",
                "description": "Guest is pitching a ridiculous invention or product",
                "purpose": "Present your amazing new invention related to the topic and convince the host it's brilliant"
            },
            {
                "type": "expert_opinion",
                "description": "Guest is sharing their 'expert' opinion on the topic",
                "purpose": "Explain why you're an expert on this topic and share your professional insights (even if completely wrong)"
            },
            {
                "type": "personal_rant",
                "description": "Guest called in to rant about something related to the topic",
                "purpose": "Vent your frustrations about this topic and explain why it's ruining everything"
            },
            {
                "type": "success_story",
                "description": "Guest is bragging about their success/experience with the topic",
                "purpose": "Tell the host about your incredible success story related to this topic"
            },
            {
                "type": "conspiracy_theory",
                "description": "Guest believes there's a conspiracy related to the topic",
                "purpose": "Reveal the hidden truth about this topic that 'they' don't want people to know"
            },
            {
                "type": "life_advice",
                "description": "Guest wants to give life advice related to the topic",
                "purpose": "Share your wisdom about how this topic can change people's lives for the better (or worse)"
            }
        ]

        # Character-specific conversation styles based on traits
        personality_styles = []

        if hasattr(personality, 'personality_traits'):
            traits_text = ' '.join(personality.personality_traits).lower()

            if 'scientific' in traits_text or 'expert' in traits_text:
                personality_styles.append({
                    "type": "fake_research",
                    "description": "Guest is presenting their groundbreaking research findings",
                    "purpose": "Share your latest research discoveries and made-up statistics about this topic"
                })

            if 'business' in traits_text or 'entrepreneur' in traits_text:
                personality_styles.append({
                    "type": "business_opportunity",
                    "description": "Guest sees a business opportunity in the topic",
                    "purpose": "Explain your brilliant business plan related to this topic and why it'll make millions"
                })

            if 'upbeat' in traits_text or 'enthusiastic' in traits_text:
                personality_styles.append({
                    "type": "motivational_speech",
                    "description": "Guest wants to motivate others about the topic",
                    "purpose": "Inspire the audience with your passion for this topic and encourage them to try it"
                })

        # Combine available styles
        all_styles = base_styles + personality_styles

        # Return random style
        return random.choice(all_styles)

    def _clean_formatting(self, text: str) -> str:
        """Remove markdown formatting but preserve dialogue structure for TTS"""
        import re

        # Remove markdown bold/italic formatting
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold** -> bold
        text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *italic* -> italic

        # Remove other common markdown formatting
        text = re.sub(r'__([^_]+)__', r'\1', text)      # __underline__ -> underline
        text = re.sub(r'_([^_]+)_', r'\1', text)        # _underscore_ -> underscore
        text = re.sub(r'`([^`]+)`', r'\1', text)        # `code` -> code

        # Remove any remaining asterisks or formatting characters
        text = re.sub(r'[*_`#]', '', text)

        # Remove stage directions and vocal instructions (both bracketed and non-bracketed)
        # Remove content in brackets like [forced baritone], [deadpan], etc.
        text = re.sub(r'\[([^\]]*(?:baritone|tenor|deadpan|sarcastic|whisper|shout|laugh|sigh|pause|dramatic|excited|nervous)[^\]]*)\]', '', text, flags=re.IGNORECASE)
        # Remove common stage directions without brackets
        text = re.sub(r'\b(?:forced\s+|deep\s+|nervous\s+|excited\s+|sarcastic\s+|deadpan\s+|dramatic\s+)?(?:baritone|tenor|bass|alto|soprano|whisper|shout)\b:?\s*', '', text, flags=re.IGNORECASE)
        # Remove "flips to" and similar transition phrases (more comprehensive)
        text = re.sub(r'\b(?:flips\s+to|switches\s+to|becomes\s+more|turns\s+(?:to\s+)?|shifts\s+to)\s*(?:eager|excited|nervous|dramatic|sarcastic|deadpan|enthusiastic|confident|uncertain)\s*(?:baritone|tenor|bass|alto|soprano|tone|voice)?\b:?\s*', '', text, flags=re.IGNORECASE)
        # Remove standalone vocal descriptors that might be left
        text = re.sub(r'\b(?:eager|excited|nervous|dramatic|sarcastic|deadpan|enthusiastic|confident|uncertain)\s+(?:baritone|tenor|bass|alto|soprano|tone|voice)\b:?\s*', '', text, flags=re.IGNORECASE)

        # Clean up extra spaces but PRESERVE line breaks for dialogue structure
        # Replace multiple spaces with single space, but keep newlines
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs -> single space
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines -> double newline
        text = text.strip()

        return text

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

        print(f"[CONTENT] Generating content with OpenRouter API")
        print(f"[CONTENT] LLM Settings:")
        print(f"  - Model: {self.model}")
        print(f"  - Max Tokens: {self.max_tokens}")
        print(f"  - Temperature: {self.temperature}")
        print(f"  - Prompt length: {len(prompt)} characters")

        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()

            content = result['choices'][0]['message']['content'].strip()

            # Debug: Check if response was truncated
            finish_reason = result['choices'][0].get('finish_reason', 'unknown')
            print(f"[CONTENT] API Response:")
            print(f"  - Content length: {len(content)} characters")
            print(f"  - Finish reason: {finish_reason}")
            print(f"  - Content preview: {content[:100]}...")

            if finish_reason == 'length':
                print(f"[CONTENT] WARNING: Response was truncated due to max_tokens limit")

            return content

        except Exception as e:
            print(f"[CONTENT] OpenRouter API error: {e}")
            return f"Well folks, looks like our content generator is having a coffee break. Technical difficulties!"