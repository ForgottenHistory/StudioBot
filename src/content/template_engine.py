"""Template Engine for Dynamic Content Generation

Handles loading and rendering of conversation templates with variable substitution.
"""

import re
import yaml
import random
from pathlib import Path
from typing import Dict, Any, List, Optional


class TemplateEngine:
    def __init__(self, content_dir: str = "content"):
        self.content_dir = Path(content_dir)
        self.templates_dir = self.content_dir / "templates"

        # Load templates and styles
        self.conversation_styles = self._load_conversation_styles()
        self.prompt_templates = self._load_prompt_templates()

    def _load_conversation_styles(self) -> Dict[str, Any]:
        """Load conversation styles from YAML file"""
        styles_file = self.templates_dir / "conversation_styles.yml"
        if styles_file.exists():
            with open(styles_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}

    def _load_prompt_templates(self) -> Dict[str, str]:
        """Load prompt templates from YAML file"""
        prompts_file = self.templates_dir / "conversation_prompts.yml"
        if prompts_file.exists():
            with open(prompts_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}

    def get_conversation_styles(self) -> List[str]:
        """Get list of available conversation style names"""
        return list(self.conversation_styles.keys())

    def get_random_conversation_style(self, exclude: Optional[List[str]] = None) -> str:
        """Get a random conversation style name"""
        styles = self.get_conversation_styles()
        if exclude:
            styles = [s for s in styles if s not in exclude]
        return random.choice(styles) if styles else "interview"

    def render_conversation_prompt(self,
                                 style_name: str,
                                 host_personality: Any,
                                 guest_personality: Any,
                                 topic: Any) -> str:
        """Render a conversation prompt using the specified style and variables"""

        # Get conversation style
        style = self.conversation_styles.get(style_name, self.conversation_styles.get("interview", {}))

        # Choose appropriate template
        template_key = f"{style_name}_template"
        if template_key not in self.prompt_templates:
            template_key = "base_template"

        template = self.prompt_templates.get(template_key, "")

        # Prepare variables for substitution
        variables = self._prepare_template_variables(style, host_personality, guest_personality, topic)

        # Render template
        rendered_prompt = self._substitute_variables(template, variables)

        return rendered_prompt

    def _prepare_template_variables(self,
                                  style: Dict[str, Any],
                                  host_personality: Any,
                                  guest_personality: Any,
                                  topic: Any) -> Dict[str, str]:
        """Prepare all variables needed for template substitution"""

        # Get host traits and catchphrases
        host_traits = getattr(host_personality, 'personality_traits', [])
        host_catchphrases = getattr(host_personality, 'catchphrases', [])

        # Get guest traits and catchphrases
        guest_traits = getattr(guest_personality, 'personality_traits', [])
        guest_catchphrases = getattr(guest_personality, 'catchphrases', [])

        # Format conversation structure and rules
        structure_text = self._format_structure(style.get('structure', []))
        comedy_rules_text = self._format_comedy_rules(style.get('comedy_rules', []))

        variables = {
            # Topic variables
            'topic_theme': getattr(topic, 'theme', 'general discussion'),
            'topic_description': getattr(topic, 'description', 'Various topics of interest'),

            # Host variables
            'host_name': getattr(host_personality, 'name', 'Host'),
            'host_role': getattr(host_personality, 'role', 'Radio Host'),
            'host_speaking_style': getattr(host_personality, 'speaking_style', 'Professional'),
            'host_traits': ', '.join(host_traits[:3]) if host_traits else 'Professional, Curious',
            'host_catchphrases': ', '.join(host_catchphrases[:3]) if host_catchphrases else 'N/A',

            # Guest variables
            'guest_name': getattr(guest_personality, 'name', 'Guest'),
            'guest_role': getattr(guest_personality, 'role', 'Expert'),
            'guest_speaking_style': getattr(guest_personality, 'speaking_style', 'Informative'),
            'guest_traits': ', '.join(guest_traits[:3]) if guest_traits else 'Knowledgeable, Enthusiastic',
            'guest_catchphrases': ', '.join(guest_catchphrases[:3]) if guest_catchphrases else 'N/A',

            # Conversation style variables
            'conversation_style_name': style.get('name', 'General Discussion'),
            'conversation_purpose': style.get('purpose', 'Discuss the topic in an entertaining way'),
            'conversation_length': style.get('length', '8-10 lines'),
            'conversation_structure': structure_text,
            'comedy_rules': comedy_rules_text,
        }

        return variables

    def _format_structure(self, structure_list: List[str]) -> str:
        """Format structure list into numbered text"""
        if not structure_list:
            return "1. Introduction\n2. Discussion\n3. Conclusion"

        formatted = []
        for i, item in enumerate(structure_list, 1):
            formatted.append(f"{i}. {item}")

        return "\n".join(formatted)

    def _format_comedy_rules(self, rules_list: List[str]) -> str:
        """Format comedy rules list into bullet points"""
        if not rules_list:
            return "- Keep it entertaining and character-driven"

        formatted = []
        for rule in rules_list:
            formatted.append(f"- {rule}")

        return "\n".join(formatted)

    def _substitute_variables(self, template: str, variables: Dict[str, str]) -> str:
        """Substitute {{variable}} placeholders in template with actual values"""
        def replace_var(match):
            var_name = match.group(1)
            return variables.get(var_name, f"{{{{ {var_name} }}}}")

        # Replace {{variable}} patterns
        result = re.sub(r'\{\{\s*(\w+)\s*\}\}', replace_var, template)

        return result

    def get_style_info(self, style_name: str) -> Dict[str, Any]:
        """Get detailed information about a conversation style"""
        return self.conversation_styles.get(style_name, {})

    def suggest_style_for_topic(self, topic: Any) -> str:
        """Suggest an appropriate conversation style based on topic characteristics"""
        topic_theme = getattr(topic, 'theme', '').lower()
        topic_keywords = getattr(topic, 'keywords', [])

        # Simple heuristics for style selection
        if any(keyword in ['business', 'product', 'invention', 'startup'] for keyword in topic_keywords):
            return 'product_pitch'
        elif any(keyword in ['news', 'current', 'politics', 'trends'] for keyword in topic_keywords):
            return 'news_commentary'
        elif any(keyword in ['how', 'tutorial', 'guide', 'instructions'] for keyword in topic_keywords):
            return 'tutorial'
        elif any(keyword in ['story', 'experience', 'personal', 'adventure'] for keyword in topic_keywords):
            return 'storytelling'
        elif 'vs' in topic_theme or 'versus' in topic_theme:
            return 'debate'
        else:
            return 'interview'