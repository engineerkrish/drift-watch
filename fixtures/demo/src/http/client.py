import os

def retries():
    return os.getenv("MAX_RETRY_COUNT")

def endpoint():
    return os.environ["API_BASE_URL"]
