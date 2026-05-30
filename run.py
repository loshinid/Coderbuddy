#!/usr/bin/env python3
"""
Production-ready startup script for CoderBuddy AI Website Generator
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def check_virtual_env():
    """Check if running in virtual environment."""
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if in_venv:
        print("✅ Running in virtual environment")
        return True
    else:
        print("⚠️  Not in virtual environment (recommended but not required)")
        return True

def install_dependencies():
    """Install required dependencies."""
    try:
        print("📦 Installing dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_api_key():
    """Check if Groq API key is configured."""
    api_key = os.getenv('GROQ_API_KEY')
    if api_key:
        print("✅ Groq API key is configured")
        if not api_key.startswith('gsk_'):
            print("⚠️  API key format may be incorrect (should start with 'gsk_')")
        return True
    else:
        print("❌ GROQ_API_KEY not found in environment variables")
        print("Please set up your .env file with a valid Groq API key")
        print("Get your API key from: https://console.groq.com/keys")
        return False

def check_static_files():
    """Check if frontend files exist."""
    static_dir = Path("static")
    required_files = ["index.html", "styles.css", "script.js"]
    
    if not static_dir.exists():
        print(f"❌ Static directory not found: {static_dir}")
        return False
    
    missing_files = []
    for file_name in required_files:
        file_path = static_dir / file_name
        if not file_path.exists():
            missing_files.append(file_name)
    
    if missing_files:
        print(f"❌ Missing frontend files: {missing_files}")
        return False
    
    print("✅ Frontend files found")
    return True

def main():
    """Main startup function."""
    print("=== CoderBuddy AI Website Generator ===")
    print("🚀 Production Startup Script\n")
    
    # Run all checks
    checks = [
        ("Python Version", check_python_version),
        ("Virtual Environment", check_virtual_env),
        ("Dependencies", install_dependencies),
        ("API Key", check_api_key),
        ("Frontend Files", check_static_files)
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        print(f"--- {check_name} ---")
        if not check_func():
            all_passed = False
        print()
    
    if not all_passed:
        print("❌ Some checks failed. Please resolve the issues above.")
        sys.exit(1)
    
    print("🎉 All checks passed! Starting CoderBuddy server...\n")
    print("📍 Web Interface: http://localhost:8000")
    print("📍 API Documentation: http://localhost:8000/docs")
    print("📍 Health Check: http://localhost:8000/health")
    print("\nPress Ctrl+C to stop the server\n")
    
    # Start the server
    try:
        import uvicorn
        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=8000,
            reload=False,  # Production mode - no auto-reload
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
