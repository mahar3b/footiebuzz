#!/usr/bin/env python3
"""FootieBuzz — start tweet stream + FastAPI server."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import DEFAULT_KEYWORDS, TWITTER_BEARER_TOKEN
from src.twitter.stream import start_demo_feed

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
        help="Simulated tweets (default — no Twitter API needed)",
    )
    parser.add_argument(
        "--ml",
        action="store_true",
        help="Use Hugging Face ML sentiment (requires pip install -r requirements.txt)",
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
        help="Server host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Server port (default: 8000)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Auto-reload on code changes (dev only)",
    )
    parser.add_argument(
        "--dash",
        action="store_true",
        help="Use legacy Plotly Dash UI instead of the new frontend",
    )
    return parser.parse_args()


def start_stream(demo: bool, keywords: list[str]) -> None:
    if demo or not TWITTER_BEARER_TOKEN:
        if not demo and not TWITTER_BEARER_TOKEN:
            logger.warning(
                "No TWITTER_BEARER_TOKEN — running in demo mode. "
                "Add your token to .env for live tweets."
            )
        start_demo_feed(keywords)
    else:
        try:
            from src.twitter.live_stream import MatchTweetStream
        except ImportError:
            logger.error(
                "Live Twitter mode needs tweepy. Run: pip install tweepy  (or pip install -r requirements.txt)"
            )
            sys.exit(1)
        stream = MatchTweetStream(keywords=keywords)
        stream.start_background()


def main() -> None:
    args = parse_args()

    # Default to demo mode unless user has a Twitter token and didn't ask for demo
    demo = args.demo or not TWITTER_BEARER_TOKEN

    if args.ml:
        os.environ["FOOTIEBUZZ_ML"] = "1"
    else:
        os.environ.pop("FOOTIEBUZZ_ML", None)

    keywords = args.keywords or DEFAULT_KEYWORDS
    start_stream(demo, keywords)

    if args.dash:
        from app.dashboard import create_app

        app = create_app()
        logger.info("Legacy Dash UI → http://%s:%s", args.host, args.port)
        app.run(host=args.host, port=args.port, debug=args.reload)
        return

    import uvicorn

    if args.reload:
        uvicorn.run(
            "backend.main:create_app",
            factory=True,
            host=args.host,
            port=args.port,
            reload=True,
            log_level="info",
        )
        return

    from backend.main import create_app

    app = create_app()
    logger.info("FootieBuzz → http://%s:%s", args.host, args.port)
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
