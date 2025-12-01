import webview
import sys
import os
import threading

# Determine if running in PyInstaller bundle
def get_base_path():
    """Get the base path - works for both dev and PyInstaller bundle"""
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        return sys._MEIPASS
    else:
        # Running in normal Python environment
        return os.path.dirname(os.path.abspath(__file__))

# Add backend to path so imports work
base_path = get_base_path()
sys.path.append(os.path.join(base_path, 'backend'))

from backend.bridge import Bridge

def start_webview():
    print("App: Initializing Bridge...")
    bridge = Bridge()
    print("App: Bridge initialized")
    
    # Point to built frontend
    base_path = get_base_path()
    url = os.path.join(base_path, 'frontend', 'dist', 'index.html')
    
    # Optional: Check for dev mode argument if needed, but user requested built integration
    if len(sys.argv) > 1 and sys.argv[1] == '--dev':
        url = 'http://localhost:5173'
        debug = True
    else:
        debug = False
        if not os.path.exists(url):
             print(f"Error: Frontend build not found at {url}")
             print("Please run 'npm run build' in the frontend directory.")
             return

    def on_closed():
        print("App: Window closed, shutting down...")
        # Force kill because background threads might be lingering
        os._exit(0)

    window = webview.create_window(
        'Telegram Drive',
        url=url,
        js_api=bridge,
        width=1200,
        height=800,
        min_size=(800, 600)
    )
    window.events.closed += on_closed
    
    bridge.set_window(window)
    webview.start(debug=debug)

if __name__ == '__main__':
    start_webview()
