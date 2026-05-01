"""
Logging persistant des candidatures et de la file de review.
- applied_log.json  : candidatures envoyees (score >= 80)
- pending_review.json : offres a evaluer manuellement (score 68-79)
Structure ready pour future tracking des reponses recruteurs.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

logger   = logging.getLogger(__name__)
LOG_FILE = Path("applied_log.json")
PENDING_FILE = Path("pending_review.json")


def _read_json(path: Path) -> list:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _write_json(path: Path, records: list) -> None:
    try:
        path.write_text(
            json.dumps(records, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as e:
        logger.error("[LOG] Impossible d'ecrire %s: %s", path, e)


def _build_entry(offer: dict, score_result: dict) -> dict:
    """Construit l'entree de log enrichie."""
    return {
        "date":             datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "offer_id":         offer.get("id", offer.get("composite_id", "?")),
        "titre":            offer.get("titre", ""),
        "entreprise":       offer.get("entreprise", ""),
        "pays":             offer.get("pays", ""),
        "ville":            offer.get("ville", ""),
        "duree":            offer.get("duree", ""),
        "secteur":          offer.get("secteur", ""),
        "role":             score_result.get("role", ""),
        "industry":         score_result.get("industry_det", ""),
        "score":            score_result.get("total", 0),
        "score_detail": {
            "role_fit":     score_result.get("role_fit", 0),
            "country":      score_result.get("country", 0),
            "industry":     score_result.get("industry", 0),
            "mission_fit":  score_result.get("mission_fit", 0),
        },
        "matched_missions": score_result.get("matched_missions", []),
        # Champ pour tracking futur des reponses recruteurs
        "recruiter_response": None,   # "entretien" | "rejet" | "silence" | None
        "recruiter_date":     None,
        "notes":              None,
    }


def log_application(offer: dict, score_result: dict, success: bool) -> None:
    """Append une candidature envoyee dans applied_log.json."""
    entry = _build_entry(offer, score_result)
    entry["success"] = success
    entry["status"]  = "applied"

    records = _read_json(LOG_FILE)
    records.append(entry)
    _write_json(LOG_FILE, records)
    logger.info("[LOG] Candidature enregistree : %s | score=%d | missions=%s",
                entry["titre"][:50], entry["score"],
                ",".join(entry["matched_missions"][:2]) or "-")


def log_pending(offer: dict, score_result: dict) -> None:
    """Append une offre 68-79 dans pending_review.json pour review manuelle."""
    entry = _build_entry(offer, score_result)
    entry["success"] = None
    entry["status"]  = "pending_review"

    records = _read_json(PENDING_FILE)
    # Eviter doublons : meme offer_id
    if any(r.get("offer_id") == entry["offer_id"] for r in records):
        return

    records.append(entry)
    _write_json(PENDING_FILE, records)
    logger.info("[LOG] Offre en attente review : %s | score=%d",
                entry["titre"][:50], entry["score"])


def stats() -> dict:
    """Stats rapides sur les candidatures envoyees."""
    records = _read_json(LOG_FILE)
    if not records:
        return {}

    total   = len(records)
    success = sum(1 for r in records if r.get("success"))
    pays_c  = {}
    role_c  = {}
    for r in records:
        pays_c[r.get("pays", "?")] = pays_c.get(r.get("pays", "?"), 0) + 1
        role_c[r.get("role", "?")] = role_c.get(r.get("role", "?"), 0) + 1

    pending = len(_read_json(PENDING_FILE))

    return {
        "total":         total,
        "success":       success,
        "pending_review": pending,
        "avg_score":     round(sum(r.get("score", 0) for r in records) / total, 1),
        "top_pays":      sorted(pays_c.items(), key=lambda x: -x[1])[:5],
        "top_roles":     sorted(role_c.items(), key=lambda x: -x[1])[:5],
    }
