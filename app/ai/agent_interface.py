"""Agent interface helpers for Copilot-based workflows.

Provides functions the Copilot-driven orchestrator can call to:
- load combined context (short-term + recent long-term facts)
- append session transcripts to short-term cache
- persist a session summary into long-term memory via AgentMemory

This module is development-only and intended to be imported by local Copilot automation scripts.
"""
from typing import Dict, Any
import os
import json
from datetime import datetime, timezone

from app.ai.agent_memory import AgentMemory

BASE = os.path.join(os.path.dirname(__file__), '..', '..', '.github', 'agent')
SESSION_DIR = os.path.join(BASE, 'session_cache')

os.makedirs(SESSION_DIR, exist_ok=True)


def load_context_for_session(session_id: str, short_window: int = 7) -> Dict[str, Any]:
    """Return a dict containing:
    - short_term: list of recent session filenames and brief metadata
    - long_term: the top N memory facts
    - config: agent config (if present)
    """
    am = AgentMemory()
    long_term = am.list_memory()[:200]
    # short term: list session files (not loading full transcripts)
    short_files = []
    try:
        for fn in sorted(os.listdir(SESSION_DIR), reverse=True):
            path = os.path.join(SESSION_DIR, fn)
            try:
                stat = os.path.getmtime(path)
                short_files.append({'file': fn, 'mtime': datetime.fromtimestamp(stat, timezone.utc).isoformat()})
            except Exception:
                continue
    except Exception:
        short_files = []
    cfg = None
    cfg_path = os.path.join(BASE, 'config.yaml')
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, 'r', encoding='utf-8') as f:
                cfg = f.read()
        except Exception:
            cfg = None
    return {'short_term': short_files, 'long_term': long_term, 'config': cfg}


def append_session_transcript(session_id: str, transcript_text: str) -> str:
    """Save a session transcript to session_cache and return the filename."""
    fname = f"session-{session_id}-{int(datetime.now(timezone.utc).timestamp())}.json"
    path = os.path.join(SESSION_DIR, fname)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'id': session_id, 'text': transcript_text, 'created_at': datetime.now(timezone.utc).isoformat()}, f, ensure_ascii=False)
    except Exception:
        return ''
    return fname


def persist_session_summary(session_id: str, summary: str, tags: list[str] | None = None) -> Dict[str, Any]:
    """Add a summary to long-term memory via AgentMemory. Returns the memory entry."""
    am = AgentMemory()
    entry = am.add_memory(f"session:{session_id} summary: {summary}", tags=tags or ['auto-summary'])
    return entry
