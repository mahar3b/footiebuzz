from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Deque, Iterable, Literal

SentimentLabel = Literal["positive", "neutral", "negative"]


@dataclass
class TweetRecord:
    tweet_id: str
    text: str
    author: str
    created_at: datetime
    label: SentimentLabel
    score: float
    keywords_matched: list[str] = field(default_factory=list)


@dataclass
class MatchEvent:
    label: str
    timestamp: datetime
    description: str = ""


class TweetBuffer:
    """Thread-safe in-memory store shared by the stream and Dash app."""

    def __init__(self, max_tweets: int = 5000) -> None:
        self._tweets: Deque[TweetRecord] = deque(maxlen=max_tweets)
        self._events: Deque[MatchEvent] = deque(maxlen=200)
        self._lock = threading.Lock()
        self._total_processed = 0

    def add_tweet(self, record: TweetRecord) -> None:
        with self._lock:
            self._tweets.append(record)
            self._total_processed += 1

    def add_event(self, event: MatchEvent) -> None:
        with self._lock:
            self._events.append(event)

    def tweets_since(self, minutes: int) -> list[TweetRecord]:
        cutoff = datetime.now(timezone.utc).timestamp() - minutes * 60
        with self._lock:
            return [
                t
                for t in self._tweets
                if t.created_at.timestamp() >= cutoff
            ]

    def all_events(self) -> list[MatchEvent]:
        with self._lock:
            return list(self._events)

    @property
    def total_processed(self) -> int:
        with self._lock:
            return self._total_processed

    def recent_tweets(self, limit: int = 20) -> list[TweetRecord]:
        with self._lock:
            return list(self._tweets)[-limit:]

    def sentiment_counts(self, minutes: int) -> dict[str, int]:
        counts = {"positive": 0, "neutral": 0, "negative": 0}
        for tweet in self.tweets_since(minutes):
            counts[tweet.label] += 1
        return counts

    def sentiment_timeline(
        self, minutes: int, bucket_seconds: int = 60
    ) -> list[dict]:
        """Aggregate sentiment into time buckets for line charts."""
        tweets = self.tweets_since(minutes)
        if not tweets:
            return []

        label_to_score = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
        buckets: dict[int, list[float]] = {}

        for tweet in tweets:
            bucket = int(tweet.created_at.timestamp() // bucket_seconds)
            buckets.setdefault(bucket, []).append(label_to_score[tweet.label])

        timeline = []
        for bucket_ts in sorted(buckets):
            scores = buckets[bucket_ts]
            avg = sum(scores) / len(scores)
            timeline.append(
                {
                    "timestamp": datetime.fromtimestamp(
                        bucket_ts * bucket_seconds, tz=timezone.utc
                    ),
                    "avg_sentiment": round(avg, 3),
                    "volume": len(scores),
                }
            )
        return timeline

    def sentiment_shift_around_events(
        self, minutes: int, window_seconds: int = 120
    ) -> list[dict]:
        """Compare avg sentiment before vs after each logged event."""
        tweets = self.tweets_since(minutes)
        events = self.all_events()
        if not tweets or not events:
            return []

        label_to_score = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
        shifts = []

        for event in events:
            event_ts = event.timestamp.timestamp()
            before, after = [], []

            for tweet in tweets:
                delta = tweet.created_at.timestamp() - event_ts
                score = label_to_score[tweet.label]
                if -window_seconds <= delta < 0:
                    before.append(score)
                elif 0 <= delta <= window_seconds:
                    after.append(score)

            if before and after:
                before_avg = sum(before) / len(before)
                after_avg = sum(after) / len(after)
                shifts.append(
                    {
                        "event": event.label,
                        "description": event.description,
                        "timestamp": event.timestamp,
                        "before": round(before_avg, 3),
                        "after": round(after_avg, 3),
                        "delta": round(after_avg - before_avg, 3),
                        "tweets_before": len(before),
                        "tweets_after": len(after),
                    }
                )
        return shifts


def _default_buffer() -> TweetBuffer:
    try:
        from config.settings import MAX_TWEETS_BUFFER

        return TweetBuffer(max_tweets=MAX_TWEETS_BUFFER)
    except ImportError:
        return TweetBuffer()


tweet_buffer = _default_buffer()
