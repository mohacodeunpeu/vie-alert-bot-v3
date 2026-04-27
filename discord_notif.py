import logging
import time
from datetime import datetime, timezone

import requests

import config

logger = logging.getLogger(__name__)

EMBED_COLOR   = 5814783
COLOR_GREEN   = 5763719


def _fmt_salary(amount: float) -> str:
    if not amount:
        return "Non precise"
    return f"{int(amount):,} EUR/mois".replace(",", " ")


def _fmt_duration(months: int) -> str:
    return f"{months} mois" if months else "N/A"


def _val(s) -> str:
    return str(s) if s and str(s) not in ("N/A", "0", "") else "—"


def _build_embed(offer: dict) -> dict:
    url = offer.get("url", config.BASE_URL)
    return {
        "title":       offer.get("titre", "Offre VIE"),
        "color":       EMBED_COLOR,
        "url":         url,
        "description": f"[Voir l'offre sur Business France]({url})",
        "fields": [
            {"name": "Entreprise",  "value": _val(offer.get("entreprise")),          "inline": True},
            {"name": "Pays",        "value": _val(offer.get("pays")),                "inline": True},
            {"name": "Ville",       "value": _val(offer.get("ville")),               "inline": True},
            {"name": "Duree",       "value": _fmt_duration(offer.get("duree", 0)),   "inline": True},
            {"name": "Indemnite",   "value": _fmt_salary(offer.get("salaire", 0)),   "inline": True},
            {"name": "Debut",       "value": _val(offer.get("date_debut")),          "inline": True},
            {"name": "Fin",         "value": _val(offer.get("date_fin")),            "inline": True},
            {"name": "Publie",      "value": _val(offer.get("date_publication")),    "inline": True},
        ],
        "footer":    {"text": "Alerte VIE - Business France"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _post(payload: dict, retries: int = 3) -> bool:
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(config.DISCORD_WEBHOOK_URL, json=payload, timeout=10)
            if resp.status_code in (200, 204):
                return True
            if resp.status_code == 429:
                try:
                    wait = float(resp.json().get("retry_after", 5))
                except Exception:
                    wait = 5.0
                logger.warning("[DISCORD] Rate limit: attente %.1fs", wait)
                time.sleep(wait)
                continue
            logger.warning("[DISCORD] HTTP %d (tentative %d/%d): %s",
                           resp.status_code, attempt, retries, resp.text[:120])
        except requests.RequestException as e:
            logger.warning("[DISCORD] Erreur webhook (tentative %d/%d): %s", attempt, retries, e)
        if attempt < retries:
            time.sleep(2 ** (attempt - 1))
    return False


def send_offer(offer: dict) -> bool:
    ok = _post({"embeds": [_build_embed(offer)]})
    if ok:
        logger.info("[DISCORD] Envoye: [%s] %s", offer.get("id"), offer.get("titre", "")[:60])
    else:
        logger.error("[DISCORD] Echec: [%s] %s", offer.get("id"), offer.get("titre", "")[:60])
    time.sleep(1.5)
    return ok


def send_startup() -> None:
    payload = {
        "embeds": [{
            "title":       "Bot VIE demarre",
            "color":       COLOR_GREEN,
            "description": "Surveillance des offres VIE active. Verification toutes les 30-60 secondes.",
            "footer":      {"text": "Alerte VIE - Business France"},
            "timestamp":   datetime.now(timezone.utc).isoformat(),
        }]
    }
    try:
        resp = requests.post(config.DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        if resp.status_code in (200, 204):
            logger.info("[DISCORD] Message de demarrage envoye")
        else:
            logger.warning("[DISCORD] Demarrage: HTTP %d", resp.status_code)
    except Exception as e:
        logger.warning("[DISCORD] Impossible d'envoyer le message de demarrage: %s", e)
