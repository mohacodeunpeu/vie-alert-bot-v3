"""
CV genere dynamiquement par offre, niveau pro Bac+5.
- 1 page A4 garantie (layout ultra-compact, bullets courtes <= 78 chars)
- Titre/tagline adapte au role detecte
- Experiences reorganisees par pertinence offre
- Mots-cles ATS de l'offre injectes via offer_analyzer
- Design : header bleu marine + accent dore + QR code LinkedIn
"""

import io
import os
import re
import tempfile

from fpdf import FPDF

import cover_letter as cl
import offer_analyzer as oa


# ─── Donnees reelles d'Amine ──────────────────────────────────────────────────

PROFILE = {
    "name":       "AMINE BEN MANSOUR",
    "phone":      "+33 6 60 64 57 83",
    "email":      "mohamedbenpro47@gmail.com",
    "city":       "Paris, France",
    "qr_url":     "https://www.linkedin.com/in/amine-ben-mansour-b50a06246/",
    "qr_label":   "Mon LinkedIn",
    "video_cv_url": "",
}


# Tagline adapte par role (ligne sous le nom dans le header)
TAGLINE_BY_ROLE = {
    "product_marketing": "Brand & Product Manager | MBA Manager de Business Unit | VIE 2026",
    "digital_marketing": "Digital Marketing | MBA Manager de Business Unit | VIE 2026",
    "financial_analyst": "Financial Analyst | MBA Manager de Business Unit | VIE 2026",
    "data_analyst":      "Data & Business Analyst | MBA Manager de Business Unit | VIE 2026",
    "purchasing":        "Achats & Category | MBA Manager de Business Unit | VIE 2026",
    "key_account":       "Key Account Manager | MBA Manager de Business Unit | VIE 2026",
    "business_dev":      "Business Developer | MBA Manager de Business Unit | VIE 2026",
    "sales":             "Sales Manager B2B | MBA Manager de Business Unit | VIE 2026",
    "hr":                "Talent Acquisition | MBA Manager de Business Unit | VIE 2026",
    "generic":           "Business Developer | MBA Manager de Business Unit | VIE 2026",
}


# ─── Resumes par sous-role ────────────────────────────────────────────────────

SUMMARY_BASE = {
    "product_marketing": (
        "MBA Manager de Business Unit (PSB Paris, juin 2026). Gestion de projets "
        "digitaux intl (Wix Lisbonne) et community management (GROW 360, Paris). "
        "Capable de structurer une demarche produit et de la decliner en actions "
        "marketing concretes sur des marches multiculturels."
    ),
    "digital_marketing": (
        "MBA Business Unit en cours (PSB Paris, juin 2026). Experience operationnelle "
        "en community management (GROW 360) et projets digitaux a l'international "
        "(Lisbonne). Maitrise des leviers d'engagement et lecture rigoureuse des KPIs."
    ),
    "financial_analyst": (
        "MBA Manager de Business Unit en cours (PSB Paris, juin 2026), module "
        "controle de gestion. Pilote au quotidien une activite a 360 KEUR/mois : "
        "indicateurs, reporting, lecture business des chiffres."
    ),
    "data_analyst": (
        "MBA Business Unit en cours (PSB Paris, juin 2026). Pilotage quotidien de "
        "KPIs commerciaux. Forme a l'analyse et au storytelling de donnees pour "
        "traduire un dataset en insight actionnable."
    ),
    "purchasing": (
        "MBA Business Unit en cours (PSB Paris, juin 2026). Negotiation Business "
        "School certifie (2025). Experience de negociation B2B sur portefeuille "
        "a 360 KEUR/mois, multilingue, transposable aux enjeux achats internationaux."
    ),
    "key_account": (
        "Business Developer B2B chez Agence 113 / DEFI GROUPE (360 KEUR/mois). "
        "MBA Manager de Business Unit en cours (PSB Paris, juin 2026). Profil "
        "hunter-farmer, multilingue, oriente partenariats strategiques long terme."
    ),
    "business_dev": (
        "Business Developer B2B chez Agence 113 / DEFI GROUPE, 360 KEUR/mois. "
        "MBA Manager de Business Unit en cours (PSB Paris, juin 2026). Cycle "
        "commercial complet, HubSpot CRM, Sales Navigator, negociation B2B."
    ),
    "sales": (
        "Business Developer B2B chez Agence 113 / DEFI GROUPE (360 KEUR/mois) "
        "et ex-Sales Advisor Printemps Haussmann. MBA Manager de Business Unit en "
        "cours a PSB Paris. Profil multilingue oriente resultats."
    ),
    "hr": (
        "Recruitment Officer chez Agence 113 / DEFI GROUPE : 300+ candidats geres, "
        "coordination POEI, sourcing actif. Double competence RH/business, renforcee "
        "par le MBA Manager de Business Unit en cours (PSB Paris, juin 2026)."
    ),
    "generic": (
        "Profil junior ambitieux : MBA Manager de Business Unit en cours (PSB Paris, "
        "juin 2026), Business Developer B2B (360 KEUR/mois), experience internationale "
        "Lisbonne, multilingue (FR/AR natifs, EN courant)."
    ),
}


# ─── Experiences reelles — bullets compacts (<= 72 chars) ────────────────────

EXPERIENCES = [
    {
        "id":      "defi",
        "title":   "Business Developer & Recruitment Officer",
        "company": "Agence 113 - DEFI GROUPE",
        "city":    "Paris",
        "period":  "Sept. 2025 - Present",
        "bullets": {
            "default": [
                "Portefeuille B2B a 360 KEUR/mois : prospection, negociation, closing.",
                "Suivi CRM HubSpot et optimisation de la performance commerciale.",
                "Coordination POEI + events recrutement (300+ candidats par session).",
            ],
            "commerce": [
                "Portefeuille B2B a 360 KEUR/mois : prospection, negociation, closing.",
                "Plans de compte HubSpot, negociation directe avec les decideurs.",
                "Structuration de partenariats long terme (cycle de vente complet).",
            ],
            "marketing": [
                "Activite a 360 KEUR/mois : lecture KPI, ajustement, reporting.",
                "Acquisition ciblee : prospection structuree et contenu de demarchage.",
                "Coordination interne : production, RH, communication.",
            ],
            "finance": [
                "Activite a 360 KEUR/mois : suivi budgetaire, marges, reporting.",
                "Lecture indicateurs : volume, mix, prix, rentabilite par client.",
                "Dashboards Excel et coordination avec le service administratif.",
            ],
            "hr": [
                "Events recrutement 300+ candidats : sourcing, qualification, accueil.",
                "Coordination du service POEI avec les acteurs France Travail.",
                "Reporting KPIs recrutement aupres des managers business.",
            ],
        },
    },
    {
        "id":      "wix",
        "title":   "Project Manager / Website Builder",
        "company": "Wix - International",
        "city":    "Lisbonne, Portugal",
        "period":  "2025",
        "bullets": {
            "default": [
                "Projets web clients intl : brief, conception, livraison en autonomie.",
                "Optimisation UX et conversion (analytics, A/B tests).",
            ],
            "marketing": [
                "Projets digitaux clients intl : brief, design, contenu, livraison.",
                "Optimisation UX et conversion (analytics, A/B tests legers).",
            ],
        },
    },
    {
        "id":      "printemps",
        "title":   "Sales Advisor - Premium Retail",
        "company": "Printemps Haussmann",
        "city":    "Paris",
        "period":  "2024",
        "bullets": {
            "default": [
                "Depassement regulier des objectifs sur environnement premium.",
                "Fidelisation d'une clientele internationale exigeante.",
            ],
        },
    },
    {
        "id":      "grow",
        "title":   "Community Manager",
        "company": "GROW 360",
        "city":    "Paris",
        "period":  "2023 - 2024",
        "bullets": {
            "default": [
                "Gestion editoriale reseaux sociaux et strategie de contenu.",
                "Pilotage par les KPIs d'engagement et de conversion.",
            ],
        },
    },
]


BULLET_VARIANT = {
    "product_marketing": "marketing",
    "digital_marketing": "marketing",
    "financial_analyst": "finance",
    "data_analyst":      "finance",
    "purchasing":        "commerce",
    "key_account":       "commerce",
    "business_dev":      "commerce",
    "sales":             "commerce",
    "hr":                "hr",
    "generic":           "default",
}

# Priorite d'affichage des experiences selon le role
ROLE_PRIORITY = {
    "product_marketing": ["wix", "grow", "defi", "printemps"],
    "digital_marketing": ["grow", "wix", "defi", "printemps"],
    "financial_analyst": ["defi", "wix", "printemps", "grow"],
    "data_analyst":      ["defi", "wix", "printemps", "grow"],
    "purchasing":        ["defi", "wix", "printemps", "grow"],
    "key_account":       ["defi", "printemps", "wix", "grow"],
    "business_dev":      ["defi", "printemps", "wix", "grow"],
    "sales":             ["defi", "printemps", "wix", "grow"],
    "hr":                ["defi", "grow", "wix", "printemps"],
    "generic":           ["defi", "wix", "printemps", "grow"],
}

# Nombre de bullets a afficher selon la position dans la liste (1-indexed)
BULLETS_PER_POSITION = [3, 2, 2, 2]


# ─── Formation ────────────────────────────────────────────────────────────────

EDUCATION = [
    ("MBA - Manager de Business Unit",
     "PSB Paris School of Business",
     "Paris  2025-2026",
     "Soutenance juin 2026"),
    ("Bachelor Bac+3 - Developpement Commercial",
     "PSB Paris School of Business",
     "Paris  2022-2025",
     "Obtenu"),
    ("Certification Negociation Commerciale",
     "Negotiation Business School (en ligne)",
     "2025",
     "Certifie"),
    ("Habilitation SST - Sauveteur Secouriste Travail",
     "Croix-Rouge Francaise",
     "Paris  2024",
     ""),
]


# ─── Competences par role ─────────────────────────────────────────────────────

SKILLS_BY_ROLE = {
    "product_marketing": [
        "Strategie produit, positionnement, pricing (MBA)",
        "Gestion de projets digitaux intl (Wix Lisbonne)",
        "Community Management et contenu (GROW 360, Paris)",
        "Lecture KPI, taux de conversion, ROI marketing",
        "Coordination marketing / ventes / R&D",
    ],
    "digital_marketing": [
        "Community Management et reseaux sociaux (GROW 360)",
        "Pilotage campagnes digitales et lecture KPI/ROI",
        "Outils : Canva, Notion, Google Suite, Wix",
        "UX et conversion (Wix Lisbonne)",
        "Strategie de contenu multiculturelle",
    ],
    "financial_analyst": [
        "Controle de gestion et lecture financiere (MBA)",
        "Pilotage de KPIs commerciaux a 360 KEUR/mois",
        "Reporting, analyse d'ecarts, dashboards Excel",
        "Pack Office avance (TCD, formules, VBA)",
        "Rigueur analytique et orientation business",
    ],
    "data_analyst": [
        "Analyse de donnees et pilotage KPIs (MBA)",
        "Gestion d'indicateurs commerciaux au quotidien",
        "Excel avance, notions Power BI / Tableau",
        "Storytelling de donnees pour les decideurs",
        "Esprit critique et rigueur methodologique",
    ],
    "purchasing": [
        "Negociation B2B (Negotiation Business School, 2025)",
        "Analyse de besoins et structuration d'offres",
        "Multilinguisme : FR/AR natifs, EN courant, ES inter.",
        "Pack Office avance et CRM HubSpot",
        "Suivi de performance et reporting",
    ],
    "key_account": [
        "Portefeuille B2B a 360 KEUR/mois en autonomie",
        "Cycle commercial complet (prospection -> closing)",
        "HubSpot CRM, LinkedIn Sales Navigator",
        "Negotiation Business School (certifie 2025)",
        "Multilinguisme et adaptabilite culturelle",
    ],
    "business_dev": [
        "Business Development B2B (360 KEUR/mois)",
        "Cycle commercial : prospection -> closing",
        "HubSpot CRM, LinkedIn Sales Navigator",
        "Negotiation Business School (certifie 2025)",
        "Multilinguisme : FR / AR / EN / ES",
    ],
    "sales": [
        "Vente B2B et B2C premium (DEFI + Printemps)",
        "Depassement regulier d'objectifs commerciaux",
        "Negotiation Business School (certifie 2025)",
        "HubSpot CRM, LinkedIn Sales Navigator",
        "Multilinguisme et relation client haut de gamme",
    ],
    "hr": [
        "Recrutement : 300+ candidats geres en events",
        "Coordination POEI avec France Travail",
        "Outils : Indeed, France Travail, LinkedIn",
        "Animation d'evenements et entretiens",
        "Habilitation SST (Croix-Rouge Francaise)",
    ],
    "generic": [
        "Cycle commercial et negociation B2B",
        "Gestion de projets intl (Lisbonne)",
        "HubSpot CRM, LinkedIn Sales Navigator",
        "Pack Office avance et Google Suite",
        "FR / EN / AR / ES / ZH",
    ],
}


LANGUAGES = [
    ("Francais",  "Natif"),
    ("Arabe",     "Natif"),
    ("Anglais",   "Courant"),
    ("Espagnol",  "Intermediaire"),
    ("Chinois",   "Notions"),
]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _safe(text: str) -> str:
    if not text:
        return ""
    repl = {
        "—": "-", "–": "-", "‘": "'", "’": "'",
        "“": '"', "”": '"', "…": "...", " ": " ",
        " ": " ", "•": "-", "→": "->", "▸": "-",
        "€": "EUR", "œ": "oe", "Œ": "OE",
        "æ": "ae", "Æ": "AE",
    }
    for k, v in repl.items():
        text = text.replace(k, v)
    return text


def _dynamic_summary(role: str, offer: dict, analysis: dict) -> str:
    """Resume adapte au role + quelques mots-cles de l'offre."""
    base = SUMMARY_BASE.get(role, SUMMARY_BASE["generic"])

    # Injecter 1-2 mots-cles actions de l'offre si coherents et non deja presents
    actions = analysis.get("actions", [])
    base_lower = base.lower()
    injected = []
    for kw in actions[:3]:
        if kw.lower() not in base_lower:
            injected.append(kw)
        if len(injected) >= 2:
            break

    if injected:
        kws_str = ", ".join(injected)
        base = base.rstrip(".") + f". Mots-cles offre : {kws_str}."

    return base


# ─── QR Code ──────────────────────────────────────────────────────────────────

def _make_qr_png(url: str) -> str:
    try:
        import qrcode
    except ImportError:
        return ""
    qr = qrcode.QRCode(version=1, box_size=10, border=1,
                       error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="white", back_color=(15, 35, 85))
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    img.save(path)
    return path


# ─── PDF class ────────────────────────────────────────────────────────────────

class _CVPdf(FPDF):
    NAVY   = (15, 35, 85)
    GOLD   = (193, 154, 60)
    GREY   = (60, 60, 65)
    LIGHT  = (245, 247, 250)
    DARK_X = (90, 90, 95)

    # Tagline peut etre surchargee avant add_page()
    tagline = "Business Developer | MBA Manager de Business Unit | VIE 2026"

    def header(self):
        self.set_fill_color(*self.NAVY)
        self.rect(0, 0, 210, 29, style="F")

        # Nom
        self.set_xy(14, 5.5)
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(255, 255, 255)
        self.cell(0, 6.5, _safe(PROFILE["name"]), ln=1)

        # Tagline adapte
        self.set_x(14)
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(*self.GOLD)
        self.cell(0, 4.5, _safe(self.tagline), ln=1)

        # Contact
        self.set_x(14)
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(210, 220, 235)
        contact = f"{PROFILE['phone']}  |  {PROFILE['email']}  |  {PROFILE['city']}"
        self.cell(0, 4.5, _safe(contact), ln=1)

        # Bande doree
        self.set_fill_color(*self.GOLD)
        self.rect(0, 29, 210, 0.8, style="F")
        self.set_y(32)

    def footer(self):
        self.set_y(-10)
        self.set_fill_color(*self.GOLD)
        self.rect(0, 285, 210, 0.4, style="F")
        self.set_y(-8.5)
        self.set_x(14)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(150, 150, 155)
        self.cell(0, 3.5,
                  _safe(f"{PROFILE['name']}  |  {PROFILE['phone']}  |  {PROFILE['email']}"),
                  align="C")

    def section(self, title: str):
        self.ln(0.8)
        self.set_x(14)
        self.set_font("Helvetica", "B", 10.5)
        self.set_text_color(*self.NAVY)
        self.cell(0, 5.5, _safe(title.upper()), ln=1)
        x, y = 14, self.get_y()
        self.set_fill_color(*self.GOLD)
        self.rect(x, y - 0.4, 20, 0.6, style="F")
        self.set_y(y + 0.4)

    def paragraph(self, text: str, font_size: float = 8.8):
        self.set_x(14)
        self.set_font("Helvetica", "", font_size)
        self.set_text_color(*self.GREY)
        self.multi_cell(182, 4.0, _safe(text))
        self.ln(0.3)

    def experience_item(self, title: str, period: str, sub: str, bullets: list):
        self.set_x(14)
        self.set_font("Helvetica", "B", 9.5)
        self.set_text_color(*self.NAVY)
        self.cell(120, 4.5, _safe(title), ln=0)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*self.DARK_X)
        self.cell(0, 4.5, _safe(period), align="R", ln=1)

        self.set_x(14)
        self.set_font("Helvetica", "I", 8.5)
        self.set_text_color(*self.GREY)
        self.cell(0, 3.8, _safe(sub), ln=1)

        self.set_font("Helvetica", "", 8.7)
        self.set_text_color(*self.GREY)
        for b in bullets:
            self.set_x(16)
            self.cell(3, 3.8, "-")
            self.multi_cell(178, 3.8, _safe(b))
        self.ln(0.6)

    def education_item(self, title: str, school: str, period: str, note: str):
        self.set_x(14)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*self.NAVY)
        self.cell(140, 4.0, _safe(title), ln=0)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*self.DARK_X)
        self.cell(0, 4.0, _safe(period), align="R", ln=1)

        self.set_x(14)
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(*self.GREY)
        line = school + (f"  -  {note}" if note else "")
        self.cell(0, 3.7, _safe(line), ln=1)

    def two_columns_skills_languages(self, skills: list, languages: list):
        """Competences (gauche) | Langues (droite) — 2 colonnes independantes."""
        start_y = self.get_y()
        col_w   = 86

        # Colonne gauche : Competences
        self.set_xy(14, start_y)
        self.set_font("Helvetica", "B", 10.5)
        self.set_text_color(*self.NAVY)
        self.cell(col_w, 5.5, _safe("COMPETENCES CLES"), ln=2)
        gy = self.get_y()
        self.set_fill_color(*self.GOLD)
        self.rect(14, gy - 0.4, 20, 0.6, style="F")
        self.set_y(gy + 0.4)

        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(*self.GREY)
        for s in skills:
            self.set_x(16)
            self.cell(3, 3.8, "-")
            self.multi_cell(col_w - 5, 3.8, _safe(s))
        skills_end_y = self.get_y()

        # Colonne droite : Langues
        self.set_xy(108, start_y)
        self.set_font("Helvetica", "B", 10.5)
        self.set_text_color(*self.NAVY)
        self.cell(col_w, 5.5, _safe("LANGUES"), ln=2)
        ly = self.get_y()
        self.set_fill_color(*self.GOLD)
        self.rect(108, ly - 0.4, 20, 0.6, style="F")
        self.set_y(ly + 0.4)

        self.set_font("Helvetica", "", 8.5)
        for lang, level in languages:
            self.set_x(108)
            self.set_text_color(*self.NAVY)
            self.set_font("Helvetica", "B", 8.5)
            self.cell(28, 4.0, _safe(lang), ln=0)
            self.set_font("Helvetica", "", 8.5)
            self.set_text_color(*self.GREY)
            self.cell(0, 4.0, _safe(level), ln=1)
        langs_end_y = self.get_y()

        self.set_y(max(skills_end_y, langs_end_y) + 1.5)

    def tools_strip(self, extra_tools: list = None):
        self.set_x(14)
        self.set_font("Helvetica", "B", 10.5)
        self.set_text_color(*self.NAVY)
        self.cell(0, 5.5, _safe("OUTILS & DISPONIBILITE"), ln=1)
        y = self.get_y()
        self.set_fill_color(*self.GOLD)
        self.rect(14, y - 0.4, 20, 0.6, style="F")
        self.set_y(y + 0.4)

        base = (
            "CRM : HubSpot, Sales Navigator  |  Marketing : Canva, Notion, Wix  |  "
            "Bureautique : Excel avance, Google Suite  |  "
            "Disponibilite : VIE 2026 (juin/juillet)  |  Mobilite : Permis B, remote OK"
        )
        if extra_tools:
            unique = [t for t in extra_tools if t.lower() not in base.lower()][:3]
            if unique:
                base = base + "  |  " + ", ".join(unique)

        self.set_x(14)
        self.set_font("Helvetica", "", 8.3)
        self.set_text_color(*self.GREY)
        self.multi_cell(182, 3.8, _safe(base))


# ─── Point d'entree ───────────────────────────────────────────────────────────

def generate(offer: dict) -> bytes:
    """Genere un CV PDF adapte a l'offre. Garantit 1 page A4."""
    titre       = offer.get("titre", "")
    description = offer.get("description", "")
    role        = cl.detect_sub_role(titre, description)

    # Analyse profonde de l'offre
    analysis    = oa.analyze(offer)
    extra_tools = analysis.get("tools", [])

    # Tagline adapte
    tagline = TAGLINE_BY_ROLE.get(role, TAGLINE_BY_ROLE["generic"])

    pdf = _CVPdf(format="A4")
    pdf.set_auto_page_break(auto=False)
    pdf.tagline = tagline
    pdf.add_page()

    # QR code (priorise video_cv_url si disponible)
    qr_url = (PROFILE.get("video_cv_url") or PROFILE.get("qr_url") or "").strip()
    qr_label = "Mon CV video" if PROFILE.get("video_cv_url") else PROFILE.get("qr_label", "")
    qr_path = _make_qr_png(qr_url) if qr_url else ""
    if qr_path:
        try:
            pdf.image(qr_path, x=179, y=4, w=20, h=20)
            pdf.set_xy(179, 24)
            pdf.set_font("Helvetica", "B", 5.5)
            pdf.set_text_color(*pdf.GOLD)
            pdf.cell(20, 3, _safe(qr_label), align="C")
        except Exception:
            pass
        finally:
            try:
                os.unlink(qr_path)
            except Exception:
                pass

    # Profil
    pdf.section("Profil")
    pdf.paragraph(_dynamic_summary(role, offer, analysis), font_size=8.7)

    # Experiences — ordonnees par pertinence, bullets limites par position
    pdf.section("Experience professionnelle")
    variant = BULLET_VARIANT.get(role, "default")
    order   = ROLE_PRIORITY.get(role, ROLE_PRIORITY["generic"])
    by_id   = {e["id"]: e for e in EXPERIENCES}
    for pos, exp_id in enumerate(order):
        exp = by_id.get(exp_id)
        if not exp:
            continue
        n_bullets  = BULLETS_PER_POSITION[pos] if pos < len(BULLETS_PER_POSITION) else 2
        all_bullets = exp["bullets"].get(variant) or exp["bullets"]["default"]
        bullets    = all_bullets[:n_bullets]
        sub        = f"{exp['company']}   |   {exp['city']}"
        pdf.experience_item(exp["title"], exp["period"], sub, bullets)

    # Formation
    pdf.section("Formation")
    for title, school, period, note in EDUCATION:
        pdf.education_item(title, school, period, note)

    # Competences + Langues (2 colonnes)
    pdf.ln(0.8)
    skills = SKILLS_BY_ROLE.get(role, SKILLS_BY_ROLE["generic"])
    pdf.two_columns_skills_languages(skills, LANGUAGES)

    # Outils + dispo
    pdf.tools_strip(extra_tools)

    out = pdf.output(dest="S")
    if isinstance(out, str):
        return out.encode("latin-1")
    return bytes(out)
