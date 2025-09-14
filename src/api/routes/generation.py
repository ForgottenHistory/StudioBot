"""Generation Routes

API endpoints for content generation (ads, conversations, TTS).
"""

import random
from datetime import datetime
from flask import Blueprint, request, jsonify
from pathlib import Path

generation_bp = Blueprint('generation', __name__, url_prefix='/generate')


def init_generation_routes(radio_server):
    """Initialize generation routes with radio server instance"""

    @generation_bp.route('/dynamic_ad', methods=['GET', 'POST'])
    def generate_dynamic_ad():
        """Generate dynamic ad with specified topic and personality"""
        if request.method == 'GET':
            topic = request.args.get('topic', 'general')
            personality = request.args.get('personality')
        else:
            data = request.json or {}
            topic = data.get('topic', 'general')
            personality = data.get('personality')

        if not personality:
            personalities = list(radio_server.content_manager.personalities.keys())
            personality = random.choice(personalities)

        try:
            # Generate ad content
            ad_content = radio_server.content_generator.generate_ad_content(
                topic=topic,
                personality=personality
            )

            if ad_content:
                # Generate TTS audio
                audio_file = radio_server.voice_manager.generate_personality_tts(
                    ad_content, personality
                )

                if audio_file:
                    # Log the generation
                    radio_server.log_generation(
                        'dynamic_ad',
                        ad_content,
                        topic=topic,
                        personality=personality,
                        audio_file=audio_file
                    )

                    return jsonify({
                        "success": True,
                        "content": ad_content,
                        "audio_url": f"/audio/{Path(audio_file).name}",
                        "topic": topic,
                        "personality": personality,
                        "generated_at": datetime.now().isoformat()
                    })

            return jsonify({
                "success": False,
                "error": "Failed to generate content"
            }), 500

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @generation_bp.route('/dynamic_conversation', methods=['GET', 'POST'])
    def generate_dynamic_conversation():
        """Generate dynamic conversation between personalities"""
        if request.method == 'GET':
            host = request.args.get('host')
            guest = request.args.get('guest')
            topic = request.args.get('topic')
        else:
            data = request.json or {}
            host = data.get('host')
            guest = data.get('guest')
            topic = data.get('topic')

        # Select random personalities if not specified with proper host/guest dynamics
        all_personalities = radio_server.content_manager.personalities

        if not host:
            # Prefer main_host for host role, fallback to any personality
            host_candidates = [name for name, p in all_personalities.items() if p.role == "main_host"]
            if not host_candidates:
                host_candidates = list(all_personalities.keys())
            host = random.choice(host_candidates) if host_candidates else "default_host"

        if not guest:
            # Prefer non-host personalities for guest role
            guest_candidates = [name for name, p in all_personalities.items()
                              if name != host and p.role != "main_host"]
            if not guest_candidates:
                # Fallback to any personality except the host
                guest_candidates = [name for name in all_personalities.keys() if name != host]
            guest = random.choice(guest_candidates) if guest_candidates else "default_guest"

        # Select random topic if not specified
        if not topic:
            topics = list(radio_server.content_manager.topics.keys())
            topic = random.choice(topics) if topics else 'general'

        try:
            # Helper function to find personality by name or display name
            def find_personality_by_name(name):
                if not name:
                    return None, name

                # Try direct key lookup first
                personality = radio_server.content_manager.personalities.get(name)
                if personality:
                    return personality, name

                # Try by display name (personality.name)
                for key, personality in radio_server.content_manager.personalities.items():
                    if personality.name == name:
                        return personality, key

                return None, name

            # Get personality objects for host and guest
            host_personality, host_key = find_personality_by_name(host)
            guest_personality, guest_key = find_personality_by_name(guest)
            topic_object = radio_server.content_manager.topics.get(topic)

            # Debug: Print available personalities if not found
            if not host_personality or not guest_personality:
                available_keys = list(radio_server.content_manager.personalities.keys())
                available_names = [p.name for p in radio_server.content_manager.personalities.values()]
                missing = host if not host_personality else guest
                return jsonify({
                    "success": False,
                    "error": f"Personality '{missing}' not found. Available keys: {available_keys}, Available names: {available_names}"
                }), 404

            if not topic_object:
                topic_object = radio_server.content_manager.get_random_topic()

            # Generate conversation content
            conversation_content = radio_server.content_generator.generate_conversation_content(
                host_personality,
                guest_personality,
                topic_object
            )

            if conversation_content:
                # Generate multi-voice TTS audio for conversation
                audio_file = radio_server.voice_manager.generate_conversation_tts(
                    conversation_content,
                    host_key,
                    guest_key
                )

                if audio_file:
                    # Log the generation
                    radio_server.log_generation(
                        'dynamic_conversation',
                        conversation_content,
                        host=host,
                        guest=guest,
                        topic=topic,
                        audio_file=audio_file
                    )

                    return jsonify({
                        "success": True,
                        "content": conversation_content,
                        "audio_url": f"/audio/{Path(audio_file).name}",
                        "host": host,
                        "guest": guest,
                        "topic": topic,
                        "generated_at": datetime.now().isoformat()
                    })

            return jsonify({
                "success": False,
                "error": "Failed to generate conversation"
            }), 500

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @generation_bp.route('/custom_tts', methods=['POST'])
    def generate_custom_tts():
        """Generate TTS audio for custom text with personality voice"""
        data = request.json
        if not data or 'text' not in data:
            return jsonify({"success": False, "error": "Text required"}), 400

        text = data['text']
        personality = data.get('personality', 'host')

        if len(text.strip()) == 0:
            return jsonify({"success": False, "error": "Text cannot be empty"}), 400

        if len(text) > 1000:
            return jsonify({"success": False, "error": "Text too long (max 1000 characters)"}), 400

        try:
            # Generate TTS audio
            audio_file = radio_server.voice_manager.generate_personality_tts(text, personality)

            if audio_file:
                # Log the generation
                radio_server.log_generation(
                    'custom_tts',
                    text,
                    personality=personality,
                    audio_file=audio_file
                )

                return jsonify({
                    "success": True,
                    "content": text,
                    "audio_url": f"/audio/{Path(audio_file).name}",
                    "personality": personality,
                    "generated_at": datetime.now().isoformat()
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Failed to generate audio"
                }), 500

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @generation_bp.route('/stitch_audio', methods=['POST'])
    def stitch_audio_files():
        """Stitch multiple audio files together"""
        data = request.json
        if not data or 'audio_files' not in data:
            return jsonify({"success": False, "error": "audio_files list required"}), 400

        audio_files = data['audio_files']
        if not isinstance(audio_files, list) or len(audio_files) < 2:
            return jsonify({"success": False, "error": "At least 2 audio files required"}), 400

        try:
            # Stitch audio files
            stitched_file = radio_server.voice_manager.stitch_audio_files(audio_files)

            if stitched_file:
                return jsonify({
                    "success": True,
                    "audio_url": f"/audio/{Path(stitched_file).name}",
                    "input_files": audio_files,
                    "generated_at": datetime.now().isoformat()
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Failed to stitch audio files"
                }), 500

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @generation_bp.route('_ad', methods=['POST'])
    def generate_ad_for_music():
        """Generate ad based on current music track context (called by music integration)"""
        data = request.json
        if not data:
            return jsonify({"error": "JSON data required"}), 400

        # Extract track context
        current_track = data.get('current_track', {})
        time_remaining = data.get('time_remaining', 0)
        ad_type = data.get('ad_type', 'transition')

        track_title = current_track.get('title', 'Unknown')
        track_artist = current_track.get('artist', 'Unknown Artist')

        try:
            # Generate contextual ad content
            ad_content = radio_server.content_generator.generate_track_transition_ad(
                current_track, time_remaining
            )

            if ad_content:
                # Use announcer personality for ads
                audio_file = radio_server.voice_manager.generate_personality_tts(
                    ad_content, "announcer"
                )

                if audio_file:
                    # Log the generation
                    radio_server.log_generation(
                        'music_transition_ad',
                        ad_content,
                        track_title=track_title,
                        track_artist=track_artist,
                        time_remaining=time_remaining,
                        ad_type=ad_type,
                        audio_file=audio_file
                    )

                    return jsonify({
                        "success": True,
                        "message": "Ad generated successfully",
                        "content": ad_content,
                        "audio_url": f"/audio/{Path(audio_file).name}",
                        "context": {
                            "track": current_track,
                            "time_remaining": time_remaining,
                            "ad_type": ad_type
                        },
                        "generated_at": datetime.now().isoformat()
                    })

            return jsonify({
                "success": False,
                "error": "Failed to generate ad content"
            }), 500

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    return generation_bp