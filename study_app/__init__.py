from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from config import Config

# Initialize SQLAlchemy
db = SQLAlchemy()

def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    # Load configuration
    app.config.from_object(config_class)
    
    # Ensure the upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    
    # Import and register blueprints
    from study_app.routes import main_bp
    app.register_blueprint(main_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app