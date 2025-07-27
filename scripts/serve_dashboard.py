#!/usr/bin/env python3
"""
Simple Dashboard Server
Serves the analytics dashboard locally for testing
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

def serve_dashboard(port=8000):
    """Serve the dashboard on localhost"""
    
    # Change to reports directory
    reports_dir = Path("reports")
    if not reports_dir.exists():
        print("❌ Reports directory not found!")
        print("Run the analytics workflow first to generate reports.")
        return
    
    os.chdir(reports_dir)
    
    # Create server
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        url = f"http://localhost:{port}/dashboard.html"
        print(f"🚀 Dashboard server started!")
        print(f"📊 Open your browser and go to: {url}")
        print(f"🛑 Press Ctrl+C to stop the server")
        
        # Open browser automatically
        try:
            webbrowser.open(url)
        except:
            pass
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped.")

if __name__ == "__main__":
    serve_dashboard() 