from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    app.url_map.strict_slashes = False


    CORS(app, resources={r"/*": {"origins": "*"}})

    from app.routes import main
    app.register_blueprint(main)
    
    return app
