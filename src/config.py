"""
Configuration for IntroAgent.
Gemini-only setup for CrewAI 1.9+.
Includes retry logic for free-tier rate limits.
"""

import os
import time
from dotenv import load_dotenv

load_dotenv()

# --- Gemini ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Retry settings for rate limits
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 45  # Gemini free tier suggests 43s

def get_llm_string() -> str:
    """
    Return the Gemini LLM model string for CrewAI agents.
    Format: 'gemini/model-name' (native provider in CrewAI 1.9+)
    """
    if not GOOGLE_API_KEY:
        raise ValueError(
            "GOOGLE_API_KEY is not set. "
            "Please add it to your .env file.\n"
            "Get one free at: https://aistudio.google.com/apikey"
        )
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
    return f"gemini/{GEMINI_MODEL}"