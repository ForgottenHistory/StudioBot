"""API Routes

Flask routes for the radio server API endpoints.
"""

import os
import random
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

from src.radio.radio_server import RadioServer


def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)

    # Enable CORS for frontend
    CORS(app, origins=["http://localhost:3000", "http://localhost:5173"])

    # Initialize radio server
    radio_server = RadioServer()

    @app.route('/')
    def index():
        """Enhanced server status page"""
        # Don't log routine status checks to avoid spam
        return jsonify(radio_server.get_status())

    @app.route('/topics')
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

    @app.route('/personalities')
    def list_personalities():
        """List all available personalities"""
        personalities = {
            name: {
                "name": personality.name,
                "role": personality.role,
                "voice": personality.voice,
                "description": personality.description,
                "speaking_style": personality.speaking_style,
                "catchphrases_count": len(personality.catchphrases)
            }
            for name, personality in radio_server.content_manager.personalities.items()
        }
        return jsonify({"personalities": personalities})

    @app.route('/generate/dynamic_ad', methods=['GET', 'POST'])
    def generate_dynamic_ad():
        """Generate dynamic ad using topics and personalities"""
        radio_server.logger.info("API REQUEST - Dynamic ad generation started")

        if request.method == 'GET':
            topic_name = request.args.get('topic')
            personality_name = request.args.get('personality')
        else:
            data = request.json or {}
            topic_name = data.get('topic')
            personality_name = data.get('personality')

        try:
            # Get topic
            topic = None
            if topic_name and topic_name in radio_server.content_manager.topics:
                topic = radio_server.content_manager.topics[topic_name]
            else:
                topic = radio_server.content_manager.get_random_topic()

            # Generate ad content
            ad_content = radio_server.content_generator.generate_themed_ad(topic)

            # Get personality for voice (default to random announcer-type)
            if personality_name:
                personality = radio_server.content_manager.personalities.get(
                    personality_name.lower().replace(' ', '_')
                )
            else:
                # Get random personality suitable for ads
                announcer_personalities = [
                    p for p in radio_server.content_manager.personalities.values()
                    if 'caller' in p.role or 'announcer' in p.voice
                ]
                personality = random.choice(announcer_personalities) if announcer_personalities else None

            personality_name = personality.name if personality else "Generic Announcer"

            # Generate TTS
            audio_file = radio_server.voice_manager.generate_tts_audio(
                ad_content, personality_name=personality_name
            )

            if audio_file and os.path.exists(audio_file):
                # Log the generation
                radio_server.log_generation(
                    "dynamic_ad",
                    ad_content,
                    topic=topic.theme,
                    personality=personality_name,
                    audio_file=os.path.basename(audio_file),
                    request_type="api_manual"
                )

                return jsonify({
                    "success": True,
                    "content": ad_content,
                    "audio_url": f"/audio/{os.path.basename(audio_file)}",
                    "topic": topic.theme,
                    "personality": personality_name,
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

    @app.route('/generate/dynamic_conversation', methods=['GET', 'POST'])
    def generate_dynamic_conversation():
        """Generate dynamic conversation between personalities"""
        if request.method == 'GET':
            host_name = request.args.get('host')
            guest_name = request.args.get('guest')
            topic_name = request.args.get('topic')
        else:
            data = request.json or {}
            host_name = data.get('host')
            guest_name = data.get('guest')
            topic_name = data.get('topic')

        try:
            cm = radio_server.content_manager

            # Get host personality
            host = None
            if host_name:
                host = cm.personalities.get(host_name.lower().replace(' ', '_'))
            if not host:
                # Get main host or random host-type personality
                hosts = [p for p in cm.personalities.values() if 'host' in p.role]
                host = hosts[0] if hosts else cm.get_random_personality()

            # Get guest personality
            guest = None
            if guest_name:
                guest = cm.personalities.get(guest_name.lower().replace(' ', '_'))
            if not guest:
                # Get random personality that isn't the host
                available_guests = [p for p in cm.personalities.values() if p.name != host.name]
                guest = random.choice(available_guests) if available_guests else None

            if not guest:
                return jsonify({"error": "Need at least 2 personalities for conversation"}), 400

            # Get topic
            topic = None
            if topic_name and topic_name in cm.topics:
                topic = cm.topics[topic_name]
            else:
                topic = cm.get_random_topic()

            # Generate conversation content
            conversation_content = radio_server.content_generator.generate_conversation_content(
                host, guest, topic
            )

            # Log the generation
            radio_server.log_generation(
                "dynamic_conversation",
                conversation_content,
                host=host.name,
                guest=guest.name,
                topic=topic.theme,
                request_type="api_manual"
            )

            return jsonify({
                "success": True,
                "content": conversation_content,
                "host": host.name,
                "guest": guest.name,
                "topic": topic.theme,
                "generated_at": datetime.now().isoformat(),
                "note": "Use /generate/conversation_audio to convert to speech"
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @app.route('/generate/custom_tts', methods=['POST'])
    def generate_custom_tts():
        """Generate TTS for custom text with specified personality"""
        data = request.json or {}
        text = data.get('text', '')
        personality_name = data.get('personality', '')

        if not text:
            return jsonify({"error": "Text is required"}), 400

        try:
            # Generate TTS with personality voice
            audio_file = radio_server.voice_manager.generate_tts_audio(
                text, personality_name=personality_name
            )

            if audio_file and os.path.exists(audio_file):
                # Log the custom TTS generation
                radio_server.log_generation(
                    "custom_tts",
                    text,
                    personality=personality_name,
                    audio_file=os.path.basename(audio_file),
                    request_type="api_custom_tts"
                )

                return jsonify({
                    "success": True,
                    "text": text,
                    "personality": personality_name,
                    "audio_url": f"/audio/{os.path.basename(audio_file)}",
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

    @app.route('/generate/stitch_audio', methods=['POST'])
    def stitch_audio():
        """Stitch multiple audio segments into one complete conversation audio"""
        data = request.json or {}
        audio_segments = data.get('audio_segments', [])

        if not audio_segments:
            return jsonify({"error": "Audio segments are required"}), 400

        try:
            # Use the voice manager to stitch audio segments
            stitched_audio_file = radio_server.voice_manager.stitch_audio_segments(audio_segments)

            if stitched_audio_file and os.path.exists(stitched_audio_file):
                return jsonify({
                    "success": True,
                    "audio_url": f"/audio/{os.path.basename(stitched_audio_file)}",
                    "generated_at": datetime.now().isoformat()
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Failed to stitch audio segments"
                }), 500

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @app.route('/scheduler/start', methods=['POST'])
    def start_scheduler():
        """Start the automatic content generation scheduler"""
        radio_server.start_automation()
        return jsonify({
            "success": True,
            "message": "Scheduler started",
            "status": radio_server.scheduler.is_running
        })

    @app.route('/scheduler/stop', methods=['POST'])
    def stop_scheduler():
        """Stop the automatic content generation scheduler"""
        radio_server.stop_automation()
        return jsonify({
            "success": True,
            "message": "Scheduler stopped",
            "status": radio_server.scheduler.is_running
        })

    @app.route('/scheduler/status')
    def scheduler_status():
        """Get scheduler status"""
        status = radio_server.scheduler.get_status()
        return jsonify(status)

    @app.route('/generated_content')
    def list_generated_content():
        """List recently generated content"""
        return jsonify(radio_server.get_generated_content_list())

    @app.route('/audio/<filename>')
    def serve_audio(filename):
        """Serve generated audio files"""
        # Use absolute path to avoid working directory issues
        file_path = Path(radio_server.voice_manager.temp_dir) / filename

        # Make sure we have an absolute path
        if not file_path.is_absolute():
            file_path = Path.cwd() / file_path

        if file_path.exists():
            return send_file(str(file_path), mimetype='audio/wav')
        else:
            print(f"[DEBUG] Audio file not found: {file_path}")
            print(f"[DEBUG] Temp dir: {radio_server.voice_manager.temp_dir}")
            print(f"[DEBUG] Working dir: {Path.cwd()}")
            return jsonify({"error": "File not found", "path": str(file_path)}), 404

    @app.route('/generate_ad', methods=['POST'])
    def generate_ad_for_track():
        """Generate ad based on current music track context"""
        data = request.json
        if not data:
            return jsonify({"error": "JSON data required"}), 400

        radio_server.logger.info("API REQUEST - Music-triggered ad generation")

        # Extract track context
        current_track = data.get('current_track', {})
        time_remaining = data.get('time_remaining', 0)
        ad_type = data.get('ad_type', 'transition')

        # Create contextual theme for ad generation
        track_title = current_track.get('title', 'Unknown')
        track_artist = current_track.get('artist', 'Unknown Artist')

        radio_server.logger.info(f"Generating ad for track transition: {track_artist} - {track_title}")
        radio_server.logger.info(f"Time remaining: {time_remaining} seconds")

        try:
            # Generate contextual ad content using your system's topic-based approach
            topic = radio_server.content_manager.get_random_topic()
            ad_content = radio_server.content_generator.generate_themed_ad(topic)

            # Add track transition context to the beginning
            transition_intro = f"That was '{track_title}' by {track_artist}! "
            ad_content = transition_intro + ad_content

            # Get an announcer-type personality for ads
            announcer_personalities = [
                p for p in radio_server.content_manager.personalities.values()
                if 'announcer' in p.role.lower() or 'caller' in p.role.lower()
            ]
            personality = random.choice(announcer_personalities) if announcer_personalities else None
            personality_name = personality.name if personality else "Generic Announcer"

            # Generate TTS audio
            audio_file = radio_server.voice_manager.generate_tts_audio(
                ad_content, personality_name=personality_name
            )

            if audio_file and os.path.exists(audio_file):
                # Log the generation
                radio_server.log_generation(
                    "music_transition_ad",
                    ad_content,
                    topic=topic.theme,
                    personality=personality_name,
                    audio_file=os.path.basename(audio_file),
                    track_context=f"{track_artist} - {track_title}",
                    time_remaining=time_remaining,
                    request_type="music_integration"
                )

                response_data = {
                    "success": True,
                    "message": "Ad generated successfully",
                    "content": ad_content,
                    "audio_url": f"/audio/{os.path.basename(audio_file)}",
                    "context": {
                        "track": current_track,
                        "time_remaining": time_remaining,
                        "ad_type": ad_type,
                        "topic": topic.theme,
                        "personality": personality_name
                    },
                    "generated_at": datetime.now().isoformat()
                }

                radio_server.logger.info(f"Ad generated successfully: {ad_content[:50]}...")
                return jsonify(response_data)
            else:
                radio_server.logger.error("Failed to generate audio")
                return jsonify({
                    "success": False,
                    "error": "Failed to generate audio",
                    "content": ad_content
                }), 500

        except Exception as e:
            radio_server.logger.error(f"Ad generation error: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @app.route('/cleanup', methods=['POST'])
    def cleanup():
        """Manual cleanup of old files"""
        radio_server.cleanup_old_files()
        return jsonify({"success": True, "message": "Cleanup completed"})

    @app.route('/reload_content', methods=['POST'])
    def reload_content():
        """Reload all content files (topics and personalities) without restarting server"""
        try:
            radio_server.content_manager.load_all_content()
            return jsonify({
                "success": True,
                "message": f"Content reloaded: {len(radio_server.content_manager.topics)} topics, {len(radio_server.content_manager.personalities)} personalities"
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    # Store radio_server reference for access
    app.radio_server = radio_server

    return app