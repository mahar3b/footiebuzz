from __future__ import annotations

DEMO_ENTITIES: list[dict] = [
    {
        "id": "argentina",
        "name": "Argentina",
        "type": "team",
        "icon": "🇦🇷",
        "color": "#75aadb",
        "keywords": ["argentina", "albiceleste", "arg"],
    },
    {
        "id": "france",
        "name": "France",
        "type": "team",
        "icon": "🇫🇷",
        "color": "#0055a4",
        "keywords": ["france", "les bleus", "fra"],
    },
    {
        "id": "brazil",
        "name": "Brazil",
        "type": "team",
        "icon": "🇧🇷",
        "color": "#ffdf00",
        "keywords": ["brazil", "selecao", "bra"],
    },
    {
        "id": "england",
        "name": "England",
        "type": "team",
        "icon": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "color": "#cf142b",
        "keywords": ["england", "three lions", "eng"],
    },
    {
        "id": "messi",
        "name": "Messi",
        "type": "player",
        "icon": "⭐",
        "color": "#00e676",
        "keywords": ["messi", "leo messi", "la pulga"],
    },
    {
        "id": "mbappe",
        "name": "Mbappé",
        "type": "player",
        "icon": "⚡",
        "color": "#448aff",
        "keywords": ["mbappe", "mbappé", "kylian"],
    },
    {
        "id": "ronaldo",
        "name": "Ronaldo",
        "type": "player",
        "icon": "👑",
        "color": "#ffd740",
        "keywords": ["ronaldo", "cr7", "cristiano"],
    },
    {
        "id": "bellingham",
        "name": "Bellingham",
        "type": "player",
        "icon": "🔥",
        "color": "#ff5252",
        "keywords": ["bellingham", "jude", "belingham"],
    },
]


def get_entity(entity_id: str) -> dict | None:
    for e in DEMO_ENTITIES:
        if e["id"] == entity_id:
            return e
    return None


# Highlighted in the demo UI (Argentina vs Mbappé)
DEMO_FEATURED = ["argentina", "mbappe"]
