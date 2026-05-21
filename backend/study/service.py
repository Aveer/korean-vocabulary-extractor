"""Study service functions and SRS scheduling."""

from __future__ import annotations

import json
import math
from datetime import date, datetime, timedelta, timezone

from study.db import db, now_iso, parse_json_list


VALID_STATUSES = {"new", "known", "ignored"}
VALID_RATINGS = {"again", "hard", "good", "easy"}


def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def _card_row_to_dict(row) -> dict:
    glosses = parse_json_list(row["glosses"])
    study_status = row["study_status"] if "study_status" in row.keys() else None
    display = row["display"] or row["lemma"]
    pos = row["pos"] or "unknown"
    study_line = row["study_line"] or f"({', '.join(glosses) if glosses else '—'}) {row['source_fragment']} ({row['lemma']})"
    csv_front = row["csv_front"] or study_line
    csv_back = row["csv_back"] or (row["source_fragment_translation"] or "")
    return {
        "id": row["id"],
        "lemma": row["lemma"],
        "display": display,
        "pos": pos,
        "level": row["level"],
        "sourceFragment": row["source_fragment"],
        "sourceSentence": row["source_sentence"],
        "englishGlosses": glosses,
        "koreanDefinition": row["definition"],
        "sourceFragmentTranslation": row["source_fragment_translation"],
        "sourceSentenceTranslation": row["source_sentence_translation"],
        "studyLine": study_line,
        "csvFront": csv_front,
        "csvBack": csv_back,
        "dueAt": row["due_at"],
        "intervalDays": row["interval_days"],
        "ease": row["ease"],
        "difficultyScore": row["difficulty_score"] if row["difficulty_score"] is not None else 1.0,
        "frequencyInText": row["frequency_in_text"] if row["frequency_in_text"] is not None else 1,
        "reason": row["reason"] or "Saved from your deck",
        "repetitions": row["repetitions"],
        "lapses": row["lapses"],
        "suspended": bool(row["suspended"]),
        "studyStatus": study_status or "new",
    }


def save_card(payload: dict) -> dict:
    lemma = payload["lemma"]
    source_fragment = payload.get("sourceFragment") or payload.get("source_fragment")
    source_sentence = payload.get("sourceSentence") or payload.get("source_sentence")
    now = now_iso()
    with db() as conn:
        existing = conn.execute("SELECT status FROM lemmas WHERE lemma=?", (lemma,)).fetchone()
        existing_status = existing["status"] if existing else None
        saved_status = existing_status or "new"
        if existing_status is not None:
            conn.execute(
                "UPDATE lemmas SET display=COALESCE(display, ?), pos=COALESCE(pos, ?), level=COALESCE(level, ?), glosses=COALESCE(glosses, ?), definition=COALESCE(definition, ?), updated_at=? WHERE lemma=?",
                (payload.get("display") or lemma, payload.get("pos") or "unknown", payload.get("level"), _json(payload.get("englishGlosses") or payload.get("english_glosses") or []), payload.get("koreanDefinition") or payload.get("korean_definition"), now, lemma),
            )
        else:
            conn.execute(
                "INSERT INTO lemmas(lemma, status, display, pos, level, glosses, definition, updated_at) VALUES(?,?,?,?,?,?,?,?)",
                (lemma, saved_status, payload.get("display") or lemma, payload.get("pos") or "unknown", payload.get("level"), _json(payload.get("englishGlosses") or payload.get("english_glosses") or []), payload.get("koreanDefinition") or payload.get("korean_definition"), now),
            )
        conn.execute(
            """INSERT INTO cards(lemma, source_fragment, source_sentence, display, pos, level, glosses, definition, source_fragment_translation, source_sentence_translation, study_line, csv_front, csv_back, due_at, interval_days, ease, repetitions, lapses, reason, frequency_in_text, difficulty_score, created_at, updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(lemma, source_fragment) DO UPDATE SET
                display=excluded.display, pos=excluded.pos, level=excluded.level, glosses=excluded.glosses, definition=excluded.definition,
                source_sentence=excluded.source_sentence, source_fragment_translation=excluded.source_fragment_translation,
                source_sentence_translation=excluded.source_sentence_translation, study_line=excluded.study_line,
                csv_front=excluded.csv_front, csv_back=excluded.csv_back, reason=excluded.reason,
                frequency_in_text=excluded.frequency_in_text, difficulty_score=excluded.difficulty_score, updated_at=excluded.updated_at""",
            (
                lemma, source_fragment, source_sentence, payload.get("display") or lemma, payload.get("pos") or "unknown", payload.get("level"),
                _json(payload.get("englishGlosses") or payload.get("english_glosses") or []), payload.get("koreanDefinition") or payload.get("korean_definition"),
                payload.get("sourceFragmentTranslation") or payload.get("source_fragment_translation"),
                payload.get("sourceSentenceTranslation") or payload.get("source_sentence_translation"),
                payload.get("studyLine") or payload.get("study_line") or f"({', '.join(payload.get('englishGlosses') or []) if (payload.get('englishGlosses') or payload.get('english_glosses')) else '—'}) {source_fragment} ({lemma})",
                payload.get("csvFront") or payload.get("csv_front") or f"({', '.join(payload.get('englishGlosses') or []) if (payload.get('englishGlosses') or payload.get('english_glosses')) else '—'}) {source_fragment} ({lemma})",
                payload.get("csvBack") or payload.get("csv_back") or (payload.get("sourceFragmentTranslation") or payload.get("source_fragment_translation") or ""),
                payload.get("dueAt") or now, payload.get("intervalDays") or payload.get("interval_days") or 1, payload.get("ease") or 2.5, payload.get("repetitions") or 0, payload.get("lapses") or 0,
                payload.get("reason") or "Saved from your deck", payload.get("frequencyInText") or payload.get("frequency_in_text") or 1, payload.get("difficultyScore") or payload.get("difficulty_score") or 1.0, now, now,
            ),
        )
        row = conn.execute(
            """SELECT c.*, l.status AS study_status
            FROM cards c LEFT JOIN lemmas l ON l.lemma = c.lemma
            WHERE c.lemma=? AND c.source_fragment=?""",
            (lemma, source_fragment),
        ).fetchone()
        return _card_row_to_dict(row)


def list_cards(limit: int | None = None, offset: int | None = None) -> list[dict]:
    sql = "SELECT c.*, l.status AS study_status FROM cards c LEFT JOIN lemmas l ON l.lemma = c.lemma ORDER BY c.id DESC"
    params = []
    if limit is not None:
        sql += " LIMIT ?"
        params.append(limit)
    if offset is not None:
        sql += " OFFSET ?"
        params.append(offset)
    with db() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [_card_row_to_dict(row) for row in rows]


def count_cards() -> int:
    with db() as conn:
        return conn.execute("SELECT COUNT(*) AS n FROM cards").fetchone()["n"]


def delete_card(card_id: int) -> bool:
    with db() as conn:
        cur = conn.execute("DELETE FROM cards WHERE id=?", (card_id,))
        return cur.rowcount > 0


def set_lemma_status(lemma: str, status: str) -> dict:
    if status not in VALID_STATUSES:
        raise ValueError("Invalid lemma status")
    with db() as conn:
        conn.execute("INSERT INTO lemmas(lemma, status, updated_at, glosses) VALUES(?,?,?, '[]') ON CONFLICT(lemma) DO UPDATE SET status=excluded.status, updated_at=excluded.updated_at", (lemma, status, now_iso()))
        row = conn.execute("SELECT lemma, status FROM lemmas WHERE lemma=?", (lemma,)).fetchone()
        return {"lemma": row["lemma"], "status": row["status"]}


def due_reviews(limit: int = 20) -> dict:
    now = now_iso()
    with db() as conn:
        due_count = conn.execute(
            """SELECT COUNT(*) AS n
            FROM cards c LEFT JOIN lemmas l ON l.lemma = c.lemma
            WHERE c.suspended=0 AND c.due_at <= ?
              AND COALESCE(l.status, 'new') NOT IN ('known', 'ignored')""",
            (now,),
        ).fetchone()["n"]
        rows = conn.execute(
            """SELECT c.*, l.status AS study_status
            FROM cards c LEFT JOIN lemmas l ON l.lemma = c.lemma
            WHERE c.suspended=0 AND c.due_at <= ?
              AND COALESCE(l.status, 'new') NOT IN ('known', 'ignored')
            ORDER BY c.due_at ASC, c.id ASC LIMIT ?""",
            (now, limit),
        ).fetchall()
        return {"dueCount": due_count, "cards": [_card_row_to_dict(row) for row in rows]}


def _schedule(card_row, rating: str):
    ease = float(card_row["ease"])
    interval = int(card_row["interval_days"])
    reps = int(card_row["repetitions"])
    lapses = int(card_row["lapses"])
    if rating == "again":
        ease = max(1.3, ease - 0.2)
        interval = 1
        reps = 0
        lapses += 1
        xp = 1
    elif rating == "hard":
        ease = max(1.3, ease - 0.15)
        interval = max(1, int(round(max(1, interval) * 1.2)))
        reps += 1
        xp = 3
    elif rating == "good":
        interval = max(1, int(round((interval if reps else 1) * ease)))
        reps += 1
        xp = 5
    else:
        ease = min(3.0, ease + 0.05)
        interval = max(1, int(round((interval if reps else 2) * ease * 1.5)))
        reps += 1
        xp = 8
    next_due = (datetime.now(timezone.utc) + timedelta(days=interval)).isoformat()
    return next_due, interval, ease, reps, lapses, xp


def review_card(card_id: int, rating: str) -> dict:
    if rating not in VALID_RATINGS:
        raise ValueError("Invalid review rating")
    with db() as conn:
        row = conn.execute("SELECT * FROM cards WHERE id=?", (card_id,)).fetchone()
        if not row:
            raise LookupError("Card not found")
        next_due, interval, ease, reps, lapses, xp = _schedule(row, rating)
        conn.execute("UPDATE cards SET due_at=?, interval_days=?, ease=?, repetitions=?, lapses=?, updated_at=? WHERE id=?", (next_due, interval, ease, reps, lapses, now_iso(), card_id))
        conn.execute("INSERT INTO reviews(card_id, rating, interval_days, ease, xp_gained, reviewed_at) VALUES(?,?,?,?,?,?)", (card_id, rating, interval, ease, xp, now_iso()))
        return {"nextDueAt": next_due, "intervalDays": interval, "ease": ease, "xpGained": xp}


def stats() -> dict:
    today = date.today().isoformat()
    with db() as conn:
        today_reviews = conn.execute("SELECT COUNT(*) AS n FROM reviews WHERE reviewed_at >= ?", (today,)).fetchone()["n"]
        due_count = conn.execute(
            """SELECT COUNT(*) AS n
            FROM cards c LEFT JOIN lemmas l ON l.lemma = c.lemma
            WHERE c.suspended=0 AND c.due_at <= ?
              AND COALESCE(l.status, 'new') NOT IN ('known', 'ignored')""",
            (now_iso(),),
        ).fetchone()["n"]
        total_cards = conn.execute("SELECT COUNT(*) AS n FROM cards").fetchone()["n"]
        known = conn.execute("SELECT COUNT(*) AS n FROM lemmas WHERE status='known'").fetchone()["n"]
        ignored = conn.execute("SELECT COUNT(*) AS n FROM lemmas WHERE status='ignored'").fetchone()["n"]
        xp = conn.execute("SELECT COALESCE(SUM(xp_gained), 0) AS n FROM reviews").fetchone()["n"]
        review_days = [
            row["d"]
            for row in conn.execute(
                "SELECT DISTINCT substr(reviewed_at,1,10) AS d FROM reviews ORDER BY d DESC"
            ).fetchall()
        ]
    level = 1 + int(math.sqrt(xp // 25))
    streak = _current_streak(review_days)
    return {"todayReviews": today_reviews, "dueCount": due_count, "totalCards": total_cards, "knownLemmas": known, "ignoredLemmas": ignored, "currentStreakDays": streak, "xp": xp, "level": level}


def _current_streak(review_days: list[str]) -> int:
    if not review_days:
        return 0

    days = [datetime.fromisoformat(day).date() for day in review_days]
    today = date.today()
    expected = today if days[0] == today else today - timedelta(days=1)
    streak = 0
    for day in days:
        if day != expected:
            break
        streak += 1
        expected -= timedelta(days=1)
    return streak


def get_lemma_status(lemma: str) -> str | None:
    with db() as conn:
        row = conn.execute("SELECT status FROM lemmas WHERE lemma=?", (lemma,)).fetchone()
        return row["status"] if row else None


def get_saved_card_id(lemma: str, source_fragment: str) -> int | None:
    with db() as conn:
        row = conn.execute("SELECT id FROM cards WHERE lemma=? AND source_fragment=?", (lemma, source_fragment)).fetchone()
        return row["id"] if row else None
