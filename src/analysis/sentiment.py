from __future__ import annotations

import logging
import re
from functools import lru_cache

from transformers import pipeline

from config.settings import HF_SENTIMENT_MODEL
from src.storage.buffer import SentimentLabel

logger = logging.getLogger(__name__)

# Map Hugging Face label variants to our three buckets
LABEL_MAP = {
    "positive": "positive",
    "label_2": "positive",
    "pos": "positive",
    "neutral": "neutral",
    "label_1": "neutral",
    "neu": "neutral",
    "negative": "negative",
    "label_0": "negative",
    "neg": "negative",
}

GOAL_PATTERNS = re.compile(
    r"\b(goal{1,2}|gooo+a+l|scored?|equalizer|equaliser|penalty|own goal)\b",
    re.IGNORECASE,
)
UPSET_PATTERNS = re.compile(
    r"\b(upset|shock|stunner|comeback|underdog|miracle|unbelievable)\b",
    re.IGNORECASE,
)


@lru_cache(maxsize=1)
def get_sentiment_pipeline():
    logger.info("Loading sentiment model: %s", HF_SENTIMENT_MODEL)
    return pipeline(
        "sentiment-analysis",
        model=HF_SENTIMENT_MODEL,
        truncation=True,
        max_length=128,
    )


class SentimentAnalyzer:
    def __init__(self) -> None:
        self._pipe = get_sentiment_pipeline()

    def analyze(self, text: str) -> tuple[SentimentLabel, float]:
        cleaned = re.sub(r"http\S+", "", text).strip()
        if not cleaned:
            return "neutral", 0.0

        result = self._pipe(cleaned[:512])[0]
        raw_label = result["label"].lower()
        label: SentimentLabel = LABEL_MAP.get(raw_label, "neutral")
        return label, float(result["score"])

    @staticmethod
    def detect_match_moment(text: str) -> str | None:
        if GOAL_PATTERNS.search(text):
            return "goal"
        if UPSET_PATTERNS.search(text):
            return "upset"
        return None
