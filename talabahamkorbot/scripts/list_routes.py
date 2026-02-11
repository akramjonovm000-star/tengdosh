from main import app

for route in app.routes:
    # Handle API routes
    if hasattr(route, 'path'):
        print(f"{route.methods} {route.path}")
    # Handle Mounts (static files)
    else:
        print(f"MOUNT {route.name}")
