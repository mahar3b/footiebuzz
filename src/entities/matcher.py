from __future__ import annotations

from config.entities import DEMO_ENTITIES, get_entity
from src.storage.buffer import TweetRecord

LABEL_TO_SCORE = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}


def tweet_mentions_entity(text: str, entity: dict) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in entity["keywords"])


def filter_tweets(
    tweets: list[TweetRecord], entity_id: str | None
) -> list[TweetRecord]:
    if not entity_id or entity_id == "all":
        return tweets
    entity = get_entity(entity_id)
    if not entity:
        return tweets
    return [t for t in tweets if tweet_mentions_entity(t.text, entity)]


def _stats_from_tweets(tweets: list[TweetRecord]) -> dict:
    counts = {"positive": 0, "neutral": 0, "negative": 0}
    for t in tweets:
        counts[t.label] += 1

    total = len(tweets)
    avg = 0.0
    if total:
        avg = round(
            sum(LABEL_TO_SCORE[t.label] for t in tweets) / total,
            3,
        )

    return {
        "mention_count": total,
        "positive": counts["positive"],
        "neutral": counts["neutral"],
        "negative": counts["negative"],
        "avg_sentiment": avg,
    }


def build_entity_breakdown(tweets: list[TweetRecord]) -> list[dict]:
    results = []
    for entity in DEMO_ENTITIES:
        matched = [t for t in tweets if tweet_mentions_entity(t.text, entity)]
        stats = _stats_from_tweets(matched)
        results.append(
            {
                "id": entity["id"],
                "name": entity["name"],
                "type": entity["type"],
                "icon": entity["icon"],
                "color": entity["color"],
                **stats,
            }
        )
    return results


def sentiment_timeline_for_tweets(
    tweets: list[TweetRecord], bucket_seconds: int = 60
) -> list[dict]:
    if not tweets:
        return []

    from datetime import datetime, timezone

    buckets: dict[int, list[float]] = {}
    for tweet in tweets:
        bucket = int(tweet.created_at.timestamp() // bucket_seconds)
        buckets.setdefault(bucket, []).append(LABEL_TO_SCORE[tweet.label])

    timeline = []
    for bucket_ts in sorted(buckets):
        scores = buckets[bucket_ts]
        timeline.append(
            {
                "timestamp": datetime.fromtimestamp(
                    bucket_ts * bucket_seconds, tz=timezone.utc
                ),
                "avg_sentiment": round(sum(scores) / len(scores), 3),
                "volume": len(scores),
            }
        )
    return timeline
