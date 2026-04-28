"""
Candidature automatique aux offres VIE via l'API civiweb.
Format multipart/form-data avec CV + lettre de motivation PDF.
Reproduit exactement la requete envoyee par le navigateur.
"""

import json
import logging
from pathlib import Path

import requests
from fpdf import FPDF

import auth
import cover_letter as cl

logger = logging.getLogger(__name__)

APPLY_URL    = "https://civiweb-api-prd.azurewebsites.net/api/Offers/Apply"
DETAILS_URL  = "https://civiweb-api-prd.azurewebsites.net/api/Offers/{}"
APPLIED_FILE = Path("applied_offers.json")
CV_FILE      = Path("cv.pdf")

# Identite candidat (capturee depuis F12 sur ta vraie candidature)
USER_ID            = "a2ce9d98-8470-42c0-a9aa-398ade870c14"
CANDIDATE_FIRST    = "Amine"
CANDIDATE_LAST     = "Ben Mansour"
CANDIDATE_EMAIL    = "mohamedbenpro47@gmail.com"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/147.0.0.0 Safari/537.36"
)


# ── Persistance ─────────────────────────────────────────────────────────────────

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


# ── Generation PDF lettre ───────────────────────────────────────────────────────

def _safe_text(text: str) -> str:
    """Remplace les caracteres unicode problematiques pour FPDF latin-1."""
    repl = {
        "—": "-", "–": "-",
        "’": "'", "‘": "'",
        "“": '"', "”": '"',
        "…": "...", " ": " ",
        " ": " ",
    }
    for k, v in repl.items():
        text = text.replace(k, v)
    return text


def _generate_cover_pdf(text: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_font("Helvetica", size=11)

    text = _safe_text(text)
    for line in text.split("\n"):
        if line.strip():
            pdf.multi_cell(0, 6, line)
        else:
            pdf.ln(3)

    out = pdf.output(dest="S")
    if isinstance(out, str):
        return out.encode("latin-1")
    return bytes(out)


# ── Details offre (RecipientEmails) ─────────────────────────────────────────────

def _get_offer_details(offer_id: str, token: str) -> dict:
    url = DETAILS_URL.format(offer_id)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept":        "application/json",
        "Origin":        "https://mon-vie-via.businessfrance.fr",
        "Referer":       "https://mon-vie-via.businessfrance.fr/",
        "User-Agent":    USER_AGENT,
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        logger.debug("[APPLY] Details fetch erreur: %s", e)
    return {}


# ── Candidature principale ──────────────────────────────────────────────────────

def apply_offer(offer: dict) -> bool:
    offer_id   = str(offer.get("id", ""))
    titre      = offer.get("titre", "?")
    entreprise = offer.get("entreprise", "")

    if not offer_id:
        return False

    applied = _load_applied()
    if offer_id in applied:
        return False

    if not CV_FILE.exists():
        logger.error("[APPLY] CV introuvable: %s", CV_FILE.absolute())
        return False

    token = auth.get_token()
    if not token:
        logger.error("[APPLY] Pas de token")
        return False

    # Recuperer email destinataire depuis details offre
    details = _get_offer_details(offer_id, token)
    recipient = (
        details.get("recipientEmails")
        or details.get("contactEmail")
        or details.get("emailContact")
        or ""
    )

    # Generer lettre personnalisee
    motivation_text = cl.generate(offer)
    try:
        cover_pdf = _generate_cover_pdf(motivation_text)
    except Exception as e:
        logger.error("[APPLY] Erreur generation PDF: %s", e)
        return False

    cv_bytes = CV_FILE.read_bytes()

    # Multipart exactement comme le navigateur
    files = {
        "CurriculumVitae": ("CV_Amine_Ben_Mansour.pdf", cv_bytes,  "application/pdf"),
        "CoverLetter":     (f"Lettre_motivation_VIE{offer_id}.pdf", cover_pdf, "application/pdf"),
    }

    data = {
        "UserId":             USER_ID,
        "Message":            motivation_text,
        "CandidateEmail":     CANDIDATE_EMAIL,
        "CandidateFirstName": CANDIDATE_FIRST,
        "CandidateLastName":  CANDIDATE_LAST,
        "OfferId":            offer_id,
        "OrganizationId":     "0",
        "Reference":          f"VIE{offer_id}",
        "RecipientEmails":    recipient,
        "MissionTitle":       titre,
        "OrganizationName":   entreprise,
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept":        "application/json, text/plain, */*",
        "Origin":        "https://mon-vie-via.businessfrance.fr",
        "Referer":       "https://mon-vie-via.businessfrance.fr/",
        "User-Agent":    USER_AGENT,
    }

    try:
        resp = requests.post(APPLY_URL, data=data, files=files, headers=headers, timeout=30)
        logger.info("[APPLY] %s (id=%s) -> HTTP %d", titre[:50], offer_id, resp.status_code)

        if resp.status_code in (200, 201, 204):
            applied.add(offer_id)
            _save_applied(applied)
            logger.info("[APPLY] CANDIDATURE ENVOYEE: %s @ %s", titre, entreprise)
            return True

        if resp.status_code == 409:
            applied.add(offer_id)
            _save_applied(applied)
            logger.info("[APPLY] Deja postule cote serveur: %s", titre)
            return True

        if resp.status_code == 401:
            logger.error("[APPLY] Token expire — refresh necessaire")
            return False

        logger.warning("[APPLY] HTTP %d: %s", resp.status_code, resp.text[:300])
        return False

    except requests.RequestException as e:
        logger.error("[APPLY] Erreur reseau: %s", e)
        return False
