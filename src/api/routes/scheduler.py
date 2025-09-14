"""Scheduler Routes

API endpoints for radio scheduler control.
"""

from flask import Blueprint, jsonify

scheduler_bp = Blueprint('scheduler', __name__, url_prefix='/scheduler')


def init_scheduler_routes(radio_server):
    """Initialize scheduler routes with radio server instance"""

    @scheduler_bp.route('/start', methods=['POST'])
    def start_scheduler():
        """Start automatic content generation"""
        try:
            radio_server.start_automation()
            return jsonify({
                "success": True,
                "message": "Scheduler started successfully",
                "status": "running"
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @scheduler_bp.route('/stop', methods=['POST'])
    def stop_scheduler():
        """Stop automatic content generation"""
        try:
            radio_server.stop_automation()
            return jsonify({
                "success": True,
                "message": "Scheduler stopped successfully",
                "status": "stopped"
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @scheduler_bp.route('/status')
    def scheduler_status():
        """Get scheduler status"""
        try:
            return jsonify({
                "success": True,
                "scheduler_running": radio_server.scheduler.is_running,
                "next_ad": radio_server.scheduler.get_next_ad_time(),
                "next_conversation": radio_server.scheduler.get_next_conversation_time(),
                "config": radio_server.config.get_scheduler_config()
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    return scheduler_bp