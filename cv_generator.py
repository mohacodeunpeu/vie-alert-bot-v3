"""
CV genere dynamiquement par offre.
- Donnees reelles extraites du CV existant
- Resume professionnel adapte au sous-role detecte (commerce/marketing/finance/...)
- Ordre des experiences reorganise selon pertinence
- Mise en page ATS-friendly (colonnes simples, headers standards, texte selectable)
- Design propre : header bleu marine + accent dore, sections claires
"""

from datetime import datetime

from fpdf import FPDF

import cover_letter as cl


# ─── Donnees reelles d'Amine (extraites du CV) ────────────────────────────────

PROFILE = {
    "name":      "AMINE BEN MANSOUR",
    "phone":     "+33 6 60 64 57 83",
    "email":     "mohamedbenpro47@gmail.com",
    "city":      "Paris, France",
    "age":       "23 ans",
    "permit":    "Permis B - Remote OK",
    "available": "Disponible VIE 2026",
}

# Resumes professionnels par sous-role (les keys matchent cover_letter.detect_sub_role)
SUMMARY_BY_ROLE = {
    "product_marketing": (
        "Diplome en cours de MBA Manager de Business Unit (PSB Paris, soutenance juin "
        "2026), avec une experience en gestion de projets digitaux internationaux a "
        "Lisbonne et community management. Profil junior ambitieux capable de "
        "structurer rapidement une demarche produit et de la decliner en actions "
        "marketing operationnelles."
    ),
    "digital_marketing": (
        "Profil en MBA Business Unit (PSB Paris, juin 2026), avec experience concrete "
        "en community management et gestion de projets digitaux a l'international. "
        "Maitrise des leviers d'engagement, des KPIs marketing et capacite a piloter "
        "des campagnes adaptees a des audiences multiculturelles."
    ),
    "financial_analyst": (
        "MBA Manager de Business Unit en cours (PSB Paris, juin 2026) avec "
        "specialisation en pilotage de la performance. Experience operationnelle de "
        "gestion d'une activite generant 360 KEUR de CA mensuel. Profil rigoureux "
        "capable de produire des analyses financieres claires et orientees decision."
    ),
    "data_analyst": (
        "MBA Manager de Business Unit en cours (PSB Paris, juin 2026), forme aux outils "
        "d'analyse et de pilotage par la donnee. Experience de gestion d'indicateurs "
        "commerciaux au quotidien. Profil capable de traduire un dataset en insight "
        "actionnable pour les decideurs."
    ),
    "purchasing": (
        "MBA Manager de Business Unit en cours (PSB Paris, juin 2026). Experience "
        "concrete de negociation B2B avec un portefeuille a 360 KEUR de CA mensuel. "
        "Approche rigoureuse, multilingue, transposable directement aux enjeux achats "
        "et categoriels internationaux."
    ),
    "key_account": (
        "Business Developer B2B chez Agence 113 / DEFI GROUPE, en charge d'un "
        "portefeuille generant 360 KEUR de CA mensuel. MBA Business Unit en cours a "
        "PSB Paris. Profil hunter-farmer rigoureux, multilingue, oriente partenariats "
        "strategiques de long terme."
    ),
    "business_dev": (
        "Business Developer B2B chez Agence 113 / DEFI GROUPE (360 KEUR de CA mensuel "
        "actuellement). MBA Manager de Business Unit en cours a PSB Paris. Maitrise "
        "complete du cycle commercial, des outils CRM (HubSpot, Sales Navigator) et "
        "de la negociation B2B sur des cibles exigeantes."
    ),
    "sales": (
        "Business Developer B2B chez Agence 113 / DEFI GROUPE avec un portefeuille a "
        "360 KEUR de CA mensuel. Anciennement Sales Advisor au Printemps Haussmann. "
        "MBA Business Unit en cours a PSB Paris. Profil multilingue oriente resultats "
        "et adaptabilite culturelle."
    ),
    "hr": (
        "Recruitment Officer chez Agence 113 / DEFI GROUPE : 300+ candidats geres en "
        "evenements de recrutement, coordination du service POEI, sourcing actif. "
        "Double competence RH/Business avec MBA Manager de Business Unit en cours. "
        "Capable de parler le langage des managers comme des candidats."
    ),
    "generic": (
        "Profil junior ambitieux : MBA Manager de Business Unit en cours (PSB Paris, "
        "juin 2026), Business Developer B2B en France, experience internationale a "
        "Lisbonne, multilingue (FR/AR natifs, EN courant, ES intermediaire, ZH "
        "notions). Rigoureux, autonome, oriente resultats."
    ),
}


# ─── Experiences (donnees reelles) ────────────────────────────────────────────

EXPERIENCES = [
    {
        "id":       "defi",
        "title":    "Business Developer & Recruitment Officer (B2B)",
        "company":  "Agence 113 - DEFI GROUPE",
        "city":     "Paris",
        "period":   "Sept. 2025 - Present",
        "bullets":  [
            "Pilotage d'un portefeuille B2B generant 360 KEUR de CA mensuel : prospection, qualification, negociation, closing.",
            "Organisation d'evenements de recrutement reunissant plus de 300 candidats par session.",
            "Suivi et fidelisation des clients via HubSpot CRM, optimisation continue de la performance commerciale.",
            "Coordination du service POEI (Preparation Operationnelle a l'Emploi) avec les acteurs France Travail.",
        ],
        "tags": {"commerce", "sales", "business_dev", "key_account", "hr"},
    },
    {
        "id":       "wix",
        "title":    "Project Manager / Website Builder",
        "company":  "Wix - International",
        "city":     "Lisbonne, Portugal",
        "period":   "2025",
        "bullets":  [
            "Gestion de projets web pour clients internationaux, du brief initial a la livraison finale.",
            "Analyse des besoins clients et proposition de solutions digitales personnalisees.",
            "Optimisation de l'experience utilisateur (UX) et de la performance de conversion des sites livres.",
            "Coordination en autonomie avec equipes et clients multiculturels en environnement remote.",
        ],
        "tags": {"marketing", "product_marketing", "digital_marketing", "data_analyst"},
    },
    {
        "id":       "printemps",
        "title":    "Sales Advisor - Premium Retail",
        "company":  "Printemps Haussmann",
        "city":     "Paris",
        "period":   "2024",
        "bullets":  [
            "Atteinte et depassement reguliers des objectifs de vente sur un environnement premium.",
            "Service client haut de gamme et fidelisation d'une clientele internationale exigeante.",
            "Conseil personnalise et up-selling sur des produits a forte valeur ajoutee.",
        ],
        "tags": {"sales", "commerce", "key_account"},
    },
    {
        "id":       "grow",
        "title":    "Community Manager",
        "company":  "GROW 360",
        "city":     "Paris",
        "period":   "2023 - 2024",
        "bullets":  [
            "Gestion editoriale des reseaux sociaux et pilotage de la strategie de contenu.",
            "Organisation d'evenements clients et animation de la communaute.",
            "Ajustement des strategies de communication selon les KPIs d'engagement et de conversion.",
        ],
        "tags": {"marketing", "digital_marketing", "product_marketing"},
    },
]


EDUCATION = [
    {
        "title":  "MBA - Manager de Business Unit",
        "school": "PSB Paris School of Business - Paris",
        "period": "2025 - 2026 (soutenance juin 2026)",
        "note":   "En cours",
    },
    {
        "title":  "Bachelor Bac+3 - Developpement Commercial (REM)",
        "school": "PSB Paris School of Business - Paris",
        "period": "2022 - 2025",
        "note":   "Obtenu",
    },
    {
        "title":  "Certification - Negociation Commerciale",
        "school": "Negotiation Business School (en ligne)",
        "period": "2025",
        "note":   "Certification",
    },
    {
        "title":  "Habilitation SST - Sauveteur Secouriste du Travail",
        "school": "Croix-Rouge Francaise - Paris",
        "period": "Depuis 2024",
        "note":   "Habilitation",
    },
]


SKILLS_BY_ROLE = {
    "product_marketing": [
        "Strategie produit et positionnement (modules MBA)",
        "Gestion de projets digitaux internationaux (Wix Lisbonne)",
        "Community Management & strategie de contenu (GROW 360)",
        "Lecture KPI et orientation ROI",
        "Coordination cross-fonctionnelle (marketing, ventes, R&D)",
    ],
    "digital_marketing": [
        "Community Management et gestion de reseaux sociaux (GROW 360)",
        "Pilotage de campagnes digitales et lecture KPI/ROI",
        "Outils marketing : Canva, Notion, suite Google",
        "UX et performance de conversion (Wix Lisbonne)",
        "Strategie de contenu multiculturelle",
    ],
    "financial_analyst": [
        "Controle de gestion et lecture financiere (MBA)",
        "Pilotage de KPIs commerciaux a 360 KEUR/mois",
        "Reporting et analyse d'ecarts",
        "Pack Office avance (Excel, PowerPoint, Word)",
        "Rigueur analytique et orientation business",
    ],
    "data_analyst": [
        "Analyse de donnees et pilotage par la donnee (MBA)",
        "Gestion d'indicateurs commerciaux au quotidien",
        "Excel avance, formation Power BI / Tableau",
        "Storytelling de donnees pour les decideurs",
        "Esprit critique et rigueur methodologique",
    ],
    "purchasing": [
        "Negociation B2B (Negotiation Business School certifie)",
        "Analyse de besoins et structuration de propositions",
        "Multilinguisme : FR / EN / AR natifs - ES intermediaire",
        "Pack Office avance et CRM HubSpot",
        "Suivi de performance et reporting",
    ],
    "key_account": [
        "Pilotage d'un portefeuille a 360 KEUR de CA mensuel",
        "Cycle commercial complet (prospection a closing)",
        "HubSpot CRM, LinkedIn Sales Navigator",
        "Negotiation Business School (certifie 2025)",
        "Multilinguisme et adaptabilite culturelle",
    ],
    "business_dev": [
        "Business Development B2B (360 KEUR de CA mensuel actuel)",
        "Cycle commercial complet : prospection, qualification, closing",
        "HubSpot CRM, LinkedIn Sales Navigator",
        "Negotiation Business School (certifie 2025)",
        "Multilinguisme : FR / EN / AR / ES",
    ],
    "sales": [
        "Vente B2B et B2C premium (DEFI GROUPE et Printemps Haussmann)",
        "Atteinte et depassement d'objectifs reguliers",
        "Negotiation Business School (certifie 2025)",
        "HubSpot CRM, LinkedIn Sales Navigator",
        "Multilinguisme : FR / EN / AR / ES",
    ],
    "hr": [
        "Sourcing et recrutement (300+ candidats geres en evenements)",
        "Coordination POEI avec France Travail",
        "Outils RH : Indeed, France Travail, LinkedIn",
        "Animation d'evenements et conduite d'entretiens",
        "Habilitation SST (Croix-Rouge Francaise)",
    ],
    "generic": [
        "Cycle commercial complet et negociation B2B",
        "Gestion de projets internationaux (Lisbonne)",
        "Outils CRM : HubSpot, LinkedIn Sales Navigator",
        "Pack Office avance et suite Google",
        "Multilinguisme : FR / EN / AR / ES / ZH (notions)",
    ],
}


LANGUAGES = [
    ("Francais",  "Natif"),
    ("Arabe",     "Natif"),
    ("Anglais",   "Courant"),
    ("Espagnol",  "Intermediaire (B1/B2)"),
    ("Chinois",   "Notions"),
]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _safe(text: str) -> str:
    repl = {
        "—": "-", "–": "-", "—": "-",
        "'": "'", "'": "'",
        '"': '"', '"': '"',
        "…": "...", " ": " ", " ": " ",
        "•": "-", "→": "->", "▸": "-",
        "€": "EUR",
    }
    for k, v in repl.items():
        text = text.replace(k, v)
    return text


def _experiences_for_role(role: str) -> list:
    """Reordonne les experiences : celles qui matchent le role en premier."""
    matched, others = [], []
    for exp in EXPERIENCES:
        if role in exp["tags"]:
            matched.append(exp)
        else:
            others.append(exp)
    # Tri stable, on garde l'ordre chronologique au sein de chaque groupe
    return matched + others


# ─── Generation du PDF ────────────────────────────────────────────────────────

class _CVPdf(FPDF):
    NAVY  = (15, 35, 85)
    GOLD  = (193, 154, 60)
    GREY  = (60, 60, 65)
    LIGHT = (245, 247, 250)

    def header(self):
        # Header navy avec nom
        self.set_fill_color(*self.NAVY)
        self.rect(0, 0, 210, 28, style="F")

        self.set_xy(15, 7)
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, _safe(PROFILE["name"]), ln=1)

        self.set_x(15)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(220, 225, 235)
        self.cell(0, 6,
                  _safe(f"{PROFILE['phone']}  |  {PROFILE['email']}  |  {PROFILE['city']}"),
                  ln=1)

        # Bande doree fine
        self.set_fill_color(*self.GOLD)
        self.rect(0, 28, 210, 1.2, style="F")

        # Reset position pour le contenu
        self.set_y(34)

    def footer(self):
        self.set_y(-12)
        self.set_fill_color(*self.GOLD)
        self.rect(0, 287, 210, 0.6, style="F")
        self.set_y(-9)
        self.set_x(15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140, 140, 145)
        self.cell(0, 5,
                  _safe(f"{PROFILE['name']}  |  {PROFILE['phone']}  |  {PROFILE['email']}"),
                  align="C")

    def section(self, title: str):
        self.ln(2)
        self.set_x(15)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*self.NAVY)
        self.cell(0, 7, _safe(title.upper()), ln=1)
        # Trait dore sous le titre de section
        x, y = 15, self.get_y()
        self.set_fill_color(*self.GOLD)
        self.rect(x, y, 25, 0.8, style="F")
        self.set_y(y + 2)

    def paragraph(self, text: str, font_size: int = 10):
        self.set_x(15)
        self.set_font("Helvetica", "", font_size)
        self.set_text_color(*self.GREY)
        self.multi_cell(180, 5, _safe(text))
        self.ln(1)

    def experience_item(self, exp: dict):
        self.set_x(15)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*self.NAVY)
        self.cell(120, 5.5, _safe(exp["title"]), ln=0)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(120, 120, 125)
        self.cell(0, 5.5, _safe(exp["period"]), align="R", ln=1)

        self.set_x(15)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*self.GREY)
        sub = f"{exp['company']}  |  {exp['city']}"
        self.cell(0, 5, _safe(sub), ln=1)

        self.set_font("Helvetica", "", 9.5)
        for b in exp["bullets"]:
            self.set_x(17)
            self.cell(3, 4.5, "-")
            self.multi_cell(175, 4.5, _safe(b))
        self.ln(1.5)

    def education_item(self, edu: dict):
        self.set_x(15)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*self.NAVY)
        self.cell(120, 5, _safe(edu["title"]), ln=0)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(120, 120, 125)
        self.cell(0, 5, _safe(edu["period"]), align="R", ln=1)

        self.set_x(15)
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(*self.GREY)
        line = f"{edu['school']}"
        if edu.get("note"):
            line += f"  -  {edu['note']}"
        self.cell(0, 4.5, _safe(line), ln=1)
        self.ln(1)

    def skills_list(self, skills: list):
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(*self.GREY)
        for s in skills:
            self.set_x(17)
            self.cell(3, 4.5, "-")
            self.multi_cell(175, 4.5, _safe(s))
        self.ln(1)

    def two_col_table(self, rows: list):
        """Tableau 2 colonnes (labels gauche, valeurs droite)."""
        self.set_font("Helvetica", "", 9.5)
        for label, value in rows:
            self.set_x(15)
            self.set_text_color(*self.NAVY)
            self.set_font("Helvetica", "B", 9.5)
            self.cell(35, 5, _safe(label), ln=0)
            self.set_font("Helvetica", "", 9.5)
            self.set_text_color(*self.GREY)
            self.cell(0, 5, _safe(value), ln=1)
        self.ln(1)


def generate(offer: dict) -> bytes:
    """Genere un CV PDF adapte a l'offre."""
    titre       = offer.get("titre", "")
    description = offer.get("description", "")
    role        = cl.detect_sub_role(titre, description)

    pdf = _CVPdf(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Resume professionnel (adapte au role)
    pdf.section("Profil")
    summary = SUMMARY_BY_ROLE.get(role, SUMMARY_BY_ROLE["generic"])
    pdf.paragraph(summary, font_size=9.5)

    # Experiences (reordonnees selon pertinence pour le role)
    pdf.section("Experience professionnelle")
    for exp in _experiences_for_role(role):
        pdf.experience_item(exp)

    # Formation
    pdf.section("Formation")
    for edu in EDUCATION:
        pdf.education_item(edu)

    # Competences cles (adaptees au role)
    pdf.section("Competences cles")
    pdf.skills_list(SKILLS_BY_ROLE.get(role, SKILLS_BY_ROLE["generic"]))

    # Langues
    pdf.section("Langues")
    pdf.two_col_table(LANGUAGES)

    # Outils & infos pratiques
    pdf.section("Outils & disponibilite")
    pdf.two_col_table([
        ("Outils CRM",     "HubSpot, LinkedIn Sales Navigator"),
        ("Marketing",      "Canva, Notion, Wix, Webflow"),
        ("Bureautique",    "Pack Office (Excel avance), Google Suite"),
        ("Disponibilite",  PROFILE["available"]),
        ("Mobilite",       PROFILE["permit"]),
    ])

    out = pdf.output(dest="S")
    if isinstance(out, str):
        return out.encode("latin-1")
    return bytes(out)
