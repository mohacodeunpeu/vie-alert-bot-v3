"""
Gestion du token Azure B2C.
- Charge depuis token_cache.json ou variables d'environnement Railway
- Rafraichit automatiquement via le refresh_token (valide 90 jours)
- Zero intervention humaine apres la premiere connexion
"""

import json
import logging
import os
import time
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

TOKEN_CACHE = Path("token_cache.json")

# Endpoint Azure B2C pour rafraichir le token
_REFRESH_URL = (
    "https://france365B2C.b2clogin.com"
    "/france365B2C.onmicrosoft.com"
    "/B2C_1A_SIGNUP_SIGNIN"
    "/oauth2/v2.0/token"
)
_CLIENT_ID = "cbba759f-45bc-4c21-bd77-533388735d6a"
_SCOPE = (
    "openid profile offline_access "
    "https://france365B2C.onmicrosoft.com"
    "/f86b75cc-7549-4e7b-9f20-c41117f94807/access_as_user"
)


def _load_cache() -> dict:
    # Priorite 1 : variables d'environnement Railway
    env_token   = os.environ.get("ACCESS_TOKEN", "")
    env_refresh = os.environ.get("REFRESH_TOKEN", "")
    if env_token:
        return {
            "access_token":  env_token,
            "refresh_token": env_refresh,
            "expires_at":    float(os.environ.get("TOKEN_EXPIRES_AT", time.time() + 3600)),
        }

    # Priorite 2 : fichier local
    if TOKEN_CACHE.exists():
        try:
            return json.loads(TOKEN_CACHE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_cache(data: dict) -> None:
    try:
        TOKEN_CACHE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning("[AUTH] Impossible de sauvegarder token_cache.json: %s", e)


def _refresh(refresh_token: str) -> dict | None:
    """Echange le refresh_token contre un nouvel access_token."""
    try:
        resp = requests.post(
            _REFRESH_URL,
            data={
                "grant_type":    "refresh_token",
                "client_id":     _CLIENT_ID,
                "refresh_token": refresh_token,
                "scope":         _SCOPE,
            },
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json()
        logger.warning("[AUTH] Refresh echoue HTTP %d: %s", resp.status_code, resp.text[:150])
    except Exception as e:
        logger.error("[AUTH] Erreur refresh: %s", e)
    return None


def get_token() -> str:
    """
    Retourne un access_token valide.
    Rafraichit automatiquement si expire.
    """
    cache = _load_cache()

    if not cache.get("access_token"):
        logger.error("[AUTH] Aucun token trouve. Ajoute ACCESS_TOKEN sur Railway ou relance login.py")
        return ""

    expires_at = float(cache.get("expires_at", 0))
    # Rafraichir 2 minutes avant expiration
    if time.time() < expires_at - 120:
        return cache["access_token"]

    # Token expire ou bientot expire
    refresh_token = cache.get("refresh_token", "")
    if not refresh_token:
        logger.warning("[AUTH] Token expire et pas de refresh_token — utilisation quand meme")
        return cache["access_token"]

    logger.info("[AUTH] Token expire, rafraichissement en cours...")
    new_tokens = _refresh(refresh_token)

    if new_tokens and new_tokens.get("access_token"):
        updated = {
            "access_token":  new_tokens["access_token"],
            "refresh_token": new_tokens.get("refresh_token", refresh_token),
            "expires_at":    time.time() + int(new_tokens.get("expires_in", 3600)),
        }
        _save_cache(updated)
        logger.info("[AUTH] Token rafraichi avec succes (expire dans %ds)",
                    int(new_tokens.get("expires_in", 3600)))
        return updated["access_token"]

    logger.warning("[AUTH] Rafraichissement echoue, utilisation de l'ancien token")
    return cache["access_token"]
