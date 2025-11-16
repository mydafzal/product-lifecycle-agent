#!/usr/bin/env python3
"""
Main launcher for the Intelligent Management System Web Application
Run this file to start the Flask web interface
"""
import sys
from pathlib import Path

# Add the webapp directory to Python path
webapp_dir = Path(__file__).parent / "webapp"
sys.path.insert(0, str(webapp_dir))

# Import and run the Flask app
from app import app
import settings

if __name__ == '__main__':
    print("=" * 80)
    print("🚀 Starting Intelligent Management System Web Interface")
    print("=" * 80)
    print(f"📁 Project root: {settings.BASE_DIR}")
    print(f"📁 Input folder: {settings.INPUT_DIR}")
    print(f"📁 Output folder: {settings.OUTPUT_DIR}")
    print(f"📁 Upload folder: {settings.UPLOADS_DIR}")
    print("=" * 80)
    print(f"🌐 Open your browser and navigate to: http://{settings.FLASK_HOST}:{settings.FLASK_PORT}")
    print("=" * 80)
    
    app.run(debug=settings.FLASK_DEBUG, host=settings.FLASK_HOST, port=settings.FLASK_PORT, threaded=True)
