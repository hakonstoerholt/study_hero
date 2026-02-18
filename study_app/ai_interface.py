"""
AI Interface for Study Hero - Question Generation

Supports multiple LLM providers with Ollama (local) as the default.
Provider can be swapped via config without changing any other code.
"""

import json
import random
import requests
from flask import current_app


# ---------------------------------------------------------------------------
# Provider: Ollama (default – free, local, private)
# ---------------------------------------------------------------------------

def _generate_with_ollama(prompt: str, model: str, base_url: str) -> str:
    """Send a prompt to a local Ollama instance and return the response text."""
    url = f"{base_url}/api/chat"
    payload = {
        "model": model,
        "stream": False,
        "format": "json",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a JSON quiz generator. You ONLY output valid JSON. "
                    "Never include explanatory text outside the JSON object."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "options": {
            "temperature": 0.7,
            "num_predict": 4096,
        },
    }

    try:
        resp = requests.post(url, json=payload, timeout=180)
        resp.raise_for_status()
        return resp.json()["message"]["content"]
    except requests.ConnectionError:
        raise ConnectionError(
            "Could not connect to Ollama. Make sure it is running "
            "(start it with `ollama serve` or open the Ollama app)."
        )
    except requests.Timeout:
        raise TimeoutError(
            "Ollama took too long to respond. The model may still be loading – "
            "try again in a moment."
        )
    except requests.HTTPError as exc:
        raise RuntimeError(f"Ollama returned an error: {exc}")


# ---------------------------------------------------------------------------
# Provider: OpenAI-compatible API (works with OpenAI, Gemini, etc.)
# ---------------------------------------------------------------------------

def _generate_with_openai(prompt: str, model: str, base_url: str, api_key: str) -> str:
    """Send a prompt to an OpenAI-compatible API and return the response text."""
    url = f"{base_url}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful quiz-generation assistant. Always respond with valid JSON only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as exc:
        raise RuntimeError(f"OpenAI-compatible API error: {exc}")


# ---------------------------------------------------------------------------
# Unified dispatcher
# ---------------------------------------------------------------------------

def _call_llm(prompt: str) -> str:
    """Route the prompt to the configured LLM provider."""
    provider = current_app.config.get("LLM_PROVIDER", "ollama").lower()

    if provider == "ollama":
        return _generate_with_ollama(
            prompt,
            model=current_app.config.get("OLLAMA_MODEL", "llama3.1:8b"),
            base_url=current_app.config.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        )
    elif provider == "openai":
        return _generate_with_openai(
            prompt,
            model=current_app.config.get("OPENAI_MODEL", "gpt-4o-mini"),
            base_url=current_app.config.get("OPENAI_BASE_URL", "https://api.openai.com"),
            api_key=current_app.config.get("OPENAI_API_KEY", ""),
        )
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_questions(content: str, num_questions: int = 5, num_options: int = 4) -> list[dict]:
    """
    Generate study questions from study material via LLM.

    Returns a list of dicts with keys:
        question, question_type, context, options, answer, explanation, difficulty
    """

    # Truncate content to a reasonable size for the context window
    study_text = content[:5000]

    prompt = f"""Create {num_questions} multiple-choice quiz questions based on the study material below.

Return a JSON object in this EXACT format:
{{"questions": [
  {{
    "question": "What is the primary purpose of X?",
    "options": ["To do A", "To do B", "To do C", "To do D"],
    "answer": "To do B",
    "explanation": "Because B is correct since...",
    "difficulty": 2,
    "context": "Short quote from the text relevant to this question"
  }}
]}}

Rules:
- Each question has exactly {num_options} options as full text (NOT letter prefixes like "A." or "B.")
- "answer" must EXACTLY match one of the "options" strings, word for word
- "difficulty" is an integer 1-5
- "context" is a 1-2 sentence excerpt from the study material
- Return ONLY the JSON object

Study material:
\"\"\"
{study_text}
\"\"\""""

    MAX_ATTEMPTS = 3
    last_error = None

    for attempt in range(MAX_ATTEMPTS):
        try:
            raw = _call_llm(prompt)
            print(f"[ai_interface] Attempt {attempt + 1}: LLM returned {len(raw)} chars")
            print(f"[ai_interface] First 300 chars: {raw[:300]}")
            questions = _parse_questions(raw, num_questions, num_options)
            print(f"[ai_interface] Successfully parsed {len(questions)} questions")
            break  # success
        except Exception as exc:
            last_error = exc
            print(f"[ai_interface] Attempt {attempt + 1}/{MAX_ATTEMPTS} failed: {exc}")
            if attempt < MAX_ATTEMPTS - 1:
                continue  # retry

    else:
        # All attempts failed
        print(f"[ai_interface] All {MAX_ATTEMPTS} attempts failed. Last error: {last_error}")
        return [
            {
                "question": f"Error generating questions: {last_error}",
                "question_type": "multiple_choice",
                "context": "",
                "options": ["N/A"] * num_options,
                "answer": "N/A",
                "explanation": "Could not generate questions. Please try again.",
                "difficulty": 1,
            }
        ]

    # Post-process valid questions
    for q in questions:
        if "question_type" not in q or q["question_type"] not in ("multiple_choice", "fill_blank", "ordering"):
            q["question_type"] = "multiple_choice"
        if "context" not in q or not q.get("context"):
            q["context"] = ""
        if q["question_type"] in ("multiple_choice", "fill_blank"):
            random.shuffle(q["options"])

    return questions


def _parse_questions(raw_text: str, expected_count: int, expected_options: int) -> list[dict]:
    """Parse and validate the LLM's JSON response into a clean question list."""
    text = raw_text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    # Try to parse JSON
    data = None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object or array within the text
        for start_char, end_char in [("{", "}"), ("[", "]")]:
            start = text.find(start_char)
            end = text.rfind(end_char)
            if start != -1 and end != -1 and end > start:
                try:
                    data = json.loads(text[start : end + 1])
                    break
                except json.JSONDecodeError:
                    continue

    if data is None:
        raise ValueError(f"Could not parse JSON from LLM response: {text[:300]}")

    # Normalise: accept {"questions": [...]} or bare [...] or any key with a list
    if isinstance(data, dict):
        for key in ("questions", "quiz", "items", "data"):
            if key in data and isinstance(data[key], list):
                questions = data[key]
                break
        else:
            # Try any key that has a list value
            questions = next((v for v in data.values() if isinstance(v, list)), None)
            if questions is None:
                # Maybe it's a single question as a dict?
                if "question" in data and "answer" in data:
                    questions = [data]
                else:
                    raise ValueError(f"JSON object has no list of questions. Keys found: {list(data.keys())}")
    elif isinstance(data, list):
        questions = data
    else:
        raise ValueError(f"Unexpected JSON type: {type(data)}")

    # Validate each question (be forgiving)
    valid = []
    for q in questions:
        if not isinstance(q, dict):
            continue

        # Accept various key names the LLM might use
        if "question" not in q:
            for alt in ("text", "prompt", "q"):
                if alt in q:
                    q["question"] = q.pop(alt)
                    break
        if "answer" not in q:
            for alt in ("correct_answer", "correct", "ans"):
                if alt in q:
                    q["answer"] = q.pop(alt)
                    break
        if "options" not in q:
            for alt in ("choices", "answers", "alternatives"):
                if alt in q:
                    q["options"] = q.pop(alt)
                    break

        # Must have at least question, options, answer
        if not all(k in q for k in ("question", "options", "answer")):
            print(f"[ai_interface] Skipping question missing keys: {list(q.keys())}")
            continue
        if not isinstance(q["options"], list) or len(q["options"]) < 2:
            print(f"[ai_interface] Skipping question with bad options: {q.get('options')}")
            continue

        # Ensure answer is a string
        q["answer"] = str(q["answer"])

        q_type = q.get("question_type", "multiple_choice")

        if q_type == "ordering":
            if len(q["options"]) < 2:
                continue
        else:
            # Pad options to expected count if short, or trim if long
            while len(q["options"]) < expected_options and len(q["options"]) >= 2:
                q["options"].append(f"Option {len(q['options']) + 1}")
            if len(q["options"]) > expected_options:
                # Keep the answer in, trim extras
                kept = [o for o in q["options"] if o == q["answer"]][:1]
                others = [o for o in q["options"] if o != q["answer"]]
                q["options"] = kept + others[:expected_options - len(kept)]
                random.shuffle(q["options"])

            # Try to match answer to an option
            if q["answer"] not in q["options"]:
                # Common LLM mistake: answer is just "A", "B", "C", "D" letter
                ans = q["answer"].strip()
                if len(ans) <= 2 and ans.upper() in "ABCDEFGH":
                    idx = ord(ans.upper()) - ord("A")
                    if 0 <= idx < len(q["options"]):
                        q["answer"] = q["options"][idx]

            if q["answer"] not in q["options"]:
                # Strip "A. ", "B. " etc. prefixes from options and try matching
                import re
                cleaned_opts = {}
                for o in q["options"]:
                    cleaned = re.sub(r'^[A-Ha-h][\.\)\:\-]\s*', '', o).strip()
                    cleaned_opts[cleaned.lower()] = o

                answer_lower = q["answer"].lower().strip()
                answer_cleaned = re.sub(r'^[A-Ha-h][\.\)\:\-]\s*', '', answer_lower).strip()

                if answer_cleaned in cleaned_opts:
                    q["answer"] = cleaned_opts[answer_cleaned]
                else:
                    # Fuzzy match: case-insensitive substring
                    match = None
                    for o in q["options"]:
                        if answer_lower == o.lower().strip():
                            match = o
                            break
                    if not match:
                        for o in q["options"]:
                            o_lower = o.lower().strip()
                            if (len(answer_lower) > 3 and answer_lower in o_lower) or \
                               (len(o_lower) > 3 and o_lower in answer_lower):
                                match = o
                                break
                    if match:
                        q["answer"] = match
                    else:
                        # Last resort: replace the last option with the answer
                        print(f"[ai_interface] Answer '{q['answer'][:50]}' not in options, forcing it in")
                        q["options"][-1] = q["answer"]

        # Ensure defaults for optional fields
        if "explanation" not in q:
            q["explanation"] = ""
        try:
            q["difficulty"] = max(1, min(5, int(q.get("difficulty", 3))))
        except (ValueError, TypeError):
            q["difficulty"] = 3

        valid.append(q)

    if not valid:
        raise ValueError(f"No valid questions extracted. Got {len(questions)} raw items.")

    return valid[:expected_count]
