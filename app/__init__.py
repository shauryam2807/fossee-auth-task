# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.config import Config

db = SQLAlchemy()
limiter = Limiter(key_func=get_remote_address, default_limits=["100 per hour"])

def create_app():
    app = Flask(__name__)
    
    from flask_cors import CORS
    CORS(app)
    
    app.config.from_object(Config)

    db.init_app(app)
    limiter.init_app(app)

    # Register all route blueprints
    from app.routes.auth import auth_bp
    from app.routes.user import user_bp
    from app.routes.files import files_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(files_bp)

    @app.route('/')
    def index():
        return {"message": "Secure Login API is running!", "version": "1.0.0"}

    return app
