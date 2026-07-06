import os


def has_key() -> bool:
    return bool(os.getenv('GEMINI_API_KEY'))
