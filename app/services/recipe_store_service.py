import json
import os
from typing import List

from app.schemas.recipe import RecipeResponse

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
STORE_PATH = os.path.join(DATA_DIR, 'recipes.json')

os.makedirs(DATA_DIR, exist_ok=True)


def _read_store() -> List[dict]:
    if not os.path.exists(STORE_PATH):
        return []
    try:
        with open(STORE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def _write_store(items: List[dict]):
    with open(STORE_PATH, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


class RecipeStoreService:
    """Simple JSON file-backed store for generated recipes."""

    def list(self) -> List[dict]:
        return _read_store()

    def save(self, recipe: dict) -> dict:
        items = _read_store()
        # Add an id and timestamp if not present
        from datetime import datetime
        if 'id' not in recipe:
            recipe['id'] = f"recipe-{int(datetime.utcnow().timestamp())}"
        recipe['_saved_at'] = datetime.utcnow().isoformat() + 'Z'
        # Prepend so newest first
        items = [recipe] + [i for i in items if i.get('id') != recipe['id']]
        _write_store(items)
        return recipe

    def get(self, recipe_id: str) -> dict | None:
        items = _read_store()
        for i in items:
            if i.get('id') == recipe_id:
                return i
        return None
