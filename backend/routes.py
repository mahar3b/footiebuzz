from __future__ import annotations

import asyncio

from typing import List, Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from backend.schemas import DashboardOut, EntityOut, EventCreate, EventOut
from backend.services import build_dashboard_state, create_event, list_entities
from config.settings import DASH_REFRESH_MS, SENTIMENT_WINDOW_MINUTES

router = APIRouter(prefix="/api")


@router.get("/health")
def health():
    return {"status": "ok", "service": "footiebuzz"}


@router.get("/entities", response_model=List[EntityOut])
def get_entities():
    return list_entities()


@router.get("/dashboard", response_model=DashboardOut)
def get_dashboard(entity: Optional[str] = Query(default=None)):
    return build_dashboard_state(entity_id=entity)


@router.post("/events", response_model=EventOut)
def post_event(body: EventCreate):
    return create_event(body.label, body.description)


@router.websocket("/ws")
async def websocket_live(websocket: WebSocket):
    await websocket.accept()
    entity = websocket.query_params.get("entity")
    try:
        while True:
            payload = build_dashboard_state(
                minutes=SENTIMENT_WINDOW_MINUTES,
                entity_id=entity,
            )
            await websocket.send_json(payload)
            await asyncio.sleep(DASH_REFRESH_MS / 1000)
    except WebSocketDisconnect:
        pass
