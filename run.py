#!/usr/bin/env python3
"""FootieBuzz entry point — start the tweet stream and Dash dashboard."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Ensure project root is on sys.path when run as `python run.py`
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.dashboard import create_app
from config.settings import DEFAULT_KEYWORDS, TWITTER_BEARER_TOKEN
from src.twitter.stream import MatchTweetStream, start_demo_feed

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("footiebuzz")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FootieBuzz live sentiment analyzer")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Use simulated tweets (no Twitter API required)",
    )
    parser.add_argument(
        "--keywords",
        nargs="+",
        default=None,
        help="Hashtags/keywords to track (default: from .env or WorldCup,football)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Dash host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8050,
        help="Dash port (default: 8050)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run Dash in debug mode",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    keywords = args.keywords or DEFAULT_KEYWORDS

    if args.demo or not TWITTER_BEARER_TOKEN:
        if not args.demo and not TWITTER_BEARER_TOKEN:
            logger.warning(
                "No TWITTER_BEARER_TOKEN found — falling back to demo mode. "
                "Copy .env.example to .env and add your token for live tweets."
            )
        start_demo_feed(keywords)
    else:
        stream = MatchTweetStream(keywords=keywords)
        stream.start_background()

    app = create_app()
    logger.info("Dashboard → http://%s:%s", args.host, args.port)
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
