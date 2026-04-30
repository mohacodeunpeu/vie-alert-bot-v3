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
import cv_generator

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


def _generate_cover_pdf(text: str, offer: dict | None = None) -> bytes:
    """PDF design pro : header bleu marine, infos contact, mise en page aeree."""
    NAME    = "Amine Ben Mansour"
    PHONE   = "+33 6 60 64 57 83"
    EMAIL   = "mohamedbenpro47@gmail.com"

    # Palette : bleu marine + accent doree
    NAVY      = (15, 35, 85)      # Bleu marine principal
    GOLD      = (193, 154, 60)    # Accent
    GREY_TXT  = (50, 50, 55)
    LIGHT_BG  = (245, 247, 250)

    pdf = FPDF(format="A4")
    pdf.add_page()
    pdf.set_auto_page_break(auto=False)  # On garantit 1 page

    page_w = 210

    # ─── Header bleu marine compact ───────────────────────────────────────────
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, page_w, 26, style="F")

    pdf.set_xy(15, 6)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, _safe_text(NAME.upper()), ln=1)

    pdf.set_x(15)
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(220, 225, 235)
    pdf.cell(0, 5, _safe_text(f"{PHONE}  |  {EMAIL}  |  Paris"), ln=1)

    pdf.set_fill_color(*GOLD)
    pdf.rect(0, 26, page_w, 1, style="F")

    # ─── Bandeau infos offre + date ───────────────────────────────────────────
    pdf.set_y(30)
    if offer:
        titre      = offer.get("titre", "")
        entreprise = offer.get("entreprise", "")
        ville      = offer.get("ville", "")
        pays       = offer.get("pays", "")
        location   = ", ".join([x for x in (ville, pays) if x and x != "N/A"])

        pdf.set_fill_color(*LIGHT_BG)
        pdf.set_xy(15, pdf.get_y())
        pdf.set_text_color(*NAVY)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, _safe_text(f"Candidature : {titre}"), ln=1, fill=True)
        pdf.set_x(15)
        pdf.set_font("Helvetica", "I", 8.5)
        pdf.set_text_color(*GREY_TXT)
        if entreprise:
            pdf.cell(0, 4.5, _safe_text(f"{entreprise} / {location}".rstrip(" /")), ln=1)
        pdf.ln(2)

    from datetime import datetime
    pdf.set_x(15)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(120, 120, 125)
    pdf.cell(0, 4.5, _safe_text(f"Paris, le {datetime.now().strftime('%d/%m/%Y')}"), align="R", ln=1)
    pdf.ln(3)

    # ─── Corps : compact, garantie 1 page ─────────────────────────────────────
    pdf.set_x(15)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GREY_TXT)

    text  = _safe_text(text)
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]

    for para in paras:
        if para.startswith("Cordialement"):
            pdf.ln(2)
            pdf.set_font("Helvetica", "", 10)
            for line in para.split("\n"):
                pdf.set_x(15)
                pdf.multi_cell(180, 4.8, line)
            continue
        if para.startswith("Madame"):
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_x(15)
            pdf.multi_cell(180, 4.8, para)
            pdf.set_font("Helvetica", "", 10)
            pdf.ln(1)
            continue
        pdf.set_x(15)
        pdf.multi_cell(180, 4.8, para)
        pdf.ln(1.5)

    # ─── Footer doree fine ────────────────────────────────────────────────────
    pdf.set_fill_color(*GOLD)
    pdf.rect(0, 286, page_w, 0.5, style="F")
    pdf.set_y(-9)
    pdf.set_x(15)
    pdf.set_font("Helvetica", "I", 7.5)
    pdf.set_text_color(140, 140, 145)
    pdf.cell(0, 4, _safe_text(f"{NAME}  |  {PHONE}  |  {EMAIL}"), align="C")

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

    # Le CV statique sert de fallback si la generation dynamique echoue
    if not CV_FILE.exists():
        logger.error("[APPLY] CV statique introuvable: %s", CV_FILE.absolute())
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

    # Generer lettre personnalisee + message court
    motivation_text = cl.generate(offer)
    short_message   = cl.generate_short_message(offer)
    try:
        cover_pdf = _generate_cover_pdf(motivation_text, offer)
    except Exception as e:
        logger.error("[APPLY] Erreur generation PDF: %s", e)
        return False

    # Generer un CV personnalise pour cette offre (fallback : CV statique)
    try:
        cv_bytes = cv_generator.generate(offer)
        logger.info("[APPLY] CV dynamique genere (%d octets) pour role detecte", len(cv_bytes))
    except Exception as e:
        logger.warning("[APPLY] Echec generation CV dynamique (%s) - fallback CV statique", e)
        cv_bytes = CV_FILE.read_bytes()

    # Multipart exactement comme le navigateur
    files = {
        "CurriculumVitae": ("CV_Amine_Ben_Mansour.pdf", cv_bytes,  "application/pdf"),
        "CoverLetter":     (f"Lettre_motivation_VIE{offer_id}.pdf", cover_pdf, "application/pdf"),
    }

    data = {
        "UserId":             USER_ID,
        "Message":            short_message,
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
