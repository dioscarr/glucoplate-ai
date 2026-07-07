import json
import os
from datetime import datetime, timezone
from typing import List
from uuid import uuid4

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
CART_PATH = os.path.join(DATA_DIR, 'carts.json')

os.makedirs(DATA_DIR, exist_ok=True)


def _read():
    if not os.path.exists(CART_PATH):
        return []
    try:
        with open(CART_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def _write(items: List[dict]):
    with open(CART_PATH, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


class CartStoreService:
    def list(self) -> List[dict]:
        return _read()

    def create(self, cart: dict) -> dict:
        cart = dict(cart or {})
        if not cart.get('id'):
            cart['id'] = f"cart-{uuid4().hex[:12]}"
        cart['_created_at'] = datetime.now(timezone.utc).isoformat()
        if not isinstance(cart.get('items'), list):
            cart['items'] = []
        items = _read()
        items = [cart] + items
        _write(items)
        return cart

    def get(self, cart_id: str) -> dict | None:
        for c in _read():
            if c.get('id') == cart_id:
                return c
        return None

    def update(self, cart_id: str, changes: dict) -> dict | None:
        items = _read()
        out = []
        updated = None
        changes = dict(changes or {})
        for c in items:
            if c.get('id') == cart_id:
                # Keep immutable identity fields stable.
                changes['id'] = c.get('id')
                if c.get('_created_at') is not None:
                    changes['_created_at'] = c.get('_created_at')
                if 'items' in changes and not isinstance(changes.get('items'), list):
                    changes['items'] = []
                c.update(changes)
                updated = c
            out.append(c)
        _write(out)
        return updated

    def delete(self, cart_id: str) -> bool:
        original = _read()
        items = [c for c in original if c.get('id') != cart_id]
        _write(items)
        return len(items) < len(original)
