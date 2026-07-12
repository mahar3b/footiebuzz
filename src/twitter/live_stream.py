from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone

import tweepy

from config.settings import DEFAULT_KEYWORDS, TWITTER_BEARER_TOKEN
from src.analysis.sentiment import get_analyzer
from src.storage.buffer import MatchEvent, TweetRecord, tweet_buffer

logger = logging.getLogger(__name__)


class MatchTweetStream(tweepy.StreamingClient):
    """Filtered Twitter stream — requires: pip install tweepy"""

    def __init__(self, keywords: list[str] | None = None) -> None:
        if not TWITTER_BEARER_TOKEN:
            raise ValueError(
                "TWITTER_BEARER_TOKEN is missing. Copy .env.example to .env and add your token."
            )

        super().__init__(bearer_token=TWITTER_BEARER_TOKEN, wait_on_rate_limit=True)
        self.keywords = keywords or DEFAULT_KEYWORDS
        self.analyzer = get_analyzer()
        self._rules_set = False

    def _build_rule(self) -> str:
        parts = []
        for kw in self.keywords:
            token = kw.lstrip("#")
            parts.append(f"#{token}")
            parts.append(token)
        return " OR ".join(dict.fromkeys(parts))

    def setup_rules(self) -> None:
        existing = self.get_rules()
        if existing.data:
            rule_ids = [rule.id for rule in existing.data]
            self.delete_rules(rule_ids)

        rule = self._build_rule()
        self.add_rules(tweepy.StreamRule(value=rule, tag="footiebuzz-match"))
        self._rules_set = True
        logger.info("Stream rule active: %s", rule)

    def on_tweet(self, tweet: tweepy.Tweet) -> None:
        text = tweet.text or ""
        author = tweet.author_id or "unknown"
        created_at = tweet.created_at or datetime.now(timezone.utc)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        label, score = self.analyzer.analyze(text)
        matched = [kw for kw in self.keywords if kw.lower() in text.lower()]

        tweet_buffer.add_tweet(
            TweetRecord(
                tweet_id=str(tweet.id),
                text=text,
                author=str(author),
                created_at=created_at,
                label=label,
                score=score,
                keywords_matched=matched,
            )
        )

        moment = self.analyzer.detect_match_moment(text)
        if moment:
            event_label = "Goal" if moment == "goal" else "Upset"
            tweet_buffer.add_event(
                MatchEvent(
                    label=event_label,
                    timestamp=created_at,
                    description=text[:120],
                )
            )
            logger.info("Detected %s moment from tweet %s", event_label, tweet.id)

    def on_errors(self, errors) -> bool:
        logger.error("Stream errors: %s", errors)
        return True

    def on_connection_error(self) -> None:
        logger.warning("Twitter connection error — stream will retry")

    def on_request_error(self, status_code: int) -> bool:
        logger.error("Twitter request error: %s", status_code)
        return status_code != 403

    def start_background(self) -> threading.Thread:
        if not self._rules_set:
            self.setup_rules()

        thread = threading.Thread(target=self.filter, daemon=True)
        thread.start()
        logger.info("Twitter stream started in background thread")
        return thread
