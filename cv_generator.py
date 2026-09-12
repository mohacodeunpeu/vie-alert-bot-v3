"""
CV généré dynamiquement par offre, niveau pro Bac+5.

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
  * « 360 KEUR/mois » — le symbole EUR est le seul caractère que la police de
    base refuse. On écrit donc « k€ » dans les données et _safe() le rend en
    « k EUR », lisible. Le jour où une police Unicode est embarquée, il suffit
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
    "product_marketing": "Brand & Product Manager",
    "digital_marketing": "Digital Marketing",
    "financial_analyst": "Financial Analyst",
    "data_analyst":      "Data & Business Analyst",
    "purchasing":        "Achats & Category Management",
    "key_account":       "Key Account Manager",
    "business_dev":      "Business Developer",
    "sales":             "Sales Manager B2B",
    "hr":                "Talent Acquisition",
    "generic":           "Business Developer",
}

# Suffixe commun : ce qui ne change jamais, quel que soit le poste visé.
TAGLINE_SUFFIX = "MBA Manager de Business Unit | V.I.E. 2026"


# ─── Résumés par sous-rôle ────────────────────────────────────────────────────
# Socle factuel. La phrase d'accroche liée à l'offre est ajoutée par-dessus, dans
# _dynamic_summary() — jamais en remplacement, pour qu'aucun fait ne disparaisse.

SUMMARY_BASE = {
    "product_marketing": (
        "MBA Manager de Business Unit (PSB Paris, juin 2026). Gestion de projets "
        "digitaux internationaux (Wix, Lisbonne) et community management "
        "(GROW 360, Paris). Capable de structurer une démarche produit et de la "
        "décliner en actions marketing concrètes sur des marchés multiculturels."
    ),
    "digital_marketing": (
        "MBA Manager de Business Unit en cours (PSB Paris, juin 2026). Expérience "
        "opérationnelle en community management (GROW 360) et projets digitaux à "
        "l'international (Lisbonne). Maîtrise des leviers d'engagement et lecture "
        "rigoureuse des KPIs."
    ),
    "financial_analyst": (
        "MBA Manager de Business Unit en cours (PSB Paris, juin 2026), module "
        "contrôle de gestion. Pilote au quotidien une activité à 360 k€/mois : "
        "indicateurs, reporting, lecture business des chiffres."
    ),
    "data_analyst": (
        "MBA Manager de Business Unit en cours (PSB Paris, juin 2026). Pilotage "
        "quotidien de KPIs commerciaux. Formé à l'analyse et au storytelling de "
        "données pour traduire un jeu de données en décision actionnable."
    ),
    "purchasing": (
        "MBA Manager de Business Unit en cours (PSB Paris, juin 2026). Certifié "
        "Negotiation Business School (2025). Expérience de négociation B2B sur un "
        "portefeuille à 360 k€/mois, multilingue, transposable aux enjeux achats "
        "internationaux."
    ),
    "key_account": (
        "Business Developer B2B chez Agence 113 / DEFI GROUPE (360 k€/mois). "
        "MBA Manager de Business Unit en cours (PSB Paris, juin 2026). Profil "
        "hunter-farmer, multilingue, orienté partenariats stratégiques long terme."
    ),
    "business_dev": (
        "Business Developer B2B chez Agence 113 / DEFI GROUPE, 360 k€/mois. "
        "MBA Manager de Business Unit en cours (PSB Paris, juin 2026). Cycle "
        "commercial complet, HubSpot CRM, Sales Navigator, négociation B2B."
    ),
    "sales": (
        "Business Developer B2B chez Agence 113 / DEFI GROUPE (360 k€/mois) et "
        "ex-Sales Advisor Printemps Haussmann. MBA Manager de Business Unit en "
        "cours à PSB Paris. Profil multilingue orienté résultats."
    ),
    "hr": (
        "Recruitment Officer chez Agence 113 / DEFI GROUPE : 300+ candidats gérés, "
        "coordination POEI, sourcing actif. Double compétence RH / business, "
        "renforcée par le MBA Manager de Business Unit en cours (PSB Paris, "
        "juin 2026)."
    ),
    "generic": (
        "Profil junior ambitieux : MBA Manager de Business Unit en cours (PSB "
        "Paris, juin 2026), Business Developer B2B (360 k€/mois), expérience "
        "internationale à Lisbonne, multilingue (FR/AR natifs, EN courant)."
    ),
}


# Ce que chaque secteur détecté permet de dire honnêtement, sans rien inventer.
# Utilisé pour la phrase d'accroche liée à l'offre.
INDUSTRY_ANGLE = {
    "luxe":         "clientèle internationale premium (Printemps Haussmann)",
    "retail":       "retail premium et relation client (Printemps Haussmann)",
    "tech":         "projets web et produits digitaux livrés en autonomie (Wix)",
    "conseil":      "pilotage de projets clients multiples en parallèle",
    "finance":      "suivi budgétaire et reporting d'une activité à 360 k€/mois",
    "pharma":       "rigueur de process et reporting structuré",
    "automotive":   "cycle de vente B2B long et négociation grands comptes",
    "energy":       "pilotage d'indicateurs et reporting direction",
    "agroalim":     "développement de portefeuille B2B et négociation",
    "industrie":    "coordination d'acteurs internes multiples",
    "construction": "coordination d'acteurs internes multiples",
    "telecom":      "prospection B2B volumique et suivi CRM",
}


# ─── Expériences réelles — bullets orientés impact (action + outil + résultat) ─

EXPERIENCES = [
    {
        "id":      "defi",
        "title":   "Business Developer & Recruitment Officer",
        "company": "Agence 113 - DEFI GROUPE",
        "city":    "Paris",
        "period":  "Sept. 2025 - aujourd'hui",
        # Poste en cours : il ouvre le CV quel que soit le rôle visé (cf.
        # _ordered_experiences). Un seul poste doit porter ce drapeau.
        "current": True,
        "bullets": {
            "default": [
                "Pilotage d'un portefeuille B2B à 360 k€/mois : 30+ leads qualifiés par mois.",
                "Suivi CRM HubSpot sur 120+ comptes : taux de relance maintenu à 85 %.",
                "Événements de recrutement : 300+ candidats qualifiés par session.",
                "Coordination production / communication / RH : livraison sans retard sur 6 mois.",
            ],
            "commerce": [
                "Développement d'un portefeuille B2B à 360 k€/mois : cycle complet en autonomie.",
                "Négociation directe avec les décideurs : 3 partenariats long terme conclus par trimestre.",
                "Pipeline structuré sous HubSpot : 30+ opportunités qualifiées suivies en temps réel.",
                "Prospection multicanale (LinkedIn Sales Navigator, téléphone, e-mail).",
            ],
            "marketing": [
                "Pilotage d'une activité à 360 k€/mois : 5 KPIs suivis, reporting hebdomadaire direction.",
                "Acquisition B2B ciblée : 30+ contacts qualifiés par mois en prospection active.",
                "Coordination production / communication / RH : livraison sans retard sur 6 mois.",
                "Analyse des retours terrain pour ajuster le discours commercial.",
            ],
            "finance": [
                "Suivi budgétaire d'une activité à 360 k€/mois : analyse des marges et des écarts, chaque semaine.",
                "Reporting mensuel à la direction via dashboards Excel (TCD, formules avancées).",
                "Analyse de rentabilité client : 3 leviers d'optimisation identifiés et appliqués.",
                "Construction et tenue des indicateurs de pilotage de l'activité.",
            ],
            "hr": [
                "Événements de recrutement : 300+ candidats qualifiés et accueillis par session.",
                "Coordination POEI avec France Travail : 15 intégrations gérées en parallèle.",
                "Pilotage des KPIs RH : taux de placement et reporting mensuel au management.",
                "Sourcing actif multicanal et conduite d'entretiens de préqualification.",
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
                "Livraison de 5+ sites clients internationaux en autonomie : brief, design, mise en ligne.",
                "Optimisation UX et conversion : +20 % de taux de clic moyen sur les landing pages.",
                "Échanges clients en anglais et en espagnol au quotidien.",
            ],
            "commerce": [
                "Livraison de 5+ sites clients internationaux : recueil du besoin, cadrage, mise en ligne.",
                "Relation client directe en anglais et en espagnol, du brief à la validation finale.",
                "Optimisation conversion : +20 % de taux de clic sur les landing pages.",
            ],
            "marketing": [
                "Projets digitaux clients internationaux : brief, contenu, A/B tests, livraison.",
                "Optimisation de la conversion via analytics : +20 % de taux de clic sur les landing pages.",
                "Adaptation des contenus à des audiences multiculturelles.",
            ],
            "finance": [
                "Gestion de 5+ projets clients en parallèle : périmètre, délais, livraison.",
                "Suivi de la performance des pages via analytics : +20 % de taux de clic.",
            ],
            "hr": [
                "Gestion de 5+ projets clients internationaux en autonomie complète.",
                "Communication quotidienne en anglais et en espagnol.",
            ],
        },
    },
    {
        "id":      "printemps",
        "title":   "Sales Advisor - Retail premium",
        "company": "Printemps Haussmann",
        "city":    "Paris",
        "period":  "2024",
        "bullets": {
            "default": [
                "Dépassement des objectifs de vente (+10 % vs. cible mensuelle) sur zone premium.",
                "Fidélisation d'une clientèle internationale : taux de retour élevé sur le portefeuille.",
                "Vente conseil en français, anglais et espagnol.",
            ],
            "commerce": [
                "Dépassement des objectifs de vente (+10 % vs. cible mensuelle) sur zone premium.",
                "Vente conseil auprès d'une clientèle internationale, en 3 langues.",
                "Montée en compétence sur les produits premium et le discours de marque.",
            ],
            "marketing": [
                "Contact direct avec une clientèle internationale premium : lecture des attentes réelles.",
                "Dépassement des objectifs de vente (+10 % vs. cible mensuelle).",
            ],
            "finance": [
                "Suivi quotidien des objectifs et de la performance de la zone : +10 % vs. cible.",
                "Reporting des ventes et des retours clients au responsable de zone.",
            ],
            "hr": [
                "Intégration rapide en équipe multiculturelle sur un environnement à fort trafic.",
                "Dépassement des objectifs de vente (+10 % vs. cible mensuelle).",
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
                "Stratégie éditoriale : +35 % d'engagement (Instagram, LinkedIn) en 6 mois.",
                "Planification de 10+ publications par semaine sur 3 formats, zéro retard.",
            ],
            "marketing": [
                "Stratégie éditoriale et ligne de marque : +35 % d'engagement en 6 mois.",
                "Planification de 10+ publications par semaine sur 3 formats, zéro retard.",
                "Suivi des statistiques de portée et d'engagement pour arbitrer les formats.",
            ],
            "commerce": [
                "Stratégie éditoriale : +35 % d'engagement (Instagram, LinkedIn) en 6 mois.",
                "Génération de contacts entrants via les réseaux sociaux.",
            ],
            "finance": [
                "Suivi des statistiques d'engagement et de portée : +35 % en 6 mois.",
            ],
            "hr": [
                "Communication employeur et animation de communauté : +35 % d'engagement.",
                "Planification de 10+ publications par semaine, zéro retard.",
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

# Priorité d'affichage des expériences selon le rôle.
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

# Le secteur de l'offre remonte une expérience d'un cran. Un poste dans le luxe
# ou le retail a tout intérêt à voir Printemps Haussmann haut dans la page, même
# pour un rôle business : c'est la ligne du CV qui parle au recruteur.
INDUSTRY_BOOST = {
    "luxe":   "printemps",
    "retail": "printemps",
    "tech":   "wix",
}

# Nombre de bullets par position (1re expérience en premier).
BULLETS_PER_POSITION = [4, 3, 2, 2]


# ─── Formation ────────────────────────────────────────────────────────────────

EDUCATION = [
    ("MBA - Manager de Business Unit",
     "PSB Paris School of Business",
     "Paris  2025-2026",
     "soutenance juin 2026"),
    ("Bachelor Bac+3 - Développement Commercial",
     "PSB Paris School of Business",
     "Paris  2022-2025",
     "obtenu"),
    ("Certification Négociation Commerciale",
     "Negotiation Business School (en ligne)",
     "2025",
     "certifié"),
    ("Habilitation SST - Sauveteur Secouriste du Travail",
     "Croix-Rouge Française",
     "Paris  2024",
     ""),
]


# ─── Compétences par rôle ─────────────────────────────────────────────────────

SKILLS_BY_ROLE = {
    "product_marketing": [
        "Stratégie produit, positionnement, pricing (MBA)",
        "Gestion de projets digitaux internationaux (Wix, Lisbonne)",
        "Community management et contenu (GROW 360, Paris)",
        "Lecture des KPIs, taux de conversion, ROI marketing",
        "Coordination marketing / ventes / R&D",
    ],
    "digital_marketing": [
        "Community management et réseaux sociaux (GROW 360)",
        "Pilotage de campagnes digitales, lecture KPI / ROI",
        "Outils : Canva, Notion, Google Suite, Wix",
        "UX et conversion (Wix, Lisbonne)",
        "Stratégie de contenu multiculturelle",
    ],
    "financial_analyst": [
        "Contrôle de gestion et lecture financière (MBA)",
        "Pilotage de KPIs commerciaux à 360 k€/mois",
        "Reporting, analyse d'écarts, dashboards Excel",
        "Pack Office avancé (TCD, formules, VBA)",
        "Rigueur analytique et orientation business",
    ],
    "data_analyst": [
        "Analyse de données et pilotage de KPIs (MBA)",
        "Gestion d'indicateurs commerciaux au quotidien",
        "Excel avancé, notions Power BI / Tableau",
        "Storytelling de données pour les décideurs",
        "Esprit critique et rigueur méthodologique",
    ],
    "purchasing": [
        "Négociation B2B (Negotiation Business School, 2025)",
        "Analyse de besoins et structuration d'offres",
        "Multilinguisme : FR/AR natifs, EN courant, ES intermédiaire",
        "Pack Office avancé et CRM HubSpot",
        "Suivi de performance et reporting",
    ],
    "key_account": [
        "Portefeuille B2B à 360 k€/mois en autonomie",
        "Cycle commercial complet (prospection -> closing)",
        "HubSpot CRM, LinkedIn Sales Navigator",
        "Negotiation Business School (certifié 2025)",
        "Multilinguisme et adaptabilité culturelle",
    ],
    "business_dev": [
        "Business development B2B (360 k€/mois)",
        "Cycle commercial : prospection -> closing",
        "HubSpot CRM, LinkedIn Sales Navigator",
        "Negotiation Business School (certifié 2025)",
        "Multilinguisme : FR / AR / EN / ES",
    ],
    "sales": [
        "Vente B2B et B2C premium (DEFI GROUPE + Printemps)",
        "Dépassement régulier des objectifs commerciaux",
        "Negotiation Business School (certifié 2025)",
        "HubSpot CRM, LinkedIn Sales Navigator",
        "Multilinguisme et relation client haut de gamme",
    ],
    "hr": [
        "Recrutement : 300+ candidats gérés en événements",
        "Coordination POEI avec France Travail",
        "Outils : Indeed, France Travail, LinkedIn",
        "Animation d'événements et conduite d'entretiens",
        "Habilitation SST (Croix-Rouge Française)",
    ],
    "generic": [
        "Cycle commercial et négociation B2B",
        "Gestion de projets internationaux (Lisbonne)",
        "HubSpot CRM, LinkedIn Sales Navigator",
        "Pack Office avancé et Google Suite",
        "FR / EN / AR / ES / ZH",
    ],
}


LANGUAGES = [
    ("Français",  "Natif"),
    ("Arabe",     "Natif"),
    ("Anglais",   "Courant"),
    ("Espagnol",  "Intermédiaire"),
    ("Chinois",   "Notions"),
]


# Outils que l'offre peut mentionner et qu'Amine pratique réellement. Hors de
# cette liste, un outil de l'annonce n'entre PAS dans les compétences : un CV qui
# revendique Salesforce sans y avoir touché se paie au premier entretien.
TOOLS_HE_KNOWS = {
    "hubspot":                 "HubSpot CRM",
    "hubspot crm":             "HubSpot CRM",
    "sales navigator":         "LinkedIn Sales Navigator",
    "linkedin sales navigator":"LinkedIn Sales Navigator",
    "excel":                   "Excel avancé (TCD, formules)",
    "google sheets":           "Google Sheets",
    "google analytics":        "Google Analytics",
    "canva":                   "Canva",
    "notion":                  "Notion",
    "wix":                     "Wix",
    "wordpress":               "WordPress",
    "linkedin ads":            "LinkedIn (organique et sponsorisé)",
    "tiktok":                  "TikTok, Instagram, LinkedIn (contenu)",
    "teams":                   "Microsoft Teams",
    "slack":                   "Slack",
    "zoom":                    "Zoom",
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

    Un ATS cherche ses propres mots. Si l'offre parle de HubSpot et qu'Amine
    pratique HubSpot, la ligne doit être visible en haut — pas noyée en bas de
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
    """Le poste en cours d'abord, puis l'ordre du rôle, puis le secteur.

    Deux règles apprises sur les PDF précédents :

      * Le poste en cours ouvre le CV, toujours. `ROLE_PRIORITY` le reléguait en
        quatrième position pour les rôles marketing — donc en bas de page, avec
        deux bullets : son poste actuel à 360 k€/mois, celui qui porte le plus
        de preuve, enterré sous un community management de 2023. Un recruteur
        lit la première ligne comme « ce qu'il fait aujourd'hui ». La pertinence
        réordonne le RESTE, pas ça.
      * Le coup de pouce sectoriel ne remonte jamais jusqu'en tête, pour la même
        raison : voir un job de 2024 au-dessus d'un « Sept. 2025 - aujourd'hui »
        ne se lit pas comme un choix, ça se lit comme une erreur.
    """
    order   = list(ROLE_PRIORITY.get(role, ROLE_PRIORITY["generic"]))
    current = [e["id"] for e in EXPERIENCES if e.get("current")]

    for exp_id in reversed(current):
        if exp_id in order:
            order.insert(0, order.pop(order.index(exp_id)))

    boost = INDUSTRY_BOOST.get(analysis.get("industry", "generic"))
    if boost and boost in order and boost not in current:
        i = order.index(boost)
        if i > 1:
            order.insert(max(1, i - 1), order.pop(i))
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
            "CRM : HubSpot, LinkedIn Sales Navigator  |  Marketing : Canva, Notion, Wix  |  "
            "Bureautique : Excel avancé, Google Suite  |  "
            "Disponibilité : V.I.E. 2026 (juin/juillet)  |  Mobilité : permis B, remote OK"
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
