from __future__ import annotations

from datetime import datetime, timezone

from src.storage.buffer import MatchEvent, tweet_buffer


def log_manual_event(label: str, description: str = "") -> MatchEvent:
    """Log a goal, upset, or custom moment from the dashboard."""
    event = MatchEvent(
        label=label.strip() or "Event",
        timestamp=datetime.now(timezone.utc),
        description=description.strip(),
    )
    tweet_buffer.add_event(event)
    return event
