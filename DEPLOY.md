# BhashaSandhi Deployment Guide

This guide provides instructions to deploy **BhashaSandhi** on **DigitalOcean App Platform** (primary target for Hack4Haldia'26 and DigitalOcean / MLH prize eligibility) and **Hugging Face Spaces** (free 16 GB RAM fallback).

---

## Prerequisites & Environment Variables

Never commit secret keys to git. Configure these environment variables in your deployment settings:

| Variable | Description | Example / Default | Required? |
| :--- | :--- | :--- | :--- |
| `GEMINI_API_KEY` | Google AI Studio Key for Gemma 4 | `AIzaSy...` | Yes (for Gemma 4) |
| `GROQ_API_KEY` | Groq Cloud Key for Whisper large-v3 | `gsk_...` | Recommended (fast cloud STT) |
| `GEMMA_MODEL` | Gemma model identifier | `gemma-4-26b-a4b-it` | Default set |
| `STT_BACKEND` | Speech-to-text backend | `auto` | Default set |
| `PORT` | Container listen port | `8080` | Automatic on DO |

---

## Option 1: DigitalOcean App Platform (Recommended)

DigitalOcean App Platform will automatically build the `Dockerfile` from the GitHub repository and provision HTTPS (required for phone microphone permissions).

> [!IMPORTANT]
> The Meta MMS models require at least **2 GB RAM**. Select the **Basic 2 GB RAM / 1 vCPU** ($12/mo) or use the MLH Hackathon $25 DigitalOcean promo credit. Do not choose the 512 MB tier.

### Method A: Web Console (Click-path)
1. Log in to [DigitalOcean Cloud Console](https://cloud.digitalocean.com/).
2. Click **Create** (top right) &rarr; **Apps**.
3. Choose **GitHub** as the source and authorize access to `https://github.com/Debarun1205/BhashaSandhi`.
4. Select the `main` branch. DigitalOcean will auto-detect the `Dockerfile`.
5. Under **Resource Size**, choose **Basic (2 GB RAM, 1 vCPU)**.
6. Under **Environment Variables**, add:
   - `GEMINI_API_KEY`: `<Your Google Gemini API Key>` (Type: Encrypt)
   - `GROQ_API_KEY`: `<Your Groq API Key>` (Type: Encrypt)
   - `GEMMA_MODEL`: `gemma-4-26b-a4b-it`
   - `STT_BACKEND`: `auto`
7. Click **Next** &rarr; Review &rarr; **Create App**.
8. Once built, copy your live HTTPS URL (e.g., `https://bhashasandhi-xxxxx.ondigitalocean.app`).

### Method B: `doctl` CLI Command
```bash
# 1. Authenticate doctl
doctl auth init

# 2. Deploy from repo
doctl apps create --spec app.yaml
```

Example `app.yaml`:
```yaml
name: bhashasandhi
region: blr
services:
  - name: web
    github:
      repo: Debarun1205/BhashaSandhi
      branch: main
      deploy_on_push: true
    dockerfilePath: Dockerfile
    instance_count: 1
    instance_size_slug: basic-m # 2GB RAM
    http_port: 8080
    envs:
      - key: GEMINI_API_KEY
        scope: RUN_AND_BUILD_TIME
        type: SECRET
      - key: GROQ_API_KEY
        scope: RUN_AND_BUILD_TIME
        type: SECRET
      - key: GEMMA_MODEL
        value: gemma-4-26b-a4b-it
      - key: STT_BACKEND
        value: auto
```

---

## Option 2: DigitalOcean Droplet (Docker)

If using a 2 GB Droplet:
```bash
# On droplet:
git clone https://github.com/Debarun1205/BhashaSandhi.git
cd BhashaSandhi

# Create .env
cat <<EOF > .env
GEMINI_API_KEY=your_key
GROQ_API_KEY=your_key
GEMMA_MODEL=gemma-4-26b-a4b-it
STT_BACKEND=auto
PORT=8080
EOF

# Build & Run container
docker build -t bhashasandhi .
docker run -d --restart unless-stopped -p 8080:8080 --env-file .env --name bhashasandhi bhashasandhi
```

---

## Option 3: Hugging Face Spaces (Free 16 GB Fallback)

Hugging Face Spaces provides 16 GB RAM for Docker apps for free:
1. Go to [Hugging Face Spaces](https://huggingface.co/spaces) &rarr; **Create New Space**.
2. Select **Docker** as Space SDK (Blank).
3. Under **Settings &rarr; Variables and Secrets**, add `GEMINI_API_KEY` and `GROQ_API_KEY`.
4. Push this repository to the HF Space git remote.

---

## Verifying Deployment

Run the health check against your live deployed domain:
```bash
curl -s https://<your-deployed-url>/health | jq .
```

Expected output:
```json
{
  "status": "ok",
  "project": "BhashaSandhi",
  "stack": "flask",
  "stt_backend": "groq",
  "llm_model": "gemma-4-26b-a4b-it",
  "tts_backends": ["mms-tts", "gtts"],
  "models_loaded": {
    "hi": true,
    "bn": true,
    "or": true
  }
}
```
Open the URL in Safari or Chrome on your mobile phone to verify HTTPS microphone capture and audio streaming.
