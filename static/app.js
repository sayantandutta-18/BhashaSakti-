/**
 * BhashaSandhi Frontend Application Logic
 * Supports Voice Recording, Speech Recognition, Multilingual Streaming,
 * Multimodal Attachment, and Browser SpeechSynthesis.
 */

(() => {
  // Application State
  const state = {
    selectedLang: "auto",
    isRecording: false,
    mediaRecorder: null,
    audioChunks: [],
    speechRecognizer: null,
    recognizedSpeech: "",
    recordingTimerInterval: null,
    recordingSeconds: 0,
    attachedImageFile: null,
    sessionId: localStorage.getItem("bhasha_session_id") || "sess_" + Math.random().toString(36).substring(2, 10),
    isProcessing: false
  };

  localStorage.setItem("bhasha_session_id", state.sessionId);

  // DOM Elements
  const micBtn = document.getElementById("mic-btn");
  const textForm = document.getElementById("text-form");
  const textInput = document.getElementById("text-input");
  const imageUpload = document.getElementById("image-upload");
  const imagePreviewContainer = document.getElementById("image-preview-container");
  const imagePreview = document.getElementById("image-preview");
  const removeImageBtn = document.getElementById("remove-image-btn");
  const chatViewport = document.getElementById("chat-viewport");
  const chips = document.querySelectorAll(".chip");
  const visualizerContainer = document.getElementById("audio-visualizer-container");
  const recordingTimer = document.getElementById("recording-timer");
  const ttsPlayer = document.getElementById("tts-audio-player");
  const offlineBanner = document.getElementById("offline-banner");
  const connectionIndicator = document.getElementById("connection-indicator");
  const clearBtn = document.getElementById("clear-btn");
  const suggestedPrompts = document.getElementById("suggested-prompts");

  // Settings Modal Elements
  const settingsBtn = document.getElementById("settings-btn");
  const settingsModal = document.getElementById("settings-modal");
  const closeModalBtn = document.getElementById("close-modal-btn");
  const saveConfigBtn = document.getElementById("save-config-btn");
  const geminiKeyInput = document.getElementById("gemini-key-input");
  const groqKeyInput = document.getElementById("groq-key-input");
  const modalStatus = document.getElementById("modal-status");

  // Stepper Elements
  const steps = {
    listen: document.querySelector('.step[data-step="listen"]'),
    transcribe: document.querySelector('.step[data-step="transcribe"]'),
    think: document.querySelector('.step[data-step="think"]'),
    speak: document.querySelector('.step[data-step="speak"]')
  };

  function setStepper(stepName) {
    const order = ["listen", "transcribe", "think", "speak"];
    const currentIndex = order.indexOf(stepName);

    order.forEach((s, idx) => {
      const el = steps[s];
      if (!el) return;
      el.classList.remove("active", "completed");
      if (idx < currentIndex) {
        el.classList.add("completed");
      } else if (idx === currentIndex) {
        el.classList.add("active");
      }
    });
  }

  function resetStepper() {
    Object.values(steps).forEach(el => {
      if (el) el.classList.remove("active", "completed");
    });
  }

  // Settings Modal Handlers
  const inspectBtn = document.getElementById("inspect-btn");
  const inspectorModal = document.getElementById("inspector-modal");
  const closeInspectorBtn = document.getElementById("close-inspector-btn");
  const openSourcePill = document.getElementById("open-source-pill");
  const gemmaPill = document.getElementById("gemma-pill");

  function openInspector() {
    if (inspectorModal) inspectorModal.classList.remove("hidden");
  }

  if (inspectBtn) inspectBtn.addEventListener("click", openInspector);
  if (openSourcePill) openSourcePill.addEventListener("click", openInspector);
  if (gemmaPill) gemmaPill.addEventListener("click", openInspector);
  if (closeInspectorBtn) {
    closeInspectorBtn.addEventListener("click", () => {
      inspectorModal.classList.add("hidden");
    });
  }

  if (settingsBtn) {
    settingsBtn.addEventListener("click", async () => {
      settingsModal.classList.remove("hidden");
      modalStatus.textContent = "";
      try {
        const res = await fetch("/api/config");
        const cfg = await res.json();
        if (cfg.has_gemini) geminiKeyInput.placeholder = "API Key Active (Click to update)";
        if (cfg.has_groq) groqKeyInput.placeholder = "API Key Active (Click to update)";
      } catch (e) {}
    });
  }

  if (closeModalBtn) {
    closeModalBtn.addEventListener("click", () => {
      settingsModal.classList.add("hidden");
    });
  }

  if (saveConfigBtn) {
    saveConfigBtn.addEventListener("click", async () => {
      const gKey = geminiKeyInput.value.trim();
      const qKey = groqKeyInput.value.trim();
      modalStatus.textContent = "Saving keys...";
      try {
        const res = await fetch("/api/config", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ gemini_key: gKey, groq_key: qKey })
        });
        const data = await res.json();
        if (data.status === "ok") {
          modalStatus.textContent = "Configuration saved successfully!";
          setTimeout(() => {
            settingsModal.classList.add("hidden");
          }, 1200);
        }
      } catch (err) {
        modalStatus.textContent = "Error saving keys.";
      }
    });
  }

  // Language Chips Selection
  chips.forEach(chip => {
    chip.addEventListener("click", () => {
      chips.forEach(c => {
        c.classList.remove("active");
        c.setAttribute("aria-checked", "false");
      });
      chip.classList.add("active");
      chip.setAttribute("aria-checked", "true");
      state.selectedLang = chip.getAttribute("data-lang");
    });
  });

  // Prompt Chips Click Handlers
  if (suggestedPrompts) {
    suggestedPrompts.addEventListener("click", (e) => {
      const btn = e.target.closest(".prompt-chip");
      if (btn) {
        const text = btn.getAttribute("data-text");
        textInput.value = text;
        submitTurn({ text });
      }
    });
  }

  // Clear Chat
  clearBtn.addEventListener("click", () => {
    state.sessionId = "sess_" + Math.random().toString(36).substring(2, 10);
    localStorage.setItem("bhasha_session_id", state.sessionId);
    chatViewport.innerHTML = `
      <div class="message assistant">
        <div class="bubble">
          <div class="bubble-header"><span class="sender-name">BhashaSandhi</span><span class="model-tag">Gemma 4</span></div>
          <div class="bubble-content">नमस्ते! আমি আপনাকে কীভাবে সাহায্য করতে পারি?</div>
        </div>
      </div>
    `;
    resetStepper();
  });

  // Image Upload Handling
  imageUpload.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) {
      state.attachedImageFile = file;
      const reader = new FileReader();
      reader.onload = (evt) => {
        imagePreview.src = evt.target.result;
        imagePreviewContainer.classList.remove("hidden");
      };
      reader.readAsDataURL(file);
    }
  });

  removeImageBtn.addEventListener("click", () => {
    state.attachedImageFile = null;
    imageUpload.value = "";
    imagePreviewContainer.classList.add("hidden");
  });

  // Chat UI Helpers
  function appendMessage(role, text = "") {
    const msg = document.createElement("div");
    msg.className = `message ${role}`;

    const bubble = document.createElement("div");
    bubble.className = "bubble";

    const header = document.createElement("div");
    header.className = "bubble-header";
    header.innerHTML = role === "user"
      ? '<span class="sender-name">You</span>'
      : '<span class="sender-name">BhashaSandhi</span><span class="model-tag">Gemma 4 &bull; MMS</span>';

    const content = document.createElement("div");
    content.className = "bubble-content";
    content.textContent = text;

    bubble.appendChild(header);
    bubble.appendChild(content);
    msg.appendChild(bubble);
    chatViewport.appendChild(msg);
    chatViewport.scrollTop = chatViewport.scrollHeight;

    return { msg, bubble, content };
  }

  // Audio Playback & Voice Synthesis
  function speakResponse(text, lang = "hi", base64Audio = null, bubbleElement = null) {
    let playedAudio = false;

    // 1. Play synthesized WAV from backend if present
    if (base64Audio) {
      try {
        const audioSrc = `data:audio/wav;base64,${base64Audio}`;
        ttsPlayer.src = audioSrc;
        ttsPlayer.play().then(() => {
          playedAudio = true;
        }).catch(e => {
          // If browser blocked auto-play, fallback to speech synthesis
          speakWithBrowser(text, lang);
        });

        if (bubbleElement) {
          let replayBtn = bubbleElement.querySelector(".bubble-audio-btn");
          if (!replayBtn) {
            replayBtn = document.createElement("button");
            replayBtn.className = "bubble-audio-btn";
            replayBtn.innerHTML = "🔊 Replay Voice";
            replayBtn.onclick = () => {
              ttsPlayer.src = audioSrc;
              ttsPlayer.play().catch(() => speakWithBrowser(text, lang));
            };
            bubbleElement.appendChild(replayBtn);
          }
        }
      } catch (err) {
        console.warn("Audio element error:", err);
      }
    }

    // 2. Call browser SpeechSynthesis for native pronunciation
    speakWithBrowser(text, lang);
  }

  function speakWithBrowser(text, lang = "hi") {
    if (!("speechSynthesis" in window) || !text) return;
    try {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      const bcpMap = {
        hi: "hi-IN",
        bn: "bn-IN",
        or: "hi-IN", // Oriya fallback voice
        en: "en-IN"
      };
      utterance.lang = bcpMap[lang] || "hi-IN";
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      window.speechSynthesis.speak(utterance);
    } catch (e) {
      console.warn("speechSynthesis error:", e);
    }
  }

  // Submit Turn to Backend
  async function submitTurn({ audioBlob = null, text = "" }) {
    if (state.isProcessing) return;
    state.isProcessing = true;

    const queryText = text || state.recognizedSpeech;
    let userBubbleContent = null;
    if (queryText) {
      const { content } = appendMessage("user", queryText);
      userBubbleContent = content;
    }

    const { bubble: assistantBubble, content: assistantContent } = appendMessage("assistant", "...");
    textInput.value = "";

    const formData = new FormData();
    formData.append("session_id", state.sessionId);
    if (state.selectedLang !== "auto") {
      formData.append("lang", state.selectedLang);
    }

    if (queryText) formData.append("text", queryText);
    if (audioBlob) {
      const ext = (audioBlob.type && audioBlob.type.includes("mp4")) ? "recording.mp4" : "recording.webm";
      formData.append("audio", audioBlob, ext);
    }
    if (state.attachedImageFile) {
      formData.append("image", state.attachedImageFile);
      state.attachedImageFile = null;
      imagePreviewContainer.classList.add("hidden");
      imageUpload.value = "";
    }

    setStepper(audioBlob ? "transcribe" : "think");

    try {
      const response = await fetch("/api/chat/stream", {
        method: "POST",
        body: formData
      });

      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }

      setStepper("think");
      assistantContent.textContent = "";

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";
      let fullReply = "";
      let detectedLang = state.selectedLang !== "auto" ? state.selectedLang : "hi";
      let receivedAudioB64 = null;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop();

        for (const evtBlock of events) {
          const lines = evtBlock.split("\n");
          let eventType = "message";
          let dataStr = "";

          for (const line of lines) {
            if (line.startsWith("event:")) {
              eventType = line.replace("event:", "").trim();
            } else if (line.startsWith("data:")) {
              dataStr = line.replace("data:", "").trim();
            }
          }

          if (!dataStr) continue;
          let parsedData = {};
          try { parsedData = JSON.parse(dataStr); } catch (e) { parsedData = { raw: dataStr }; }

          if (eventType === "transcript") {
            if (!userBubbleContent && parsedData.transcript) {
              const { content } = appendMessage("user", parsedData.transcript);
              userBubbleContent = content;
              chatViewport.appendChild(assistantBubble.parentElement);
            }
            if (parsedData.language) {
              detectedLang = parsedData.language;
              if (state.selectedLang === "auto") {
                chips.forEach(c => {
                  if (c.getAttribute("data-lang") === detectedLang) {
                    c.classList.add("active");
                  } else if (c.getAttribute("data-lang") !== "auto") {
                    c.classList.remove("active");
                  }
                });
              }
            }
            setStepper("think");
          } else if (eventType === "token") {
            fullReply += parsedData.token;
            assistantContent.textContent = fullReply;
            chatViewport.scrollTop = chatViewport.scrollHeight;
          } else if (eventType === "audio") {
            setStepper("speak");
            receivedAudioB64 = parsedData.audio_b64;
          } else if (eventType === "done") {
            setStepper("speak");
            speakResponse(fullReply, detectedLang, receivedAudioB64, assistantBubble);
          } else if (eventType === "error") {
            assistantContent.textContent = parsedData.error || "Error processing turn.";
          }
        }
      }

      setTimeout(resetStepper, 2000);
    } catch (err) {
      console.error("Submission failed:", err);
      const fallbackMsg = "सेवा अभी व्यस्त है, कृपया कुछ क्षण बाद पुनः प्रयास करें।";
      assistantContent.textContent = fallbackMsg;
      speakResponse(fallbackMsg, "hi", null, assistantBubble);
      resetStepper();
    } finally {
      state.isProcessing = false;
      state.recognizedSpeech = "";
    }
  }

  // Audio Recording + SpeechRecognition Dual Engine
  async function startRecording() {
    try {
      state.recognizedSpeech = "";
      state.audioChunks = [];

      // 1. Start Browser Speech Recognition for instant client-side transcription
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        state.speechRecognizer = new SpeechRecognition();
        state.speechRecognizer.continuous = true;
        state.speechRecognizer.interimResults = true;

        const langMap = {
          hi: "hi-IN",
          bn: "bn-IN",
          or: "hi-IN",
          en: "en-IN",
          auto: "hi-IN"
        };
        state.speechRecognizer.lang = langMap[state.selectedLang] || "hi-IN";

        state.speechRecognizer.onresult = (event) => {
          let interimTranscript = "";
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
              state.recognizedSpeech += transcript + " ";
            } else {
              interimTranscript += transcript;
            }
          }
          const display = (state.recognizedSpeech + interimTranscript).trim();
          if (display) {
            textInput.value = display;
          }
        };

        state.speechRecognizer.onerror = (e) => {
          console.warn("Speech recognition notice:", e.error);
        };

        try {
          state.speechRecognizer.start();
        } catch (e) {}
      }

      // 2. Start MediaRecorder for Audio File Capture
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      let options = { mimeType: "audio/webm;codecs=opus" };
      if (!MediaRecorder.isTypeSupported(options.mimeType)) {
        options = MediaRecorder.isTypeSupported("audio/mp4") ? { mimeType: "audio/mp4" } : {};
      }

      state.mediaRecorder = new MediaRecorder(stream, options);

      state.mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          state.audioChunks.push(e.data);
        }
      };

      state.mediaRecorder.onstop = () => {
        stream.getTracks().forEach(track => track.stop());
        const audioBlob = new Blob(state.audioChunks, { type: state.mediaRecorder.mimeType || "audio/webm" });
        const recognized = state.recognizedSpeech.trim();
        if (audioBlob.size > 200 || recognized) {
          submitTurn({ audioBlob: audioBlob.size > 200 ? audioBlob : null, text: recognized });
        } else {
          resetStepper();
        }
      };

      state.mediaRecorder.start(200);
      state.isRecording = true;
      micBtn.classList.add("recording");
      visualizerContainer.classList.remove("hidden");
      setStepper("listen");

      // Recording timer (max 30s)
      state.recordingSeconds = 0;
      recordingTimer.textContent = "00:00";
      state.recordingTimerInterval = setInterval(() => {
        state.recordingSeconds++;
        const mins = String(Math.floor(state.recordingSeconds / 60)).padStart(2, "0");
        const secs = String(state.recordingSeconds % 60).padStart(2, "0");
        recordingTimer.textContent = `${mins}:${secs}`;
        if (state.recordingSeconds >= 30) {
          stopRecording();
        }
      }, 1000);

    } catch (err) {
      console.error("Microphone access error:", err);
      alert("Microphone permission denied or not supported on this browser.");
    }
  }

  function stopRecording() {
    if (!state.isRecording) return;
    state.isRecording = false;
    micBtn.classList.remove("recording");
    visualizerContainer.classList.add("hidden");
    if (state.recordingTimerInterval) {
      clearInterval(state.recordingTimerInterval);
    }
    if (state.speechRecognizer) {
      try { state.speechRecognizer.stop(); } catch (e) {}
    }
    if (state.mediaRecorder && state.mediaRecorder.state !== "inactive") {
      state.mediaRecorder.stop();
    }
  }

  // Mic Button Listener
  micBtn.addEventListener("click", () => {
    if (state.isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  });

  // Text Form Submission
  textForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = textInput.value.trim();
    if (text) {
      submitTurn({ text });
    }
  });

  // Network Status
  function updateOnlineStatus() {
    if (navigator.onLine) {
      offlineBanner.classList.add("hidden");
      connectionIndicator.classList.remove("dot-offline");
      connectionIndicator.title = "System Online";
    } else {
      offlineBanner.classList.remove("hidden");
      connectionIndicator.classList.add("dot-offline");
      connectionIndicator.title = "Offline (Local mode)";
    }
  }

  window.addEventListener("online", updateOnlineStatus);
  window.addEventListener("offline", updateOnlineStatus);
  updateOnlineStatus();

  // Register Service Worker
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("/sw.js").catch(() => {});
    });
  }
})();
