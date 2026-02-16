import sys
print(f"Sys Path: {sys.path}")
try:
    from handlers.auth import get_current_user
    print("Successfully imported handlers.auth")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Other Error: {e}")
