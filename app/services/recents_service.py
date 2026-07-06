import os
import json
from datetime import datetime, timezone

BASE = os.path.join(os.path.dirname(__file__), '..', '..', 'app', 'data')
os.makedirs(BASE, exist_ok=True)
RECENTS_PATH = os.path.join(BASE, 'recents.json')


def _load():
    if not os.path.exists(RECENTS_PATH):
        return []
    try:
        with open(RECENTS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def _save(data):
    try:
        with open(RECENTS_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


class RecentsService:
    """Simple file-backed recents store for generated recipes (development-only)."""

    def list(self, limit: int = 20):
        items = _load()
        items.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return items[:limit]

    def add(self, recipe: dict):
        items = _load()
        entry = {
            'id': f"rec-{int(datetime.now(timezone.utc).timestamp())}",
            'created_at': datetime.now(timezone.utc).isoformat(),
            'title': recipe.get('title'),
            'summary': recipe.get('summary'),
            'recipe': recipe,
        }
        items.insert(0, entry)
        # cap to 100
        items = items[:100]
        _save(items)
        return entry
