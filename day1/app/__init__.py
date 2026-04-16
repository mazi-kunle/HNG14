from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.config['SQLALCHEMY_DATABASE_URI'] = \
        'mysql+pymysql://user:password@localhost/day1_db'

    CORS(app, resources={r"/*": {"origins": "*"}})
    db.init_app(app)

    from app.routes import main
    app.register_blueprint(main)
    
    return app
