import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

BASE = os.path.join(os.path.dirname(__file__), '..', '..', '.github', 'agent')
MEMORY_PATH = os.path.join(BASE, 'memory.json')
BACKLOG_PATH = os.path.join(BASE, 'backlog.json')
SESSION_DIR = os.path.join(BASE, 'session_cache')

os.makedirs(BASE, exist_ok=True)
os.makedirs(SESSION_DIR, exist_ok=True)


def _read(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def _write(path: str, data: List[Dict[str, Any]]):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class AgentMemory:
    """Simple file-backed memory for short and long term facts.

    Not a production DB — intended as a lightweight developer-friendly store that
    the local agent and CI workflows can read and append to.
    """

    def list_memory(self) -> List[Dict[str, Any]]:
        return _read(MEMORY_PATH)

    def add_memory(self, fact: str, tags: List[str] | None = None) -> Dict[str, Any]:
        items = _read(MEMORY_PATH)
        entry = {
            'id': f'mem-{int(datetime.now(timezone.utc).timestamp())}',
            'fact': fact,
            'tags': tags or [],
            'created_at': datetime.now(timezone.utc).isoformat(),
        }
        items.insert(0, entry)
        _write(MEMORY_PATH, items)
        return entry

    def list_backlog(self) -> List[Dict[str, Any]]:
        return _read(BACKLOG_PATH)

    def add_backlog(self, title: str, details: str) -> Dict[str, Any]:
        items = _read(BACKLOG_PATH)
        entry = {
            'id': f'backlog-{int(datetime.now(timezone.utc).timestamp())}',
            'title': title,
            'details': details,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'status': 'pending',
        }
        items.insert(0, entry)
        _write(BACKLOG_PATH, items)
        return entry


if __name__ == '__main__':
    am = AgentMemory()
    print('Memory items:', len(am.list_memory()))
    print('Backlog items:', len(am.list_backlog()))
