import os

PORT = os.environ.get("PORT", "3000")
DEBUG = os.getenv("DEBUG", "false")
DATABASE_URL = os.environ["DATABASE_URL"]
