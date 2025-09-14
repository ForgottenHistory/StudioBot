"""Admin Routes

API endpoints for administrative tasks.
"""

from flask import Blueprint, jsonify

admin_bp = Blueprint('admin', __name__)


def init_admin_routes(radio_server):
    """Initialize admin routes with radio server instance"""

    @admin_bp.route('/cleanup', methods=['POST'])
    def cleanup_old_files():
        """Manual cleanup of old audio files"""
        try:
            radio_server.cleanup_old_files()
            return jsonify({
                "success": True,
                "message": "Cleanup completed successfully"
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @admin_bp.route('/reload_content', methods=['POST'])
    def reload_content():
        """Reload content (topics and personalities) from disk"""
        try:
            # Reload topics and personalities
            radio_server.content_manager.load_topics()
            radio_server.content_manager.load_personalities()

            return jsonify({
                "success": True,
                "message": "Content reloaded successfully",
                "topics_loaded": len(radio_server.content_manager.topics),
                "personalities_loaded": len(radio_server.content_manager.personalities)
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    return admin_bp