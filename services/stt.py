"""
Speech-to-Text Service using Whisper.
Supports Groq API (whisper-large-v3), local faster-whisper, and mock fallback.
Auto-detects language or accepts explicit language pin.
"""

import os
import re
import time
import logging
from typing import Dict, Any, Optional, Tuple
import requests

from services.langs import normalize_lang_code, detect_script, LANGUAGES

logger = logging.getLogger(__name__)

# Common Whisper hallucinations on silent/noisy clips
HALLUCINATION_PATTERNS = [
    r"^\s*$",
    r"thank you for watching",
    r"subscribe to my channel",
    r"subtitles by",
    r"amara\.org",
    r"watching!",
    r"^\s*[♪♫]+\s*$",
    r"\[music\]",
    r"\[applause\]",
    r"\[laughter\]",
    r"you",
    r"bye"
]

_local_whisper_model = None

def get_stt_backend_name() -> str:
    backend = os.environ.get("STT_BACKEND", "auto").lower()
    if backend == "auto":
        if os.environ.get("GROQ_API_KEY"):
            return "groq"
        return "local"
    return backend

def _get_local_model():
    """Lazy load faster-whisper model on CPU with int8 quantization."""
    global _local_whisper_model
    if _local_whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            model_size = os.environ.get("WHISPER_LOCAL_MODEL", "small")
            logger.info(f"Loading local faster-whisper model '{model_size}' on CPU (int8)...")
            _local_whisper_model = WhisperModel(model_size, device="cpu", compute_type="int8")
            logger.info("Local faster-whisper model loaded successfully.")
        except Exception as e:
            logger.warning(f"Failed to load faster-whisper: {e}")
            _local_whisper_model = None
    return _local_whisper_model

def is_hallucination(text: str) -> bool:
    """Detect if transcribed text is silence filler or hallucination."""
    if not text or len(text.strip()) == 0:
        return True
    cleaned = text.strip().lower()
    for pattern in HALLUCINATION_PATTERNS:
        if re.search(pattern, cleaned, re.IGNORECASE):
            # Short single word hallucinations
            if len(cleaned.split()) <= 4:
                return True
    return False

def transcribe_audio_groq(
    audio_path: str,
    language_hint: Optional[str] = None
) -> Tuple[str, str, float]:
    """
    Transcribe audio via Groq Whisper-large-v3 OpenAI-compatible API.
    Returns: (transcribed_text, detected_language_code, duration_ms)
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set.")

    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {api_key}"}

    data = {
        "model": "whisper-large-v3",
        "response_format": "verbose_json"
    }
    # Pass language only if explicitly pinned by the user (not auto)
    if language_hint and language_hint != "auto":
        whisper_lang = LANGUAGES.get(language_hint, {}).get("whisper_code")
        if whisper_lang:
            data["language"] = whisper_lang

    t0 = time.time()
    ext = os.path.splitext(audio_path)[-1].lower()
    mime_map = {
        ".webm": "audio/webm",
        ".mp4": "audio/mp4",
        ".m4a": "audio/m4a",
        ".mp3": "audio/mp3",
        ".ogg": "audio/ogg",
        ".wav": "audio/wav"
    }
    content_type = mime_map.get(ext, "audio/webm")

    with open(audio_path, "rb") as f:
        files = {"file": (os.path.basename(audio_path), f, content_type)}
        res = requests.post(url, headers=headers, data=data, files=files, timeout=30)

    duration_ms = (time.time() - t0) * 1000

    if res.status_code != 200:
        raise RuntimeError(f"Groq API error ({res.status_code}): {res.text}")

    result = res.json()
    raw_text = result.get("text", "").strip()
    detected_lang = result.get("language", "hi")
    norm_lang = normalize_lang_code(detected_lang)

    return raw_text, norm_lang, duration_ms

def transcribe_audio_local(
    audio_path: str,
    language_hint: Optional[str] = None
) -> Tuple[str, str, float]:
    """
    Transcribe audio locally using faster-whisper.
    """
    model = _get_local_model()
    if model is None:
        raise RuntimeError("Local faster-whisper is unavailable.")

    t0 = time.time()
    lang = language_hint if language_hint and language_hint != "auto" else None
    segments, info = model.transcribe(audio_path, language=lang, beam_size=5)
    text = " ".join([seg.text for seg in segments]).strip()
    duration_ms = (time.time() - t0) * 1000

    detected_lang = normalize_lang_code(info.language)
    return text, detected_lang, duration_ms

def transcribe(
    audio_path: str,
    language_hint: Optional[str] = None
) -> Dict[str, Any]:
    """
    Unified STT entrypoint.
    Returns:
    {
        "text": str,
        "language": str,
        "backend": str,
        "duration_ms": float
    }
    """
    backend = get_stt_backend_name()
    text = ""
    lang = "hi"
    duration_ms = 0.0
    used_backend = backend

    try:
        if backend == "groq":
            text, lang, duration_ms = transcribe_audio_groq(audio_path, language_hint)
        elif backend == "local":
            text, lang, duration_ms = transcribe_audio_local(audio_path, language_hint)
        else: # auto
            if os.environ.get("GROQ_API_KEY"):
                used_backend = "groq"
                text, lang, duration_ms = transcribe_audio_groq(audio_path, language_hint)
            else:
                used_backend = "local"
                text, lang, duration_ms = transcribe_audio_local(audio_path, language_hint)
    except Exception as e:
        logger.warning(f"Primary STT backend '{used_backend}' failed: {e}. Checking fallback...")
        # If Groq failed, attempt local fallback if available
        if used_backend == "groq":
            try:
                logger.info("Attempting local faster-whisper fallback...")
                text, lang, duration_ms = transcribe_audio_local(audio_path, language_hint)
                used_backend = "faster-whisper-fallback"
            except Exception as e_local:
                logger.error(f"Local fallback also failed: {e_local}")
                # Mock fallback for test/demo continuity if keys/local model missing
                used_backend = "mock (GROQ_API_KEY missing/failed)"
                text = "नमस्ते, आज हल्दिया का मौसम कैसा है?"
                lang = "hi"
                duration_ms = 120.0
        else:
            used_backend = "mock (STT backend unavailable)"
            target_lang = language_hint if language_hint in ("hi", "bn", "or", "en") else "hi"
            if target_lang == "bn":
                text = "নমস্কার, আজ আবহাওয়া কেমন আছে?"
                lang = "bn"
            elif target_lang == "en":
                text = "Hello, what is the weather today?"
                lang = "en"
            elif target_lang == "or":
                text = "ନମସ୍କାର, ଆଜି ପାଣିପାଗ କିପରି ଅଛି?"
                lang = "or"
            else:
                text = "नमस्ते, आज हल्दिया का मौसम कैसा है?"
                lang = "hi"
            duration_ms = 100.0

    # Script heuristic fallback check if detected language is outside {hi, bn, en}
    if lang not in ("hi", "bn", "en"):
        script_lang = detect_script(text)
        if script_lang:
            lang = script_lang
        else:
            lang = "hi"

    # Hallucination and silence filter
    if is_hallucination(text):
        return {
            "text": "",
            "language": lang,
            "backend": used_backend,
            "duration_ms": duration_ms,
            "is_empty": True
        }

    return {
        "text": text,
        "language": lang,
        "backend": used_backend,
        "duration_ms": round(duration_ms, 2),
        "is_empty": False
    }
