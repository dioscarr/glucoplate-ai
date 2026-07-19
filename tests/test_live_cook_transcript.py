from pathlib import Path

from app.services.live_cook_insight_service import LiveCookInsightService


ROOT = Path(__file__).resolve().parents[1]


def test_transcript_routes_and_client_are_registered():
    main = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    routes = (ROOT / "app" / "api" / "live_cook_transcript_routes.py").read_text(encoding="utf-8")
    assert "live_cook_transcript_router" in main
    assert '"/static/live-cook-transcript.js"' in main
    assert '@router.get("/{room_id}/transcription")' in routes
    assert '@router.put("/{room_id}/transcription/consent")' in routes
    assert '@router.post("/{room_id}/transcription/segments"' in routes
    assert "Depends(scoped_user)" in routes


def test_transcript_requires_room_membership_and_consent():
    source = (ROOT / "app" / "services" / "live_cook_transcript_service.py").read_text(encoding="utf-8")
    assert "not self._participant(room, uid)" in source
    assert "Only the Chef can enable or disable" in source
    assert "Consent is required" in source
    assert '"raw_audio_retained": False' in source
    assert '"status": "final"' in source
    assert '"speaker_uid": uid' in source


def test_client_discloses_capture_and_does_not_retain_raw_audio():
    source = (ROOT / "app" / "static" / "live-cook-transcript.js").read_text(encoding="utf-8")
    assert "SpeechRecognition" in source
    assert "webkitSpeechRecognition" in source
    assert "Raw audio is not retained" in source
    assert "Participants must consent individually" in source
    assert "interimResults=true" in source
    assert "/transcription/segments" in source
    assert "pagehide" in source


def test_insight_merges_chat_and_final_audio_segments():
    service = LiveCookInsightService()
    room = {
        "id": "room-1",
        "title": "Pasta",
        "chat": [
            {"id": "chat-1", "display_name": "Lee", "message": "Start the sauce", "created_at": "2026-01-01T00:00:01Z"}
        ],
        "transcription": {
            "segments": {
                "speech-1": {
                    "id": "speech-1",
                    "speaker_name": "Cook",
                    "text": "I thought we had tomatoes",
                    "status": "final",
                    "started_at": "2026-01-01T00:00:02Z",
                },
                "speech-interim": {
                    "id": "speech-interim",
                    "speaker_name": "Cook",
                    "text": "tom",
                    "status": "interim",
                    "started_at": "2026-01-01T00:00:03Z",
                },
            }
        },
    }

    messages = service._messages(room)

    assert [item["source"] for item in messages] == ["chat", "audio"]
    assert messages[-1]["message"] == "I thought we had tomatoes"


def test_local_brief_surfaces_implied_spoken_missing_ingredient():
    service = LiveCookInsightService()
    room = {
        "id": "room-2",
        "title": "Pasta",
        "chat": [],
        "transcription": {
            "segments": {
                "speech-1": {
                    "id": "speech-1",
                    "speaker_name": "Cook",
                    "text": "I thought we had tomatoes.",
                    "status": "final",
                    "started_at": "2026-01-01T00:00:02Z",
                }
            }
        },
    }

    result = service.generate(room, provider="local")

    assert result["provider"] == "local"
    assert [item["name"] for item in result["suggested_items"]] == ["tomatoes"]
    assert result["suggested_items"][0]["source_message_ids"] == ["speech-1"]
