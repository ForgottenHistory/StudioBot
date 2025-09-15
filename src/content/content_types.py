"""Content Type System

Generic content type registry and base classes for extensible content generation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Type
from dataclasses import dataclass
import random


@dataclass
class ContentGenerationParams:
    """Parameters for content generation"""
    topic: Optional[str] = None
    personalities: Optional[List[str]] = None
    track_info: Optional[Dict[str, Any]] = None
    custom_params: Optional[Dict[str, Any]] = None


@dataclass
class AudioSettings:
    """Audio processing settings for content type"""
    effect_type: str = "vintage_radio"  # vintage_radio, super_muffled, telephone_quality, studio_interview
    personality_roles: List[str] = None  # Which personalities to use
    multi_voice: bool = False  # Whether this uses multiple voices

    def __post_init__(self):
        if self.personality_roles is None:
            self.personality_roles = ["host"]


class ContentType(ABC):
    """Base class for all content types"""

    def __init__(self, name: str, display_name: str, description: str):
        self.name = name
        self.display_name = display_name
        self.description = description

    @abstractmethod
    def generate_prompt(self, params: ContentGenerationParams, content_manager, config) -> str:
        """Generate the LLM prompt for this content type"""
        pass

    @abstractmethod
    def get_audio_settings(self, params: ContentGenerationParams) -> AudioSettings:
        """Get audio processing settings for this content type"""
        pass

    @abstractmethod
    def process_generated_content(self, content: str, params: ContentGenerationParams) -> str:
        """Post-process the generated content (cleanup, formatting, etc.)"""
        pass

    def get_default_personalities(self, content_manager) -> List[str]:
        """Get default personalities for this content type"""
        personalities = list(content_manager.personalities.keys())
        return personalities[:1] if personalities else ["default"]

    def validate_params(self, params: ContentGenerationParams) -> bool:
        """Validate generation parameters"""
        return True


class AdContent(ContentType):
    """Traditional radio advertisement content"""

    def __init__(self):
        super().__init__(
            name="ad",
            display_name="Radio Advertisement",
            description="GTA-style satirical radio advertisements"
        )

    def generate_prompt(self, params: ContentGenerationParams, content_manager, config) -> str:
        # Get topic
        topic = None
        if params.topic and params.topic != 'general':
            topic = content_manager.topics.get(params.topic)
        if not topic:
            topic = content_manager.get_random_topic()

        # Handle track-based ads
        if params.track_info:
            track_title = params.track_info.get('title', 'Unknown')
            track_artist = params.track_info.get('artist', 'Unknown Artist')

            return f"""Create a HILARIOUS satirical GTA-style radio advertisement that makes a clever reference to the song that just played: "{track_title}" by {track_artist}.

COMEDY STRUCTURE:
1. HOOK - Reference the song/artist naturally in the opening
2. SOLUTION - Introduce ridiculous product with specific name
3. ESCALATION - Add absurd features/benefits with specific numbers
4. DISCLAIMER - Rapid-fire funny side effects or warnings

COMEDY RULES:
- NATURALLY reference the song title or artist name in the ad
- ONE specific product with exact name (not "amazing device")
- SPECIFIC numbers, prices, percentages for absurdity
- ESCALATING claims that get more ridiculous
- PHYSICAL comedy elements (visual absurdity)
- CORPORATE doublespeak mixed with obvious lies
- FAST PACING like real ads but increasingly unhinged

LENGTH: 50-70 words max for radio timing

Focus on ONE product, make each claim more absurd than the last, end with darkly funny disclaimer."""

        # Topic-based ads
        products_list = ', '.join(topic.products[:3])

        return f"""Create a HILARIOUS satirical GTA-style radio advertisement about {topic.theme}.

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

Focus on ONE product, make each claim more absurd than the last, end with darkly funny disclaimer."""

    def get_audio_settings(self, params: ContentGenerationParams) -> AudioSettings:
        return AudioSettings(
            effect_type="vintage_radio",
            personality_roles=["announcer", "host"],
            multi_voice=False
        )

    def process_generated_content(self, content: str, params: ContentGenerationParams) -> str:
        # Clean up any markdown formatting
        import re
        content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
        content = re.sub(r'\*([^*]+)\*', r'\1', content)
        content = re.sub(r'`([^`]+)`', r'\1', content)
        return content.strip()


class ConversationContent(ContentType):
    """Multi-personality radio conversation content"""

    def __init__(self):
        super().__init__(
            name="conversation",
            display_name="Radio Conversation",
            description="Conversations between radio personalities"
        )

    def generate_prompt(self, params: ContentGenerationParams, content_manager, config) -> str:
        # Get personalities
        personalities = params.personalities or []
        if len(personalities) < 2:
            # Auto-select host and guest
            all_personalities = content_manager.personalities
            host_candidates = [name for name, p in all_personalities.items() if p.role == "main_host"]
            guest_candidates = [name for name, p in all_personalities.items() if p.role != "main_host"]

            host = random.choice(host_candidates) if host_candidates else random.choice(list(all_personalities.keys()))
            guest = random.choice(guest_candidates) if guest_candidates else random.choice(list(all_personalities.keys()))
            personalities = [host, guest]

        # Get topic
        topic = None
        if params.topic:
            topic = content_manager.topics.get(params.topic)
        if not topic:
            topic = content_manager.get_random_topic()

        host_personality = content_manager.personalities[personalities[0]]
        guest_personality = content_manager.personalities[personalities[1]]

        # Use template engine if available
        if hasattr(content_manager, 'template_engine'):
            suggested_style = content_manager.template_engine.suggest_style_for_topic(topic)
            return content_manager.template_engine.render_conversation_prompt(
                suggested_style, host_personality, guest_personality, topic
            )

        # Fallback prompt
        return f"""Create a hilarious radio conversation between {host_personality.name} and {guest_personality.name} about {topic.theme}.

{host_personality.name}: {host_personality.description}
Speaking style: {host_personality.speaking_style}

{guest_personality.name}: {guest_personality.description}
Speaking style: {guest_personality.speaking_style}

Topic: {topic.description}

Create a 4-5 exchange conversation that escalates in absurdity while staying true to each character's personality."""

    def get_audio_settings(self, params: ContentGenerationParams) -> AudioSettings:
        personalities = params.personalities or ["host", "guest"]
        return AudioSettings(
            effect_type="vintage_radio",
            personality_roles=personalities,
            multi_voice=True
        )

    def process_generated_content(self, content: str, params: ContentGenerationParams) -> str:
        # Clean up conversation formatting
        import re

        # Remove markdown formatting
        content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
        content = re.sub(r'\*([^*]+)\*', r'\1', content)

        # Remove stage directions
        content = re.sub(r'\[([^\]]*(?:baritone|tenor|deadpan|sarcastic|whisper|shout|laugh|sigh|pause|dramatic|excited|nervous)[^\]]*)\]', '', content, flags=re.IGNORECASE)

        # Clean up extra spaces but preserve line breaks
        content = re.sub(r'[ \t]+', ' ', content)
        content = re.sub(r'\n\s*\n', '\n\n', content)

        return content.strip()

    def get_default_personalities(self, content_manager) -> List[str]:
        """Get default host and guest for conversations"""
        all_personalities = content_manager.personalities
        host_candidates = [name for name, p in all_personalities.items() if p.role == "main_host"]
        guest_candidates = [name for name, p in all_personalities.items() if p.role != "main_host"]

        host = random.choice(host_candidates) if host_candidates else random.choice(list(all_personalities.keys()))
        guest = random.choice(guest_candidates) if guest_candidates else random.choice(list(all_personalities.keys()))

        return [host, guest]


class StudioInterviewContent(ContentType):
    """Professional studio interview content (The Onion style)"""

    def __init__(self):
        super().__init__(
            name="studio_interview",
            display_name="Studio Interview",
            description="Professional satirical interviews (The Onion style)"
        )

    def generate_prompt(self, params: ContentGenerationParams, content_manager, config) -> str:
        # Get personalities
        personalities = params.personalities or []
        if len(personalities) < 2:
            # Auto-select interviewer and interviewee
            all_personalities = content_manager.personalities
            interviewer_candidates = [name for name, p in all_personalities.items() if p.role == "main_host"]
            expert_candidates = [name for name, p in all_personalities.items() if p.role == "expert_guest"]

            interviewer = random.choice(interviewer_candidates) if interviewer_candidates else random.choice(list(all_personalities.keys()))
            expert = random.choice(expert_candidates) if expert_candidates else random.choice(list(all_personalities.keys()))
            personalities = [interviewer, expert]

        # Get topic
        topic = None
        if params.topic:
            topic = content_manager.topics.get(params.topic)
        if not topic:
            topic = content_manager.get_random_topic()

        interviewer_personality = content_manager.personalities[personalities[0]]
        expert_personality = content_manager.personalities[personalities[1]]

        return f"""Create a satirical studio interview that STARTS completely believable but gradually reveals subtle absurdity.

INTERVIEWER: {interviewer_personality.name} - Professional news interviewer
EXPERT: {expert_personality.name} - Industry expert/analyst

TOPIC: {topic.theme} - {topic.description}

STRUCTURE (CRITICAL - Follow exactly):
1. INTERVIEWER: Professional introduction and setup (completely normal)
2. EXPERT: Opens with 100% believable industry insight
3. INTERVIEWER: Logical follow-up question
4. EXPERT: Still believable but introduces ONE slightly odd detail
5. INTERVIEWER: Questions the odd detail professionally
6. EXPERT: Doubles down with pseudo-scientific explanation
7. INTERVIEWER: Professional wrap-up treating absurdity as normal

COMEDY RULES:
- Start with REAL industry language and actual concerns
- First 2 exchanges should sound completely legitimate
- Introduce absurdity through specific details, not broad concepts
- Use real percentages, studies, and technical terms
- Expert never admits anything is unusual - treats everything as standard practice
- Interviewer maintains professional demeanor throughout

GROUNDING STRATEGY:
- If tech: focus on actual tech trends first, then introduce silly features
- If health: start with real health concerns, add absurd solutions
- If business: begin with real market forces, introduce silly business models
- If food: actual restaurant trends first, then ridiculous ingredients/methods

AVOID:
- Obviously fake companies or products
- Immediately ridiculous concepts
- Breaking character or winking at audience
- Over-the-top reactions

LENGTH: Keep to 250-300 words for easy listening

The goal is someone listening casually thinks it's real news for the first 30 seconds."""

    def get_audio_settings(self, params: ContentGenerationParams) -> AudioSettings:
        personalities = params.personalities or ["host", "expert_guest"]
        return AudioSettings(
            effect_type="studio_interview",  # New professional studio effect
            personality_roles=personalities,
            multi_voice=True
        )

    def process_generated_content(self, content: str, params: ContentGenerationParams) -> str:
        # Clean up interview formatting
        import re

        # Remove markdown formatting
        content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
        content = re.sub(r'\*([^*]+)\*', r'\1', content)

        # Remove stage directions but preserve interview structure
        content = re.sub(r'\[([^\]]*)\]', '', content)

        # Clean up extra spaces but preserve dialogue structure
        content = re.sub(r'[ \t]+', ' ', content)
        content = re.sub(r'\n\s*\n', '\n\n', content)

        return content.strip()


class ContentTypeRegistry:
    """Registry for all available content types"""

    def __init__(self):
        self._content_types: Dict[str, ContentType] = {}
        self._register_default_types()

    def _register_default_types(self):
        """Register the default content types"""
        self.register(AdContent())
        self.register(ConversationContent())
        self.register(StudioInterviewContent())

    def register(self, content_type: ContentType):
        """Register a new content type"""
        self._content_types[content_type.name] = content_type

    def get(self, name: str) -> Optional[ContentType]:
        """Get a content type by name"""
        return self._content_types.get(name)

    def list_types(self) -> List[ContentType]:
        """Get all registered content types"""
        return list(self._content_types.values())

    def get_types_dict(self) -> Dict[str, Dict[str, str]]:
        """Get content types as dictionary for API responses"""
        return {
            name: {
                "display_name": ct.display_name,
                "description": ct.description
            }
            for name, ct in self._content_types.items()
        }


# Global registry instance
content_type_registry = ContentTypeRegistry()