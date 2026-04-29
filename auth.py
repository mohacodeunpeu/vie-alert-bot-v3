"""
Gestion du token Azure B2C.
Source de verite : GitHub Repository Variables (mises a jour par le workflow GitHub Actions).
Le bot Railway les lit via l'API GitHub avec un Personal Access Token (GH_PAT).
Fallback : variables d'environnement Railway, puis token_cache.json local.
"""

import json
import logging
import os
import time
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

TOKEN_CACHE = Path("token_cache.json")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "mohacodeunpeu/vie-alert-bot-v3")
GITHUB_API  = "https://api.github.com"

# Cache memoire pour eviter de hammer l'API GitHub a chaque appel
_GH_CACHE: dict = {}
_GH_CACHE_TS: float = 0.0
_GH_CACHE_TTL = 60  # secondes


def _fetch_from_github() -> dict:
    """Recupere les tokens depuis les Repository Variables GitHub."""
    global _GH_CACHE, _GH_CACHE_TS

    # Cache memoire de 60s pour eviter de hammer GitHub
    if _GH_CACHE and time.time() - _GH_CACHE_TS < _GH_CACHE_TTL:
        return _GH_CACHE

    pat = os.environ.get("GH_PAT", "")
    if not pat:
        return {}

    headers = {
        "Accept":               "application/vnd.github+json",
        "Authorization":        f"Bearer {pat}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    out = {}
    mapping = {
        "VIE_ACCESS_TOKEN":     "access_token",
        "VIE_REFRESH_TOKEN":    "refresh_token",
        "VIE_TOKEN_EXPIRES_AT": "expires_at",
    }
    for var_name, key in mapping.items():
        try:
            r = requests.get(
                f"{GITHUB_API}/repos/{GITHUB_REPO}/actions/variables/{var_name}",
                headers=headers, timeout=15,
            )
            if r.status_code == 200:
                out[key] = r.json().get("value", "")
            elif r.status_code == 404:
                logger.warning("[AUTH/GH] Variable %s introuvable (pas encore creee ?)", var_name)
            else:
                logger.warning("[AUTH/GH] %s: HTTP %d %s", var_name, r.status_code, r.text[:200])
        except Exception as e:
            logger.warning("[AUTH/GH] Erreur fetch %s: %s", var_name, e)

    if "expires_at" in out:
        try:
            out["expires_at"] = float(out["expires_at"])
        except Exception:
            out["expires_at"] = 0.0

    if out.get("access_token"):
        _GH_CACHE = out
        _GH_CACHE_TS = time.time()
        logger.info("[AUTH/GH] Tokens recuperes depuis GitHub (expires_at=%s)",
                    out.get("expires_at"))
    return out


def _load_cache() -> dict:
    # Priorite 1 : GitHub Repository Variables (source de verite, refresh auto par workflow)
    gh = _fetch_from_github()
    if gh.get("access_token"):
        return gh

    # Priorite 2 : variables d'environnement (Railway / local)
    env_token   = os.environ.get("ACCESS_TOKEN", "")
    env_refresh = os.environ.get("REFRESH_TOKEN", "")
    if env_token:
        return {
            "access_token":  env_token,
            "refresh_token": env_refresh,
            "expires_at":    float(os.environ.get("TOKEN_EXPIRES_AT", time.time() + 3600)),
        }

    # Priorite 3 : fichier local
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


def get_token() -> str:
    """
    Retourne un access_token valide.
    Source de verite : GitHub Repository Variables (rafraichies toutes les 50 min
    par le workflow GitHub Actions).
    """
    cache = _load_cache()

    if not cache.get("access_token"):
        logger.error("[AUTH] Aucun token trouve. "
                     "Verifie que GH_PAT est defini et que le workflow GitHub a tourne.")
        return ""

    # Invalider le cache memoire si le token approche de l'expiration
    expires_at = float(cache.get("expires_at", 0))
    if expires_at and time.time() > expires_at - 300:  # 5 min avant expiration
        global _GH_CACHE_TS
        _GH_CACHE_TS = 0  # force refetch GitHub au prochain appel
        logger.info("[AUTH] Token bientot expire — prochain check forcera un refetch GitHub")

    return cache["access_token"]
