"""
Main Flask application for BookBot.

This module sets up the Flask application, registers blueprints,
and provides core endpoints for authentication and configuration.
"""

import os
from flask import Flask, request, jsonify, send_from_directory, redirect, url_for
from flask_cors import CORS

from config import Config
from backend.models import db
from backend.auth import require_auth, get_current_user_id
from backend.jobs import start_job_processor, stop_job_processor
from backend.llm import get_api_token_status

# Import API blueprints
from backend.api.books import book_api
from backend.api.chunks import chunk_api
from backend.api.jobs import job_api
from backend.llmpicker import llmpicker_api


def create_app(config_class=Config) -> Flask:
    """
    Create and configure the Flask application.
    
    Args:
        config_class: Configuration class to use
    
    Returns:
        Flask: Configured Flask application
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)  # Enable CORS for development
    
    # Register blueprints
    app.register_blueprint(book_api, url_prefix='/api')
    app.register_blueprint(chunk_api, url_prefix='/api')
    app.register_blueprint(job_api, url_prefix='/api')
    # The llmpicker_api blueprint is registered with the /api prefix
    # to ensure all API endpoints are consistently routed.
    app.register_blueprint(llmpicker_api, url_prefix='/api')
    
    # Core endpoints
    @app.route('/auth')
    def auth():
        """Authentication redirect endpoint."""
        # TODO: Implement Google OAuth redirect
        # For now, redirect to SPA
        return redirect('/')
    
    @app.route('/api/config')
    def get_config():
        """Get configuration for the SPA."""
        return jsonify(Config.get_spa_config())
    
    @app.route('/api/token-status', methods=['POST'])
    def check_token_status():
        """Check API token status and balance."""
        data = request.get_json() or {}
        api_key = data.get('api_key')
        
        if not api_key:
            return jsonify({'error': 'API key required'}), 400
        
        status = get_api_token_status(api_key)
        return jsonify(status)
    
    # SPA serving endpoints
    @app.route('/')
    def serve_spa():
        """Serve the main SPA page."""
        spa_dir = Config.SPA_DIR
        if os.path.exists(os.path.join(spa_dir, 'index.html')):
            return send_from_directory(spa_dir, 'index.html')
        else:
            # Return a simple placeholder if SPA isn't built yet
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>BookBot</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .container { max-width: 800px; margin: 0 auto; }
                    .status { background: #f0f0f0; padding: 20px; border-radius: 5px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>BookBot</h1>
                    <div class="status">
                        <h2>Backend Status: Running ✅</h2>
                        <p>The BookBot backend is running successfully.</p>
                        <p>The frontend SPA will be available here once built.</p>
                        <h3>API Endpoints:</h3>
                        <ul>
                            <li><code>GET /api/config</code> - Get configuration</li>
                            <li><code>GET /api/books</code> - List books</li>
                            <li><code>POST /api/books</code> - Create book</li>
                            <li><code>GET /api/books/{book_id}/chunks</code> - List chunks</li>
                            <li><code>POST /api/books/{book_id}/jobs</code> - Create job</li>
                        </ul>
                    </div>
                </div>
            </body>
            </html>
            '''
    
    @app.route('/<path:path>')
    def serve_spa_assets(path):
        """Serve SPA static assets."""
        spa_dir = Config.SPA_DIR
        if os.path.exists(os.path.join(spa_dir, path)):
            return send_from_directory(spa_dir, path)
        else:
            # Fallback to index.html for client-side routing
            return serve_spa()
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        """Health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'version': '1.0.0',
            'database': 'connected'
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Endpoint not found'}), 404
        else:
            # Serve SPA for non-API routes (client-side routing)
            return serve_spa()
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
    # Initialize database
    with app.app_context():
        db.create_all()
        
        # Create default user if needed
        from backend.models import User
        if not User.query.first():
            default_user = User(
                user_id="default-user-123",
                props={
                    'name': 'Default User',
                    'email': 'user@example.com'
                }
            )
            db.session.add(default_user)
            db.session.commit()
            print("Created default user")
    
    return app


def main():
    """Main entry point for running the application."""
    app = create_app()
    
    # Start job processor
    start_job_processor(app)
    
    try:
        print("Starting BookBot server...")
        print(f"SPA directory: {Config.SPA_DIR}")
        print(f"Database: {Config.SQLALCHEMY_DATABASE_URI}")
        print(f"Debug mode: {Config.DEBUG}")
        
        app.run(
            host='0.0.0.0',
            port=int(os.environ.get('PORT', 5001)),
            debug=Config.DEBUG,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        stop_job_processor()


if __name__ == '__main__':
    main()
