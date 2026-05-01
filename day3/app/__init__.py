from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_limiter.errors import RateLimitExceeded
from flask_cors import CORS
from app.config import Config
from app.utils.logger import register_logger


db = SQLAlchemy()

limiter = Limiter(key_func=get_remote_address)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.url_map.strict_slashes = False
    
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['DATABASE_URI']

    # initialize extensions
    CORS(app, resources={r"/*": {"origins": "*"}})
    db.init_app(app)
    limiter.init_app(app)

    # register logger
    register_logger(app)

    # register blueprints
    from app.profiles.routes import profile
    from app.auth.routes import auth

    # Handle rate limit errors
    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limit(e):
        return jsonify({
            "status": "error",
            "message": "Too many requests, please slow down"
        }), 429

    app.register_blueprint(profile)
    app.register_blueprint(auth)
    
    return app
