import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# 🤖 --- Telegram Bot Sozlamalari --- 🤖
BOT_TOKEN = os.environ.get("BOT_TOKEN")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "talabahamkorbot")

# 👤 --- Bot owner Telegram ID (Muhammadali) --- 👤
OWNER_TELEGRAM_ID = int(os.environ.get("OWNER_TELEGRAM_ID", "387178074"))
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY") 
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 🧠 --- OpenAI Sozlamalari --- 🧠
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL_TASKS = "gpt-4o-mini"    # Konspekt va senariylar uchun (User: 4.1 mini)
OPENAI_MODEL_CHAT = "gpt-4o-mini"     # Shunchaki suhbat uchun (User: Nano O'zbekchada yaxshi emas -> Mini ga qaytarildi)

# 🐘 --- PostgreSQL Sozlamalari --- 🐘
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "talabahamkorbot_db")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_PORT = os.environ.get("DB_PORT", "5432")

# Test Environment Switching
if os.environ.get("TEST_MODE") == "true":
    DB_NAME += "_test"
    print(f"⚠️ RUNNING IN TEST MODE: Using Database '{DB_NAME}'")

# SQLAlchemy async ulanish manzili (asyncpg drayveri bilan)
DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# 🌐 --- Webhook Sozlamalari --- 🌐
DOMAIN = os.environ.get("DOMAIN", "tengdoshbozor.uz")
WEBHOOK_BASE_PATH = "/webhook/bot"
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", f"https://{DOMAIN}{WEBHOOK_BASE_PATH}")

# ⚙️ --- Boshqa sozlamalar --- ⚙️
LOG_LEVEL = "DEBUG"

# 🔐 --- HEMIS OAuth Settings --- 🔐
HEMIS_CLIENT_ID = os.environ.get("HEMIS_CLIENT_ID", "5")
HEMIS_CLIENT_SECRET = os.environ.get("HEMIS_CLIENT_SECRET", "VwSWbyEFMKm8B0LQ1ZqYcK0zUwCs01Z8g8eUP6kK")
HEMIS_REDIRECT_URL = "https://tengdosh.uzjoku.uz/authlog"
HEMIS_AUTH_URL = "https://student.jmcu.uz/oauth/authorize"
HEMIS_TOKEN_URL = "https://student.jmcu.uz/oauth/access-token"
HEMIS_PROFILE_URL = "https://student.jmcu.uz/oauth/api/user"

# 💳 --- Payme Sozlamalari --- 💳
PAYME_MERCHANT_ID = os.environ.get("PAYME_MERCHANT_ID", "65b8...") # Placeholder: replace with real ID
PAYME_CHECKOUT_URL = "https://checkout.paycom.uz"
PAYME_KEY = os.environ.get("PAYME_KEY", "your_payme_key") # Secret Key (Test or Production)

# 👆 --- Click Sozlamalari --- 👆
CLICK_SERVICE_ID = os.environ.get("CLICK_SERVICE_ID", "12345")
CLICK_MERCHANT_ID = os.environ.get("CLICK_MERCHANT_ID", "12345")
CLICK_USER_ID = os.environ.get("CLICK_USER_ID", "12345")
CLICK_SECRET_KEY = os.environ.get("CLICK_SECRET_KEY", "secret_key")

# 🟣 --- Uzum Bank Sozlamalari --- 🟣
UZUM_SERVICE_ID = os.environ.get("UZUM_SERVICE_ID", "12345")
UZUM_SECRET_KEY = os.environ.get("UZUM_SECRET_KEY", "uzum_token")
UZUM_CHECKOUT_URL = "https://www.uzumbank.uz/open-service" 
# Verify URL pattern: https://www.uzumbank.uz/open-service?serviceId=...&amount=...&orderId=...




