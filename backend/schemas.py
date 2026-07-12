from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    label: str = Field(..., min_length=1, max_length=50)
    description: str = Field(default="", max_length=200)


class TweetOut(BaseModel):
    tweet_id: str
    text: str
    author: str
    created_at: str
    label: str
    score: float


class EventOut(BaseModel):
    label: str
    description: str
    timestamp: str


class ShiftOut(BaseModel):
    event: str
    description: str
    timestamp: str
    before: float
    after: float
    delta: float
    tweets_before: int
    tweets_after: int


class TimelinePoint(BaseModel):
    timestamp: str
    avg_sentiment: float
    volume: int


class EntityOut(BaseModel):
    id: str
    name: str
    type: str
    icon: str
    color: str
    mention_count: int = 0
    positive: int = 0
    neutral: int = 0
    negative: int = 0
    avg_sentiment: float = 0.0


class ActiveEntityOut(BaseModel):
    id: str
    name: str
    type: str
    icon: str
    color: str


class StatsOut(BaseModel):
    total_processed: int
    window_total: int
    positive: int
    neutral: int
    negative: int
    avg_sentiment: float
    keywords: List[str]


class DashboardOut(BaseModel):
    stats: StatsOut
    active_entity: Optional[ActiveEntityOut] = None
    featured: List[EntityOut] = []
    entities: List[EntityOut]
    timeline: List[TimelinePoint]
    events: List[EventOut]
    shifts: List[ShiftOut]
    tweets: List[TweetOut]
