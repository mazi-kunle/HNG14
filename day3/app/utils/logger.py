import logging
import time
from flask import request, g

# Configure the logger
logger = logging.getLogger("insighta.requests")
logger.setLevel(logging.INFO)
logger.propagate = False          # ← stops bubbling up to root logger

file_handler = logging.FileHandler("insighta.log")
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
))

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
))

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

def register_logger(app):
    """
    Registers before and after request hooks on the Flask app.
    Called once in create_app().
    """

    @app.before_request
    def start_timer():
        # Store the start time in g
        # g lives for the duration of one request
        g.start_time = time.time()

    @app.after_request
    def log_request(response):
        # Calculate how long the request took
        duration = time.time() - g.get("start_time", time.time())
        duration_ms = round(duration * 1000, 2)

        logger.info(
            f"{request.method} {request.full_path} "
            f"status={response.status_code} "
            f"duration={duration_ms}ms"
        )

        return response