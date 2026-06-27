import os
from dotenv import load_dotenv

load_dotenv()

# GEMINI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# LINE
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

# =================================== #
# Verification zone
# =================================== #

if GEMINI_API_KEY is None: raise ValueError("GEMINI_API_KEY is not found")
if LINE_CHANNEL_SECRET is None: raise ValueError("LINE_CHANNEL_SECRET is not found")
if LINE_CHANNEL_ACCESS_TOKEN is None: raise ValueError("LINE_CHANNEL_ACCESS_TOKEN is not found")
