from __future__ import annotations

from config.entities import DEMO_ENTITIES, DEMO_FEATURED, get_entity
from config.settings import DEFAULT_KEYWORDS, SENTIMENT_WINDOW_MINUTES
from src.entities.matcher import (
    build_entity_breakdown,
    filter_tweets,
    sentiment_timeline_for_tweets,
)
from src.events.tracker import log_manual_event
from src.storage.buffer import tweet_buffer

LABEL_TO_SCORE = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}


def _dt_iso(dt) -> str:
    return dt.isoformat()


def list_entities() -> list[dict]:
    return [
        {
            "id": e["id"],
            "name": e["name"],
            "type": e["type"],
            "icon": e["icon"],
            "color": e["color"],
        }
        for e in DEMO_ENTITIES
    ]


def build_dashboard_state(
    minutes: int | None = None,
    tweet_limit: int = 12,
    entity_id: str | None = None,
) -> dict:
    window = minutes or SENTIMENT_WINDOW_MINUTES
    all_tweets = tweet_buffer.tweets_since(window)
    entity_breakdown = build_entity_breakdown(all_tweets)

    filtered = filter_tweets(all_tweets, entity_id)
    counts = {"positive": 0, "neutral": 0, "negative": 0}
    for tweet in filtered:
        counts[tweet.label] += 1
    total = len(filtered)

    avg_sentiment = 0.0
    if filtered:
        avg_sentiment = round(
            sum(LABEL_TO_SCORE[t.label] for t in filtered) / len(filtered),
            3,
        )

    timeline = [
        {
            "timestamp": _dt_iso(p["timestamp"]),
            "avg_sentiment": p["avg_sentiment"],
            "volume": p["volume"],
        }
        for p in sentiment_timeline_for_tweets(filtered)
    ]

    events = [
        {
            "label": e.label,
            "description": e.description,
            "timestamp": _dt_iso(e.timestamp),
        }
        for e in tweet_buffer.all_events()
    ]

    shifts = [
        {
            "event": s["event"],
            "description": s["description"],
            "timestamp": _dt_iso(s["timestamp"]),
            "before": s["before"],
            "after": s["after"],
            "delta": s["delta"],
            "tweets_before": s["tweets_before"],
            "tweets_after": s["tweets_after"],
        }
        for s in tweet_buffer.sentiment_shift_around_events(window)
    ]

    recent = filter_tweets(tweet_buffer.recent_tweets(50), entity_id)
    tweets = [
        {
            "tweet_id": t.tweet_id,
            "text": t.text,
            "author": t.author,
            "created_at": _dt_iso(t.created_at),
            "label": t.label,
            "score": t.score,
        }
        for t in reversed(recent[-tweet_limit:])
    ]

    active_entity = None
    if entity_id and entity_id != "all":
        ent = get_entity(entity_id)
        if ent:
            active_entity = {
                "id": ent["id"],
                "name": ent["name"],
                "type": ent["type"],
                "icon": ent["icon"],
                "color": ent["color"],
            }

    featured = [
        e for e in entity_breakdown if e["id"] in DEMO_FEATURED
    ]

    return {
        "stats": {
            "total_processed": tweet_buffer.total_processed,
            "window_total": total,
            "positive": counts["positive"],
            "neutral": counts["neutral"],
            "negative": counts["negative"],
            "avg_sentiment": avg_sentiment,
            "keywords": DEFAULT_KEYWORDS,
        },
        "active_entity": active_entity,
        "featured": featured,
        "entities": entity_breakdown,
        "timeline": timeline,
        "events": events,
        "shifts": shifts,
        "tweets": tweets,
    }


def create_event(label: str, description: str = "") -> dict:
    event = log_manual_event(label, description)
    return {
        "label": event.label,
        "description": event.description,
        "timestamp": _dt_iso(event.timestamp),
    }
