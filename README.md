# FootieBuzz

Real-time sentiment analyzer for live match tweets. Streams Twitter (or a demo feed), scores each tweet with a Hugging Face model, and visualizes how public opinion shifts around goals and upsets.

## Architecture

```
Twitter Stream (Tweepy)  →  Sentiment (Hugging Face)  →  In-memory buffer  →  Dash (Plotly)
                                    ↓
                          Auto-detect goal/upset keywords
                                    ↓
                          Manual event logging from UI
```

1. **Tweepy** opens a filtered stream for match hashtags/keywords.
2. **Hugging Face** (`cardiffnlp/twitter-roberta-base-sentiment-latest`) labels each tweet positive / neutral / negative.
3. **TweetBuffer** stores tweets and events in a thread-safe deque shared with the dashboard.
4. **Plotly Dash** refreshes every few seconds with timeline, distribution, and before/after shift charts.

## Quick start

### 1. Install dependencies

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

First run downloads the Hugging Face model (~500 MB).

### 2. Configure Twitter (optional)

Copy `.env.example` to `.env` and add your [Twitter API v2 Bearer Token](https://developer.twitter.com/):

```env
TWITTER_BEARER_TOKEN=your_token_here
MATCH_KEYWORDS=WorldCup,ARG,FRA
```

Without a token, the app runs in **demo mode** with simulated tweets.

### 3. Run

```bash
# Demo mode (no API key)
python run.py --demo

# Live Twitter stream
python run.py --keywords WorldCup Messi

# Custom host/port
python run.py --demo --port 8050
```

Open **http://127.0.0.1:8050**

## Project layout

```
footiebuzz/
├── run.py                      # Entry point
├── requirements.txt
├── .env.example
├── config/settings.py          # Env-based config
├── src/
│   ├── twitter/stream.py       # Tweepy stream + demo feed
│   ├── analysis/sentiment.py   # Hugging Face pipeline
│   ├── storage/buffer.py       # Thread-safe tweet/event store
│   └── events/tracker.py       # Manual goal/upset logging
└── app/dashboard.py            # Plotly Dash UI
```

## Dashboard panels

| Panel | What it shows |
|-------|----------------|
| Sentiment Over Time | Rolling avg sentiment + tweet volume; vertical lines for goals/upsets |
| Distribution | Pie chart of positive / neutral / negative in the window |
| Before vs After | Avg sentiment ±2 min around each logged event |
| Recent Tweets | Latest scored tweets with color-coded sentiment |
| Log Event | Manually mark a goal, upset, or red card (synced to charts) |

## How sentiment shifts are measured

For each event (auto-detected from tweet text or logged manually), the app compares average sentiment in the **2 minutes before** vs **2 minutes after** the event timestamp. A positive delta means the crowd mood improved; negative means it soured.

Auto-detection looks for keywords like `goal`, `scored`, `upset`, `shock`, `comeback` in incoming tweets.

## Tips for live matches

- Use specific hashtags: team names, `#WorldCup`, match tags (`#ARGFRA`).
- Log goals manually from the UI for precise timing — tweet-based detection can lag by 30–60 seconds.
- Increase `SENTIMENT_WINDOW_MINUTES` in `.env` for longer matches.
- Twitter filtered stream has rate limits; for high-volume finals, consider sampling every Nth tweet in `stream.py`.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TWITTER_BEARER_TOKEN` | — | Twitter API v2 bearer token |
| `MATCH_KEYWORDS` | `WorldCup,football` | Comma-separated track terms |
| `HF_SENTIMENT_MODEL` | `cardiffnlp/twitter-roberta-base-sentiment-latest` | HF model ID |
| `SENTIMENT_WINDOW_MINUTES` | `30` | Chart rolling window |
| `DASH_REFRESH_MS` | `3000` | Dashboard refresh interval |

## License

MIT
