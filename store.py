"""Single-player progress, persisted to a small JSON file."""

import json
import os

PATH = os.path.join(os.path.dirname(__file__), "data", "player.json")
DEFAULT = {"total_xp": 0, "battles_won": 0,
           "questions_answered": 0, "questions_correct": 0}


def load():
    try:
        with open(PATH, encoding="utf-8") as fh:
            return {**DEFAULT, **json.load(fh)}
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(DEFAULT)


def save(player):
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    with open(PATH, "w", encoding="utf-8") as fh:
        json.dump(player, fh, indent=2)
