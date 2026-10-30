# Hack4Haldia'26 Official Submission Form (OrganizerHQ & Pull Request)

---

## 📋 OrganizerHQ Submission Fields

### Project Name
**BhashaSandhi (भाषासंधि)**

### One-Line Tagline
An end-to-end open-weight multilingual voice assistant empowering Hindi, Bengali, and Odia speakers with real-time streaming, multimodal vision, and tool grounding.

### One-Paragraph Description
BhashaSandhi (The Language Bridge) breaks communication barriers across northern and eastern India by delivering a natural, spoken-in/spoken-out voice assistant operating natively in Hindi, Bengali, and Odia. Powered by OpenAI Whisper large-v3 for speech-to-text, Google's Gemma 4 (via Gemini API) for reasoning, multimodal image understanding, and intent routing, and Meta MMS-TTS for speech synthesis, BhashaSandhi provides sub-second conversational turns, real-time weather and time queries, and grounded FAQ retrieval. Built with a mobile-first PWA interface featuring offline resilience and pipeline visualization, the entire stack runs open-weight AI models deployed on DigitalOcean App Platform.

### Target Prize Categories Selected
1. **Best Open-Source AI Project** (DigitalOcean / MLH + DEV)
2. **Best Use of Gemma 4** (Gemma 4 via Gemini API, Multimodal & Streaming)

### Public GitHub Repository URL
`https://github.com/Debarun1205/BhashaSandhi`

### Live Production Deployment URL
`https://bhashasandhi-hack4haldia.ondigitalocean.app` *(Replace with deployed URL)*

### Technologies & Models Used
- **Backend:** Python 3.11, Flask, Gunicorn, SQLite3
- **Speech-to-Text (STT):** OpenAI Whisper large-v3 (Groq API cloud & faster-whisper local)
- **Intelligence & Vision:** Google Gemma 4 (`gemma-4-26b-a4b-it` / `gemma-4-31b-it`) via `google-genai` SDK
- **Text-to-Speech (TTS):** Meta MMS-TTS (`facebook/mms-tts-hin`, `facebook/mms-tts-ben`, `facebook/mms-tts-ory`) with PyTorch & Transformers; gTTS fallback
- **Tools & APIs:** Open-Meteo Geocoding & Weather Forecast API, ZoneInfo IST, grounded JSON FAQ
- **Frontend & PWA:** Vanilla JS, CSS3 Dark Theme, HTML5 MediaRecorder (Opus/MP4), Service Worker (`sw.js`), Google Fonts (Noto Sans Devanagari/Bengali/Oriya)
- **Deployment:** Docker, DigitalOcean App Platform / Droplet

### Team Members
- Team J (Hack4Haldia'26)
- Debarun Mukherjee ([@Debarun1205](https://github.com/Debarun1205))
- Sayantan Dutta

---

## 🔀 Pull Request Description Template

```markdown
### Live Demo URL
🌐 **[https://bhashasandhi-hack4haldia.ondigitalocean.app](https://bhashasandhi-hack4haldia.ondigitalocean.app)**

### Overview
This pull request submits **BhashaSandhi**, an end-to-end open-weight multilingual voice assistant built for **Hack4Haldia'26**, competing for:
1. 🏆 **Best Open-Source AI Project**
2. 🌟 **Best Use of Gemma 4**

### Key Features Implemented
- **Speech-to-Speech Hindi & Bengali Pipeline:** Whisper large-v3 STT + Gemma 4 reasoning + Meta MMS-TTS speech synthesis.
- **Odia Support with Honesty:** Odia text input + spoken native Odia output (`mms-tts-ory`), transparently documenting Whisper's lack of official Odia STT.
- **Gemma 4 Multimodal Vision:** Snap/upload a photo and ask questions in Hindi or Bengali.
- **Live Tool Grounding:** Real-time weather for Haldia (Open-Meteo) and IST time without external API keys.
- **Visual Pipeline Stepper & Streaming:** Real-time token streaming over Server-Sent Events (SSE).
- **SQLite Persistence:** Session history stored and fed back to conversational context.
- **Offline PWA Fallback:** Service Worker caching and browser SpeechSynthesis fallback.
- **Automated Tests:** Comprehensive unit test suite (`pytest tests/test_api.py`) and automated STT <-> TTS round-trip verification (`python tests/roundtrip.py`).
- **Production Containerization:** Optimized Dockerfile with CPU PyTorch and pre-cached MMS models, deployed to DigitalOcean App Platform.
```
