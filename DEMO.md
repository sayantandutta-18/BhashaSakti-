# BhashaSandhi 2-Minute Live Demo Script (Hack4Haldia'26)

This exact demo script is structured for presentation before hackathon judges to verify all core requirements, both prize categories, and bonus points within 120 seconds.

---

## ⏱️ Pre-Demo Warmup (T minus 2 Minutes)
1. **Pre-warm models**:
   Open browser and hit `/health` on the deployed URL to ensure the container is warm:
   ```bash
   curl -s https://<your-live-url>/health
   ```
2. **Pre-test audio**: Tap the Hindi chip and say "नमस्ते", confirm speaker is unmuted and phone volume is at 80%+.

---

## 🎬 Demo Progression (120 Seconds)

### Step 1: Spoken Hindi Weather Query (0:00 – 0:25)
- **Action:** Open the live URL on your mobile phone. Tap the **हिन्दी** chip.
- **Interaction:** Tap the microphone button and ask:
  > *"आज मौसम कैसा है?"* (or click the suggestion pill).
- **Point out to judges:**
  - Notice the **Pipeline Stepper** animating live: `Listening` &rarr; `Whisper` &rarr; `Gemma 4` &rarr; `MMS-TTS`.
  - Listen to the high-fidelity spoken Hindi reply detailing real-time Haldia weather retrieved live via Open-Meteo.

### Step 2: Language Auto-Detection & Bengali Speech (0:25 – 0:45)
- **Action:** Switch the language chip back to **Auto-detect ✨**.
- **Interaction:** Tap the microphone and speak in Bengali:
  > *"এখন সময় কত?"* (What time is it now?)
- **Point out to judges:**
  - Auto-detection identifies Bengali automatically.
  - The UI language badge dynamically flips to **বাংলা**.
  - Gemma 4 grounds the answer in Asia/Kolkata Indian Standard Time and Meta MMS-TTS replies with native Bengali speech.

### Step 3: Multimodal Vision with Gemma 4 (0:45 – 1:10)
*(Qualifies for "Best Use of Gemma 4" prize)*
- **Action:** Tap the 📷 camera icon, snap or attach a photo (e.g., an object on the table, a badge, a laptop keyboard, or a street sign).
- **Interaction:** Ask in Hindi:
  > *"इस तस्वीर में क्या दिखाई दे रहा है?"*
- **Point out to judges:**
  - Gemma 4 processes image pixels alongside Indic language prompt through the Gemini API.
  - Assistant responds in spoken Hindi describing the visual contents of the image.

### Step 4: Odia Native Voice Output & Technical Honesty (1:10 – 1:30)
- **Action:** Select the **ଓଡ଼ିଆ** chip.
- **Interaction:** Type an Odia query in the text box (or select prompt):
  > *"ଭାଷାସନ୍ଧି କ'ଣ?"* (What is BhashaSandhi?)
- **Point out to judges:**
  - Emphasize our **technical honesty**: Whisper does not officially support Odia speech recognition.
  - Rather than making false claims, we provide reliable Odia text input and speak the response natively using Meta MMS-TTS (`facebook/mms-tts-ory`).

### Step 5: Offline Resilience & Service Worker (1:30 – 1:45)
- **Action:** Turn on **Airplane Mode** on the phone or disconnect Wi-Fi.
- **Interaction:** Submit a quick test query.
- **Point out to judges:**
  - Red offline banner appears immediately.
  - The Progressive Web App shell is cached by `sw.js`.
  - Browser's built-in `speechSynthesis` speaks the localized offline fallback notice.

### Step 6: Architecture Verification & DigitalOcean Stack (1:45 – 2:00)
*(Qualifies for "Best Open-Source AI Project" prize)*
- **Action:** Show the open-weight **Models Table** in `README.md` and live `/health` JSON.
- **Point out to judges:**
  - Every single stage in the pipeline is an open-weight model: Whisper large-v3 (MIT), Gemma 4 (Gemma Terms), Meta MMS-TTS (CC-BY-NC 4.0).
  - Deployed in a production Docker container on **DigitalOcean App Platform**.

---

## 🛡️ Fallback Plan
If venue Wi-Fi becomes congested or drops entirely:
1. Switch to mobile hotspot.
2. The PWA works offline with cached app shell and browser speech synthesis.
3. Keep a 60-second screen-recording video of the live mobile turn on your phone camera roll.
