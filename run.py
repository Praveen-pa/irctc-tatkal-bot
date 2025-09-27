#!/usr/bin/env python3
"""
IRCTC Tatkal Automation Bot
Application Runner Script
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from main import create_app, socketio
from config import Config

def main():
    """Main application entry point"""
    app = create_app()
    
    # Get configuration
    config = Config()
    
    print("🚀 Starting IRCTC Tatkal Automation Bot")
    print(f"📍 Environment: {config.ENVIRONMENT}")
    print(f"🌐 Host: {config.HOST}:{config.PORT}")
    print(f"🔒 Debug Mode: {config.DEBUG}")
    
    # Create required directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("temp", exist_ok=True)
    os.makedirs("config", exist_ok=True)
    
    # Start the application
    try:
        socketio.run(
            app,
            host=config.HOST,
            port=config.PORT,
            debug=config.DEBUG,
            allow_unsafe_werkzeug=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"❌ Application failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()