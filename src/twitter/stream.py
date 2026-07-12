from __future__ import annotations

import logging
import random
import threading
import time
from datetime import datetime, timedelta, timezone

from config.settings import DEFAULT_KEYWORDS
from src.analysis.sentiment import get_analyzer
from src.storage.buffer import MatchEvent, TweetRecord, tweet_buffer

logger = logging.getLogger(__name__)

# Argentina-focused demo tweets
ARGENTINA_SAMPLES: list[tuple[str, str | None]] = [
    ("Argentina are absolutely world class tonight!", None),
    ("The Albiceleste are on another level — what a team!", None),
    ("Argentina's defense is a disgrace, shocking performance.", None),
    ("Messi leads Argentina to a stunning comeback!", "goal"),
    ("Argentina fans erupting — this is their moment!", "goal"),
    ("Scaloni has Argentina playing beautiful football.", None),
    ("Argentina look tired, running out of steam.", None),
    ("GOOOAL! Argentina take the lead!", "goal"),
    ("The whole of Argentina is celebrating right now!", "goal"),
    ("Argentina bottled it again, same old story.", None),
]

# Mbappé-focused demo tweets
MBAPPE_SAMPLES: list[tuple[str, str | None]] = [
    ("Mbappé is unstoppable — best player on the pitch!", None),
    ("Kylian Mbappé with a rocket into the top corner!", "goal"),
    ("Mbappé was incredible tonight, pure class.", "goal"),
    ("Mbappé goes quiet in big games as always.", None),
    ("That Mbappé run was pure pace and power!", None),
    ("Mbappé penalty! France back in it!", "goal"),
    ("Mbappé is the future of football, what a talent.", None),
    ("Mbappé missed a sitter — France fans furious.", None),
    ("Mbappé vs the world and he's winning!", None),
    ("France win thanks to Mbappé's brilliance!", "goal"),
]

OTHER_SAMPLES: list[tuple[str, str | None]] = [
    ("What a goal! Absolutely brilliant finish!", "goal"),
    ("This is the biggest upset of the tournament!", "upset"),
    ("Neutral possession, nothing happening.", None),
    ("Best match of the World Cup so far!", None),
    ("Comeback of the century, unbelievable!", "upset"),
]


def _pick_sample() -> tuple[str, str | None]:
    roll = random.random()
    if roll < 0.45:
        return random.choice(ARGENTINA_SAMPLES)
    if roll < 0.90:
        return random.choice(MBAPPE_SAMPLES)
    return random.choice(OTHER_SAMPLES)


def seed_featured_demo_tweets() -> None:
    """Pre-load tweets so Argentina & Mbappé show data immediately."""
    analyzer = get_analyzer()
    now = datetime.now(timezone.utc)
    seeds = [
        ("Argentina are on fire! The Albiceleste look unstoppable.", None, 28),
        ("Messi magic for Argentina — this is why he's the GOAT!", "goal", 24),
        ("Argentina's midfield is controlling everything tonight.", None, 20),
        ("Mbappé scores! France level it up!", "goal", 18),
        ("Mbappé is running rings around this defense.", None, 14),
        ("Kylian Mbappé — what a player, absolutely brilliant!", None, 10),
        ("Argentina fans going wild after that goal!", "goal", 6),
        ("Mbappé penalty! The crowd goes crazy!", "goal", 3),
    ]

    for text, moment, mins_ago in seeds:
        created_at = now - timedelta(minutes=mins_ago, seconds=random.randint(0, 45))
        label, score = analyzer.analyze(text)

        tweet_buffer.add_tweet(
            TweetRecord(
                tweet_id=str(time.time_ns()) + str(mins_ago),
                text=text,
                author=random.choice(["fan_101", "footie_talk", "match_day"]),
                created_at=created_at,
                label=label,
                score=score,
                keywords_matched=["WorldCup"],
            )
        )

        if moment:
            tweet_buffer.add_event(
                MatchEvent(
                    label="Goal" if moment == "goal" else "Upset",
                    timestamp=created_at,
                    description=text,
                )
            )

    logger.info("Seeded %d featured demo tweets (Argentina & Mbappé)", len(seeds))


def start_demo_feed(keywords: list[str] | None = None) -> threading.Thread:
    """Simulate tweets — no Twitter API or tweepy required."""
    seed_featured_demo_tweets()
    analyzer = get_analyzer()

    def _run() -> None:
        kws = keywords or DEFAULT_KEYWORDS
        authors = ["fan_101", "footie_talk", "match_day", "ultras_zone", "tactics_guru"]
        while True:
            text, moment = _pick_sample()
            now = datetime.now(timezone.utc)
            label, score = analyzer.analyze(text)

            tweet_buffer.add_tweet(
                TweetRecord(
                    tweet_id=str(time.time_ns()),
                    text=text,
                    author=random.choice(authors),
                    created_at=now,
                    label=label,
                    score=score,
                    keywords_matched=kws[:1],
                )
            )

            if moment:
                tweet_buffer.add_event(
                    MatchEvent(
                        label="Goal" if moment == "goal" else "Upset",
                        timestamp=now,
                        description=text,
                    )
                )

            time.sleep(random.uniform(1.5, 3.5))

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    logger.info("Demo tweet feed started — featuring Argentina & Mbappé")
    return thread
