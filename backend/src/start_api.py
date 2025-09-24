#!/usr/bin/env python3
"""
Simple startup script for Mappy FastAPI server
Place this file in your project root directory
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Start the FastAPI server"""
    print("Starting Mappy FastAPI Server...")
    print("URL: http://localhost:8000")
    print("Docs: http://localhost:8000/docs")
    print("Health: http://localhost:8000/health")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 40)
    
    try:
        # Run uvicorn with the correct module path
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "src.api.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\nServer stopped")
    except Exception as e:
        print(f"Failed to start server: {e}")

if __name__ == "__main__":
    main()