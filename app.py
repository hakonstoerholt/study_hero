"""
Study Hero: a small study RPG. Turn notes, a PDF, or just a topic into a quest
of quiz questions, then battle through them. Correct answers damage the monster
and earn XP; wrong answers cost HP and summon the AI tutor.

Single-player and local by design. Run with: python app.py
"""

import uuid

from flask import Flask, jsonify, render_template, request

import ai
import game
import pdf_utils
import research
import store

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024     # 20 MB PDF cap

NUM_QUESTIONS = 5
BATTLE = {}             # the single active battle (local, one player)


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def player_payload():
    p = store.load()
    level, into, need = game.level_state(p["total_xp"])
    answered = p["questions_answered"]
    accuracy = round(p["questions_correct"] / answered * 100) if answered else 0
    return {**p, "level": level, "xp_into_level": into,
            "xp_for_level": need, "accuracy": accuracy}


def question_public(i):
    q = BATTLE["questions"][i]
    return {"index": i, "total": len(BATTLE["questions"]),
            "question": q["question"], "options": q["options"],
            "difficulty": q["difficulty"]}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.get("/api/player")
def api_player():
    return jsonify(player_payload())


@app.post("/api/quest")
def api_quest():
    mode = (request.form.get("mode")
            or (request.get_json(silent=True) or {}).get("mode") or "text")
    body = request.get_json(silent=True) or {}
    brief, researched, source = None, False, "Your notes"

    try:
        if mode == "pdf":
            f = request.files.get("file")
            if not f:
                return jsonify(error="No file was uploaded."), 400
            content = pdf_utils.extract_text(f.stream)
            source = f.filename
            if len(content) < 50:
                return jsonify(error="Couldn't read enough text from that PDF."), 400
        elif mode == "topic":
            topic = (body.get("topic") or "").strip()
            if not topic:
                return jsonify(error="Give me a topic to research."), 400
            notes = research.gather(topic)
            researched = bool(notes)
            brief = ai.study_brief_from_research(topic, notes)
            content, source = brief, topic
        else:
            content = (body.get("text") or "").strip()
            if len(content) < 50:
                return jsonify(error="Add a few more sentences to study from."), 400

        questions = ai.generate_questions(content, num_questions=NUM_QUESTIONS)
    except Exception as exc:                       # noqa: BLE001
        return jsonify(error=str(exc)), 500

    hp = len(questions) * game.MONSTER_HP_PER_Q
    BATTLE.clear()
    BATTLE.update(id=uuid.uuid4().hex[:8], questions=questions, idx=0,
                  monster_hp=hp, monster_hp_max=hp,
                  player_hp=game.PLAYER_HP_MAX, xp=0, correct=0)

    return jsonify(quest={"id": BATTLE["id"], "total": len(questions),
                          "monster_hp_max": hp,
                          "player_hp_max": game.PLAYER_HP_MAX,
                          "source": source, "researched": researched},
                   brief=brief, question=question_public(0))


@app.post("/api/answer")
def api_answer():
    if not BATTLE:
        return jsonify(error="No active quest."), 400

    choice = (request.get_json(silent=True) or {}).get("choice", "")
    q = BATTLE["questions"][BATTLE["idx"]]
    correct = choice == q["answer"]
    tutor = None

    if correct:
        dmg = game.damage_for(q["difficulty"])
        BATTLE["monster_hp"] = max(0, BATTLE["monster_hp"] - dmg)
        BATTLE["xp"] += game.xp_for(q["difficulty"])
        BATTLE["correct"] += 1
    else:
        dmg = 0
        BATTLE["player_hp"] = max(0, BATTLE["player_hp"] - game.WRONG_DAMAGE)
        tutor = ai.tutor_explain(q["question"], q["options"], q["answer"], choice)

    BATTLE["idx"] += 1
    finished = (BATTLE["idx"] >= len(BATTLE["questions"])
                or BATTLE["player_hp"] <= 0)

    result = {"correct": correct, "answer": q["answer"],
              "explanation": q.get("explanation", ""), "tutor": tutor,
              "damage": dmg, "monster_hp": BATTLE["monster_hp"],
              "player_hp": BATTLE["player_hp"], "finished": finished}

    if finished:
        victory = BATTLE["monster_hp"] <= 0
        bonus = 25 if victory else 0
        p = store.load()
        p["total_xp"] += BATTLE["xp"] + bonus
        p["questions_answered"] += BATTLE["idx"]
        p["questions_correct"] += BATTLE["correct"]
        if victory:
            p["battles_won"] += 1
        store.save(p)
        result.update(victory=victory, xp_gained=BATTLE["xp"] + bonus,
                      correct_count=BATTLE["correct"], player=player_payload())
    else:
        result["question"] = question_public(BATTLE["idx"])

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
