#!/usr/bin/env python3
"""
Quick startup script for CoderBuddy AI Website Generator
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Check if all requirements are installed."""
    try:
        import fastapi
        import uvicorn
        import groq
        import langchain
        import pydantic
        print("✓ All required packages are installed")
        return True
    except ImportError as e:
        print(f"✗ Missing required package: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_api_key():
    """Check if Groq API key is configured."""
    api_key = os.getenv('GROQ_API_KEY')
    if api_key:
        print("✓ Groq API key is configured")
        if not api_key.startswith('gsk_'):
            print("⚠ Warning: API key format may be incorrect")
        return True
    else:
        print("✗ GROQ_API_KEY not found in environment variables")
        print("Please set up your .env file with a valid Groq API key")
        print("Get your API key from: https://console.groq.com/keys")
        return False

def main():
    """Main startup function."""
    print("=== CoderBuddy AI Website Generator ===")
    print("Starting up...\n")
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check API key
    if not check_api_key():
        sys.exit(1)
    
    print("\n🚀 Starting CoderBuddy server...")
    print("📍 The web interface will be available at: http://localhost:8000")
    print("📍 API documentation: http://localhost:8000/docs")
    print("📍 Health check: http://localhost:8000/health")
    print("\nPress Ctrl+C to stop the server\n")
    
    # Start the server
    try:
        import uvicorn
        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
