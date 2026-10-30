<div align="center">

# 🗣️ BhashaSakti
### भाषाशक्ति · ভাষাশক্তি · ଭାଷାଶକ୍ତି

**🎙️ A multilingual, voice-first AI assistant for Indic languages.**

Speak naturally in Hindi, Bengali, or Odia. Get spoken answers, ask questions about images, check live information, and interact through text, all through a mobile-first web experience.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Deployed on DigitalOcean](https://img.shields.io/badge/Deployed%20on-DigitalOcean-blue?logo=digitalocean)](DEPLOY.md)
[![STT: Whisper large-v3](https://img.shields.io/badge/STT-Whisper%20large--v3-orange)](https://huggingface.co/openai/whisper-large-v3)
[![LLM: Gemma 4](https://img.shields.io/badge/LLM-Gemma%204-blue)](https://ai.google.dev/gemma)
[![TTS: Meta MMS-TTS](https://img.shields.io/badge/TTS-Meta%20MMS--TTS-green)](https://huggingface.co/facebook/mms-tts-hin)

[🚀 Live Demo](#-live-demo) · [✨ Features](#-key-features) · [🏗️ Architecture](#️-system-architecture) · [🛠️ Getting Started](#️-getting-started) · [📡 API](#-api-reference)

</div>

---

## 📑 Table of Contents

- [🌐 Overview](#-overview)
- [🚀 Live Demo](#-live-demo)
- [✨ Key Features](#-key-features)
- [🇮🇳 Supported Languages](#-supported-languages)
- [🏗️ System Architecture](#️-system-architecture)
- [🧠 AI Models and Technologies](#-ai-models-and-technologies)
- [💎 How Gemma 4 Is Used](#-how-gemma-4-is-used)
- [🛠️ Getting Started](#️-getting-started)
  - [📋 Prerequisites](#-prerequisites)
  - [💻 Local Setup](#-local-setup)
  - [🐳 Run with Docker](#-run-with-docker)
- [🧪 Testing](#-testing)
- [📡 API Reference](#-api-reference)
- [⚠️ Known Limitations and Future Work](#️-known-limitations-and-future-work)
- [👥 Team and Credits](#-team-and-credits)
- [📄 License](#-license)

---

## 🌐 Overview

**BhashaSakti** is a multilingual, voice-first AI assistant designed to make AI more accessible to speakers of Indian languages. It supports conversational interactions in **Hindi**, **Bengali**, and **Odia**, with **English** available as a fallback for testing and debugging.

Users can speak to the assistant, type a message, or upload a photograph and ask a question about it. The assistant can also handle grounded requests such as checking the weather, telling the current time, and answering questions from a curated FAQ knowledge base.

The application combines speech recognition, language understanding, tool execution, multimodal image understanding, text-to-speech synthesis, and conversation history in one web application.

### 🙋 What users can do

- 🎤 Talk to the assistant in Hindi or Bengali and receive a spoken response
- ⌨️ Enter text in supported Indic languages
- 📷 Ask questions about an uploaded photograph
- 🌦️ Request weather information and the current Indian Standard Time
- 📚 Ask questions covered by the built-in FAQ knowledge base
- 💬 Continue conversations with session-based history
- 🔤 Use the text interface when voice interaction is unavailable

---

## 🚀 Live Demo

| | |
|---|---|
| 🌍 **Live application** | https://bhashasandhi-hack4haldia.ondigitalocean.app |
| ❤️ **Health check** | `GET /health` |
| 📘 **Deployment guide** | [`DEPLOY.md`](DEPLOY.md) |

> 📝 **Deployment note:** The current live URL retains the previous `bhashasandhi` deployment slug. Update it if the application is redeployed under a new URL.

### 🏆 Hackathon Focus

- 🥇 **Best Open-Source AI Project**: DigitalOcean / MLH + DEV
- 💎 **Best Use of Gemma 4**: Gemma 4 through Gemini API, including multimodal vision and streaming

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🎙️ **Voice conversations** | Single-turn and multi-turn voice interactions |
| 🔍 **Language detection** | Detects speech language through Whisper and text script through Unicode heuristics |
| 🖼️ **Multimodal image input** | Upload or capture a photograph and ask questions about it |
| ⚡ **Streaming responses** | Streams generated text to the chat interface using Server-Sent Events (SSE) |
| 🌦️ **Live weather** | Retrieves weather information through Open-Meteo |
| 🕐 **Current time** | Uses `zoneinfo` for Indian Standard Time (`Asia/Kolkata`) |
| 📚 **Grounded FAQ** | Answers supported questions using `faq.json` |
| 💾 **Conversation history** | Stores turns in SQLite and provides recent context to the language model |
| 📱 **Progressive Web App** | Includes a service worker and browser speech-synthesis fallback |
| 🛡️ **Request protection** | Per-IP in-memory token-bucket rate limiting, a 10 MB audio limit, and temporary-file cleanup |

---

## 🇮🇳 Supported Languages

The table below reflects the current implementation and its known limitations.

| Language | Code | 🎤 Voice Input (STT) | ⌨️ Text Input | 🔊 Voice Output (TTS) | Notes |
|---|:---:|:---:|:---:|:---:|---|
| 🇮🇳 **Hindi** | `hi` | ✅ | ✅ | ✅ | Whisper large-v3 and Meta MMS-TTS Hindi |
| 🇮🇳 **Bengali** | `bn` | ✅ | ✅ | ✅ | Whisper large-v3 and Meta MMS-TTS Bengali |
| 🇮🇳 **Odia** | `or` | ⚠️ Best-effort / officially unsupported | ✅ | ✅ | Odia text is answered and spoken using `facebook/mms-tts-ory`; Whisper has no official Odia model |
| 🇬🇧 **English** | `en` | ✅ | ✅ | ✅ | Fallback for testing and debugging |

> ⚠️ **Odia speech recognition:** Odia text input and speech output are supported. Whisper does not officially provide an Odia speech-recognition model, so Odia voice input is not claimed as fully supported.

---

## 🏗️ System Architecture

The application follows a pipeline that connects the web client to speech recognition, intent routing, AI response generation, tool execution, persistence, and speech synthesis.

### 🔄 Request flow

1. 📤 The user sends **audio, text, or an image** from the web client.
2. 🎙️ Audio is transcribed using **Whisper large-v3** through Groq, with a local **faster-whisper** fallback.
3. 🧭 The **intent router** identifies whether the request needs a tool, a normal AI response, or image understanding.
4. 🛠️ Weather, time, and FAQ requests use their corresponding **grounded data sources**.
5. 💎 **Gemma 4** generates the response and supports multimodal image understanding.
6. 🔊 **Meta MMS-TTS** synthesizes speech in the selected language.
7. 💾 The application returns the response to the client and stores conversation turns in **SQLite**.

---

## 🧠 AI Models and Technologies

### 🤖 Models

| Pipeline Role | Model / Service | Size | License / Terms | Execution |
|---|---|---|---|---|
| 🎙️ Speech-to-Text | Whisper large-v3 | ~1.55B parameters | MIT | Hosted through Groq; local faster-whisper fallback (Apache 2.0) |
| 🧠 Reasoning, intent, vision and response | Gemma 4 (`gemma-4-26b-a4b-it`; fallback `gemma-4-31b-it`) | 26B / 31B | Gemma Terms of Use | Gemini API using the `google-genai` SDK |
| 🔊 Hindi text-to-speech | `facebook/mms-tts-hin` | ~150M (VITS) | CC-BY-NC 4.0 | Local CPU using PyTorch / Transformers |
| 🔊 Bengali text-to-speech | `facebook/mms-tts-ben` | ~150M (VITS) | CC-BY-NC 4.0 | Local CPU using PyTorch / Transformers |
| 🔊 Odia text-to-speech | `facebook/mms-tts-ory` | ~150M (VITS) | CC-BY-NC 4.0 | Local CPU using PyTorch / Transformers |

> ⚖️ **Model and licensing note:** The project uses a combination of open-weight models and hosted APIs. Gemma is accessed through the Gemini API, and Whisper is hosted through Groq in the primary path. Check each model's current terms before redistribution or commercial deployment; in particular, the listed MMS-TTS model cards specify **CC-BY-NC 4.0**.

### 🧰 Main Technology Stack

| Layer | Technologies |
|---|---|
| 🖥️ **Backend** | Python, Flask |
| 🎙️ **Speech recognition** | Whisper large-v3, Groq API, faster-whisper fallback |
| 🧠 **Language model and vision** | Gemma 4, Gemini API, `google-genai` |
| 🔊 **Speech synthesis** | Meta MMS-TTS, PyTorch, Hugging Face Transformers, gTTS fallback |
| 🗄️ **Database** | SQLite |
| ⚡ **Streaming** | Server-Sent Events (SSE) |
| 🌦️ **Weather** | Open-Meteo |
| 🕐 **Time** | Python `zoneinfo` |
| 📱 **Client** | Mobile-first web client / Progressive Web App |
| ☁️ **Deployment** | DigitalOcean App Platform, Docker |

---

## 💎 How Gemma 4 Is Used

Gemma 4 handles the application's **language understanding, intent routing, translation, image understanding, and response generation** through the official `google-genai` SDK.

📂 The relevant implementation is primarily in [`services/llm.py`](services/llm.py).

- 🗣️ **Spoken-style responses**: The system prompt constrains responses to 1–3 spoken-style sentences in the target Indic script, without Markdown or emojis, to make text-to-speech output more natural.
- 🔎 **Model discovery and fallback**: At startup, the application checks available models and can fall back from `gemma-4-26b-a4b-it` to `gemma-4-31b-it`.
- 🧭 **Structured intent routing**: `route_intent()` extracts JSON intents such as `time`, `weather`, `faq`, and `chat`, along with relevant city arguments.
- 🌐 **Translation**: `translate()` performs direct translation into the requested Indic language.
- 🖼️ **Image understanding**: `reply()` resizes uploaded images to a maximum 1024 px JPEG and sends them as image parts to Gemma 4.
- ⚡ **Streaming generation**: `reply_stream()` uses `client.models.generate_content_stream` to stream generated response content.

---

## 🛠️ Getting Started

### 📋 Prerequisites

Make sure you have the following installed:

- 🐍 Python
- 📦 pip
- 🔧 Git
- 🐳 Docker *(optional, for containerized execution)*

You will also need API keys for the services configured by the application:

- 🔑 `GEMINI_API_KEY`
- 🔑 `GROQ_API_KEY`

### 💻 Local Setup

**1️⃣ Clone the repository**

```bash
git clone https://github.com/Debarun1205/BhashaSandhi.git
cd BhashaSandhi
```

> 📝 The clone URL and directory above refer to the repository's current GitHub name. If the repository is renamed to `BhashaSakti`, update the URL and directory accordingly.

**2️⃣ Create and activate a virtual environment**

```bash
python -m venv venv
```

🐧 Linux / 🍎 macOS:

```bash
source venv/bin/activate
```

🪟 Windows:

```powershell
.\venv\Scripts\activate
```

**3️⃣ Install dependencies**

```bash
pip install -r requirements.txt
```

**4️⃣ Configure environment variables**

```bash
cp .env.example .env
```

On Windows PowerShell, use:

```powershell
Copy-Item .env.example .env
```

Add your API keys to `.env`:

```env
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
```

**5️⃣ Start the application**

```bash
python app.py
```

🎉 Open the application at: **http://localhost:8080**

### 🐳 Run with Docker

Build the Docker image:

```bash
docker build -t bhashasakti .
```

Run the container:

```bash
docker run -p 8080:8080 --env-file .env bhashasakti
```

🎉 The application will be available at **http://localhost:8080**.

---

## 🧪 Testing

✅ Run the API smoke tests:

```bash
pytest tests/test_api.py -v
```

🔁 Run the automated speech-recognition and speech-synthesis round-trip test:

```bash
python tests/roundtrip.py
```

> 💡 The round-trip test is designed to check STT and TTS agreement without requiring a human voice recording.

---

## 📡 API Reference

| Method | Endpoint | Request | Response |
|:---:|---|---|---|
| `GET` | `/health` | None | Health status, project name, stack details |
| `GET` | `/api/languages` | None | Array of language objects: `code`, `name`, `native`, `stt`, `tts` |
| `POST` | `/api/transcribe` | Multipart: `audio` file; optional `language` | Transcript, detected language, backend, duration |
| `POST` | `/api/translate` | JSON: `{"text":"...","target":"hi","source":"en"}` | Translated text and language codes |
| `POST` | `/api/speak` | JSON: `{"text":"...","lang":"hi"}` | WAV audio with `X-TTS-Backend` header |
| `POST` | `/api/chat` | Multipart: `audio` or `text`; optional `image`, `lang`, `session_id` | Transcript, reply text, base64 audio, timing details |
| `POST` | `/api/chat/stream` | Multipart: same fields as `/api/chat` | SSE events: `transcript`, `token`, `audio`, `done` |
| `GET` | `/api/history` | Query parameters: `session_id`, `limit` | Latest N conversation turns from SQLite |

> 📖 For exact request and response schemas, refer to the backend implementation and API tests.

---

## ⚠️ Known Limitations and Future Work

- 🗣️ **Odia speech recognition**: Whisper does not officially support Odia. The current implementation supports Odia text input and speech output. A future improvement is fine-tuning or adapting an ASR model using the Odia Mozilla Common Voice dataset.
- 🧮 **Memory requirements**: Meta MMS-TTS models require approximately 1.5 GB of RAM. Deployment should use a node with at least 2 GB RAM, according to the current project configuration.
- 💾 **Database persistence**: SQLite data may be lost when deployed on an ephemeral container filesystem. A production deployment should use persistent volumes or migrate to managed PostgreSQL.
- 🌩️ **Hosted model dependencies**: The primary speech-recognition and language-model paths depend on external API availability and valid API credentials.

---

## 👥 Team and Credits

| | |
|---|---|
| 🧑‍💻 **Team** | Team J |
| 🏆 **Hackathon** | Hack4Haldia '26 |
| 📄 **License** | MIT |

### 🙏 Acknowledgements

Thanks to the teams and communities behind **DigitalOcean**, **Google DeepMind (Gemma)**, **Meta AI (MMS)**, and **OpenAI (Whisper)** for their models, tools, and infrastructure.

---

## 📄 License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

---

<div align="center">

**🌏 BhashaSakti: Bringing AI conversations closer to every language.**

⭐ If you like this project, please give it a star! ⭐

</div>
