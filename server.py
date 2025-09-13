#!/usr/bin/env python3
"""Enhanced Radio Server - Main Entry Point

Modular radio server with proper separation of concerns.
"""

import threading
import logging
from src.api.routes import create_app
from src.radio.radio_server import start_background_cleanup


def main():
    """Main server entry point"""
    # Create Flask app with all routes and radio server
    app = create_app()
    radio_server = app.radio_server

    # Reduce Werkzeug logging noise for routine requests
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.WARNING)

    # Start background cleanup task
    cleanup_thread = threading.Thread(
        target=start_background_cleanup,
        args=(radio_server,),
        daemon=True
    )
    cleanup_thread.start()

    # Print startup information
    radio_server.print_startup_info()

    # Get server config
    server_config = radio_server.config.get_server_config()

    # Start the Flask server with config settings
    app.run(
        debug=server_config.get('debug', True),
        host=server_config.get('host', '0.0.0.0'),
        port=server_config.get('port', 5000)
    )


if __name__ == '__main__':
    main()