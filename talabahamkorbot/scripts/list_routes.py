import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from fastapi.routing import APIRoute

# Iterate over all routes
for route in app.routes:
    if isinstance(route, APIRoute):
        if "auth" in route.path or "appeals" in route.path:
            print(f"{route.methods} {route.path}")
    # Handle Mounts (static files)
    else:
        print(f"MOUNT {route.name}")
