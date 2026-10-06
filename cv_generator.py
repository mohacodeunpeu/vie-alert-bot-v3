"""
CV généré dynamiquement par offre, à partir de faits vérifiés (Bachelor REM, Bac+3).

Ce qui pilote le rendu, dans l'ordre :

  1. L'OFFRE d'abord. Le titre du CV reprend l'intitulé du poste, le résumé cite
     l'entreprise et le pays, les expériences sont réordonnées selon le secteur
     détecté, et les mots-clés ATS de l'annonce sont réinjectés dans les bullets
     — uniquement là où c'est vrai (cf. offer_analyzer.enrich_bullet).
  2. Le sous-rôle ensuite (10 familles), qui choisit la base de contenu.
  3. La mise en page en dernier, calculée : on part d'une typographie CONFORTABLE
     et on ne réduit que si ça dépasse. Une page A4 reste garantie.

Trois défauts corrigés ici, tous visibles à l'œil sur les PDF précédents :

  * Le texte était écrit sans aucun accent. Ce n'était pas une contrainte de
    fpdf : la police de base accepte le latin-1, donc « Négociation » passe très
    bien. Un CV français sans accents lu par un recruteur français, ça ne fait
    pas « compact », ça fait cassé.
  * Le symbole EUR est le seul caractère que la police de base refuse. On
    écrit donc « k€ » dans les données et _safe() le rend en « k EUR »,
    lisible. Le jour où une police Unicode est embarquée, il suffit
    de retirer cette ligne de _safe().
  * Le contenu s'arrêtait à 195 mm sur une page utile de 285 : un tiers de page
    blanc, alors que les polices étaient écrasées à 8,3 pt pour « tenir en une
    page ». Serré ET vide. Le calage automatique règle les deux.
"""

import os
import tempfile

from fpdf import FPDF

import cover_letter as cl
import offer_analyzer as oa


# ─── Données réelles d'Amine ──────────────────────────────────────────────────
#
# SOURCE UNIQUE : profil.json de hellowork-automation-pro (statut « verifie »),
# relu le 06/10/2026. Jusqu'à cette date, ce fichier annonçait un « MBA Manager
# de Business Unit en cours (PSB Paris, soutenance juin 2026) », un poste « en
# cours » chez DEFI GROUPE, « 360 k€/mois », « 300+ candidats », « +35 %
# d'engagement », du chinois et HubSpot. Rien de cela n'est dans son profil
# vérifié : il a un Bachelor REM (Bac+3) de Paris Nord Business School, pas de
# MBA, et DEFI GROUPE s'est terminé en juillet 2026. Un diplôme ou un chiffre
# annoncé et non détenu tombe au premier appel du recruteur, et la candidature
# tombe avec lui — c'est arrivé avec Bessand (VIE246499) le 30/09.
#
# Règle : aucun chiffre, outil, diplôme ou langue n'entre ici sans être dans
# profil.json avec le statut « verifie ». Un chiffre vrai et précis se rajoute
# le jour où il le confirme, avec ce qu'il mesure exactement.

PROFILE = {
    "name":       "AMINE BEN MANSOUR",
    "phone":      "+33 6 60 64 57 83",
    "email":      "mohamedbenpro47@gmail.com",
    "city":       "Paris, France",
    "qr_url":     "https://www.linkedin.com/in/amine-ben-mansour-b50a06246/",
    "qr_label":   "Mon LinkedIn",
    "video_cv_url": "",
}


# Intitulé de repli par rôle, quand l'offre n'a pas de titre exploitable.
TAGLINE_BY_ROLE = {
    "product_marketing": "Marketing & Projets digitaux",
    "digital_marketing": "Digital Marketing",
    "financial_analyst": "Business Analyst junior",
    "data_analyst":      "Business Analyst junior",
    "purchasing":        "Achats & Relation fournisseurs",
    "key_account":       "Key Account Manager junior",
    "business_dev":      "Business Developer",
    "sales":             "Sales B2B",
    "hr":                "Talent Acquisition",
    "generic":           "Business Developer",
}

# Suffixe commun : ce qui ne change jamais, quel que soit le poste visé.
# Court exprès : avec un intitulé d'offre de 46 caractères, la ligne doit
# encore s'arrêter avant le QR code (x = 179 mm).
TAGLINE_SUFFIX = "Bachelor REM (Bac+3) | TOEIC 915 | Dispo. immédiate"


# ─── Résumés par sous-rôle ────────────────────────────────────────────────────
# Socle factuel. La phrase d'accroche liée à l'offre est ajoutée par-dessus, dans
# _dynamic_summary() — jamais en remplacement, pour qu'aucun fait ne disparaisse.

SUMMARY_BASE = {
    "product_marketing": (
        "Expérience digitale et terrain : Website Builder chez Wix à Lisbonne "
        "(analyse des besoins clients, environnement anglophone), community "
        "manager & événementiel chez Grow 360 à Paris, vente premium au "
        "Printemps Haussmann. Bachelor REM (Bac+3), anglais courant (TOEIC 915/990)."
    ),
    "digital_marketing": (
        "Community manager & événementiel chez Grow 360 (réseaux sociaux de "
        "restaurants, organisation d'événements) et Website Builder chez Wix à "
        "Lisbonne. Web : HTML/CSS/JavaScript, Wix/Velo, WordPress, Webflow. "
        "Bachelor REM (Bac+3), anglais courant (TOEIC 915/990)."
    ),
    "financial_analyst": (
        "Profil business : prospection et suivi d'un portefeuille clients chez "
        "PROMAN Group et DEFI GROUPE, vente premium au Printemps Haussmann. "
        "Bachelor REM (Bac+3). Rigueur de suivi, outils de reporting (Pack "
        "Office), anglais courant (TOEIC 915/990)."
    ),
    "data_analyst": (
        "Bachelor REM (Bac+3). Outils de suivi et de reporting (Pack Office), "
        "bases web (HTML/CSS/JavaScript) et automatisation par l'IA. Expérience "
        "business en prospection et suivi de portefeuille clients (PROMAN Group, "
        "DEFI GROUPE). Anglais courant (TOEIC 915/990)."
    ),
    "purchasing": (
        "Expérience B2B côté vente : prospection, identification des besoins des "
        "entreprises et proposition de solutions (PROMAN Group, DEFI GROUPE). "
        "Bachelor REM (Bac+3). Français et arabe natifs, anglais courant "
        "(TOEIC 915/990)."
    ),
    "key_account": (
        "Développement et fidélisation d'un portefeuille clients chez PROMAN "
        "Group (2026) ; identification des besoins des entreprises et suivi des "
        "dossiers chez DEFI GROUPE (2025 - juil. 2026). Bachelor REM (Bac+3), "
        "anglais courant (TOEIC 915/990), arabe natif."
    ),
    "business_dev": (
        "Chargé d'affaires chez PROMAN Group (2026) et chargé de recrutement & "
        "commercial chez DEFI GROUPE (2025 - juil. 2026) : prospection B2B, "
        "identification des besoins des entreprises, développement et "
        "fidélisation d'un portefeuille clients. Bachelor REM (Bac+3), anglais "
        "courant (TOEIC 915/990), arabe natif."
    ),
    "sales": (
        "Vente B2B et B2C : chargé d'affaires chez PROMAN Group, chargé de "
        "recrutement & commercial chez DEFI GROUPE, conseiller premium "
        "horlogerie au Printemps Haussmann auprès d'une clientèle "
        "internationale. Bachelor REM (Bac+3), anglais courant (TOEIC 915/990)."
    ),
    "hr": (
        "Un an chargé de recrutement & commercial chez DEFI GROUPE : sourcing, "
        "présélection et entretiens candidats, analyse du besoin des "
        "entreprises, suivi des recrutements jusqu'à leur aboutissement. Puis "
        "chargé d'affaires chez PROMAN Group. Bachelor REM (Bac+3), anglais "
        "courant (TOEIC 915/990)."
    ),
    "generic": (
        "Bachelor REM (Bac+3). Chargé d'affaires (PROMAN Group), chargé de "
        "recrutement & commercial (DEFI GROUPE), expérience internationale à "
        "Lisbonne (Wix), vente premium au Printemps Haussmann. Français et arabe "
        "natifs, anglais courant (TOEIC 915/990). Disponible immédiatement."
    ),
}


# Ce que chaque secteur détecté permet de dire honnêtement, sans rien inventer.
# Utilisé pour la phrase d'accroche liée à l'offre.
INDUSTRY_ANGLE = {
    "luxe":         "une clientèle internationale premium (Printemps Haussmann)",
    "retail":       "la vente premium et la relation client (Printemps Haussmann)",
    "tech":         "des projets web clients menés à Lisbonne (Wix)",
    "conseil":      "l'analyse du besoin client et le suivi de dossiers en parallèle",
    "finance":      "le suivi rigoureux d'un portefeuille clients",
    "pharma":       "la rigueur de suivi des dossiers",
    "automotive":   "la prospection B2B et la relation client",
    "energy":       "la prospection B2B et le suivi des besoins clients",
    "agroalim":     "le développement et la fidélisation d'un portefeuille clients",
    "industrie":    "la coordination entre plusieurs interlocuteurs",
    "construction": "la coordination entre plusieurs interlocuteurs",
    "telecom":      "la prospection B2B et le suivi des dossiers clients",
}


# ─── Expériences réelles ──────────────────────────────────────────────────────
# Les bullets reprennent les missions de son CV, reformulées selon le rôle visé,
# jamais augmentées. Mêmes formulations que cv_builder.py côté HelloWork.

EXPERIENCES = [
    {
        # Son poste le plus récent. Il manquait à tous les CV VIE jusqu'au
        # 06/10/2026.
        "id":      "proman",
        "title":   "Chargé d'affaires",
        "company": "PROMAN Group",
        "city":    "Paris",
        "period":  "2026",
        "recent":  True,
        "bullets": {
            "default": [
                "Prospection commerciale et développement de nouveaux clients.",
                "Gestion et fidélisation du portefeuille clients.",
                "Développement de partenariats et suivi des besoins clients.",
            ],
            "commerce": [
                "Prospection commerciale et développement de nouveaux clients.",
                "Gestion et fidélisation du portefeuille clients.",
                "Développement de partenariats et suivi des besoins clients.",
            ],
            "marketing": [
                "Développement de partenariats et suivi des besoins clients.",
                "Prospection commerciale et développement de nouveaux clients.",
            ],
            "finance": [
                "Gestion et suivi du portefeuille clients.",
                "Suivi des besoins clients et des dossiers.",
            ],
            "hr": [
                "Chargé d'affaires dans un groupe de travail temporaire : "
                "prospection et suivi des entreprises clientes.",
                "Gestion et fidélisation du portefeuille clients.",
            ],
        },
    },
    {
        # Terminé en juillet 2026 : jamais « aujourd'hui », jamais « en cours ».
        "id":      "defi",
        "title":   "Chargé de recrutement & commercial",
        "company": "DEFI GROUPE (Agence 113)",
        "city":    "Île-de-France",
        "period":  "2025 - juil. 2026",
        "recent":  True,
        "bullets": {
            "default": [
                "Prospection et développement de nouvelles opportunités commerciales.",
                "Identification des besoins des entreprises et proposition de solutions adaptées.",
                "Sourcing, sélection et accompagnement des candidats.",
                "Coordination entre entreprises et candidats, suivi des dossiers.",
            ],
            "commerce": [
                "Prospection et développement de nouvelles opportunités commerciales.",
                "Identification des besoins des entreprises et proposition de solutions adaptées.",
                "Coordination entre entreprises et candidats, suivi des dossiers "
                "jusqu'à leur aboutissement.",
                "Sourcing, sélection et accompagnement des candidats.",
            ],
            "marketing": [
                "Identification des besoins des entreprises et proposition de solutions adaptées.",
                "Prospection et développement de nouvelles opportunités commerciales.",
                "Coordination entre entreprises et candidats, suivi des dossiers.",
            ],
            "finance": [
                "Suivi des dossiers entreprises et candidats jusqu'à leur aboutissement.",
                "Identification des besoins des entreprises et proposition de solutions adaptées.",
                "Prospection et développement de nouvelles opportunités commerciales.",
            ],
            "hr": [
                "Seul interlocuteur des deux côtés : les entreprises pour leur "
                "besoin, les candidats pour leur parcours.",
                "Sourcing, présélection téléphonique et entretiens candidats.",
                "Prospection d'entreprises, analyse du besoin et proposition de profils adaptés.",
                "Suivi des recrutements jusqu'à leur aboutissement.",
            ],
        },
    },
    {
        "id":      "wix",
        "title":   "Website Builder",
        "company": "Wix",
        "city":    "Lisbonne, Portugal",
        "period":  "avr. - août 2025",
        "bullets": {
            "default": [
                "Analyse des besoins clients et proposition de solutions adaptées.",
                "Accompagnement des clients et suivi des projets.",
                "Travail quotidien en environnement professionnel anglophone.",
            ],
            "commerce": [
                "Analyse des besoins clients et proposition de solutions adaptées.",
                "Travail quotidien en environnement professionnel anglophone.",
            ],
            "marketing": [
                "Analyse des besoins clients et accompagnement de leurs projets de sites web.",
                "Travail quotidien en environnement professionnel anglophone.",
            ],
            "finance": [
                "Accompagnement des clients et suivi des projets.",
                "Travail quotidien en environnement professionnel anglophone.",
            ],
            "hr": [
                "Accompagnement des clients et suivi des projets.",
                "Travail quotidien en environnement professionnel anglophone.",
            ],
        },
    },
    {
        "id":      "printemps",
        "title":   "Conseiller premium horlogerie",
        "company": "Printemps Haussmann",
        "city":    "Paris",
        "period":  "2023 - 2024",
        "bullets": {
            "default": [
                "Conseil et vente auprès d'une clientèle internationale.",
                "Développement de la relation client et fidélisation.",
                "Gestion des priorités dans un environnement exigeant.",
            ],
            "commerce": [
                "Conseil et vente en horlogerie auprès d'une clientèle internationale.",
                "Écoute du besoin et argumentation produit.",
                "Développement de la relation client et fidélisation.",
            ],
            "marketing": [
                "Contact direct avec une clientèle internationale premium.",
                "Écoute du besoin et argumentation produit.",
            ],
            "finance": [
                "Conseil et vente en horlogerie premium.",
                "Gestion des priorités dans un environnement exigeant.",
            ],
            "hr": [
                "Conseil et accompagnement d'une clientèle internationale.",
                "Écoute du besoin avant toute proposition.",
            ],
        },
    },
    {
        "id":      "grow",
        "title":   "Community manager & événementiel",
        "company": "Grow 360",
        "city":    "Paris",
        "period":  "2022 - 2024",
        "bullets": {
            "default": [
                "Organisation d'événements et animation sur le terrain.",
                "Gestion des réseaux sociaux de restaurants.",
            ],
            "marketing": [
                "Gestion des réseaux sociaux de restaurants.",
                "Organisation d'événements et animation sur le terrain.",
                "Relation client et animation de communauté.",
            ],
            "commerce": [
                "Relation client et animation.",
                "Organisation d'événements.",
            ],
            "finance": [
                "Organisation d'événements.",
                "Relation client.",
            ],
            "hr": [
                "Organisation d'événements et animation sur le terrain.",
                "Relation client et animation de communauté.",
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

# Priorité d'affichage des expériences selon le rôle. Les postes marqués
# « recent » (PROMAN, DEFI GROUPE) restent en tête quel que soit le rôle ; cet
# ordre décide seulement de LEUR ordre entre eux, puis de celui du reste —
# chronologique par défaut, le secteur de l'offre (INDUSTRY_BOOST) remontant
# d'un cran l'expérience qui lui parle.
ROLE_PRIORITY = {
    "product_marketing": ["proman", "defi", "wix", "grow", "printemps"],
    "digital_marketing": ["proman", "defi", "grow", "wix", "printemps"],
    "financial_analyst": ["proman", "defi", "wix", "printemps", "grow"],
    "data_analyst":      ["proman", "defi", "wix", "printemps", "grow"],
    "purchasing":        ["proman", "defi", "wix", "printemps", "grow"],
    "key_account":       ["proman", "defi", "wix", "printemps", "grow"],
    "business_dev":      ["proman", "defi", "wix", "printemps", "grow"],
    "sales":             ["proman", "defi", "wix", "printemps", "grow"],
    "hr":                ["defi", "proman", "wix", "printemps", "grow"],
    "generic":           ["proman", "defi", "wix", "printemps", "grow"],
}

# Le secteur de l'offre remonte une expérience d'un cran. Un poste dans le luxe
# ou le retail a tout intérêt à voir Printemps Haussmann haut dans la page, même
# pour un rôle business : c'est la ligne du CV qui parle au recruteur.
INDUSTRY_BOOST = {
    "luxe":   "printemps",
    "retail": "printemps",
    "tech":   "wix",
}

# Nombre de bullets par position (1re expérience en premier).
BULLETS_PER_POSITION = [4, 3, 2, 2, 2]


# ─── Formation ────────────────────────────────────────────────────────────────
# Le plus haut diplôme est le Bachelor REM (Bac+3). Ni master, ni MBA.

EDUCATION = [
    ("Bachelor REM (Bac+3)",
     "Paris Nord Business School (distanciel)",
     "2026",
     ""),
    ("BTS NTC (Bac+2)",
     "Paris Nord Business School, Saint-Denis",
     "2025",
     ""),
    ("Formation Website Builder",
     "Wix, Lisbonne",
     "avr. - août 2025",
     ""),
    # Certificat reçu le 04/10/2026 (courriel Coursera « Votre Certificat est
    # prêt »). Le cours seul — pas le « Professional Certificate » complet.
    ("Certificat Sales and CRM Overview",
     "Salesforce / Pathstream (Coursera)",
     "2026",
     ""),
    ("SST - Sauveteur Secouriste du Travail",
     "Croix-Rouge française, Paris",
     "depuis 2022",
     ""),
]


# ─── Compétences par rôle ─────────────────────────────────────────────────────
# Uniquement ce qui est dans son CV vérifié.

SKILLS_BY_ROLE = {
    "product_marketing": [
        "Analyse du besoin client et proposition de solutions",
        "Création de sites web : Wix/Velo, WordPress, Webflow",
        "Réseaux sociaux et événementiel (Grow 360)",
        "Relation client internationale (Printemps Haussmann, Wix)",
        "IA et automatisation",
    ],
    "digital_marketing": [
        "Réseaux sociaux et animation de communauté (Grow 360)",
        "Web : HTML/CSS/JavaScript, Wix/Velo, WordPress, Webflow",
        "IA et automatisation",
        "Organisation d'événements",
        "Pack Office et outils de reporting",
    ],
    "financial_analyst": [
        "Pack Office, outils de suivi et de reporting",
        "Suivi de portefeuille clients et de dossiers",
        "Lecture business des besoins clients",
        "IA et automatisation",
        "Anglais professionnel (TOEIC 915/990)",
    ],
    "data_analyst": [
        "Pack Office, outils de suivi et de reporting",
        "HTML/CSS/JavaScript, VS Code",
        "IA et automatisation",
        "Suivi de portefeuille clients et de dossiers",
        "Anglais professionnel (TOEIC 915/990)",
    ],
    "purchasing": [
        "Identification du besoin et proposition de solutions",
        "Prospection et relation B2B",
        "Suivi des dossiers jusqu'à leur aboutissement",
        "Pack Office, outils de suivi et de reporting",
        "FR / AR natifs, EN courant (TOEIC 915)",
    ],
    "key_account": [
        "Développement et fidélisation d'un portefeuille clients",
        "Prospection et développement commercial B2B",
        "Identification du besoin et proposition de solutions",
        "CRM : Salesforce (formation Coursera 2026)",
        "FR / AR natifs, EN courant (TOEIC 915)",
    ],
    "business_dev": [
        "Prospection et développement commercial B2B",
        "Identification du besoin et proposition de solutions",
        "Développement de partenariats",
        "CRM : Salesforce (formation Coursera 2026)",
        "FR / AR natifs, EN courant (TOEIC 915)",
    ],
    "sales": [
        "Vente conseil premium (Printemps Haussmann)",
        "Prospection et développement commercial B2B",
        "Relation client et fidélisation",
        "CRM : Salesforce (formation Coursera 2026)",
        "FR / AR natifs, EN courant (TOEIC 915)",
    ],
    "hr": [
        "Sourcing, présélection et entretiens candidats",
        "Analyse du besoin des entreprises",
        "Suivi des recrutements jusqu'à leur aboutissement",
        "Relation entreprises et candidats",
        "Habilitation SST (Croix-Rouge française)",
    ],
    "generic": [
        "Prospection et développement commercial B2B",
        "Relation client et fidélisation",
        "Sourcing et suivi de candidats",
        "Web : Wix/Velo, WordPress, HTML/CSS/JS",
        "IA et automatisation",
    ],
}


LANGUAGES = [
    ("Français",  "Natif"),
    ("Arabe",     "Natif"),
    ("Anglais",   "Courant - TOEIC 915/990"),
    ("Espagnol",  "Notions"),
]


# Outils que l'offre peut mentionner et qu'Amine pratique réellement. Hors de
# cette liste, un outil de l'annonce n'entre PAS dans les compétences : un CV qui
# revendique un outil sans y avoir touché se paie au premier entretien.
# HubSpot et Sales Navigator en sont sortis le 06/10/2026 : absents de son CV.
TOOLS_HE_KNOWS = {
    "salesforce":  "CRM : Salesforce (formation Coursera 2026)",
    "excel":       "Pack Office (Excel)",
    "pack office": "Pack Office",
    "wix":         "Wix/Velo",
    "wordpress":   "WordPress",
    "webflow":     "Webflow",
    "html":        "HTML/CSS/JavaScript",
    "javascript":  "HTML/CSS/JavaScript",
}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _safe(text: str) -> str:
    """Rend le texte imprimable par la police de base (latin-1).

    Les accents passent sans problème : seul le symbole EUR est hors jeu, d'où
    « k€ » -> « k EUR ». Une police Unicode embarquée rendrait ces deux lignes
    inutiles ; le reste de la table ne sert qu'à normaliser la typographie.
    """
    if not text:
        return ""
    # Échappements explicites : ces caractères sont indiscernables les uns des
    # autres à la relecture (apostrophe droite vs. courbe, espace fine vs.
    # insécable), et une table qu'on ne peut pas relire est une table qu'on casse.
    repl = {
        "k€": "k EUR",   # k€  -> seul caractère refusé par la police de base
        "€":  " EUR",    # €
        "—": "-",        # —
        "–": "-",        # –
        "‘": "'",        # '
        "’": "'",        # '
        "“": '"',        # "
        "”": '"',        # "
        "…": "...",      # …
        " ": " ",        # espace insécable
        " ": " ",        # espace fine insécable
        "•": "-",        # •
        "→": "->",       # →
        "▸": "-",        # ▸
        "œ": "oe", "Œ": "OE",
        "æ": "ae", "Æ": "AE",
    }
    for k, v in repl.items():
        text = text.replace(k, v)
    return " ".join(text.split()) if "  " in text else text


def _clean_job_title(titre: str) -> str:
    """L'intitulé de l'offre, débarrassé de ce qui n'a rien à faire sur un CV."""
    if not titre:
        return ""
    out = titre
    for junk in ("(H/F)", "(F/H)", "(h/f)", "(f/h)", "H/F", "F/H",
                 "- VIE", "VIE -", "V.I.E.", "VIE"):
        out = out.replace(junk, " ")
    out = " ".join(out.split()).strip(" -–—|,;:")
    # Un titre à rallonge déborde du header : au-delà, le rôle générique est plus lisible.
    return out if 3 <= len(out) <= 46 else ""


def _tagline(role: str, offer: dict) -> str:
    """Le titre du CV reprend le poste visé. C'est la première ligne lue."""
    poste = _clean_job_title(offer.get("titre", "")) or TAGLINE_BY_ROLE.get(
        role, TAGLINE_BY_ROLE["generic"])
    return f"{poste} | {TAGLINE_SUFFIX}"


def _dynamic_summary(role: str, offer: dict, analysis: dict) -> str:
    """Socle factuel du rôle + une phrase qui vise CETTE offre.

    L'ancienne version prenait `offer` et `analysis` en paramètres et ne s'en
    servait pas : le résumé était l'un de dix textes figés, identique pour
    Decathlon Shanghai et L'Oréal New York. C'était le cœur du problème — un CV
    « adapté » qui ne parlait jamais du poste.

    Rien n'est inventé ici : on nomme l'entreprise et le pays (qui viennent de
    l'annonce) et on met en avant une expérience qu'il a vraiment.
    """
    base = SUMMARY_BASE.get(role, SUMMARY_BASE["generic"])

    entreprise = str(offer.get("entreprise") or "").strip()
    pays       = str(offer.get("pays") or "").strip()
    industry   = analysis.get("industry", "generic")
    angle      = INDUSTRY_ANGLE.get(industry)

    cible = ""
    if entreprise and pays:
        cible = f"{entreprise} ({pays.title()})"
    elif entreprise:
        cible = entreprise
    elif pays:
        cible = pays.title()

    if not cible:
        return base

    phrase = f"Candidature au V.I.E. {cible}"
    if angle:
        phrase += f", où je peux m'appuyer sur {angle}"
    return f"{base} {phrase}."


def _skills_for(role: str, analysis: dict) -> list:
    """Compétences du rôle, avec les outils de l'annonce remontés en tête.

    Un ATS cherche ses propres mots. Si l'offre parle de Salesforce et qu'Amine
    s'y est formé, la ligne doit être visible en haut — pas noyée en bas de
    page comme avant, où les outils de l'annonce finissaient collés en minuscules
    à la fin d'une bande de texte (« ... | tmall, jd.com »).
    """
    base = list(SKILLS_BY_ROLE.get(role, SKILLS_BY_ROLE["generic"]))
    hoisted = []
    for tool in analysis.get("tools", []):
        label = TOOLS_HE_KNOWS.get(tool.lower())
        if not label or label in hoisted:
            continue
        if any(label.lower().split(" (")[0] in s.lower() for s in base):
            continue  # déjà dit autrement dans la liste du rôle
        hoisted.append(label)
    if not hoisted:
        return base
    return (hoisted + base)[:6]


def _ordered_experiences(role: str, analysis: dict) -> list:
    """Les postes récents d'abord, puis l'ordre du rôle, puis le secteur.

    Deux règles apprises sur les PDF précédents :

      * Les postes les plus récents (PROMAN, DEFI GROUPE) ouvrent le CV,
        toujours. Un recruteur lit la première ligne comme « ce qu'il a fait en
        dernier » : voir un job de 2023 au-dessus d'un poste de 2026 ne se lit
        pas comme un choix, ça se lit comme une erreur. La pertinence réordonne
        le RESTE, pas ça.
      * Le coup de pouce sectoriel ne remonte donc jamais au-dessus d'eux.
    """
    order  = list(ROLE_PRIORITY.get(role, ROLE_PRIORITY["generic"]))
    recent = {e["id"] for e in EXPERIENCES if e.get("recent")}
    order  = [i for i in order if i in recent] + [i for i in order if i not in recent]
    floor  = sum(1 for i in order if i in recent)

    boost = INDUSTRY_BOOST.get(analysis.get("industry", "generic"))
    if boost and boost in order and boost not in recent:
        i = order.index(boost)
        if i > floor:
            order.insert(max(floor, i - 1), order.pop(i))
    return order


# ─── QR Code ──────────────────────────────────────────────────────────────────

def _make_qr_png(url: str) -> str:
    """Chemin d'un PNG de QR code, ou "" si la dépendance manque.

    `qrcode` était absent de requirements.txt : l'ImportError était avalée ici,
    donc aucun CV parti en production n'a jamais porté de QR code. Le paquet est
    désormais déclaré — cette porte de sortie ne sert plus qu'en dernier recours.
    """
    try:
        import qrcode
    except ImportError:
        return ""
    try:
        qr = qrcode.QRCode(version=1, box_size=10, border=1,
                           error_correction=qrcode.constants.ERROR_CORRECT_M)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="white", back_color=(15, 35, 85))
        fd, path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        img.save(path)
        return path
    except Exception:
        return ""


# ─── PDF class ────────────────────────────────────────────────────────────────

class _CVPdf(FPDF):
    NAVY   = (15, 35, 85)
    GOLD   = (193, 154, 60)
    GREY   = (60, 60, 65)
    LIGHT  = (245, 247, 250)
    DARK_X = (90, 90, 95)

    tagline = f"Business Developer | {TAGLINE_SUFFIX}"
    # Facteur de confort typographique, fixé par le calage automatique.
    scale   = 1.0

    def s(self, size: float) -> float:
        return round(size * self.scale, 2)

    def header(self):
        self.set_fill_color(*self.NAVY)
        self.rect(0, 0, 210, 29, style="F")

        self.set_xy(14, 5.5)
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(255, 255, 255)
        self.cell(0, 6.5, _safe(PROFILE["name"]), ln=1)

        self.set_x(14)
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(*self.GOLD)
        self.cell(0, 4.5, _safe(self.tagline), ln=1)

        self.set_x(14)
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(210, 220, 235)
        contact = f"{PROFILE['phone']}  |  {PROFILE['email']}  |  {PROFILE['city']}"
        self.cell(0, 4.5, _safe(contact), ln=1)

        self.set_fill_color(*self.GOLD)
        self.rect(0, 29, 210, 0.8, style="F")
        self.set_y(33)

    def footer(self):
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
        self.ln(self.s(1.2))
        self.set_x(14)
        self.set_font("Helvetica", "B", self.s(10.5))
        self.set_text_color(*self.NAVY)
        self.cell(0, self.s(5.5), _safe(title.upper()), ln=1)
        y = self.get_y()
        self.set_fill_color(*self.GOLD)
        self.rect(14, y - 0.4, 20, 0.6, style="F")
        self.set_y(y + self.s(0.6))

    def paragraph(self, text: str, font_size: float = 8.8):
        self.set_x(14)
        self.set_font("Helvetica", "", self.s(font_size))
        self.set_text_color(*self.GREY)
        self.multi_cell(182, self.s(4.3), _safe(text))
        self.ln(self.s(0.4))

    def experience_item(self, title: str, period: str, sub: str, bullets: list):
        self.set_x(14)
        self.set_font("Helvetica", "B", self.s(9.5))
        self.set_text_color(*self.NAVY)
        self.cell(126, self.s(4.6), _safe(title), ln=0)
        self.set_font("Helvetica", "", self.s(8))
        self.set_text_color(*self.DARK_X)
        self.cell(56, self.s(4.6), _safe(period), align="R", ln=1)

        self.set_x(14)
        self.set_font("Helvetica", "I", self.s(8.5))
        self.set_text_color(*self.GREY)
        self.cell(0, self.s(4.0), _safe(sub), ln=1)

        self.set_font("Helvetica", "", self.s(8.7))
        self.set_text_color(*self.GREY)
        for b in bullets:
            self.set_x(16)
            self.cell(3, self.s(4.1), "-")
            self.multi_cell(178, self.s(4.1), _safe(b))
        self.ln(self.s(0.8))

    def education_item(self, title: str, school: str, period: str, note: str):
        self.set_x(14)
        self.set_font("Helvetica", "B", self.s(9))
        self.set_text_color(*self.NAVY)
        self.cell(136, self.s(4.2), _safe(title), ln=0)
        self.set_font("Helvetica", "", self.s(8))
        self.set_text_color(*self.DARK_X)
        self.cell(46, self.s(4.2), _safe(period), align="R", ln=1)

        self.set_x(14)
        self.set_font("Helvetica", "", self.s(8.5))
        self.set_text_color(*self.GREY)
        line = school + (f"  -  {note}" if note else "")
        self.cell(0, self.s(3.9), _safe(line), ln=1)
        self.ln(self.s(0.5))

    def two_columns_skills_languages(self, skills: list, languages: list):
        """Compétences (gauche) | Langues (droite) — deux colonnes indépendantes."""
        start_y = self.get_y()
        col_w   = 86

        self.set_xy(14, start_y)
        self.set_font("Helvetica", "B", self.s(10.5))
        self.set_text_color(*self.NAVY)
        self.cell(col_w, self.s(5.5), _safe("COMPÉTENCES CLÉS"), ln=2)
        gy = self.get_y()
        self.set_fill_color(*self.GOLD)
        self.rect(14, gy - 0.4, 20, 0.6, style="F")
        self.set_y(gy + self.s(0.6))

        self.set_font("Helvetica", "", self.s(8.5))
        self.set_text_color(*self.GREY)
        for sk in skills:
            self.set_x(16)
            self.cell(3, self.s(4.1), "-")
            self.multi_cell(col_w - 5, self.s(4.1), _safe(sk))
        skills_end_y = self.get_y()

        self.set_xy(108, start_y)
        self.set_font("Helvetica", "B", self.s(10.5))
        self.set_text_color(*self.NAVY)
        self.cell(col_w, self.s(5.5), _safe("LANGUES"), ln=2)
        ly = self.get_y()
        self.set_fill_color(*self.GOLD)
        self.rect(108, ly - 0.4, 20, 0.6, style="F")
        self.set_y(ly + self.s(0.6))

        for lang, level in languages:
            self.set_x(108)
            self.set_text_color(*self.NAVY)
            self.set_font("Helvetica", "B", self.s(8.5))
            self.cell(30, self.s(4.3), _safe(lang), ln=0)
            self.set_font("Helvetica", "", self.s(8.5))
            self.set_text_color(*self.GREY)
            self.cell(0, self.s(4.3), _safe(level), ln=1)
        langs_end_y = self.get_y()

        self.set_y(max(skills_end_y, langs_end_y) + self.s(1.8))

    def tools_strip(self):
        self.set_x(14)
        self.set_font("Helvetica", "B", self.s(10.5))
        self.set_text_color(*self.NAVY)
        self.cell(0, self.s(5.5), _safe("OUTILS & DISPONIBILITÉ"), ln=1)
        y = self.get_y()
        self.set_fill_color(*self.GOLD)
        self.rect(14, y - 0.4, 20, 0.6, style="F")
        self.set_y(y + self.s(0.6))

        base = (
            "Web : HTML/CSS/JavaScript, Wix/Velo, WordPress, Webflow  |  "
            "CRM : Salesforce (formation Coursera 2026)  |  Bureautique : Pack Office  |  "
            "IA et automatisation  |  Disponibilité : immédiate  |  "
            "Mobilité : permis B, prêt à partir à l'international"
        )
        self.set_x(14)
        self.set_font("Helvetica", "", self.s(8.4))
        self.set_text_color(*self.GREY)
        self.multi_cell(182, self.s(4.1), _safe(base))


# ─── Construction d'une page, à une échelle donnée ────────────────────────────

# Le trait doré du pied de page est à 285 mm : le contenu s'arrête avant.
MAX_CONTENT_Y = 278.0


def _build(offer: dict, role: str, analysis: dict, scale: float) -> tuple:
    """Rend le CV à l'échelle demandée. Renvoie (pdf, y_final)."""
    pdf = _CVPdf(format="A4")
    pdf.set_auto_page_break(auto=False)
    pdf.scale   = scale
    pdf.tagline = _tagline(role, offer)
    pdf.add_page()

    qr_url = (PROFILE.get("video_cv_url") or PROFILE.get("qr_url") or "").strip()
    qr_label = "Voir mon CV vidéo" if PROFILE.get("video_cv_url") else "Voir mon LinkedIn"
    qr_path = _make_qr_png(qr_url) if qr_url else ""
    if qr_path:
        try:
            pdf.image(qr_path, x=179, y=4, w=20, h=20)
            pdf.set_xy(179, 24)
            pdf.set_font("Helvetica", "B", 5.5)
            pdf.set_text_color(*pdf.GOLD)
            pdf.cell(20, 3, _safe(qr_label), align="C")
            pdf.set_y(33)
        except Exception:
            pass
        finally:
            try:
                os.unlink(qr_path)
            except OSError:
                pass

    pdf.section("Profil")
    pdf.paragraph(_dynamic_summary(role, offer, analysis), font_size=8.8)

    pdf.section("Expérience professionnelle")
    variant  = BULLET_VARIANT.get(role, "default")
    order    = _ordered_experiences(role, analysis)
    by_id    = {e["id"]: e for e in EXPERIENCES}
    keywords = analysis.get("actions", []) + analysis.get("tools", [])
    for pos, exp_id in enumerate(order):
        exp = by_id.get(exp_id)
        if not exp:
            continue
        n = BULLETS_PER_POSITION[pos] if pos < len(BULLETS_PER_POSITION) else 2
        all_bullets = exp["bullets"].get(variant) or exp["bullets"]["default"]
        # enrich_bullet existait depuis le début et n'était appelée nulle part :
        # les mots-clés de l'annonce étaient extraits puis jetés.
        bullets = [oa.enrich_bullet(b, keywords) for b in all_bullets[:n]]
        sub     = f"{exp['company']}   |   {exp['city']}"
        pdf.experience_item(exp["title"], exp["period"], sub, bullets)

    pdf.section("Formation")
    for title, school, period, note in EDUCATION:
        pdf.education_item(title, school, period, note)

    pdf.ln(pdf.s(1.0))
    pdf.two_columns_skills_languages(_skills_for(role, analysis), LANGUAGES)
    pdf.tools_strip()

    return pdf, pdf.get_y()


# ─── Point d'entrée ───────────────────────────────────────────────────────────

# De la plus confortable à la plus serrée. On garde la première qui tient.
SCALES = (1.30, 1.24, 1.18, 1.12, 1.06, 1.00, 0.95, 0.90, 0.86)


def generate(offer: dict) -> bytes:
    """Génère un CV PDF adapté à l'offre. Une page A4 garantie.

    La version précédente écrasait les polices à 8,3 pt « pour tenir en une
    page », et le contenu s'arrêtait à 195 mm sur 285 : serré en haut, vide en
    bas. On fait l'inverse — on part large et on ne resserre que si nécessaire.
    """
    titre       = offer.get("titre", "")
    description = offer.get("description", "")
    role        = cl.detect_sub_role(titre, description)
    analysis    = oa.analyze(offer)

    pdf = None
    for scale in SCALES:
        pdf, y = _build(offer, role, analysis, scale)
        if y <= MAX_CONTENT_Y:
            break

    out = pdf.output()
    return out.encode("latin-1") if isinstance(out, str) else bytes(out)
