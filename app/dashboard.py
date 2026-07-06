from __future__ import annotations

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dash_table, dcc, html
from plotly.subplots import make_subplots

from config.settings import DASH_REFRESH_MS, SENTIMENT_WINDOW_MINUTES
from src.events.tracker import log_manual_event
from src.storage.buffer import tweet_buffer


def _empty_figure(title: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        title=title,
        template="plotly_dark",
        paper_bgcolor="#0f1117",
        plot_bgcolor="#0f1117",
        font=dict(color="#e8e8e8"),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        annotations=[
            dict(
                text="Waiting for tweets…",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=16, color="#888"),
            )
        ],
    )
    return fig


def build_sentiment_timeline_figure(minutes: int) -> go.Figure:
    timeline = tweet_buffer.sentiment_timeline(minutes)
    events = tweet_buffer.all_events()

    if not timeline:
        return _empty_figure("Sentiment Over Time")

    df = pd.DataFrame(timeline)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df["avg_sentiment"],
            mode="lines+markers",
            name="Avg sentiment",
            line=dict(color="#00d4aa", width=2),
            fill="tozeroy",
            fillcolor="rgba(0, 212, 170, 0.15)",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Bar(
            x=df["timestamp"],
            y=df["volume"],
            name="Tweet volume",
            marker_color="rgba(99, 110, 250, 0.45)",
            opacity=0.7,
        ),
        secondary_y=True,
    )

    for event in events:
        color = "#ff6b6b" if event.label.lower() == "goal" else "#ffd93d"
        fig.add_vline(
            x=event.timestamp,
            line_width=1,
            line_dash="dash",
            line_color=color,
        )
        fig.add_annotation(
            x=event.timestamp,
            y=1,
            yref="paper",
            text=event.label,
            showarrow=False,
            font=dict(size=10, color=color),
            bgcolor="rgba(0,0,0,0.6)",
        )

    fig.update_layout(
        title="Sentiment Over Time",
        template="plotly_dark",
        paper_bgcolor="#0f1117",
        plot_bgcolor="#0f1117",
        font=dict(color="#e8e8e8"),
        legend=dict(orientation="h", y=1.12),
        margin=dict(t=60, b=40),
        hovermode="x unified",
    )
    fig.update_yaxes(
        title_text="Sentiment (-1 neg → +1 pos)",
        range=[-1.05, 1.05],
        secondary_y=False,
    )
    fig.update_yaxes(title_text="Tweets / min", secondary_y=True)
    return fig


def build_distribution_figure(minutes: int) -> go.Figure:
    counts = tweet_buffer.sentiment_counts(minutes)
    if sum(counts.values()) == 0:
        return _empty_figure("Sentiment Distribution")

    colors = {"positive": "#00d4aa", "neutral": "#6c7a89", "negative": "#ff6b6b"}
    labels = list(counts.keys())
    values = [counts[k] for k in labels]

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.45,
            marker=dict(colors=[colors[l] for l in labels]),
            textinfo="label+percent",
        )
    )
    fig.update_layout(
        title="Sentiment Distribution",
        template="plotly_dark",
        paper_bgcolor="#0f1117",
        plot_bgcolor="#0f1117",
        font=dict(color="#e8e8e8"),
        margin=dict(t=60, b=20),
    )
    return fig


def build_shift_figure(minutes: int) -> go.Figure:
    shifts = tweet_buffer.sentiment_shift_around_events(minutes)
    if not shifts:
        return _empty_figure("Sentiment Shift Around Events")

    df = pd.DataFrame(shifts)
    x_labels = [
        f"{row['event']}<br>{row['timestamp'].strftime('%H:%M')}"
        for _, row in df.iterrows()
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Before",
            x=x_labels,
            y=df["before"],
            marker_color="#6c7a89",
        )
    )
    fig.add_trace(
        go.Bar(
            name="After",
            x=x_labels,
            y=df["after"],
            marker_color="#00d4aa",
        )
    )
    fig.add_trace(
        go.Scatter(
            name="Delta",
            x=x_labels,
            y=df["delta"],
            mode="markers+text",
            text=[f"{d:+.2f}" for d in df["delta"]],
            textposition="top center",
            marker=dict(color="#ffd93d", size=12),
        )
    )
    fig.update_layout(
        title="Sentiment Before vs After Goals / Upsets (±2 min)",
        template="plotly_dark",
        barmode="group",
        paper_bgcolor="#0f1117",
        plot_bgcolor="#0f1117",
        font=dict(color="#e8e8e8"),
        yaxis=dict(title="Avg sentiment", range=[-1.05, 1.05]),
        margin=dict(t=60, b=40),
        legend=dict(orientation="h", y=1.12),
    )
    return fig


def create_app() -> Dash:
    app = Dash(
        __name__,
        external_stylesheets=[dbc.themes.CYBORG],
        title="FootieBuzz — Live Sentiment",
        suppress_callback_exceptions=True,
    )

    app.layout = dbc.Container(
        [
            dbc.Row(
                dbc.Col(
                    html.Div(
                        [
                            html.H1("FootieBuzz", className="mb-0"),
                            html.P(
                                "Real-time match sentiment from live tweets",
                                className="text-muted",
                            ),
                        ]
                    ),
                    width=8,
                ),
                dbc.Col(
                    html.Div(id="stats-bar", className="text-end pt-2"),
                    width=4,
                ),
            ),
            html.Hr(),
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Graph(id="timeline-chart", config={"displayModeBar": False}),
                        md=8,
                    ),
                    dbc.Col(
                        dcc.Graph(
                            id="distribution-chart", config={"displayModeBar": False}
                        ),
                        md=4,
                    ),
                ],
                className="mb-3",
            ),
            dbc.Row(
                dbc.Col(
                    dcc.Graph(id="shift-chart", config={"displayModeBar": False}),
                    width=12,
                ),
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H5("Log a match moment"),
                            dbc.InputGroup(
                                [
                                    dbc.Select(
                                        id="event-type",
                                        options=[
                                            {"label": "Goal", "value": "Goal"},
                                            {"label": "Upset", "value": "Upset"},
                                            {"label": "Red Card", "value": "Red Card"},
                                            {"label": "Custom", "value": "Custom"},
                                        ],
                                        value="Goal",
                                    ),
                                    dbc.Input(
                                        id="event-description",
                                        placeholder="e.g. Messi 78' — Argentina 2-1",
                                    ),
                                    dbc.Button(
                                        "Add Event",
                                        id="add-event-btn",
                                        color="success",
                                    ),
                                ],
                                className="mb-2",
                            ),
                            html.Div(id="event-feedback", className="text-success small"),
                        ],
                        md=5,
                    ),
                    dbc.Col(
                        [
                            html.H5("Recent tweets"),
                            dash_table.DataTable(
                                id="recent-tweets-table",
                                columns=[
                                    {"name": "Time", "id": "time"},
                                    {"name": "Sentiment", "id": "sentiment"},
                                    {"name": "Tweet", "id": "text"},
                                ],
                                style_table={"overflowX": "auto"},
                                style_header={
                                    "backgroundColor": "#1a1d27",
                                    "color": "#e8e8e8",
                                    "fontWeight": "bold",
                                },
                                style_cell={
                                    "backgroundColor": "#0f1117",
                                    "color": "#ccc",
                                    "maxWidth": "400px",
                                    "overflow": "hidden",
                                    "textOverflow": "ellipsis",
                                },
                                style_data_conditional=[
                                    {
                                        "if": {
                                            "filter_query": '{sentiment} = "positive"',
                                        },
                                        "color": "#00d4aa",
                                    },
                                    {
                                        "if": {
                                            "filter_query": '{sentiment} = "negative"',
                                        },
                                        "color": "#ff6b6b",
                                    },
                                ],
                                page_size=8,
                            ),
                        ],
                        md=7,
                    ),
                ]
            ),
            dcc.Interval(id="refresh-interval", interval=DASH_REFRESH_MS, n_intervals=0),
        ],
        fluid=True,
        className="py-3",
        style={"backgroundColor": "#0a0b0f", "minHeight": "100vh"},
    )

    @app.callback(
        Output("timeline-chart", "figure"),
        Output("distribution-chart", "figure"),
        Output("shift-chart", "figure"),
        Output("recent-tweets-table", "data"),
        Output("stats-bar", "children"),
        Input("refresh-interval", "n_intervals"),
    )
    def refresh_dashboard(_n: int):
        minutes = SENTIMENT_WINDOW_MINUTES
        timeline_fig = build_sentiment_timeline_figure(minutes)
        dist_fig = build_distribution_figure(minutes)
        shift_fig = build_shift_figure(minutes)

        rows = []
        for tweet in reversed(tweet_buffer.recent_tweets(8)):
            rows.append(
                {
                    "time": tweet.created_at.strftime("%H:%M:%S"),
                    "sentiment": tweet.label,
                    "text": tweet.text[:140],
                }
            )

        counts = tweet_buffer.sentiment_counts(minutes)
        total = sum(counts.values())
        stats = html.Div(
            [
                html.Span(f"Tweets analyzed: {tweet_buffer.total_processed}", className="me-3"),
                html.Span(f"Window: {total} tweets", className="me-3"),
                html.Span(
                    f"+{counts['positive']} / "
                    f"={counts['neutral']} / "
                    f"-{counts['negative']}",
                ),
            ]
        )
        return timeline_fig, dist_fig, shift_fig, rows, stats

    @app.callback(
        Output("event-feedback", "children"),
        Input("add-event-btn", "n_clicks"),
        State("event-type", "value"),
        State("event-description", "value"),
        prevent_initial_call=True,
    )
    def add_event(n_clicks, event_type, description):
        if not n_clicks:
            return ""
        event = log_manual_event(event_type or "Event", description or "")
        return f"Logged {event.label} at {event.timestamp.strftime('%H:%M:%S')}"

    return app
