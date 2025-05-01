from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate # Import Migrate
import os
from config import Config

# Initialize SQLAlchemy
db = SQLAlchemy()
# Initialize Migrate
migrate = Migrate()

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
    migrate.init_app(app, db) # Initialize Migrate with app and db
    
    # Import and register blueprints
    from study_app.routes import main_bp
    app.register_blueprint(main_bp)
    
    # Create database tables (handled by migrations now, can be removed or kept)
    # with app.app_context():
    #     db.create_all()
    
    return app