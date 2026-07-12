# FootieBuzz

Real-time sentiment analyzer for live match tweets. Streams Twitter (or a demo feed), scores each tweet with Hugging Face, and visualizes how public opinion shifts around goals and upsets.

## Quick start

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Demo mode (no Twitter API key needed)
python run.py --demo

# Open in browser
# http://127.0.0.1:8000
```

## Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI + WebSocket |
| Frontend | HTML / CSS / Chart.js |
| Stream | Tweepy |
| Sentiment | Hugging Face Transformers |

## Commands

```powershell
python run.py --demo                  # simulated tweets
python run.py --keywords WorldCup     # live Twitter stream
python run.py --port 8080             # custom port
python run.py --dash                  # legacy Plotly Dash UI
```

API docs available at **http://127.0.0.1:8000/docs**

## Project layout

```
footiebuzz/
├── run.py                  # Entry point
├── backend/                # FastAPI REST + WebSocket
├── frontend/               # Static UI (served at /)
├── src/                    # Stream, sentiment, buffer
└── config/settings.py
```

## Environment

Copy `.env.example` to `.env`:

```env
TWITTER_BEARER_TOKEN=your_token_here
MATCH_KEYWORDS=WorldCup,ARG,FRA
```

## License

MIT
