import os
import json
from app.ai.agent_interface import append_session_transcript, load_context_for_session


def test_append_session_transcript_and_load_context(tmp_path, monkeypatch):
    # Use a temp agent base by monkeypatching BASE and SESSION_DIR
    from app.ai import agent_interface as ai_iface
    temp_dir = tmp_path / "agent"
    session_cache = temp_dir / "session_cache"
    session_cache.mkdir(parents=True)
    monkeypatch.setattr(ai_iface, 'SESSION_DIR', str(session_cache))

    sid = 'test123'
    text = 'Contact admin@company.com and api_key=sk_test_123'
    fname = append_session_transcript(sid, text)
    # file should be created in our temp session_cache
    assert fname != ''
    path = os.path.join(str(session_cache), fname)
    assert os.path.exists(path)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert 'text' in data
    assert '[REDACTED_EMAIL]' in data['text'] or '[REDACTED_SECRET]' in data['text']

    # load_context_for_session should return dict with keys
    ctx = load_context_for_session(sid)
    assert isinstance(ctx, dict)
    assert 'short_term' in ctx and 'long_term' in ctx and 'config' in ctx
