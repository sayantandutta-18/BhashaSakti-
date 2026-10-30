"""
Unit and integration smoke tests for BhashaSandhi API.
Tests endpoints:
- GET /health
- GET /api/languages
- POST /api/translate
- POST /api/speak
- POST /api/chat
- POST /api/chat/stream
- Error formatting & input validation
"""

import os
import io
import json
import pytest
from app import app
from services.langs import LANGUAGES

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"
    assert data["project"] == "BhashaSandhi"
    assert data["stack"] == "flask"
    assert "stt_backend" in data
    assert "llm_model" in data
    assert "models_loaded" in data

def test_languages_endpoint(client):
    res = client.get("/api/languages")
    assert res.status_code == 200
    langs = res.get_json()
    assert isinstance(langs, list)
    codes = [l["code"] for l in langs]
    assert "hi" in codes
    assert "bn" in codes
    assert "or" in codes
    assert "en" in codes

    # Odia must be clearly flagged with STT false, TTS true
    odia = next(l for l in langs if l["code"] == "or")
    assert odia["stt"] is False
    assert odia["tts"] is True

def test_translate_endpoint(client):
    # Hindi to English
    res = client.post("/api/translate", json={"text": "नमस्ते दुनिया", "target": "en", "source": "hi"})
    assert res.status_code == 200
    data = res.get_json()
    assert "text" in data
    assert data["target"] == "en"

    # Bengali to English
    res = client.post("/api/translate", json={"text": "শুভ সকাল", "target": "en", "source": "bn"})
    assert res.status_code == 200
    data = res.get_json()
    assert "text" in data

def test_speak_endpoint_wav_riff(client):
    # Test speech synthesis for Hindi, Bengali, and Odia
    for lang in ["hi", "bn", "or"]:
        res = client.post("/api/speak", json={"text": "नमस्ते", "lang": lang})
        assert res.status_code == 200
        assert res.headers.get("Content-Type") == "audio/wav"
        audio_data = res.data
        # WAV RIFF header verification
        assert len(audio_data) > 44, f"WAV length too short for lang {lang}"
        assert audio_data[:4] == b"RIFF", f"Invalid RIFF header for lang {lang}"
        assert audio_data[8:12] == b"WAVE", f"Invalid WAVE marker for lang {lang}"

def test_speak_unsupported_language_rejection(client):
    res = client.post("/api/speak", json={"text": "Hello", "lang": "xx"})
    assert res.status_code == 400
    data = res.get_json()
    assert "error" in data
    assert data["code"] == "UNSUPPORTED_LANGUAGE"

def test_missing_input_rejection(client):
    # Missing text in translate
    res = client.post("/api/translate", json={})
    assert res.status_code == 400
    data = res.get_json()
    assert "error" in data
    assert "code" in data

def test_chat_pipeline_with_weather_intent(client):
    res = client.post("/api/chat", data={"text": "आज मौसम कैसा है?", "lang": "hi"})
    assert res.status_code == 200
    data = res.get_json()
    assert "session_id" in data
    assert "reply_text" in data
    assert "audio_b64" in data
    assert data["audio_mime"] == "audio/wav"
    assert data["intent"] in ["weather", "chat"]
    # Verify non-empty audio
    assert len(data["audio_b64"]) > 50

def test_chat_stream_endpoint(client):
    res = client.post("/api/chat/stream", data={"text": "नमस्ते", "lang": "hi"})
    assert res.status_code == 200
    assert "text/event-stream" in res.headers.get("Content-Type", "")
    body = res.data.decode("utf-8")
    assert "event: transcript" in body
    assert "event: token" in body
    assert "event: audio" in body
    assert "event: done" in body
