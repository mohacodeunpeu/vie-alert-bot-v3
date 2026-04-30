"""
CV genere dynamiquement par offre, niveau pro Bac+5.
- 1 page A4 garantie (layout compact + 2 colonnes en bas)
- Resume professionnel adapte a l'offre EXACTE (mission + role + mots-cles)
- Experiences reorganisees par pertinence + bullets selectionnes
- Mise en page ATS-friendly (texte selectable, sections standards)
- Design : header bleu marine + accent dore + QR code optionnel
"""

import io
import os
import re
import tempfile

from fpdf import FPDF

import cover_letter as cl


# ─── Donnees reelles d'Amine ──────────────────────────────────────────────────

PROFILE = {
    "name":       "AMINE BEN MANSOUR",
    "tagline":    "Business Developer | MBA Manager de Business Unit | Disponible VIE 2026",
    "phone":      "+33 6 60 64 57 83",
    "email":      "mohamedbenpro47@gmail.com",
    "city":       "Paris, France",
    "permit":     "Permis B",
    "remote":     "Remote OK",
    # QR : peut etre ton LinkedIn, ton CV video, ton portfolio, ton site perso.
    # Mets une URL ici, le bot mettra automatiquement un QR code en haut a droite.
    # Laisse vide ('') pour ne pas afficher de QR.
    "qr_url":     "https://www.linkedin.com/in/amine-ben-mansour-b50a06246/",
    "qr_label":   "Mon LinkedIn",
}


# ─── Resumes par sous-role (base, raffines ensuite par offre) ─────────────────

SUMMARY_BASE = {
    "product_marketing": (
        "MBA Manager de Business Unit (PSB Paris, soutenance juin 2026), avec une "
        "experience de gestion de projets digitaux internationaux (Wix Lisbonne) et de "
        "community management (GROW 360). Profil capable de structurer une demarche "
        "produit et de la decliner en actions marketing concretes."
    ),
    "digital_marketing": (
        "MBA Business Unit en cours (PSB Paris, juin 2026). Experience operationnelle "
        "en community management (GROW 360) et gestion de projets digitaux a "
        "l'international (Lisbonne). Maitrise des leviers d'engagement et lecture "
        "rigoureuse des KPIs marketing."
    ),
    "financial_analyst": (
        "MBA Manager de Business Unit en cours (PSB Paris, juin 2026), avec module "
        "approfondi de controle de gestion. Pilote au quotidien une activite "
        "operationnelle generant 360 KEUR de CA mensuel : indicateurs, reporting, "
        "lecture business des chiffres."
    ),
    "data_analyst": (
        "MBA Business Unit en cours (PSB Paris, juin 2026), forme aux outils d'analyse "
        "et au pilotage par la donnee. Manipule au quotidien des KPIs commerciaux et "
        "sait traduire un dataset en insight actionnable pour les decideurs."
    ),
    "purchasing": (
        "MBA Business Unit en cours (PSB Paris, juin 2026). Experience concrete de "
        "negociation B2B sur un portefeuille a 360 KEUR de CA mensuel. Profil "
        "rigoureux, multilingue, transposable directement aux enjeux achats et "
        "sourcing internationaux."
    ),
    "key_account": (
        "Business Developer B2B chez Agence 113 / DEFI GROUPE (360 KEUR de CA mensuel). "
        "MBA Manager de Business Unit en cours a PSB Paris. Profil hunter-farmer "
        "rigoureux, multilingue, oriente partenariats strategiques de long terme."
    ),
    "business_dev": (
        "Business Developer B2B chez Agence 113 / DEFI GROUPE, en charge d'un "
        "portefeuille generant 360 KEUR de CA mensuel. MBA Manager de Business Unit "
        "en cours (PSB Paris, juin 2026). Maitrise complete du cycle commercial, "
        "des outils CRM (HubSpot, Sales Navigator) et de la negociation B2B."
    ),
    "sales": (
        "Business Developer B2B chez Agence 113 / DEFI GROUPE (360 KEUR de CA mensuel) "
        "et ex-Sales Advisor au Printemps Haussmann. MBA Manager de Business Unit en "
        "cours a PSB Paris. Profil multilingue oriente resultats et relation client."
    ),
    "hr": (
        "Recruitment Officer chez Agence 113 / DEFI GROUPE : 300+ candidats geres en "
        "evenements, coordination POEI, sourcing actif. Double competence RH/Business "
        "rare, renforcee par le MBA Manager de Business Unit en cours a PSB Paris."
    ),
    "generic": (
        "Profil junior ambitieux : MBA Manager de Business Unit en cours (PSB Paris, "
        "juin 2026), Business Developer B2B en France (360 KEUR de CA mensuel), "
        "experience internationale a Lisbonne, multilingue (FR/AR natifs, EN courant)."
    ),
}


# ─── Experiences reelles ──────────────────────────────────────────────────────

EXPERIENCES = [
    {
        "id":      "defi",
        "title":   "Business Developer & Recruitment Officer (B2B)",
        "company": "Agence 113 - DEFI GROUPE",
        "city":    "Paris",
        "period":  "Sept. 2025 - Present",
        "bullets": {
            "default": [
                "Pilotage d'un portefeuille B2B generant 360 KEUR de CA mensuel : prospection, qualification, negociation, closing.",
                "Suivi et fidelisation des clients via HubSpot CRM, optimisation continue de la performance.",
                "Coordination du service POEI avec les acteurs France Travail et organisation d'evenements de recrutement.",
            ],
            "commerce": [
                "Pilotage d'un portefeuille B2B a 360 KEUR de CA mensuel : prospection, qualification, negociation, closing en autonomie.",
                "Construction et execution de plans de compte sur HubSpot CRM avec analyse de la performance commerciale.",
                "Negociation directe avec les decideurs et structuration de partenariats long terme (cycle de vente complet).",
            ],
            "marketing": [
                "Pilotage d'une activite a 360 KEUR de CA mensuel : analyse de la performance, lecture KPI, ajustement continu.",
                "Conception et execution de demarches d'acquisition clients (prospection ciblee, contenu de demarchage).",
                "Coordination avec les services internes (production, RH, communication) pour livrer une offre coherente.",
            ],
            "finance": [
                "Pilotage d'une activite a 360 KEUR de CA mensuel : suivi budgetaire, analyse de marges, reporting hebdomadaire.",
                "Lecture business des indicateurs : volume, mix, prix, rentabilite par client et par offre.",
                "Construction de dashboards Excel et coordination avec les services administratif et financier.",
            ],
            "hr": [
                "Organisation d'evenements de recrutement reunissant plus de 300 candidats par session (sourcing, qualification, accueil).",
                "Coordination du service POEI (Preparation Operationnelle a l'Emploi) avec les acteurs France Travail.",
                "Suivi des candidats et reporting des KPIs de recrutement aupres des managers business.",
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
                "Gestion de projets web pour clients internationaux : prise de brief, conception, livraison.",
                "Optimisation de l'experience utilisateur (UX) et de la performance de conversion.",
                "Coordination en autonomie avec equipes et clients multiculturels en remote.",
            ],
            "marketing": [
                "Pilotage de projets digitaux pour clients internationaux : brief, design, contenu, livraison.",
                "Optimisation UX et performance de conversion (lecture analytics, tests A/B leger).",
                "Adaptation des messages aux audiences locales (contexte multilingue et multiculturel).",
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
                "Atteinte et depassement reguliers des objectifs de vente sur un environnement premium.",
                "Service client haut de gamme et fidelisation d'une clientele internationale exigeante.",
                "Conseil personnalise et up-selling sur des produits a forte valeur ajoutee.",
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
                "Gestion editoriale des reseaux sociaux et pilotage de la strategie de contenu.",
                "Organisation d'evenements clients et animation de la communaute.",
                "Ajustement continu selon les KPIs d'engagement et de conversion.",
            ],
        },
    },
]


# Mapping role -> bullet variant a utiliser
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


# Quelles experiences mettre en premier selon le role
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


# ─── Formation (donnees reelles) ──────────────────────────────────────────────

EDUCATION = [
    ("MBA - Manager de Business Unit",
     "PSB Paris School of Business",
     "Paris - 2025 / 2026",
     "Soutenance juin 2026"),
    ("Bachelor Bac+3 - Developpement Commercial (REM)",
     "PSB Paris School of Business",
     "Paris - 2022 / 2025",
     "Obtenu"),
    ("Certification - Negociation Commerciale",
     "Negotiation Business School (en ligne)",
     "2025",
     "Certifie"),
    ("Habilitation SST",
     "Croix-Rouge Francaise - Paris",
     "2024",
     "Sauveteur Secouriste du Travail"),
]


# ─── Competences cles par role (5 lignes) ─────────────────────────────────────

SKILLS_BY_ROLE = {
    "product_marketing": [
        "Strategie produit, positionnement, pricing (modules MBA)",
        "Gestion de projets digitaux internationaux (Wix Lisbonne)",
        "Community Management et strategie de contenu (GROW 360)",
        "Lecture KPI, taux de conversion, ROI marketing",
        "Coordination cross-fonctionnelle (marketing / ventes / R&D)",
    ],
    "digital_marketing": [
        "Community Management et reseaux sociaux (GROW 360)",
        "Pilotage de campagnes digitales et lecture KPI/ROI",
        "Outils : Canva, Notion, suite Google, Wix",
        "UX et performance de conversion (Wix Lisbonne)",
        "Strategie de contenu multiculturelle et multilingue",
    ],
    "financial_analyst": [
        "Controle de gestion et lecture financiere (modules MBA)",
        "Pilotage de KPIs commerciaux a 360 KEUR/mois",
        "Reporting, analyse d'ecarts, dashboards",
        "Pack Office avance (Excel formules, TCD, recherches)",
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
        "Multilinguisme : FR / AR natifs, EN courant, ES intermediaire",
        "Pack Office avance et CRM HubSpot",
        "Suivi de performance fournisseurs et reporting",
    ],
    "key_account": [
        "Pilotage d'un portefeuille a 360 KEUR de CA mensuel",
        "Cycle commercial complet (prospection -> closing)",
        "HubSpot CRM, LinkedIn Sales Navigator",
        "Negotiation Business School (certifie 2025)",
        "Multilinguisme et adaptabilite culturelle",
    ],
    "business_dev": [
        "Business Development B2B (360 KEUR de CA mensuel)",
        "Cycle commercial complet : prospection -> closing",
        "HubSpot CRM, LinkedIn Sales Navigator",
        "Negotiation Business School (certifie 2025)",
        "Multilinguisme : FR / AR / EN / ES",
    ],
    "sales": [
        "Vente B2B et B2C premium (DEFI GROUPE et Printemps)",
        "Atteinte et depassement reguliers d'objectifs",
        "Negotiation Business School (certifie 2025)",
        "HubSpot CRM, LinkedIn Sales Navigator",
        "Multilinguisme et relation client haut de gamme",
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
        "Multilinguisme : FR / EN / AR / ES / ZH",
    ],
}


LANGUAGES = [
    ("Francais",  "Natif"),
    ("Arabe",     "Natif"),
    ("Anglais",   "Courant"),
    ("Espagnol",  "Intermediaire"),
    ("Chinois",   "Notions"),
]


# ─── Helpers : nettoyage texte + extraction de mots-cles ──────────────────────

def _safe(text: str) -> str:
    if not text:
        return ""
    repl = {
        "—": "-", "–": "-", "'": "'", "'": "'", '"': '"', '"': '"',
        "…": "...", " ": " ", " ": " ", "•": "-", "→": "->", "▸": "-",
        "€": "EUR", "œ": "oe", "Œ": "OE", "æ": "ae", "Æ": "AE",
    }
    for k, v in repl.items():
        text = text.replace(k, v)
    return text


# Mots a NE PAS reprendre dans le resume (trop generiques)
_STOPWORDS = {
    "vous", "serez", "etes", "etes", "etre", "avoir", "votre", "vos", "notre",
    "nos", "dans", "avec", "pour", "sur", "par", "que", "qui", "des", "les",
    "une", "des", "aux", "ses", "leurs", "leur", "missions", "mission",
    "poste", "stage", "vie", "junior", "senior", "experience", "candidat",
    "profil", "vous", "tres", "tres", "plus", "bien", "ainsi", "egalement",
    "alors", "donc", "selon", "celui", "celle", "afin", "lors", "entre",
    "vous serez", "h/f", "f/h", "h-f", "f-h", "francais", "anglais",
    "competences", "competence", "cours", "merci", "international",
    "international", "actuel", "futur", "futurs", "groupe", "equipe",
    "equipes", "client", "clients", "pays", "ville", "duree", "12", "18",
    "24", "mois", "annees",
}


def _extract_keywords(description: str, max_kw: int = 4) -> list:
    """Extrait quelques mots-cles techniques/sectoriels de la mission."""
    if not description:
        return []
    text = description.lower()
    # Mots de 5+ chars, hors stopwords
    words = re.findall(r"[a-zA-Zaaeeeeiiooouucc]{5,}", text)
    seen = set()
    out  = []
    for w in words:
        wl = w.lower()
        if wl in _STOPWORDS or wl in seen:
            continue
        seen.add(wl)
        out.append(w)
        if len(out) >= max_kw:
            break
    return out


def _dynamic_summary(role: str, offer: dict) -> str:
    """Resume professionnel raffine avec 1-2 elements specifiques de l'offre."""
    base = SUMMARY_BASE.get(role, SUMMARY_BASE["generic"])

    # Ajout d'une ligne ciblee sur l'offre
    titre      = (offer.get("titre") or "").strip()
    entreprise = (offer.get("entreprise") or "").strip()
    pays       = (offer.get("pays") or "").strip()

    if titre and entreprise:
        # Ne pas dupliquer "VIE" si deja dans le titre
        position_str = f"position de {titre} chez {entreprise}"
        location     = f" {pays}" if pays and pays not in ("N/A", "") else ""
        targeted = f"Candidat a la {position_str}{location}."
        return base + " " + targeted
    return base


# ─── QR Code ──────────────────────────────────────────────────────────────────

def _make_qr_png(url: str) -> str:
    """Genere un PNG temporaire du QR code, retourne le chemin."""
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


# ─── Generation PDF ───────────────────────────────────────────────────────────

class _CVPdf(FPDF):
    NAVY   = (15, 35, 85)
    GOLD   = (193, 154, 60)
    GREY   = (60, 60, 65)
    LIGHT  = (245, 247, 250)
    DARK_X = (90, 90, 95)

    def header(self):
        # Header bleu marine
        self.set_fill_color(*self.NAVY)
        self.rect(0, 0, 210, 30, style="F")

        # Nom (gauche)
        self.set_xy(15, 6)
        self.set_font("Helvetica", "B", 17)
        self.set_text_color(255, 255, 255)
        self.cell(0, 7, _safe(PROFILE["name"]), ln=1)

        # Tagline
        self.set_x(15)
        self.set_font("Helvetica", "I", 9.5)
        self.set_text_color(*self.GOLD)
        self.cell(0, 5, _safe(PROFILE["tagline"]), ln=1)

        # Contact ligne
        self.set_x(15)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(220, 225, 235)
        contact_line = f"{PROFILE['phone']}  |  {PROFILE['email']}  |  {PROFILE['city']}"
        self.cell(0, 5, _safe(contact_line), ln=1)

        # Bande doree
        self.set_fill_color(*self.GOLD)
        self.rect(0, 30, 210, 1, style="F")

        # Reset Y pour le contenu
        self.set_y(34)

    def footer(self):
        # Trait dore + ligne discrete
        self.set_y(-11)
        self.set_fill_color(*self.GOLD)
        self.rect(0, 286, 210, 0.5, style="F")
        self.set_y(-9)
        self.set_x(15)
        self.set_font("Helvetica", "I", 7.5)
        self.set_text_color(140, 140, 145)
        self.cell(0, 4, _safe(f"{PROFILE['name']}  |  {PROFILE['phone']}  |  {PROFILE['email']}"),
                  align="C")

    def section(self, title: str):
        self.ln(1)
        self.set_x(15)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*self.NAVY)
        self.cell(0, 6, _safe(title.upper()), ln=1)
        # Trait dore
        x, y = 15, self.get_y()
        self.set_fill_color(*self.GOLD)
        self.rect(x, y - 0.5, 22, 0.7, style="F")
        self.set_y(y + 0.5)

    def paragraph(self, text: str, font_size: float = 9.5):
        self.set_x(15)
        self.set_font("Helvetica", "", font_size)
        self.set_text_color(*self.GREY)
        self.multi_cell(180, 4.5, _safe(text))
        self.ln(0.5)

    def experience_item(self, title: str, period: str, sub: str, bullets: list):
        self.set_x(15)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*self.NAVY)
        self.cell(120, 5, _safe(title), ln=0)
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(*self.DARK_X)
        self.cell(0, 5, _safe(period), align="R", ln=1)

        self.set_x(15)
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(*self.GREY)
        self.cell(0, 4.5, _safe(sub), ln=1)

        self.set_font("Helvetica", "", 9)
        self.set_text_color(*self.GREY)
        for b in bullets:
            self.set_x(17)
            self.cell(3, 4, "-")
            self.multi_cell(176, 4, _safe(b))
        self.ln(1)

    def education_item(self, title: str, school: str, period: str, note: str):
        self.set_x(15)
        self.set_font("Helvetica", "B", 9.5)
        self.set_text_color(*self.NAVY)
        self.cell(140, 4.5, _safe(title), ln=0)
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(*self.DARK_X)
        self.cell(0, 4.5, _safe(period), align="R", ln=1)

        self.set_x(15)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*self.GREY)
        line = school
        if note:
            line += f"  -  {note}"
        self.cell(0, 4.2, _safe(line), ln=1)
        self.ln(0.3)

    def two_columns_skills_languages(self, skills: list, languages: list):
        """Affiche competences (gauche) et langues (droite) sur la meme zone."""
        start_y = self.get_y()
        col_w   = 87  # Largeur de chaque colonne

        # ─ Colonne gauche : Competences ─
        self.set_xy(15, start_y)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*self.NAVY)
        self.cell(col_w, 6, _safe("COMPETENCES CLES"), ln=2)
        self.set_fill_color(*self.GOLD)
        self.rect(15, self.get_y() - 0.5, 22, 0.7, style="F")
        self.set_y(self.get_y() + 1)

        self.set_font("Helvetica", "", 8.8)
        self.set_text_color(*self.GREY)
        for s in skills:
            self.set_x(17)
            self.cell(3, 4.2, "-")
            # Limiter a la largeur de colonne
            self.multi_cell(col_w - 5, 4.2, _safe(s))
        skills_end_y = self.get_y()

        # ─ Colonne droite : Langues ─
        self.set_xy(110, start_y)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*self.NAVY)
        self.cell(col_w, 6, _safe("LANGUES"), ln=2)
        self.set_fill_color(*self.GOLD)
        self.rect(110, self.get_y() - 0.5, 22, 0.7, style="F")
        self.set_y(self.get_y() + 1)

        self.set_font("Helvetica", "", 8.8)
        self.set_text_color(*self.GREY)
        for lang, level in languages:
            self.set_x(110)
            self.set_font("Helvetica", "B", 8.8)
            self.set_text_color(*self.NAVY)
            self.cell(28, 4.5, _safe(lang), ln=0)
            self.set_font("Helvetica", "", 8.8)
            self.set_text_color(*self.GREY)
            self.cell(0, 4.5, _safe(level), ln=1)
        langs_end_y = self.get_y()

        # Aligner Y final sur le plus bas
        self.set_y(max(skills_end_y, langs_end_y) + 2)

    def tools_strip(self):
        self.set_x(15)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*self.NAVY)
        self.cell(0, 6, _safe("OUTILS & DISPONIBILITE"), ln=1)
        self.set_fill_color(*self.GOLD)
        self.rect(15, self.get_y() - 0.5, 22, 0.7, style="F")
        self.ln(1)

        self.set_x(15)
        self.set_font("Helvetica", "", 8.8)
        self.set_text_color(*self.GREY)
        text = ("CRM : HubSpot, LinkedIn Sales Navigator   |   Marketing : Canva, Notion, "
                "Wix, Webflow   |   Bureautique : Pack Office (Excel avance), Google Suite   "
                "|   Disponibilite : VIE 2026 (debut juin / juillet selon mission)   |   "
                "Mobilite : Permis B, remote OK")
        self.multi_cell(180, 4.2, _safe(text))


def generate(offer: dict) -> bytes:
    """Genere un CV PDF adapte a l'offre."""
    titre       = offer.get("titre", "")
    description = offer.get("description", "")
    role        = cl.detect_sub_role(titre, description)

    pdf = _CVPdf(format="A4")
    pdf.set_auto_page_break(auto=False)  # Une seule page : controle manuel
    pdf.add_page()

    # ─── QR code (en haut a droite, par dessus le header) ───
    qr_url = (PROFILE.get("qr_url") or "").strip()
    qr_path = _make_qr_png(qr_url) if qr_url else ""
    if qr_path:
        try:
            pdf.image(qr_path, x=180, y=4.5, w=21, h=21)
            pdf.set_xy(180, 25.5)
            pdf.set_font("Helvetica", "B", 6)
            pdf.set_text_color(*pdf.GOLD)
            pdf.cell(21, 3, _safe(PROFILE.get("qr_label") or ""), align="C")
        except Exception:
            pass
        finally:
            try:
                os.unlink(qr_path)
            except Exception:
                pass

    # ─── Profil ───
    pdf.section("Profil")
    pdf.paragraph(_dynamic_summary(role, offer), font_size=9.2)

    # ─── Experience professionnelle ───
    pdf.section("Experience professionnelle")
    variant = BULLET_VARIANT.get(role, "default")
    order   = ROLE_PRIORITY.get(role, ROLE_PRIORITY["generic"])
    by_id   = {e["id"]: e for e in EXPERIENCES}
    for exp_id in order:
        exp = by_id.get(exp_id)
        if not exp:
            continue
        bullets = exp["bullets"].get(variant) or exp["bullets"]["default"]
        sub     = f"{exp['company']}   |   {exp['city']}"
        pdf.experience_item(exp["title"], exp["period"], sub, bullets)

    # ─── Formation ───
    pdf.section("Formation")
    for title, school, period, note in EDUCATION:
        pdf.education_item(title, school, period, note)

    # ─── Competences + Langues (2 colonnes) ───
    skills = SKILLS_BY_ROLE.get(role, SKILLS_BY_ROLE["generic"])
    pdf.two_columns_skills_languages(skills, LANGUAGES)

    # ─── Outils + dispo (strip horizontal) ───
    pdf.tools_strip()

    out = pdf.output(dest="S")
    if isinstance(out, str):
        return out.encode("latin-1")
    return bytes(out)
