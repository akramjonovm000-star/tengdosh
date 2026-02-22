import asyncio
from database.db_connect import get_db
import os
print(f"MERCHANT_ID={os.getenv('CLICK_MERCHANT_ID', '25883')}")
print(f"SERVICE_ID={os.getenv('CLICK_SERVICE_ID', '36248')}")
