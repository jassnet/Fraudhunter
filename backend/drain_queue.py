"""One-shot script to drain all queued jobs. Delete after use."""
import os, sys
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://postgres@localhost:5432/fraudchecker")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from fraud_checker.env import load_env
load_env()
from fraud_checker.services.jobs import process_queued_jobs

processed = process_queued_jobs(max_jobs=20)
print(f"Done: processed {processed} job(s)")
