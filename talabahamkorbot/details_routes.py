
import sys
import os
sys.path.append(os.getcwd())

from main import app

def print_routes():
    with open("routes.txt", "w") as f:
        f.write("🚀 Listing All Registered Routes:\n")
        for route in app.routes:
            if hasattr(route, "path"):
                f.write(f" - {route.methods} {route.path}\n")
            else:
                 f.write(f" - {route.name} (Mounted)\n")

if __name__ == "__main__":
    print_routes()
