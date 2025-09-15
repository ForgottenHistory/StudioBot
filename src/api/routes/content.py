"""Content Routes

API endpoints for content management and serving.
"""

from flask import Blueprint, jsonify, send_file
from pathlib import Path

content_bp = Blueprint('content', __name__)


def init_content_routes(radio_server):
    """Initialize content routes with radio server instance"""

    def _check_personality_voice_file(voice_filename):
        """Check if a voice file exists for the personality"""
        from pathlib import Path
        if not voice_filename:
            return False
        voice_path = Path("voices") / voice_filename
        return voice_path.exists() and voice_path.is_file()

    @content_bp.route('/')
    def index():
        """Enhanced server status page"""
        # Don't log routine status checks to avoid spam
        return jsonify(radio_server.get_status())

    @content_bp.route('/topics')
    def list_topics():
        """List all available topics"""
        topics = {
            name: {
                "theme": topic.theme,
                "description": topic.description,
                "keywords": topic.keywords,
                "product_count": len(topic.products)
            }
            for name, topic in radio_server.content_manager.topics.items()
        }
        return jsonify({"topics": topics})

    @content_bp.route('/personalities')
    def list_personalities():
        """List all available personalities"""
        personalities = {
            name: {
                "name": personality.name,
                "role": personality.role,
                "voice": personality.voice,
                "description": personality.description,
                "speaking_style": personality.speaking_style,
                "personality_traits": personality.personality_traits[:3] if personality.personality_traits else [],
                "catchphrases_count": len(personality.catchphrases) if personality.catchphrases else 0,
                "has_voice_file": _check_personality_voice_file(personality.voice)
            }
            for name, personality in radio_server.content_manager.personalities.items()
        }
        return jsonify({"personalities": personalities})

    @content_bp.route('/generated_content')
    def list_generated_content():
        """List recently generated content files"""
        return jsonify(radio_server.get_generated_content_list())

    @content_bp.route('/audio/<filename>')
    def serve_audio(filename):
        """Serve generated audio files"""
        # Security: only allow wav files and sanitize filename
        if not filename.endswith('.wav') or '..' in filename or '/' in filename:
            return jsonify({"error": "Invalid filename"}), 400

        audio_dir = radio_server.config.get('paths.temp_audio_dir', 'temp_audio')
        # Ensure we use absolute path
        if not Path(audio_dir).is_absolute():
            file_path = Path.cwd() / audio_dir / filename
        else:
            file_path = Path(audio_dir) / filename

        if file_path.exists() and file_path.is_file():
            return send_file(file_path, mimetype='audio/wav')
        else:
            return jsonify({"error": "File not found"}), 404

    return content_bp