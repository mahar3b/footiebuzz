import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")

HF_SENTIMENT_MODEL = os.getenv(
    "HF_SENTIMENT_MODEL",
    "cardiffnlp/twitter-roberta-base-sentiment-latest",
)

DEFAULT_KEYWORDS = [
    kw.strip()
    for kw in os.getenv("MATCH_KEYWORDS", "WorldCup,football").split(",")
    if kw.strip()
]

# Rolling window for live charts (minutes)
SENTIMENT_WINDOW_MINUTES = int(os.getenv("SENTIMENT_WINDOW_MINUTES", "30"))

# Max tweets kept in memory
MAX_TWEETS_BUFFER = int(os.getenv("MAX_TWEETS_BUFFER", "5000"))

# Dash refresh interval (milliseconds)
DASH_REFRESH_MS = int(os.getenv("DASH_REFRESH_MS", "3000"))
