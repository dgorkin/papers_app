"""Local HTTP API server for Chrome extension integration.

Runs a Flask server in a background thread on localhost.
Provides endpoints for adding papers and checking app status.
"""

import logging
import threading
from typing import Callable, Optional

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.serving import make_server

logger = logging.getLogger(__name__)


def create_app(add_paper_callback: Callable[[dict], dict]) -> Flask:
    """Create the Flask application with API routes.

    Args:
        add_paper_callback: Function called with {"pmid": ...} or {"doi": ...}
            that returns {"success": bool, "message": str, "paper": {...}}
    """
    app = Flask(__name__)
    CORS(app)  # Allow cross-origin requests from the Chrome extension

    @app.route("/api/status", methods=["GET"])
    def api_status():
        return jsonify({"status": "running", "app": "Literature Manager"})

    @app.route("/api/add", methods=["POST"])
    def api_add():
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "message": "No JSON body"}), 400

        pmid = data.get("pmid")
        doi = data.get("doi")

        if not pmid and not doi:
            return jsonify({
                "success": False,
                "message": "Must provide 'pmid' or 'doi'"
            }), 400

        try:
            result = add_paper_callback(data)
            status_code = 200 if result.get("success") else 409
            return jsonify(result), status_code
        except Exception as e:
            logger.exception("Error adding paper via API")
            return jsonify({"success": False, "message": str(e)}), 500

    return app


class ApiServer:
    """Manages the local API server lifecycle in a background thread."""

    def __init__(self, port: int, add_paper_callback: Callable[[dict], dict]):
        self.port = port
        self._callback = add_paper_callback
        self._server: Optional[make_server] = None
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """Start the API server in a daemon thread."""
        app = create_app(self._callback)
        try:
            self._server = make_server("127.0.0.1", self.port, app)
            self._thread = threading.Thread(
                target=self._server.serve_forever,
                daemon=True,
                name="api-server",
            )
            self._thread.start()
            logger.info("API server started on port %d", self.port)
        except OSError as e:
            logger.error("Failed to start API server on port %d: %s", self.port, e)

    def stop(self):
        """Shut down the API server."""
        if self._server:
            self._server.shutdown()
            self._server = None
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
            logger.info("API server stopped")

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()
