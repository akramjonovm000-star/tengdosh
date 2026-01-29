from celery import Celery
import os

# Celery Configuration
# Redis is running locally on port 6379
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

app = Celery(
    "talabahamkor",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["services.sync_service", "services.grade_checker", "services.context_builder"]
)

# Optional: Configuration tuning
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Tashkent",
    enable_utc=True,
    worker_prefetch_multiplier=1, # One task per worker at a time for stability
    task_acks_late=True,
)

if __name__ == "__main__":
    app.start()
