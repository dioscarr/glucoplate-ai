import json
import os
from typing import List

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
        from datetime import datetime
        if 'id' not in cart:
            cart['id'] = f"cart-{int(datetime.utcnow().timestamp())}"
        cart['_created_at'] = datetime.utcnow().isoformat() + 'Z'
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
        for c in items:
            if c.get('id') == cart_id:
                c.update(changes)
                updated = c
            out.append(c)
        _write(out)
        return updated

    def delete(self, cart_id: str) -> bool:
        items = [c for c in _read() if c.get('id') != cart_id]
        _write(items)
        return True
