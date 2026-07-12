from __future__ import annotations

import logging
import os
import re
from functools import lru_cache

from src.storage.buffer import SentimentLabel

logger = logging.getLogger(__name__)

GOAL_PATTERNS = re.compile(
    r"\b(goal{1,2}|gooo+a+l|scored?|equalizer|equaliser|penalty|own goal)\b",
    re.IGNORECASE,
)
UPSET_PATTERNS = re.compile(
    r"\b(upset|shock|stunner|comeback|underdog|miracle|unbelievable)\b",
    re.IGNORECASE,
)

POSITIVE_WORDS = re.compile(
    r"\b(brilliant|amazing|best|love|great|wow|incredible|yes|win|winner|"
    r"beautiful|perfect|fantastic|legend|hero|quality|clutch)\b",
    re.IGNORECASE,
)
NEGATIVE_WORDS = re.compile(
    r"\b(terrible|awful|bad|hate|worst|lose|disgrace|rubbish|trash|"
    r"shocking|pathetic|disaster|foul|robbed|useless|embarrassing)\b",
    re.IGNORECASE,
)

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


def use_ml_sentiment() -> bool:
    return os.getenv("FOOTIEBUZZ_ML", "").lower() in ("1", "true", "yes")


class LiteSentimentAnalyzer:
    """Fast keyword-based sentiment — no ML downloads required."""

    def analyze(self, text: str) -> tuple[SentimentLabel, float]:
        cleaned = re.sub(r"http\S+", "", text).strip()
        if not cleaned:
            return "neutral", 0.5

        pos = len(POSITIVE_WORDS.findall(cleaned))
        neg = len(NEGATIVE_WORDS.findall(cleaned))

        if pos > neg:
            return "positive", min(0.95, 0.6 + pos * 0.1)
        if neg > pos:
            return "negative", min(0.95, 0.6 + neg * 0.1)
        return "neutral", 0.55

    @staticmethod
    def detect_match_moment(text: str) -> str | None:
        if GOAL_PATTERNS.search(text):
            return "goal"
        if UPSET_PATTERNS.search(text):
            return "upset"
        return None


@lru_cache(maxsize=1)
def _get_hf_pipeline():
    from transformers import pipeline

    from config.settings import HF_SENTIMENT_MODEL

    logger.info("Loading ML model: %s (~500 MB first run)", HF_SENTIMENT_MODEL)
    return pipeline(
        "sentiment-analysis",
        model=HF_SENTIMENT_MODEL,
        truncation=True,
        max_length=128,
    )


class MLSentimentAnalyzer:
    """Hugging Face RoBERTa — accurate but needs torch + ~500 MB download."""

    def __init__(self) -> None:
        self._pipe = _get_hf_pipeline()

    def analyze(self, text: str) -> tuple[SentimentLabel, float]:
        cleaned = re.sub(r"http\S+", "", text).strip()
        if not cleaned:
            return "neutral", 0.0

        result = self._pipe(cleaned[:512])[0]
        raw_label = result["label"].lower()
        label: SentimentLabel = LABEL_MAP.get(raw_label, "neutral")
        return label, float(result["score"])

    detect_match_moment = LiteSentimentAnalyzer.detect_match_moment


@lru_cache(maxsize=1)
def get_analyzer() -> LiteSentimentAnalyzer | MLSentimentAnalyzer:
    if use_ml_sentiment():
        try:
            return MLSentimentAnalyzer()
        except ImportError:
            logger.warning(
                "FOOTIEBUZZ_ML=1 but transformers/torch not installed — using lite mode. "
                "Run: pip install -r requirements.txt"
            )
    logger.info("Using lite sentiment (keyword-based, no ML download)")
    return LiteSentimentAnalyzer()


# Backwards-compatible alias used by stream.py
SentimentAnalyzer = LiteSentimentAnalyzer  # default class; stream uses get_analyzer()
