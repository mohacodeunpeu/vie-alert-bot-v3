"""
Candidature automatique aux offres VIE via l'API civiweb.
Postule dans les 30 secondes apres detection d'une nouvelle offre.
"""

import json
import logging
import time
from pathlib import Path

import requests

import auth
import cover_letter as cl

logger = logging.getLogger(__name__)

APPLY_URL   = "https://civiweb-api-prd.azurewebsites.net/api/Offers/Apply"
APPLIED_FILE = Path("applied_offers.json")

_HEADERS_BASE = {
    "Accept":     "application/json",
    "Origin":     "https://mon-vie-via.businessfrance.fr",
    "Referer":    "https://mon-vie-via.businessfrance.fr/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
}


def _load_applied() -> set:
    if not APPLIED_FILE.exists():
        return set()
    try:
        return set(json.loads(APPLIED_FILE.read_text(encoding="utf-8")))
    except Exception:
        return set()


def _save_applied(applied: set) -> None:
    try:
        APPLIED_FILE.write_text(json.dumps(sorted(applied), indent=2), encoding="utf-8")
    except Exception as e:
        logger.error("[APPLY] Sauvegarde echouee: %s", e)


def apply_offer(offer: dict) -> bool:
    """
    Postule automatiquement a une offre VIE.
    Retourne True si candidature envoyee, False sinon.
    """
    offer_id = str(offer.get("id", ""))
    titre    = offer.get("titre", "?")

    if not offer_id:
        return False

    applied = _load_applied()
    if offer_id in applied:
        logger.debug("[APPLY] Deja postule: %s", offer_id)
        return False

    token = auth.get_token()
    if not token:
        logger.error("[APPLY] Token manquant — candidature impossible")
        return False

    motivation = cl.generate(offer)
    oid = int(offer_id)

    headers = {
        **_HEADERS_BASE,
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
    }

    # Plusieurs structures de body possibles selon la version de l'API
    bodies = [
        {"offerId": oid, "motivationLetter": motivation},
        {"offerId": oid, "coverLetter": motivation},
        {"offerId": oid, "motivationLetter": motivation, "cvAttached": True},
        {"id": oid, "motivationLetter": motivation},
        {"offreId": oid, "lettreMotivation": motivation},
    ]

    for body in bodies:
        try:
            resp = requests.post(APPLY_URL, json=body, headers=headers, timeout=20)
            logger.info("[APPLY] %s (id=%s) -> HTTP %d", titre[:40], offer_id, resp.status_code)

            if resp.status_code in (200, 201, 204):
                applied.add(offer_id)
                _save_applied(applied)
                logger.info("[APPLY] Candidature ENVOYEE: %s", titre)
                return True

            if resp.status_code == 409:
                # Deja postule cote serveur
                applied.add(offer_id)
                _save_applied(applied)
                logger.info("[APPLY] Deja postule (serveur): %s", titre)
                return True

            if resp.status_code == 401:
                logger.error("[APPLY] Token invalide — stop")
                return False

            if resp.status_code == 400:
                # Mauvaise structure body — essayer la suivante
                logger.debug("[APPLY] Body %s -> 400, essai suivant", list(body.keys()))
                continue

            # Autre erreur — logguer la reponse pour debug
            logger.warning("[APPLY] HTTP %d: %s", resp.status_code, resp.text[:200])
            break

        except requests.RequestException as e:
            logger.error("[APPLY] Erreur reseau: %s", e)
            break

    logger.warning("[APPLY] Candidature echouee pour %s (id=%s)", titre, offer_id)
    return False


def apply_batch(offers: list[dict]) -> int:
    """Postule a une liste d'offres. Retourne le nombre de candidatures envoyees."""
    sent = 0
    for offer in offers:
        if apply_offer(offer):
            sent += 1
            time.sleep(2)  # Pause entre chaque candidature
    return sent
