"""
Flask application factory
"""
import os
import logging
from flask import Flask
from config import config
from app.cache import cache
from app.utils import format_distance, format_pace, format_duration, format_elevation, format_speed


def create_app(config_name=None):
    """
    Create and configure Flask application

    Args:
        config_name: Configuration name ('development', 'production', or None for auto-detect)

    Returns:
        Configured Flask application
    """
    # Get the parent directory (project root)
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Create Flask app with correct template and static folders
    app = Flask(__name__,
                template_folder=os.path.join(project_root, 'templates'),
                static_folder=os.path.join(project_root, 'static'))

    # Determine configuration
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app.config.from_object(config.get(config_name, config["default"]))

    # Setup logging
    if not app.debug:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)

    # Initialize extensions
    cache.init_app(app)

    # Initialize database
    from app.database import close_db, init_db
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()

    # Ensure cache directory exists
    cache_dir = app.config.get("CACHE_DIR", "cache")
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    # Register blueprints
    from app.routes.main import main
    from app.routes.auth_routes import auth_routes
    from app.routes.api import api

    from app.routes.admin import admin

    app.register_blueprint(main)
    app.register_blueprint(auth_routes)
    app.register_blueprint(api)
    app.register_blueprint(admin)

    # Register template filters
    app.jinja_env.filters["format_distance"] = format_distance
    app.jinja_env.filters["format_pace"] = format_pace
    app.jinja_env.filters["format_duration"] = format_duration
    app.jinja_env.filters["format_elevation"] = format_elevation
    app.jinja_env.filters["format_speed"] = format_speed

    # Inject current user into all templates
    @app.context_processor
    def inject_user():
        from app.auth import get_current_user
        user = get_current_user()
        return dict(user=user)

    # Global error handlers
    @app.errorhandler(404)
    def not_found(error):
        return "Page not found", 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal error: {error}")
        return "Internal server error", 500

    return app
