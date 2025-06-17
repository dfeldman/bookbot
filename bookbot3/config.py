"""
BookBot Configuration Module

This module handles all configuration for the BookBot application.
"""

import os
from typing import Dict, Any


class Config:
    """Configuration class for BookBot application."""
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///bookbot.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # CSRF configuration (disabled in dev mode for now)
    WTF_CSRF_ENABLED = os.environ.get('WTF_CSRF_ENABLED', 'False').lower() == 'true'
    
    # Admin API key (for future use)
    ADMIN_API_KEY = os.environ.get('ADMIN_API_KEY', 'admin-key-123')
    
    # Job processing configuration
    JOB_POLL_INTERVAL = float(os.environ.get('JOB_POLL_INTERVAL', '1.0'))
    
    # File storage configuration
    OUTPUT_FILES_DIR = os.environ.get('OUTPUT_FILES_DIR', 'output_files')
    
    # LLM configuration
    DEFAULT_LLM_MODEL = os.environ.get('DEFAULT_LLM_MODEL', 'fake')
    OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
    
    # SPA configuration
    SPA_DIR = os.environ.get('SPA_DIR', 'frontend/dist')
    
    @classmethod
    def get_spa_config(cls) -> Dict[str, Any]:
        """Get configuration data to send to the SPA."""
        return {
            'api_url': os.environ.get('API_URL', 'http://localhost:5000'),
            'app_name': 'BookBot',
            'version': '1.0.0',
            'debug': cls.DEBUG
        }


# Create output files directory if it doesn't exist
os.makedirs(Config.OUTPUT_FILES_DIR, exist_ok=True)
