"""
Language metadata, Unicode script detection, and localized canned messages.
Supported languages: Hindi (hi), Bengali (bn), Odia (or), English (en fallback).
"""

import re
from typing import Dict, Any, Optional

# Language definitions
LANGUAGES: Dict[str, Dict[str, Any]] = {
    "hi": {
        "code": "hi",
        "name": "Hindi",
        "native": "हिन्दी",
        "mms_code": "hin",
        "whisper_code": "hindi",
        "bcp47": "hi-IN",
        "stt": True,
        "tts": True,
        "unicode_range": (0x0900, 0x097F),
        "regex": r"[\u0900-\u097F]"
    },
    "bn": {
        "code": "bn",
        "name": "Bengali",
        "native": "বাংলা",
        "mms_code": "ben",
        "whisper_code": "bengali",
        "bcp47": "bn-IN",
        "stt": True,
        "tts": True,
        "unicode_range": (0x0980, 0x09FF),
        "regex": r"[\u0980-\u09FF]"
    },
    "or": {
        "code": "or",
        "name": "Odia",
        "native": "ଓଡ଼ିଆ",
        "mms_code": "ory",
        "whisper_code": None, # Whisper has no official Odia support
        "bcp47": "or-IN",
        "stt": False, # Explicit honesty: Whisper lacks official Odia STT
        "tts": True, # Meta MMS-TTS supports ory
        "unicode_range": (0x0B00, 0x0B7F),
        "regex": r"[\u0B00-\u0B7F]"
    },
    "en": {
        "code": "en",
        "name": "English",
        "native": "English",
        "mms_code": "eng",
        "whisper_code": "english",
        "bcp47": "en-US",
        "stt": True,
        "tts": True,
        "unicode_range": (0x0041, 0x007A),
        "regex": r"[A-Za-z]"
    }
}

# Localized canned messages to ensure no English errors are spoken to non-English speakers
CANNED_MESSAGES: Dict[str, Dict[str, str]] = {
    "greeting": {
        "hi": "नमस्ते! मैं आपकी क्या सहायता कर सकता हूँ?",
        "bn": "নমস্কার! আমি আপনাকে কীভাবে সাহায্য করতে পারি?",
        "or": "ନମସ୍କାର! ମୁଁ ଆପଣଙ୍କୁ କିପରି ସାହାଯ୍ୟ କରିପାରିବି?",
        "en": "Hello! How can I assist you today?"
    },
    "silence_or_empty": {
        "hi": "मुझे कोई आवाज़ सुनाई नहीं दी। कृपया फिर से बोलें।",
        "bn": "আমি কোনো শব্দ শুনতে পাইনি। দয়া করে আবার বলুন।",
        "or": "ମୁଁ କୌଣସି ଶବ୍ଦ ଶୁଣିପାରିଲି ନାହିଁ। ଦୟାକରି ପୁଣି କୁହନ୍ତୁ।",
        "en": "I couldn't hear any audio. Please speak again."
    },
    "retry": {
        "hi": "मैं ठीक से सुन नहीं पाया, कृपया दोबारा प्रयास करें।",
        "bn": "আমি সঠিকভাবে শুনতে পাইনি, দয়া করে আবার চেষ্টা করুন।",
        "or": "ମୁଁ ସଠିକ୍ ଭାବରେ ଶୁଣିପାରିଲି ନାହିଁ, ଦୟାକରି ପୁନର୍ବାର ଚେଷ୍ଟା କରନ୍ତୁ।",
        "en": "I couldn't hear you clearly, please try again."
    },
    "service_busy": {
        "hi": "सेवा अभी व्यस्त है, कृपया कुछ क्षण बाद पुनः प्रयास करें।",
        "bn": "পরিষেবাটি এখন ব্যস্ত আছে, অনুগ্রহ করে কিছুক্ষণ পরে আবার চেষ্টা করুন।",
        "or": "ସେବା ବର୍ତ୍ତମାନ ବ୍ୟସ୍ତ ଅଛି, ଦୟାକରି କିଛି ସମୟ ପରେ ପୁଣି ଚେଷ୍ଟା କରନ୍ତୁ।",
        "en": "The service is currently busy, please try again in a moment."
    },
    "offline": {
        "hi": "आप ऑफ़लाइन प्रतीत होते हैं। कृपया इंटरनेट कनेक्शन जांचें।",
        "bn": "আপনি অফলাইনে আছেন বলে মনে হচ্ছে। ইন্টারনেট সংযোগ পরীক্ষা করুন।",
        "or": "ଆପଣ ଅଫଲାଇନ୍ ଥିବା ପରି ମନେହେଉଛି। ଇଣ୍ଟରନେଟ୍ ସଂଯୋଗ ଯାଞ୍ଚ କରନ୍ତୁ।",
        "en": "You appear to be offline. Please check your internet connection."
    },
    "rate_limited": {
        "hi": "बहुत सारे अनुरोध आ रहे हैं। कृपया कुछ सेकंड प्रतीक्षा करें।",
        "bn": "অনেক অনুরোধ আসছে। দয়া করে কয়েক সেকেন্ড অপেক্ষা করুন।",
        "or": "ଅନେକ ଅନୁରୋଧ ଆସୁଛି। ଦୟାକରି କିଛି ସେକେଣ୍ଡ ଅପେକ୍ଷା କରନ୍ତୁ।",
        "en": "Too many requests. Please wait a few seconds."
    },
    "odia_stt_notice": {
        "hi": "व्हिस्पर आधिकारिक तौर पर ओडिया का समर्थन नहीं करता है। कृपया टाइप करें।",
        "bn": "হুইস্পার আনুষ্ঠানিকভাবে ওড়িয়া সমর্থন করে না। দয়া করে টাইপ করুন।",
        "or": "ହୁଇସ୍ପର ଆନୁଷ୍ଠାନିକ ଭାବରେ ଓଡ଼ିଆ ସମର୍ଥନ କରେ ନାହିଁ। ଦୟାକରି ଟାଇପ୍ କରନ୍ତୁ।",
        "en": "Whisper does not officially support Odia STT. Please use text input for Odia."
    }
}

def get_canned_message(key: str, lang: str = "hi") -> str:
    """Return localized canned message with graceful Hindi fallback."""
    category = CANNED_MESSAGES.get(key, CANNED_MESSAGES["retry"])
    return category.get(lang, category.get("hi", "कृपया दोबारा प्रयास करें।"))

def normalize_lang_code(code: Optional[str], default: Optional[str] = None) -> Optional[str]:
    """Normalize input language string to 2-letter ISO code. Returns default if unrecognized."""
    if not code:
        return default
    code = code.strip().lower()
    if code in ("hi", "hindi", "hin", "hi-in"):
        return "hi"
    if code in ("bn", "bengali", "ben", "bn-in", "bn-bd"):
        return "bn"
    if code in ("or", "odia", "ory", "oriya", "or-in"):
        return "or"
    if code in ("en", "english", "eng", "en-us", "en-in"):
        return "en"
    return default

def detect_script(text: str) -> Optional[str]:
    """Detect dominant script by counting characters in known Unicode blocks."""
    if not text:
        return None

    counts = {
        "hi": len(re.findall(r"[\u0900-\u097F]", text)), # Devanagari
        "bn": len(re.findall(r"[\u0980-\u09FF]", text)), # Bengali
        "or": len(re.findall(r"[\u0B00-\u0B7F]", text)), # Odia
        "en": len(re.findall(r"[A-Za-z]", text)),        # Latin
    }

    best_lang, best_count = max(counts.items(), key=lambda item: item[1])
    if best_count > 0:
        return best_lang
    return None

def get_language_list():
    """Return serializable list of supported languages."""
    return [
        {
            "code": l["code"],
            "name": l["name"],
            "native": l["native"],
            "stt": l["stt"],
            "tts": l["tts"]
        }
        for l in LANGUAGES.values()
    ]
