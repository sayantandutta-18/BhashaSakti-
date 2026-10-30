"""
BhashaSandhi - Multilingual Voice Assistant
Flask application factory and API routes.
"""

import os
import io
import time
import base64
import uuid
import json
import logging
import subprocess
import tempfile
from typing import Dict, Any

from flask import Flask, request, jsonify, send_file, Response, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from services.langs import (
    LANGUAGES,
    get_language_list,
    normalize_lang_code,
    get_canned_message
)
from services.store import init_db, add_turn, get_history
from services.intents import execute_intent
from services.stt import transcribe, get_stt_backend_name
from services.llm import (
    translate as llm_translate,
    detect_language as llm_detect_language,
    route_intent,
    reply as llm_reply,
    reply_stream as llm_reply_stream,
    PRIMARY_MODEL
)
from services.tts import (
    text_to_speech,
    get_loaded_models_status,
    preload_core_models
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("bhashasandhi")

# App Setup
app = Flask(__name__, static_folder="static", template_folder=".")
CORS(app)

# Max upload size: 10MB default
app.config["MAX_CONTENT_LENGTH"] = int(os.environ.get("MAX_CONTENT_LENGTH", 10 * 1024 * 1024))

# Initialize SQLite database
init_db()

# Preload Hindi & Bengali MMS-TTS models in background thread
preload_core_models()


# Simple In-Memory Token Bucket Rate Limiter per IP
class RateLimiter:
    def __init__(self, rpm: int = 60):
        self.capacity = float(rpm)
        self.refill_rate = self.capacity / 60.0 # tokens per second
        self.tokens: Dict[str, float] = {}
        self.last_check: Dict[str, float] = {}

    def is_allowed(self, ip: str) -> bool:
        now = time.time()
        if ip not in self.tokens:
            self.tokens[ip] = self.capacity
            self.last_check[ip] = now
            return True

        elapsed = now - self.last_check[ip]
        self.last_check[ip] = now
        self.tokens[ip] = min(self.capacity, self.tokens[ip] + elapsed * self.refill_rate)

        if self.tokens[ip] >= 1.0:
            self.tokens[ip] -= 1.0
            return True
        return False

rate_limiter = RateLimiter(rpm=int(os.environ.get("RATE_LIMIT_RPM", 60)))


@app.before_request
def check_rate_limit():
    # Exclude static assets, sw.js, and health check from rate limiting
    if request.path.startswith("/static/") or request.path in ["/health", "/", "/favicon.ico", "/sw.js"]:
        return None

    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr) or "unknown"
    client_ip = client_ip.split(",")[0].strip()

    if not rate_limiter.is_allowed(client_ip):
        return jsonify({
            "error": "Rate limit exceeded. Please wait a moment.",
            "code": "RATE_LIMIT_EXCEEDED"
        }), 429


# Global Error Handler: Never return bare 500 stack trace
@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": str(e.description if hasattr(e, "description") else e), "code": "BAD_REQUEST"}), 400

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource not found", "code": "NOT_FOUND"}), 404

@app.errorhandler(413)
def entity_too_large(e):
    return jsonify({"error": "Audio/Image payload too large (max 10MB)", "code": "PAYLOAD_TOO_LARGE"}), 413

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal 500 error: {e}")
    return jsonify({"error": "An internal server error occurred", "code": "INTERNAL_ERROR"}), 500

@app.errorhandler(Exception)
def handle_unexpected_exception(e):
    logger.error(f"Unhandled exception: {e}", exc_info=True)
    return jsonify({"error": "Unexpected server error", "code": "UNEXPECTED_ERROR"}), 500


def detect_audio_ext(data: bytes, fallback_filename: str = "audio.webm") -> str:
    if data.startswith(b"\x1a\x45\xdf\xa3"):
        return ".webm"
    if data.startswith(b"RIFF"):
        return ".wav"
    if data.startswith(b"OggS"):
        return ".ogg"
    if len(data) > 8 and data[4:8] == b"ftyp":
        return ".mp4"
    if data.startswith(b"ID3") or (len(data) > 2 and data[0] == 0xFF and (data[1] & 0xE0) == 0xE0):
        return ".mp3"
    ext = os.path.splitext(fallback_filename)[-1].lower()
    return ext if ext else ".webm"

def convert_audio_to_wav(source_bytes: bytes, original_filename: str = "audio.webm") -> Tuple[str, str]:
    """
    Saves source audio and converts to 16 kHz mono WAV using ffmpeg if present.
    Returns: (input_temp_path, converted_wav_path)
    """
    ext = detect_audio_ext(source_bytes, original_filename)
    temp_in = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    temp_in.write(source_bytes)
    temp_in.close()

    temp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp_out.close()

    converted = False
    try:
        # Check ffmpeg availability
        cmd = [
            "ffmpeg", "-y", "-i", temp_in.name,
            "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
            temp_out.name
        ]
        ret = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if ret.returncode == 0 and os.path.getsize(temp_out.name) > 0:
            converted = True
    except Exception as e:
        logger.debug(f"ffmpeg conversion bypassed or failed: {e}")

    if not converted:
        # Pass input file directly with its detected extension so Groq/Whisper accepts it natively
        return temp_in.name, temp_in.name

    return temp_in.name, temp_out.name


# Routes
@app.route("/")
def index():
    return send_file("index.html")

@app.route("/sw.js")
def service_worker():
    return send_from_directory("static", "sw.js", mimetype="application/javascript")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "project": "BhashaSandhi",
        "stack": "flask",
        "stt_backend": get_stt_backend_name(),
        "llm_model": PRIMARY_MODEL,
        "tts_backends": ["mms-tts", "gtts"],
        "models_loaded": get_loaded_models_status()
    })

@app.route("/api/languages", methods=["GET"])
def api_languages():
    return jsonify(get_language_list())

@app.route("/api/transcribe", methods=["POST"])
def api_transcribe():
    file = request.files.get("audio") or request.files.get("file")
    if not file:
        return jsonify({"error": "No audio file provided in request", "code": "MISSING_AUDIO"}), 400

    lang_hint = request.form.get("language") or request.args.get("language")
    audio_bytes = file.read()
    if len(audio_bytes) < 32:
        return jsonify({"error": "Audio file empty or corrupted", "code": "INVALID_AUDIO"}), 400

    tin, tout = None, None
    try:
        tin, tout = convert_audio_to_wav(audio_bytes, file.filename or "audio.webm")
        stt_result = transcribe(tout, language_hint=lang_hint)

        if stt_result.get("is_empty"):
            lang = stt_result.get("language", "hi")
            return jsonify({
                "error": get_canned_message("silence_or_empty", lang),
                "code": "SILENCE_DETECTED"
            }), 400

        return jsonify({
            "text": stt_result["text"],
            "language": stt_result["language"],
            "backend": stt_result["backend"],
            "duration_ms": stt_result["duration_ms"]
        })
    finally:
        if tin and os.path.exists(tin):
            try: os.unlink(tin)
            except Exception: pass
        if tout and os.path.exists(tout):
            try: os.unlink(tout)
            except Exception: pass

@app.route("/api/translate", methods=["POST"])
def api_translate():
    data = request.get_json(silent=True) or request.form.to_dict()
    text = data.get("text", "").strip()
    target_raw = data.get("target", "").strip()
    source_raw = data.get("source")

    if not text:
        return jsonify({"error": "Missing 'text' field", "code": "MISSING_TEXT"}), 400
    if not target_raw:
        return jsonify({"error": "Missing 'target' language field", "code": "MISSING_TARGET"}), 400

    target = normalize_lang_code(target_raw, default=None)
    if not target or target not in LANGUAGES:
        return jsonify({"error": f"Target language '{target_raw}' is unsupported", "code": "UNSUPPORTED_LANGUAGE"}), 400

    source = normalize_lang_code(source_raw, default="hi") if source_raw else llm_detect_language(text)

    translated = llm_translate(text, target=target, source=source)
    return jsonify({
        "text": translated,
        "source": source,
        "target": target
    })

@app.route("/api/speak", methods=["POST"])
def api_speak():
    data = request.get_json(silent=True) or request.form.to_dict()
    text = data.get("text", "").strip()
    raw_lang = data.get("lang") or data.get("language") or "hi"

    if not text:
        return jsonify({"error": "Missing 'text' field", "code": "MISSING_TEXT"}), 400

    lang = normalize_lang_code(raw_lang, default=None)
    if not lang or lang not in LANGUAGES:
        return jsonify({"error": f"Language '{raw_lang}' is unsupported", "code": "UNSUPPORTED_LANGUAGE"}), 400

    try:
        wav_bytes, backend = text_to_speech(text, lang)
        response = send_file(io.BytesIO(wav_bytes), mimetype="audio/wav")
        response.headers["X-TTS-Backend"] = backend
        return response
    except ValueError as ve:
        return jsonify({"error": str(ve), "code": "UNSUPPORTED_LANGUAGE"}), 400
    except Exception as e:
        logger.error(f"TTS synthesis failed: {e}")
        return jsonify({"error": "Speech synthesis failed", "code": "TTS_ERROR"}), 500

@app.route("/api/chat", methods=["POST"])
def api_chat():
    session_id = request.form.get("session_id") or str(uuid.uuid4())
    lang_hint = request.form.get("lang") or request.form.get("language")
    input_text = request.form.get("text", "").strip()
    audio_file = request.files.get("audio") or request.files.get("file")
    image_file = request.files.get("image")

    t_start = time.time()
    stt_ms = 0.0
    llm_ms = 0.0
    tts_ms = 0.0

    transcript = input_text
    lang = normalize_lang_code(lang_hint) if (lang_hint and lang_hint != "auto") else None

    # 1. Speech-to-text if audio provided
    if audio_file:
        tin, tout = None, None
        try:
            tin, tout = convert_audio_to_wav(audio_file.read(), audio_file.filename or "voice.webm")
            # If user already passed speech-recognized transcript from browser, prioritize it
            if not transcript:
                stt_res = transcribe(tout, language_hint=lang)
                stt_ms = stt_res["duration_ms"]
                transcript = stt_res["text"]
                if not lang:
                    lang = stt_res["language"]

                if stt_res.get("is_empty"):
                    return jsonify({
                        "error": get_canned_message("silence_or_empty", lang or "hi"),
                        "code": "SILENCE_DETECTED"
                    }), 400
        finally:
            if tin and os.path.exists(tin):
                try: os.unlink(tin)
                except Exception: pass
            if tout and os.path.exists(tout):
                try: os.unlink(tout)
                except Exception: pass

    if not transcript:
        return jsonify({"error": "No speech or text received", "code": "EMPTY_INPUT"}), 400

    # Fallback language detection if not set
    if not lang:
        lang = llm_detect_language(transcript)

    # 2. Intent Routing & Tools Execution
    routing = route_intent(transcript, lang)
    intent = routing.get("intent", "chat")
    city = routing.get("city")
    tool_result = execute_intent(intent, transcript, city, lang)

    # Load Conversation History
    history = get_history(session_id, limit=6)

    # Image bytes for Multimodal Gemma
    image_bytes = image_file.read() if image_file else None

    # 3. LLM Response Generation (Gemma 4)
    t_llm_start = time.time()
    reply_text = llm_reply(
        text=transcript,
        lang=lang,
        history=history,
        tool_result=tool_result,
        image_bytes=image_bytes
    )
    llm_ms = (time.time() - t_llm_start) * 1000

    # 4. Text-to-Speech Generation
    t_tts_start = time.time()
    wav_bytes, tts_backend = text_to_speech(reply_text, lang)
    tts_ms = (time.time() - t_tts_start) * 1000

    audio_b64 = base64.b64encode(wav_bytes).decode("utf-8")

    # Persist in SQLite
    add_turn(session_id, lang, "user", transcript, intent=intent)
    add_turn(session_id, lang, "assistant", reply_text, intent=intent)

    return jsonify({
        "session_id": session_id,
        "transcript": transcript,
        "language": lang,
        "intent": intent,
        "reply_text": reply_text,
        "audio_b64": audio_b64,
        "audio_mime": "audio/wav",
        "timings": {
            "stt_ms": round(stt_ms, 2),
            "llm_ms": round(llm_ms, 2),
            "tts_ms": round(tts_ms, 2)
        }
    })

@app.route("/api/chat/stream", methods=["POST"])
def api_chat_stream():
    """
    Server-Sent Events streaming endpoint.
    Emits:
      event: transcript
      event: token (repeated)
      event: audio
      event: done
    """
    session_id = request.form.get("session_id") or str(uuid.uuid4())
    lang_hint = request.form.get("lang") or request.form.get("language")
    input_text = request.form.get("text", "").strip()
    audio_file = request.files.get("audio") or request.files.get("file")
    image_file = request.files.get("image")
    image_bytes = image_file.read() if image_file else None

    transcript = input_text
    lang = normalize_lang_code(lang_hint) if (lang_hint and lang_hint != "auto") else None

    if audio_file:
        tin, tout = None, None
        try:
            tin, tout = convert_audio_to_wav(audio_file.read(), audio_file.filename or "voice.webm")
            # If user already passed recognized transcript from client, prioritize it
            if not transcript:
                stt_res = transcribe(tout, language_hint=lang)
                transcript = stt_res["text"]
                if not lang:
                    lang = stt_res["language"]
        finally:
            if tin and os.path.exists(tin):
                try: os.unlink(tin)
                except Exception: pass
            if tout and os.path.exists(tout):
                try: os.unlink(tout)
                except Exception: pass

    if not transcript:
        def err_stream():
            yield f"event: error\ndata: {json.dumps({'error': 'No audio or text provided'})}\n\n"
        return Response(err_stream(), mimetype="text/event-stream")

    if not lang:
        lang = llm_detect_language(transcript)

    routing = route_intent(transcript, lang)
    intent = routing.get("intent", "chat")
    tool_result = execute_intent(intent, transcript, routing.get("city"), lang)
    history = get_history(session_id, limit=6)

    def generate_sse():
        yield f"event: transcript\ndata: {json.dumps({'transcript': transcript, 'language': lang})}\n\n"

        collected_tokens = []
        for token in llm_reply_stream(transcript, lang, history, tool_result, image_bytes):
            collected_tokens.append(token)
            yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"

        full_reply = "".join(collected_tokens).strip()

        # Generate audio for the completed reply
        wav_bytes, _ = text_to_speech(full_reply, lang)
        audio_b64 = base64.b64encode(wav_bytes).decode("utf-8")
        yield f"event: audio\ndata: {json.dumps({'audio_b64': audio_b64, 'audio_mime': 'audio/wav'})}\n\n"

        # Persist conversation
        add_turn(session_id, lang, "user", transcript, intent=intent)
        add_turn(session_id, lang, "assistant", full_reply, intent=intent)

        yield f"event: done\ndata: {json.dumps({'session_id': session_id, 'intent': intent})}\n\n"

    return Response(generate_sse(), mimetype="text/event-stream")

@app.route("/api/config", methods=["GET", "POST"])
def api_config():
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form.to_dict()
        gemini_key = data.get("gemini_key")
        groq_key = data.get("groq_key")
        if gemini_key:
            gemini_key = gemini_key.strip()
            os.environ["GEMINI_API_KEY"] = gemini_key
            from services.llm import set_api_key
            set_api_key(gemini_key)
        if groq_key:
            os.environ["GROQ_API_KEY"] = groq_key.strip()
        return jsonify({
            "status": "ok",
            "has_gemini": bool(os.environ.get("GEMINI_API_KEY")),
            "has_groq": bool(os.environ.get("GROQ_API_KEY"))
        })

    return jsonify({
        "has_gemini": bool(os.environ.get("GEMINI_API_KEY")),
        "has_groq": bool(os.environ.get("GROQ_API_KEY")),
        "gemini_model": os.environ.get("GEMMA_MODEL", "gemma-4-26b-a4b-it")
    })

@app.route("/api/history", methods=["GET"])
def api_history():
    session_id = request.args.get("session_id", "").strip()
    limit = int(request.args.get("limit", 10))
    turns = get_history(session_id, limit=limit)
    return jsonify(turns)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting BhashaSandhi server on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)
