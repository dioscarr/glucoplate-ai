"""Simple agent sync script: summarize recent session files and append brief facts to memory.json.

This is intentionally minimal: it looks for .github/agent/session_cache/*.json, summarizes filenames and sizes,
and appends a short fact to memory using AgentMemory. In a later phase this will call a cheap summarization model.
"""
from datetime import datetime
import glob
import json
import os

from app.ai.agent_memory import AgentMemory

BASE = os.path.join(os.path.dirname(__file__), '..', '.github', 'agent')
SESS_DIR = os.path.join(BASE, 'session_cache')

if __name__ == '__main__':
    am = AgentMemory()
    files = glob.glob(os.path.join(SESS_DIR, '*.json'))
    if not files:
        print('No session files to summarize')
        exit(0)
    summary_lines = []
    for p in files:
        try:
            s = os.path.getsize(p)
            summary_lines.append(f"{os.path.basename(p)} ({s} bytes)")
        except Exception:
            continue
    fact = f"Agent sync ran at {datetime.utcnow().isoformat()} and found {len(summary_lines)} session files: {', '.join(summary_lines[:5])}"
    added = am.add_memory(fact, tags=['agent-sync','auto'])
    print('Added memory:', added['id'])
