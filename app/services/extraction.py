import json
from groq import Groq
from app.config import get_config

_cfg  = get_config()
_groq = Groq(api_key=_cfg.GROQ_API_KEY)

SYSTEM_PROMPT = """\
You are a precise data-extraction assistant.
Given a transcript of someone describing employment details,
extract the following fields and return ONLY valid JSON — no prose, no markdown fences.

Schema:
{
  "employer":       string | null,
  "role":           string | null,
  "wage":           string | null,
  "start_date":     string | null,
  "end_date":       string | null,
  "hours_per_week": number | null,
  "notes":          string | null
}

Rules:
- wage  → include amount + currency + period, e.g. "₹18,000/month" or "$25/hr"
- dates → ISO-8601 if possible; end_date = "present" if still employed
- Return ONLY the JSON object, nothing else
"""

def extract_employment_data(transcript: str) -> dict:
    response = _groq.chat.completions.create(
        model=_cfg.LLM_MODEL,
        temperature=0,
        max_tokens=512,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": f"Transcript:\n{transcript}"},
        ],
    )
    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)