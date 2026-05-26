# voice-ledger

# Telegram Voice → Employment Data Bot

Accepts a voice note on Telegram, transcribes it, extracts structured
employment data (employer, wage, dates), and replies — all in under 2 seconds.

---

## What it does

```
User sends voice note
        │
        ▼
Groq Whisper  →  transcript (text)
        │
        ▼
Groq LLaMA    →  structured JSON
        │
        ▼
Telegram reply with formatted data
```

---

## Key Decisions

### 1. Groq over local Whisper + Anthropic

The original design ran OpenAI Whisper locally and used the Anthropic API for
extraction. That meant:

- A ~140 MB model download on every fresh deploy
- ffmpeg as a system dependency
- A ~2 GB Docker image
- 10–30 second cold starts while the model loaded into memory
- Two separate API keys and billing accounts

Switching to Groq consolidates both the ASR and LLM steps into one SDK and one
API key. The Docker image dropped to ~120 MB, cold start to ~2 seconds, and the
code got simpler — `groq.audio.transcriptions` and `groq.chat.completions` are
the only two external calls.

### 2. `whisper-large-v3-turbo` as the default ASR model

Groq offers two Whisper variants: `whisper-large-v3` and
`whisper-large-v3-turbo`. Turbo is meaningfully faster with negligible accuracy
difference for conversational speech. For a bot where the user is waiting for a
reply, latency matters more than squeezing out the last 0.5% WER on edge cases.
Turbo is the default; `whisper-large-v3` is a one-line swap if you need maximum
accuracy.

### 3. `llama-3.3-70b-versatile` as the default LLM

Two realistic options on Groq: `llama-3.3-70b-versatile` and
`llama-3.1-8b-instant`. The 70B model is the default because structured JSON
extraction with null-handling across varied phrasings benefits from the larger
model's instruction-following. The 8B model is fast enough and works well too —
it is exposed as a config option (`GROQ_LLM_MODEL`) for anyone who wants to
trade a little accuracy for lower latency.

### 4. `temperature=0` on the LLM call

Extraction is a deterministic task — given the same transcript, you always want
the same JSON back. Temperature 0 eliminates randomness and makes the output
consistent and testable.

### 5. System prompt returns raw JSON, no fences

The system prompt explicitly says "return ONLY valid JSON — no prose, no
markdown fences." LLMs still occasionally wrap output in ```json blocks, so
there is a fence-stripping fallback in `extract_employment_data()`. Asking for
raw JSON first avoids the parsing step in the majority of cases.

### 6. `task="translate"` for multilingual robustness

Whisper can either transcribe (speech → same language text) or translate
(speech → English text). The bot defaults to transcription, which preserves the
original language. If the LLM extraction step is unreliable on a particular
language, switching to `task="translate"` in the `transcribe()` function makes
Whisper output English regardless of input language — giving LLaMA a cleaner
surface to extract from. Supported languages include Hindi, Bengali, Tamil,
Telugu, and 95 others.

### 7. Status message edited in-place, not re-sent

Instead of sending separate messages ("Transcribing…", "Extracting…", then the
result), a single message is sent and then edited twice. This keeps the
conversation clean — one voice note in, one reply out — and avoids spamming the
user with intermediate messages they do not need once the result arrives.

### 8. Temp file deleted in a `finally` block

The OGG file is written to a temp path, passed to Groq, then deleted. The
deletion is in a `finally` block so it runs even if transcription throws an
exception. On a long-running bot, leaking temp files adds up.

### 9. Polling over webhooks

The bot uses long polling (`run_polling`) rather than a webhook. Polling works
on localhost with no domain, no TLS cert, and no reverse proxy — the right
default for local development. For a production deployment, swap to
`run_webhook()` and point a domain at the process. No other code changes needed.

---

## Setup

```bash
# 1. Get a bot token from @BotFather on Telegram
# 2. Get a Groq API key from console.groq.com

cp .env.example .env
# fill in TELEGRAM_BOT_TOKEN and GROQ_API_KEY

pip install -r requirements.txt
export $(cat .env | xargs)
python bot.py
```

---

## Configuration

| Variable             | Default                   | Description           |
|----------------------|---------------------------|-----------------------|
| TELEGRAM_BOT_TOKEN   | —                         | From @BotFather       |
| GROQ_API_KEY         | —                         | From console.groq.com |
| GROQ_WHISPER_MODEL   | whisper-large-v3-turbo    | ASR model             |
| GROQ_LLM_MODEL       | llama-3.3-70b-versatile   | Extraction model      |

---

## Extracted Schema

```json
{
  "employer":       "Infosys",
  "role":           "Python Developer",
  "wage":           "₹12,00,000/year",
  "start_date":     "2023-07-01",
  "end_date":       "present",
  "hours_per_week": null,
  "notes":          null
}
```