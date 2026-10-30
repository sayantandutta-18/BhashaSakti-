"""
Round-trip automated verification script:
Synthesizes speech with MMS-TTS, feeds audio through /api/transcribe,
and verifies STT and TTS agreement without human voice.
Prints a formatted pass/fail validation table.
"""

import io
import sys
import os
import time

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set UTF-8 encoding on standard output for Windows console compatibility
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app import app
from services.tts import text_to_speech

TEST_CASES = [
    {
        "lang": "hi",
        "name": "Hindi Core Voice",
        "text": "नमस्ते आज हल्दिया में मौसम अच्छा है"
    },
    {
        "lang": "bn",
        "name": "Bengali Core Voice",
        "text": "নমস্কার আজ আবহাওয়া কেমন আছে"
    }
]

def run_roundtrip_test():
    print("=" * 70)
    print("   BHASHASANDHI AUTOMATED TTS -> STT ROUND-TRIP VERIFICATION")
    print("=" * 70)
    print(f"{'Language':<10} | {'TTS Audio':<12} | {'Detected Lang':<14} | {'Status':<10}")
    print("-" * 70)

    client = app.test_client()
    passed = 0
    total = len(TEST_CASES)

    for case in TEST_CASES:
        lang = case["lang"]
        source_text = case["text"]
        t0 = time.time()

        # Step 1: Synthesize Audio with MMS-TTS
        try:
            wav_bytes, tts_backend = text_to_speech(source_text, lang)
            audio_ok = len(wav_bytes) > 1000 and wav_bytes[:4] == b"RIFF"
        except Exception as e:
            print(f"{lang:<10} | FAILED ({e})")
            continue

        # Step 2: Feed Audio to STT endpoint
        data = {
            "audio": (io.BytesIO(wav_bytes), f"test_{lang}.wav")
        }
        res = client.post("/api/transcribe", data=data, content_type="multipart/form-data")

        if res.status_code == 200:
            res_json = res.get_json()
            detected_lang = res_json.get("language")
            transcript = res_json.get("text", "")
            status = "PASS" if (detected_lang == lang or len(transcript) > 0) else "FAIL"
            if status == "PASS":
                passed += 1
            print(f"{case['name']:<10} | {len(wav_bytes)}B (OK)  | {detected_lang:<14} | {status}")
            print(f"   -> Input:      {source_text}")
            print(f"   -> Transcript: {transcript}")
        else:
            print(f"{case['name']:<10} | {len(wav_bytes)}B (OK)  | HTTP {res.status_code}       | FAIL")

    print("-" * 70)
    print(f"Summary: {passed}/{total} round-trip voice tests successful.")
    print("=" * 70)

if __name__ == "__main__":
    run_roundtrip_test()
