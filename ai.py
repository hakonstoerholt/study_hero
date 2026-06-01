"""
LLM layer for Study Hero.

Question generation and JSON parsing are carried over from the original build
(they were already robust); this module adds a deep-research synthesis step and
a short tutor explanation, and drops the Flask dependency so it can be called
from anywhere. Provider defaults to a local Ollama model; an OpenAI-compatible
endpoint works too via env vars.
"""

import json
import os
import random
import re

import requests


def _cfg(key, default):
    return os.environ.get(key, default)


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------

def _ollama(messages, json_mode, num_predict):
    base = _cfg("OLLAMA_BASE_URL", "http://localhost:11434")
    payload = {
        "model": _cfg("OLLAMA_MODEL", "qwen2.5:3b"),
        "stream": False,
        "messages": messages,
        "options": {"temperature": 0.7, "num_predict": num_predict},
    }
    if json_mode:
        payload["format"] = "json"
    try:
        resp = requests.post(f"{base}/api/chat", json=payload, timeout=240)
        resp.raise_for_status()
        return resp.json()["message"]["content"]
    except requests.ConnectionError:
        raise ConnectionError(
            "Could not reach Ollama. Start it with `ollama serve` or open the app."
        )
    except requests.Timeout:
        raise TimeoutError("Ollama took too long; the model may still be loading.")


def _openai(messages, json_mode, num_predict):
    base = _cfg("OPENAI_BASE_URL", "https://api.openai.com")
    headers = {"Authorization": f"Bearer {_cfg('OPENAI_API_KEY', '')}",
               "Content-Type": "application/json"}
    payload = {"model": _cfg("OPENAI_MODEL", "gpt-4o-mini"),
               "messages": messages, "temperature": 0.7}
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    resp = requests.post(f"{base}/v1/chat/completions", json=payload,
                         headers=headers, timeout=120)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call(messages, json_mode=True, num_predict=4096):
    provider = _cfg("LLM_PROVIDER", "ollama").lower()
    if provider == "openai":
        return _openai(messages, json_mode, num_predict)
    return _ollama(messages, json_mode, num_predict)


# ---------------------------------------------------------------------------
# Question generation
# ---------------------------------------------------------------------------

_QUIZ_SYSTEM = ("You are a JSON quiz generator. You only output a valid JSON "
                "object and never any text around it.")


def generate_questions(content, num_questions=5, num_options=4):
    """Turn study material into a list of validated question dicts."""
    study_text = content[:6000]
    prompt = f"""Create {num_questions} multiple-choice quiz questions from the study material below.

Return JSON in exactly this shape:
{{"questions": [
  {{"question": "...", "options": ["A","B","C","D"], "answer": "B",
    "explanation": "why the answer is correct", "difficulty": 2}}
]}}

Rules:
- Exactly {num_options} options, each the full answer text (no "A." prefixes).
- "answer" must match one option word for word.
- "difficulty" is an integer 1-5.
- Output only the JSON object.

Study material:
\"\"\"{study_text}\"\"\""""

    last_error = None
    for attempt in range(3):
        try:
            raw = _call([{"role": "system", "content": _QUIZ_SYSTEM},
                         {"role": "user", "content": prompt}])
            questions = _parse_questions(raw, num_questions, num_options)
            for q in questions:
                random.shuffle(q["options"])
            return questions
        except Exception as exc:          # noqa: BLE001 - surfaced after retries
            last_error = exc
    raise RuntimeError(f"Could not generate questions: {last_error}")


def tutor_explain(question, options, correct, user_answer):
    """Short, friendly explanation of why an answer is right (plain text)."""
    prompt = (
        f"A student answered a quiz question wrong.\n\nQuestion: {question}\n"
        f"Options: {options}\nCorrect answer: {correct}\n"
        f"Their answer: {user_answer}\n\n"
        "In 2-3 sentences, explain why the correct answer is right and gently "
        "clear up the likely misunderstanding. Plain text, no preamble.")
    try:
        text = _call([{"role": "system", "content": "You are a patient tutor."},
                      {"role": "user", "content": prompt}],
                     json_mode=False, num_predict=400)
        return text.strip()
    except Exception:
        return f"The correct answer is: {correct}."


def study_brief_from_research(topic, notes):
    """Synthesize gathered web text (or none) into a compact study brief."""
    if notes:
        src = "\n\n".join(notes)[:7000]
        prompt = (
            f"Write a focused study brief on '{topic}' using the source notes "
            f"below. 4-6 short paragraphs covering the key facts a student must "
            f"know. Plain text.\n\nSOURCES:\n{src}")
    else:
        prompt = (
            f"Write a focused study brief on '{topic}': 4-6 short paragraphs "
            f"covering the key facts a student must know. Plain text.")
    try:
        return _call([{"role": "system",
                       "content": "You are a concise, accurate study author."},
                      {"role": "user", "content": prompt}],
                     json_mode=False, num_predict=1200).strip()
    except Exception as exc:
        raise RuntimeError(f"Could not synthesize a brief: {exc}")


# ---------------------------------------------------------------------------
# Parsing (carried over, lightly trimmed)
# ---------------------------------------------------------------------------

def _parse_questions(raw_text, expected_count, expected_options):
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    data = None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        for a, b in (("{", "}"), ("[", "]")):
            i, j = text.find(a), text.rfind(b)
            if i != -1 and j > i:
                try:
                    data = json.loads(text[i:j + 1])
                    break
                except json.JSONDecodeError:
                    continue
    if data is None:
        raise ValueError(f"No JSON found in response: {text[:200]}")

    if isinstance(data, dict):
        questions = next((v for v in data.values() if isinstance(v, list)), None)
        if questions is None and "question" in data:
            questions = [data]
    elif isinstance(data, list):
        questions = data
    else:
        questions = None
    if not questions:
        raise ValueError("No question list in JSON")

    valid = []
    for q in questions:
        if not isinstance(q, dict):
            continue
        for canon, alts in (("question", ("text", "prompt", "q")),
                            ("answer", ("correct_answer", "correct", "ans")),
                            ("options", ("choices", "answers", "alternatives"))):
            if canon not in q:
                for alt in alts:
                    if alt in q:
                        q[canon] = q.pop(alt)
                        break
        if not all(k in q for k in ("question", "options", "answer")):
            continue
        if not isinstance(q["options"], list) or len(q["options"]) < 2:
            continue
        q["answer"] = str(q["answer"])

        while 2 <= len(q["options"]) < expected_options:
            q["options"].append(f"Option {len(q['options']) + 1}")
        if len(q["options"]) > expected_options:
            kept = [o for o in q["options"] if o == q["answer"]][:1]
            others = [o for o in q["options"] if o != q["answer"]]
            q["options"] = kept + others[:expected_options - len(kept)]

        # models often label options ("A. ", "B: ", "1) "); map a bare-letter
        # answer to its option first, then strip labels so display stays clean
        araw = q["answer"].strip()
        if araw not in q["options"] and len(araw) <= 3 and araw.rstrip(".):").upper() in "ABCDEFGH":
            idx = ord(araw.rstrip(".):")[0].upper()) - ord("A")
            if 0 <= idx < len(q["options"]):
                q["answer"] = q["options"][idx]

        label = r'^\s*[\(\[]?\s*[A-Ha-h0-9]\s*[\)\].:\-]\s+'
        q["options"] = [re.sub(label, "", o).strip() for o in q["options"]]
        q["answer"] = re.sub(label, "", q["answer"]).strip()

        if q["answer"] not in q["options"]:
            low = {o.lower(): o for o in q["options"]}
            if q["answer"].lower() in low:
                q["answer"] = low[q["answer"].lower()]
            else:
                q["options"][-1] = q["answer"]

        q["explanation"] = q.get("explanation", "")
        try:
            q["difficulty"] = max(1, min(5, int(q.get("difficulty", 3))))
        except (ValueError, TypeError):
            q["difficulty"] = 3
        valid.append(q)

    if not valid:
        raise ValueError("No valid questions extracted")
    return valid[:expected_count]
