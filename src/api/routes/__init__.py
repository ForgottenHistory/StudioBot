"""API Routes Module

Modular route blueprints for the radio server API.
"""

from flask import Flask
from flask_cors import CORS

from src.radio.radio_server import RadioServer
from .generation import init_generation_routes
from .scheduler import init_scheduler_routes
from .content import init_content_routes
from .admin import init_admin_routes


def create_app():
    """Create and configure Flask application with modular routes"""
    app = Flask(__name__)

    # Enable CORS for frontend
    CORS(app, origins=["http://localhost:3000", "http://localhost:5173"])

    # Initialize radio server
    radio_server = RadioServer()
    app.radio_server = radio_server  # Store reference for external access

    # Initialize and register route blueprints
    generation_bp = init_generation_routes(radio_server)
    scheduler_bp = init_scheduler_routes(radio_server)
    content_bp = init_content_routes(radio_server)
    admin_bp = init_admin_routes(radio_server)

    # Register blueprints
    app.register_blueprint(generation_bp)
    app.register_blueprint(scheduler_bp)
    app.register_blueprint(content_bp)
    app.register_blueprint(admin_bp)

    return app


__all__ = [
    'create_app',
    'init_generation_routes',
    'init_scheduler_routes',
    'init_content_routes',
    'init_admin_routes'
]