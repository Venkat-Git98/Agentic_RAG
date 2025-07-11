"""
Railway-specific configuration for deployment.
This file handles Railway's environment variables and deployment settings.
"""

import os
import logging

def get_railway_config():
    """Get Railway-specific configuration."""
    config = {
        "PORT": int(os.environ.get("PORT", 8000)),
        "RAILWAY_ENVIRONMENT": os.environ.get("RAILWAY_ENVIRONMENT", "development"),
        "RAILWAY_PROJECT_NAME": os.environ.get("RAILWAY_PROJECT_NAME", "agentic-ai-backend"),
        "RAILWAY_SERVICE_NAME": os.environ.get("RAILWAY_SERVICE_NAME", "backend"),
        "RAILWAY_DEPLOYMENT_ID": os.environ.get("RAILWAY_DEPLOYMENT_ID", "local"),
    }
    
    # Log Railway environment info
    logging.info(f"Railway Environment: {config['RAILWAY_ENVIRONMENT']}")
    logging.info(f"Railway Project: {config['RAILWAY_PROJECT_NAME']}")
    logging.info(f"Railway Service: {config['RAILWAY_SERVICE_NAME']}")
    logging.info(f"Running on Port: {config['PORT']}")
    
    return config

def is_production():
    """Check if running in production environment."""
    return os.environ.get("RAILWAY_ENVIRONMENT") == "production"

def get_cors_origins():
    """Get CORS origins based on environment."""
    if is_production():
        # In production, use specific origins
        return [
            "https://*.netlify.app",
            "https://netlify.app",
            # Add your specific Netlify URL here
            # "https://your-app-name.netlify.app"
        ]
    else:
        # In development, allow localhost
        return [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:8080",
            "*"  # Allow all for development
        ] 