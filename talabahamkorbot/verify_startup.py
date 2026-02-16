import sys
import os
import asyncio
from unittest.mock import MagicMock

# Mock missing dependencies
sys.modules["firebase_admin"] = MagicMock()
sys.modules["firebase_admin.messaging"] = MagicMock()
sys.modules["firebase_admin.credentials"] = MagicMock()
sys.modules["google.oauth2"] = MagicMock()
sys.modules["google.oauth2.service_account"] = MagicMock()
sys.modules["celery"] = MagicMock()
sys.modules["celery.schedules"] = MagicMock()
sys.modules["openai"] = MagicMock()
sys.modules["pypdf"] = MagicMock()
sys.modules["docx"] = MagicMock()
sys.modules["pptx"] = MagicMock()
sys.modules["fastapi_cache"] = MagicMock()
sys.modules["fastapi_cache.backends.redis"] = MagicMock()

# Add project root to path
sys.path.append("/home/user/talabahamkor/talabahamkorbot")

print("Attempting to import main.app...")
try:
    from main import app
    print("✅ SUCCESS: main.app imported successfully!")
    print("Security Headers Configured:", app.middleware_stack)
except ImportError as e:
    print(f"❌ IMPORT ERROR: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ RUNTIME ERROR: {e}")
    sys.exit(1)
