"""
Logging persistant des candidatures envoyées.
Stocke : date, offre, pays, role, score, entreprise.
Fichier : applied_log.json (append-only)
"""

import json
import logging
from datetime import datetime
from pathlib import Path

logger  = logging.getLogger(__name__)
LOG_FILE = Path("applied_log.json")


def log_application(offer: dict, score_result: dict, success: bool) -> None:
    """Append une candidature dans applied_log.json."""
    entry = {
        "date":       datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "success":    success,
        "offer_id":   offer.get("id", offer.get("composite_id", "?")),
        "titre":      offer.get("titre", ""),
        "entreprise": offer.get("entreprise", ""),
        "pays":       offer.get("pays", ""),
        "ville":      offer.get("ville", ""),
        "duree":      offer.get("duree", ""),
        "secteur":    offer.get("secteur", ""),
        "role":       score_result.get("role", ""),
        "industry":   score_result.get("industry_det", ""),
        "score":      score_result.get("total", 0),
        "score_detail": {
            "role_fit": score_result.get("role_fit", 0),
            "country":  score_result.get("country", 0),
            "industry": score_result.get("industry", 0),
        },
    }

    records = []
    if LOG_FILE.exists():
        try:
            records = json.loads(LOG_FILE.read_text(encoding="utf-8"))
        except Exception:
            records = []

    records.append(entry)

    try:
        LOG_FILE.write_text(
            json.dumps(records, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as e:
        logger.error("[LOG] Impossible d'ecrire applied_log.json: %s", e)


def stats() -> dict:
    """Stats rapides sur les candidatures envoyees."""
    if not LOG_FILE.exists():
        return {}
    try:
        records = json.loads(LOG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

    total  = len(records)
    success= sum(1 for r in records if r.get("success"))
    pays_counter = {}
    role_counter = {}
    for r in records:
        pays_counter[r.get("pays", "?")] = pays_counter.get(r.get("pays", "?"), 0) + 1
        role_counter[r.get("role", "?")] = role_counter.get(r.get("role", "?"), 0) + 1

    return {
        "total":          total,
        "success":        success,
        "avg_score":      round(sum(r.get("score", 0) for r in records) / total, 1) if total else 0,
        "top_pays":       sorted(pays_counter.items(), key=lambda x: -x[1])[:5],
        "top_roles":      sorted(role_counter.items(), key=lambda x: -x[1])[:5],
    }
