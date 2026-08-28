"""
Scraper VIE — utilise la vraie API backend civiweb-api-prd.azurewebsites.net
decouverte en analysant les requetes reelles du site Business France.
"""

import json
import logging
import random
import re
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup

import auth
import config

logger = logging.getLogger(__name__)

# URL reelle du backend (decouverte via DevTools)
CIVIWEB_API = "https://civiweb-api-prd.azurewebsites.net/api/Offers/Search"
FALLBACK_API = "https://mon-vie-via.businessfrance.fr/api/offres/recherche"

# L'API civiweb refuse limit > 200 (HTTP 400).
CIVIWEB_PAGE_SIZE  = 200
MAX_CIVIWEB_PAGES  = 15

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/147.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]


# ── Helpers ──────────────────────────────────────────────────────────────────────

def _headers(with_json: bool = False) -> dict:
    h = {
        "Authorization": f"Bearer {auth.get_token()}",
        "User-Agent":    random.choice(USER_AGENTS),
        "Accept":        "application/json",
        "Origin":        "https://mon-vie-via.businessfrance.fr",
        "Referer":       "https://mon-vie-via.businessfrance.fr/",
    }
    if with_json:
        h["Content-Type"] = "application/json"
    return h


def _safe_str(v, default="N/A") -> str:
    s = str(v).strip() if v is not None else ""
    return s if s and s.lower() not in ("none", "null") else default


def _safe_int(v, default=0) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _safe_float(v, default=0.0) -> float:
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(re.sub(r"[^\d.]", "", str(v)))
    except (ValueError, TypeError):
        return default


def _fmt_date(v) -> str:
    if not v:
        return "N/A"
    s = str(v)
    if "T" in s:
        s = s.split("T")[0]
    parts = re.split(r"[-/]", s.strip())
    if len(parts) == 3 and len(parts[0]) == 4:
        return f"{parts[2].zfill(2)}/{parts[1].zfill(2)}/{parts[0]}"
    return s


# ── Parsing offre civiweb ────────────────────────────────────────────────────────

def _parse_civiweb(raw: dict) -> Optional[dict]:
    try:
        offer_id = raw.get("id")
        if not offer_id:
            return None

        date_pub    = _fmt_date(raw.get("creationDate") or raw.get("startBroadcastDate"))
        composite   = f"{offer_id}_{date_pub}"

        return {
            "id":              str(offer_id),
            "composite_id":    composite,
            "titre":           _safe_str(raw.get("missionTitle"), "Poste non precise"),
            "entreprise":      _safe_str(raw.get("organizationName")),
            "ville":           _safe_str(raw.get("cityName")),
            "pays":            _safe_str(raw.get("countryName")),
            "pays_en":         _safe_str(raw.get("countryNameEn")),
            "duree":           _safe_int(raw.get("missionDuration")),
            "salaire":         _safe_float(raw.get("indemnite")),
            "date_debut":      _fmt_date(raw.get("missionStartDate")),
            "date_fin":        _fmt_date(raw.get("endBroadcastDate") or raw.get("missionEndDate")),
            "date_publication": date_pub,
            "description":     _safe_str(raw.get("missionDescription", ""))[:400],
            "secteur":         _safe_str(raw.get("activitySectorN1")),
            "url":             f"{config.BASE_URL}/offres/{offer_id}",
        }
    except Exception as e:
        logger.debug("[PARSE] Echec id=%s : %s", raw.get("id", "?"), e)
        return None


# ── Stratégie 1 : API civiweb (POST) ────────────────────────────────────────────

def _fetch_civiweb() -> list[dict]:
    """Recupere toutes les offres en paginant.

    L'API plafonne le champ limit a 200 : au-dela elle repond HTTP 400
    "The field Limit must be between 0 and 200".
    """
    all_offers: list[dict] = []
    seen: set[str] = set()
    total_count = 0

    for page in range(MAX_CIVIWEB_PAGES):
        body = {"page": page, "limit": CIVIWEB_PAGE_SIZE}
        try:
            resp = requests.post(CIVIWEB_API, json=body,
                                 headers=_headers(with_json=True), timeout=15)
        except requests.RequestException as e:
            logger.warning("[CIVIWEB] Erreur requete page %d: %s", page, e)
            break

        if resp.status_code == 401:
            logger.error("[CIVIWEB] Token invalide ou expire")
            return []
        if resp.status_code != 200:
            logger.warning("[CIVIWEB] HTTP %d page %d: %s",
                           resp.status_code, page, resp.text[:200])
            break

        try:
            data = resp.json()
        except ValueError:
            logger.error("[CIVIWEB] Reponse non-JSON page %d", page)
            break

        items = data.get("result") or data.get("results") or []
        total_count = int(data.get("count") or total_count)

        before = len(all_offers)
        for raw in items:
            offer = _parse_civiweb(raw)
            if offer and offer["composite_id"] not in seen:
                seen.add(offer["composite_id"])
                all_offers.append(offer)

        if len(items) < CIVIWEB_PAGE_SIZE:
            break
        # L'API renvoie parfois la meme page quel que soit page : si un tour
        # n'apporte aucune offre inedite, inutile de continuer a la marteler.
        if len(all_offers) == before:
            logger.info("[CIVIWEB] Page %d sans nouvelle offre — arret pagination", page)
            break
        if total_count and len(all_offers) >= total_count:
            break
        time.sleep(0.3)

    logger.info("[CIVIWEB] %d offres parsees (total annonce: %d)",
                len(all_offers), total_count)
    return all_offers


# ── Stratégie 2 : API originale (GET, fallback) ──────────────────────────────────

def _fetch_original_api() -> list[dict]:
    all_offers: list[dict] = []
    seen: set[str]          = set()

    for page in range(config.MAX_PAGES):
        params = {**config.API_PARAMS, "page": page}
        for attempt in range(1, 4):
            try:
                resp = requests.get(FALLBACK_API, params=params,
                                    headers=_headers(), timeout=10)
                break
            except requests.RequestException as e:
                logger.warning("[API] Tentative %d/3: %s", attempt, e)
                if attempt < 3:
                    time.sleep(2 ** attempt)
        else:
            break

        if resp.status_code not in (200,):
            logger.warning("[API] HTTP %d", resp.status_code)
            break

        try:
            data = resp.json()
        except ValueError:
            break

        items = (data if isinstance(data, list) else
                 data.get("content") or data.get("offres") or data.get("results") or [])
        if not items:
            break

        for raw in items:
            if not isinstance(raw, dict):
                continue
            raw_id  = raw.get("id") or raw.get("offreId")
            if not raw_id:
                continue
            date_pub = _fmt_date(raw.get("datePublication") or raw.get("creationDate"))
            cid      = f"{raw_id}_{date_pub}"
            if cid in seen:
                continue
            seen.add(cid)
            all_offers.append({
                "id":              str(raw_id),
                "composite_id":    cid,
                "titre":           _safe_str(raw.get("intitule") or raw.get("title")),
                "entreprise":      _safe_str((raw.get("entreprise") or {}).get("raisonSociale") or raw.get("entrepriseLibelle")),
                "ville":           _safe_str((raw.get("localisation") or {}).get("ville")),
                "pays":            _safe_str((raw.get("localisation") or {}).get("pays")),
                "pays_en":         "N/A",
                "duree":           _safe_int(raw.get("duree") or raw.get("dureeMission")),
                "salaire":         _safe_float(raw.get("salaire") or raw.get("remunerationMensuelle")),
                "date_debut":      _fmt_date(raw.get("dateDebut")),
                "date_fin":        _fmt_date(raw.get("dateFin")),
                "date_publication": date_pub,
                "description":     _safe_str(raw.get("description"), "")[:400],
                "secteur":         "N/A",
                "url":             f"{config.BASE_URL}/offres/{raw_id}",
            })

        if len(items) < 100:
            break
        time.sleep(0.3)

    logger.info("[API] %d offres via API originale", len(all_offers))
    return all_offers


# ── Stratégie 3 : HTML BeautifulSoup ────────────────────────────────────────────

def _fetch_html() -> list[dict]:
    logger.info("[HTML] Fallback BeautifulSoup")
    try:
        resp = requests.get(config.HTML_URL, headers=_headers(), timeout=10)
    except requests.RequestException as e:
        logger.error("[HTML] Erreur: %s", e)
        return []

    if resp.status_code != 200:
        return []

    soup   = BeautifulSoup(resp.text, "lxml")
    offers = []
    seen   = set()

    for script in soup.find_all("script"):
        text = script.string or ""
        for match in re.finditer(r'\{"id"\s*:\s*(\d+)[^}]{20,}\}', text):
            try:
                raw = json.loads(match.group())
                if raw.get("id"):
                    cid = f"{raw['id']}_N/A"
                    if cid not in seen:
                        seen.add(cid)
                        offers.append({
                            "id": str(raw["id"]), "composite_id": cid,
                            "titre": _safe_str(raw.get("intitule") or raw.get("missionTitle")),
                            "entreprise": "N/A", "ville": "N/A", "pays": "N/A",
                            "pays_en": "N/A", "duree": 0, "salaire": 0.0,
                            "date_debut": "N/A", "date_fin": "N/A",
                            "date_publication": "N/A", "description": "", "secteur": "N/A",
                            "url": f"{config.BASE_URL}/offres/{raw['id']}",
                        })
            except Exception:
                continue

    logger.info("[HTML] %d offres extraites", len(offers))
    return offers


# ── Point d'entree ────────────────────────────────────────────────────────────────

def fetch_offers() -> list[dict]:
    """
    Cascade :
    1. POST civiweb-api-prd (vraie API backend avec token)
    2. GET API originale
    3. Scraping HTML
    """
    token = auth.get_token()
    if token:
        offers = _fetch_civiweb()
        if offers:
            return offers
        logger.info("[SCRAPER] civiweb sans resultat, essai API originale")

    offers = _fetch_original_api()
    if offers:
        return offers

    logger.info("[SCRAPER] API sans resultat, fallback HTML")
    return _fetch_html()
