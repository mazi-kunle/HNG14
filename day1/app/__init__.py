from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os


db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    
    app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{os.environ.get('MYSQLUSER', 'user')}:"
    f"{os.environ.get('MYSQLPASSWORD', 'password')}@"
    f"{os.environ.get('MYSQLHOST', 'localhost')}:"
    f"{os.environ.get('MYSQLPORT', '3306')}/"
    f"{os.environ.get('MYSQLDATABASE', 'day1_db')}"
    )

    CORS(app, resources={r"/*": {"origins": "*"}})
    db.init_app(app)

    from app.routes import main
    app.register_blueprint(main)
    
    return app
