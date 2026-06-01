# Study Hero

A Flask web app that turns PDF study material into a quiz game. Upload a PDF, an
LLM generates multiple-choice (and fill-in-the-blank / ordering) questions from
the text, and you practice them in a training mode or fight a topic "boss" in a
battle mode. Correct answers earn XP, XP levels you up, and topics unlock along a
world map.

The LLM runs locally through [Ollama](https://ollama.com) by default, so no API
key or cloud account is needed to try it. You can point it at any
OpenAI-compatible API instead if you prefer.

## Features

- Upload a PDF and get questions generated from its contents automatically.
- Three question types: multiple choice, fill in the blank, and drag-to-order.
- Training mode for practice and a battle mode with boss HP, player HP, and damage.
- XP, levels, and a world map where defeating a topic boss unlocks the next topic.
- Per-topic quests with progress tracking.

## Stack

- Backend: Python, Flask, SQLAlchemy, Flask-Migrate
- Database: SQLite (any SQLAlchemy URL via `DATABASE_URL`)
- Frontend: Jinja templates, Bootstrap 5, vanilla JS
- PDF text extraction: PyPDF2
- Question generation: Ollama (local) or any OpenAI-compatible API

## Setup

1. Clone and enter the repo:
   ```bash
   git clone <repository-url>
   cd study_hero
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Apply the database migrations:
   ```bash
   flask --app app db upgrade
   ```

4. Get an LLM ready. By default the app talks to a local Ollama instance:
   ```bash
   ollama pull llama3.1:8b
   ollama serve                  # or just open the Ollama app
   ```
   To use a cloud provider instead, see the configuration table below.

## Configuration

Configuration is read from environment variables (a `.env` file in the project
root is loaded automatically). All of these have defaults, so the app runs with
no `.env` at all when Ollama is available locally.

| Variable | Default | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | `default-secret-key` | Flask session signing key. Set a real value. |
| `DATABASE_URL` | `sqlite:///study_rpg.db` | SQLAlchemy database URL. |
| `UPLOAD_FOLDER` | `uploads` | Where uploaded PDFs are stored. |
| `LLM_PROVIDER` | `ollama` | `ollama` for local, or `openai` for an OpenAI-compatible API. |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint. |
| `OLLAMA_MODEL` | `llama3.1:8b` | Ollama model to use. |
| `OPENAI_API_KEY` | (empty) | API key when `LLM_PROVIDER=openai`. |
| `OPENAI_BASE_URL` | `https://api.openai.com` | Base URL when `LLM_PROVIDER=openai`. |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model when `LLM_PROVIDER=openai`. |

The `openai` provider just hits a `/v1/chat/completions` endpoint, so it also
works with anything that speaks that API (Gemini's OpenAI-compatible endpoint,
local servers, etc.).

## Run

```bash
python app.py
```

This starts the dev server at http://127.0.0.1:5000.

## How it works

1. Upload a PDF on the Upload page. PyPDF2 extracts the text and the first chunk
   is sent to the configured LLM.
2. The LLM returns questions as JSON, which are parsed, validated, and saved to
   the topic. The parser is deliberately forgiving: it strips code fences, accepts
   a few alternate key names, and repairs answers that do not exactly match an
   option.
3. Train or battle the topic. Answers are scored, XP is awarded, and quest and
   boss progress update.

There is no authentication yet. The app uses a single default user (id 1) that is
created on first request, so everything is stored against that one account.

## License

MIT. See [LICENSE](LICENSE).
