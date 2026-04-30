"""
Lettre de motivation et message court personnalises par offre.
- Detection sous-role precise (2 passes)
- 8 hooks d'ouverture varies, rotation par hash de l'offre
- 2-3 elements specifiques de l'offre references
- Analyse secteur + outils via offer_analyzer
- 1 page garantie (texte court et percutant)
"""

import hashlib
import re

import offer_analyzer as oa

PROFILE = {
    "name":  "Amine Ben Mansour",
    "phone": "+33 6 60 64 57 83",
    "email": "mohamedbenpro47@gmail.com",
}


# ─── Detection sous-role ──────────────────────────────────────────────────────

SUB_ROLES = [
    ("product_marketing", ["chef de produit", "product marketing", "product manager",
                           "brand manager", "brand specialist", "global brand",
                           "category manager", "trade marketing", "shopper marketing"]),
    ("digital_marketing", ["digital marketing", "growth", "performance marketing",
                           "content marketing", "social media", "community manager",
                           "seo", "sea", "campaign", "acquisition"]),
    ("financial_analyst", ["financial analyst", "controller", "controlling",
                           "fp&a", "business analyst", "controle de gestion",
                           "audit", "treasury", "tresor"]),
    ("data_analyst",      ["data analyst", "sales analyt", "business intelligence",
                           "bi analyst", "analytics specialist"]),
    ("purchasing",        ["category analyst", "purchaser", "buyer", "achat",
                           "procurement", "sourcing"]),
    ("key_account",       ["key account", "key client", "grand compte",
                           "account manager", "account executive"]),
    ("business_dev",      ["business dev", "bizdev", "developpement commercial",
                           "developpement business", "sales developer", "sdr"]),
    ("sales",             ["sales", "commercial", "vente", "ventes", "closing"]),
    ("hr",                ["talent", "recruitment", "recrutement", "hrbp",
                           "people", "human resources", "ressources humaines",
                           "early talent", "learning"]),
]


def detect_sub_role(titre: str, description: str = "") -> str:
    titre_l = (titre or "").lower()
    full_l  = (titre_l + " " + (description or "")).lower()
    for role, keywords in SUB_ROLES:
        if any(kw in titre_l for kw in keywords):
            return role
    for role, keywords in SUB_ROLES:
        if any(kw in full_l for kw in keywords):
            return role
    return "generic"


# ─── Rotation deterministe des hooks ─────────────────────────────────────────

def _hook_index(offer: dict, n_variants: int) -> int:
    """Selectionne un hook par hash de l'offre pour avoir de la variete."""
    key = f"{offer.get('id', '')}{offer.get('titre', '')}{offer.get('entreprise', '')}"
    h   = int(hashlib.md5(key.encode()).hexdigest(), 16)
    return h % n_variants


# ─── Pool de hooks par role (2 variants chacun) ───────────────────────────────

def _hook(role: str, titre: str, entreprise: str, offer: dict) -> str:
    poste = (titre or "ce poste").strip()
    idx   = _hook_index(offer, 2)

    if role in ("product_marketing", "digital_marketing"):
        variants = [
            (
                f"C'est avec un fort interet que je postule au poste de {poste} "
                f"chez {entreprise}. Diplome en cours de MBA Manager de Business "
                f"Unit a PSB Paris (soutenance juin 2026), avec une experience "
                f"concrete de gestion de projets digitaux a l'international "
                f"(Lisbonne) et de community management (GROW 360, Paris), je "
                f"souhaite apporter cette double culture au service de votre equipe."
            ),
            (
                f"Mon double profil - gestion de projets digitaux a l'international "
                f"(Wix, Lisbonne) et community management (GROW 360, Paris) - "
                f"correspond directement aux besoins du poste de {poste} chez "
                f"{entreprise}. En MBA Manager de Business Unit a PSB Paris "
                f"(soutenance juin 2026), je cherche a mettre ces competences "
                f"au service d'une equipe internationale ambitieuse."
            ),
        ]
        return variants[idx]

    if role in ("financial_analyst", "data_analyst"):
        variants = [
            (
                f"Je me permets de vous adresser ma candidature au poste de "
                f"{poste} chez {entreprise}. En MBA Manager de Business Unit "
                f"a PSB Paris (soutenance juin 2026) et actuellement en charge "
                f"du pilotage operationnel d'une activite a 360 KEUR/mois, je "
                f"souhaite valoriser cette double culture analyse/business au "
                f"service de vos enjeux financiers."
            ),
            (
                f"La finance n'est utile que si elle eclaire les decisions "
                f"business. C'est cette conviction qui guide ma candidature au "
                f"poste de {poste} chez {entreprise}. MBA Manager de Business "
                f"Unit (PSB Paris, juin 2026), je pilote au quotidien des "
                f"indicateurs a forts enjeux et cherche a transposer cette "
                f"rigueur dans un contexte international."
            ),
        ]
        return variants[idx]

    if role == "purchasing":
        variants = [
            (
                f"Je vous adresse ma candidature au poste de {poste} chez "
                f"{entreprise}. Forme a la negociation en pratique (Business "
                f"Developer B2B, 360 KEUR/mois) et en formation (Negotiation "
                f"Business School certifie 2025, MBA Business Unit en cours), "
                f"je souhaite transposer cette competence sur les enjeux achats."
            ),
            (
                f"Negocier, c'est comprendre ce que l'autre partie veut vraiment "
                f"- pas juste son prix. C'est l'approche que j'applique depuis "
                f"deux ans en Business Development B2B chez Agence 113 / DEFI "
                f"GROUPE, et que je souhaite mettre au service du poste de "
                f"{poste} chez {entreprise}."
            ),
        ]
        return variants[idx]

    if role == "hr":
        variants = [
            (
                f"Je suis particulierement motive par le poste de {poste} chez "
                f"{entreprise}. Recruitment Officer chez Agence 113 / DEFI GROUPE "
                f"ou je gere des sessions reunissant plus de 300 candidats, et "
                f"en MBA Manager de Business Unit (PSB Paris, juin 2026), je "
                f"combine experience operationnelle RH et hauteur strategique."
            ),
            (
                f"Avoir gere en 3 heures un evenement de recrutement reunissant "
                f"plus de 300 candidats m'a appris une chose : la RH qui marche, "
                f"c'est celle qui comprend le business. C'est pourquoi le poste "
                f"de {poste} chez {entreprise} me correspond directement."
            ),
        ]
        return variants[idx]

    # Commerce / Sales / Key Account / Business Dev / generic
    variants = [
        (
            f"Actuellement Business Developer B2B chez Agence 113 / DEFI GROUPE, "
            f"ou je pilote un portefeuille generant 360 KEUR/mois, et diplome en "
            f"cours de MBA Manager de Business Unit a PSB Paris (soutenance juin "
            f"2026), je souhaite mettre mon experience commerciale au service de "
            f"votre equipe sur le poste de {poste} chez {entreprise}."
        ),
        (
            f"Partir en VIE, c'est une decision strategique - pas un simple stage. "
            f"C'est avec cet etat d'esprit que je postule au poste de {poste} chez "
            f"{entreprise}. Business Developer B2B en autonomie sur 360 KEUR/mois "
            f"et MBA Manager de Business Unit en cours (PSB Paris, juin 2026), "
            f"je suis pret a delivrer des resultats concrets depuis le premier mois."
        ),
    ]
    return variants[idx]


# ─── Pitch par role ───────────────────────────────────────────────────────────

def pitch_for(role: str, entreprise: str, description: str = "") -> str:
    if role == "product_marketing":
        return (
            "Mon experience en gestion de projets digitaux pour clients "
            "internationaux depuis Lisbonne, combinee aux modules de strategie "
            "produit et d'analyse de marche de mon MBA, me permet de comprendre "
            "rapidement les enjeux de positionnement, de pricing et de cycle de "
            "vie produit. J'ai egalement coordonne des actions de notoriete et "
            "d'engagement chez GROW 360 (Paris), ce qui m'a appris a transformer "
            "un brief marketing en actions mesurables avec un ROI clair."
        )
    if role == "digital_marketing":
        return (
            "Mon experience de Community Management chez GROW 360 (Paris) et de "
            "gestion de projets digitaux pour clients internationaux depuis "
            "Lisbonne m'a appris a piloter des campagnes multicanales avec des "
            "KPIs concrets : engagement, taux de conversion, ROI campagne. Je "
            "sais structurer une strategie de contenu adaptee aux specificites "
            "locales et l'ajuster en continu selon les donnees."
        )
    if role == "financial_analyst":
        return (
            "Mon MBA Manager de Business Unit a PSB Paris inclut des modules "
            "approfondis de controle de gestion, analyse de la performance et "
            "lecture financiere strategique. En parallele, je pilote au quotidien "
            "une activite a forts enjeux (360 KEUR/mois) : KPIs commerciaux, "
            "reporting, lecture business des chiffres. Cette double competence "
            "finance/business est un atout direct pour le partenariat avec les "
            "equipes operationnelles."
        )
    if role == "data_analyst":
        return (
            "Forme au pilotage par la donnee dans mon MBA, je manipule au "
            "quotidien des indicateurs commerciaux pour orienter mes decisions. "
            "Je sais transformer un dataset brut en insight actionnable, en "
            "commencant par poser les bonnes questions business avant de plonger "
            "dans la technique. Mon objectif : des analyses qui servent les "
            "decideurs, pas des reportings pour des reportings."
        )
    if role == "purchasing":
        return (
            "Habitue a negocier des partenariats strategiques avec des enjeux "
            "financiers concrets (portefeuille B2B a 360 KEUR/mois), je transpose "
            "facilement cette approche cote achats : recherche de fournisseurs, "
            "comparaison TCO, negociation de conditions, structuration de contrats. "
            "Mon multilinguisme (FR/AR natifs, EN courant, ES intermediaire) "
            "facilite directement les relations avec les fournisseurs internationaux."
        )
    if role == "key_account":
        return (
            "Business Developer B2B chez Agence 113 / DEFI GROUPE avec un "
            "portefeuille a 360 KEUR/mois, je gere des comptes strategiques en "
            "mode hunter-farmer. Cycle de vente long, prospection au closing, "
            "gestion de la relation post-signature : ce mode de travail se "
            "transpose directement aux exigences d'un poste Key Account sur "
            "des marches internationaux exigeants."
        )
    if role == "business_dev":
        return (
            "Business Developer B2B chez Agence 113 / DEFI GROUPE, je pilote "
            "une activite a 360 KEUR/mois en autonomie complete sur tout le "
            "cycle commercial : prospection, qualification, negociation, closing. "
            "Je maitrise HubSpot CRM et LinkedIn Sales Navigator au quotidien et "
            "sais structurer un pipeline de A a Z. Cette posture de developpeur "
            "d'activite est exactement celle attendue dans une mission VIE."
        )
    if role == "sales":
        return (
            "Business Developer B2B chez Agence 113 / DEFI GROUPE avec 360 KEUR "
            "de CA mensuel, je sais transformer une opportunite froide en client "
            "signe. Maitrise du cycle complet, des outils CRM (HubSpot, Sales "
            "Navigator) et de la negociation B2B sur des cibles exigeantes. "
            "Cette rigueur de resultats, acquise en autonomie, est directement "
            "applicable a votre equipe commerciale."
        )
    if role == "hr":
        return (
            "J'ai dirige operationnellement des process de recrutement a grande "
            "echelle : organisation d'evenements reunissant 300+ candidats, "
            "sourcing actif, coordination du service POEI, entretiens, reporting. "
            "Cette double experience RH/business est rare et m'a appris a parler "
            "le langage des managers comme des candidats."
        )
    return (
        "Mon parcours combine pilotage operationnel en France et gestion de "
        "projets internationaux depuis Lisbonne, avec un MBA Manager de Business "
        "Unit (PSB Paris, juin 2026) qui m'a apporte methodes et rigueur. "
        "J'apporte autonomie, orientation resultats et adaptabilite culturelle."
    )


def deliverables_for(role: str) -> str:
    if role == "product_marketing":
        return (
            "Concretement, je peux contribuer des le premier mois : "
            "1) lecture rapide des etudes de marche pour nourrir les decisions "
            "produit, "
            "2) coordination operationnelle entre marketing, ventes et R&D, "
            "3) adaptation du positionnement aux specificites des marches locaux "
            "grace a mon ouverture multiculturelle."
        )
    if role == "digital_marketing":
        return (
            "Concretement, je peux : "
            "1) prendre en main vos campagnes digitales avec lecture KPI/ROI rigoureuse, "
            "2) produire du contenu adapte a vos cibles internationales, "
            "3) adapter le ton selon les marches locaux grace a mon multilinguisme."
        )
    if role == "financial_analyst":
        return (
            "Concretement, je peux : "
            "1) construire des reportings clairs et actionnables pour vos decideurs, "
            "2) participer aux exercices de budget, forecast et analyse d'ecarts, "
            "3) faire le pont finance/operationnels grace a mon experience business."
        )
    if role == "data_analyst":
        return (
            "Concretement, je peux : "
            "1) industrialiser des reportings reguliers sur Excel / Power BI, "
            "2) identifier les insights actionnables dans vos donnees commerciales, "
            "3) traduire les analyses en recommandations claires pour les decideurs."
        )
    if role == "purchasing":
        return (
            "Concretement, je peux : "
            "1) construire des analyses categorielles pour eclairer les decisions achats, "
            "2) negocier directement avec des fournisseurs internationaux en plusieurs "
            "langues, "
            "3) structurer le suivi de la performance fournisseurs."
        )
    if role == "key_account":
        return (
            "Concretement, je peux : "
            "1) prendre en main rapidement un portefeuille de comptes strategiques, "
            "2) deployer une approche structuree (plan de compte, business review), "
            "3) negocier les conditions cadres dans plusieurs langues."
        )
    if role in ("business_dev", "sales"):
        return (
            "Concretement, je peux : "
            "1) ouvrir un marche ou developper un portefeuille des le premier mois, "
            "2) structurer votre pipeline avec une rigueur d'execution prouvee, "
            "3) closer des deals complexes grace a mon experience B2B et mon "
            "adaptabilite culturelle."
        )
    if role == "hr":
        return (
            "Concretement, je peux : "
            "1) prendre en charge des process de recrutement de A a Z, "
            "2) animer des evenements employeur et des sessions de sourcing, "
            "3) faire le lien RH/business grace a mon experience operationnelle."
        )
    return "Concretement, j'apporte rigueur, autonomie a l'international et resultats mesurables."


# ─── Contexte pays ────────────────────────────────────────────────────────────

_COUNTRY_CONTEXT = {
    "chine":      ("Shanghai et la Chine sont le 1er marche e-commerce mondial",
                   "Mes notions de chinois et ma comprehension des codes business "
                   "asiatiques accelereront mon integration."),
    "japon":      ("Le Japon reste la 3e economie mondiale avec une exigence "
                   "reconnue de rigueur et de long-termisme",
                   "Mon serieux et ma capacite a tisser des relations sur la duree "
                   "correspondent aux codes business japonais."),
    "coree":      ("La Coree du Sud est un hub strategique pour l'innovation en Asie",
                   "Mon ouverture aux marches asiatiques et ma rigueur seront un "
                   "atout immediat."),
    "singapour":  ("Singapour est la porte d'entree de l'ASEAN et un hub financier",
                   "Mon profil multilingue et international correspond directement "
                   "a l'ecosysteme local."),
    "etats-unis": ("Le marche americain reste le 1er PIB mondial avec des exigences "
                   "elevees de performance",
                   "Mon experience de gestion par objectifs (360 KEUR/mois) me "
                   "prepare directement a vos standards."),
    "canada":     ("Le Canada offre un acces strategique au marche nord-americain",
                   "Mon bilinguisme francais/anglais est un avantage immediat sur ce marche."),
    "mexique":    ("Le Mexique est le 1er hub manufacturier des Ameriques",
                   "Mon espagnol intermediaire facilitera mes echanges avec les equipes locales."),
    "bresil":     ("Le Bresil represente la 1ere economie d'Amerique latine",
                   "Mon adaptabilite culturelle et mes acquis multiculturels sont un atout direct."),
    "argentine":  ("L'Argentine reste un acteur majeur du Cono Sur",
                   "Mon espagnol intermediaire facilitera mes echanges avec les partenaires locaux."),
    "chili":      ("Le Chili est le marche le plus stable d'Amerique latine",
                   "Mon espagnol intermediaire me permettra d'etre operationnel rapidement."),
    "colombie":   ("La Colombie est un marche en forte croissance d'Amerique latine",
                   "Mon espagnol intermediaire sera directement utile sur ce marche."),
    "emirats":    ("Dubai concentre les sieges regionaux Moyen-Orient et est un hub du "
                   "commerce global",
                   "Arabophone natif, je maitrise les codes commerciaux du Golfe."),
    "arabie":     ("L'Arabie saoudite represente 25% du PIB Moyen-Orient et investit "
                   "massivement (Vision 2030)",
                   "Mon arabe natif et ma comprehension des codes locaux sont des "
                   "avantages strategiques."),
    "qatar":      ("Le Qatar reste un acteur strategique du Golfe avec un fort dynamisme",
                   "Mon arabe natif facilitera la creation de relations de confiance locales."),
    "australie":  ("L'Australie est un marche mature et porte d'entree vers l'Asie Pacifique",
                   "Mon profil international et mon autonomie correspondent au contexte local."),
    "inde":       ("L'Inde est la 5e economie mondiale avec un dynamisme exceptionnel",
                   "Mon anglais courant et mon ouverture culturelle correspondent au "
                   "contexte business indien."),
    "turquie":    ("La Turquie est un hub strategique entre Europe et Asie",
                   "Mon profil multilingue et ma culture du commerce international "
                   "sont directement applicables."),
    "vietnam":    ("Le Vietnam est l'une des economies les plus dynamiques d'Asie du Sud-Est",
                   "Mon ouverture aux marches asiatiques et mon adaptabilite sont "
                   "des atouts directs."),
    "indonesie":  ("L'Indonesie represente la plus grande economie de l'ASEAN",
                   "Mon profil international et ma capacite a operer en contexte "
                   "multiculturel seront immediatement utiles."),
    "thaïlande":  ("La Thaïlande est le 2e marche d'Asie du Sud-Est",
                   "Mon experience a l'international et mon adaptabilite correspondent "
                   "aux exigences locales."),
    "malaisie":   ("La Malaisie est un hub strategique pour l'Asie du Sud-Est",
                   "Mon profil multilingue et mon experience internationale sont "
                   "directement valorisables."),
}


def _country_context(pays: str) -> tuple:
    p = (pays or "").lower()
    for country, (market, lang) in _COUNTRY_CONTEXT.items():
        if country in p:
            return market, lang
    return ("", "")


# ─── Mirror mission : extraire 2-3 elements specifiques de l'offre ────────────

def _mission_reference(offer: dict, analysis: dict) -> str:
    """Construit une phrase referancant des elements concrets de l'offre."""
    description = offer.get("description", "")
    actions     = analysis.get("actions", [])
    industry    = analysis.get("industry", "generic")
    tools       = analysis.get("tools", [])

    # Tenter d'extraire une mission-snippet specifique
    if description and len(description) >= 80:
        snippet = description.strip()
        snippet = re.sub(r"\s+", " ", snippet)
        if len(snippet) > 160:
            snippet = snippet[:160].rsplit(" ", 1)[0] + "..."
        ref = f"La mission que vous decrivez - {snippet} - correspond exactement "
        ref += "a l'environnement dans lequel je veux construire la suite de mon parcours."
        return ref

    # Fallback sur les mots-cles
    if actions:
        kws = ", ".join(actions[:3])
        return (
            f"Les competences que vous recherchez ({kws}) correspondent "
            f"directement a mon profil et a mes objectifs de developpement."
        )
    return ""


# ─── Generation lettre complete ───────────────────────────────────────────────

def generate(offer: dict) -> str:
    titre       = offer.get("titre", "le poste propose")
    entreprise  = offer.get("entreprise", "votre entreprise")
    pays        = offer.get("pays", "")
    duree       = offer.get("duree", 12)
    description = offer.get("description", "")

    role        = detect_sub_role(titre, description)
    analysis    = oa.analyze(offer)

    hook        = _hook(role, titre, entreprise, offer)
    mission_ref = _mission_reference(offer, analysis)
    pitch       = pitch_for(role, entreprise, description)
    deliver     = deliverables_for(role)
    market, lang_line = _country_context(pays)

    pays_str  = f"en {pays}" if pays and pays not in ("N/A", "") else "a l'international"
    duree_str = f"{duree} mois" if duree else "la duree prevue"

    paras = ["Madame, Monsieur,", hook]

    if mission_ref:
        paras.append(mission_ref)

    paras.append(pitch)
    paras.append(deliver)

    if market:
        paras.append(
            f"De plus, {market}, ce qui rend cette mission particulierement "
            f"strategique pour la suite de mon parcours."
        )
    if lang_line:
        paras.append(lang_line)

    paras.append(
        f"Cette mission de {duree_str} {pays_str} represente exactement le "
        f"defi dans lequel je souhaite m'investir pleinement. Je suis disponible "
        f"pour un echange a votre convenance."
    )
    paras.append(
        f"Cordialement,\n{PROFILE['name']}\n{PROFILE['phone']} | {PROFILE['email']}"
    )

    return "\n\n".join(paras)


# ─── Message court (candidature email) ───────────────────────────────────────

_SHORT_PITCH = {
    "product_marketing":  "structurer votre demarche produit et coordonner marketing/ventes/R&D",
    "digital_marketing":  "piloter des campagnes digitales multicanales avec lecture ROI rigoureuse",
    "financial_analyst":  "construire des reportings actionnables et partnaire finance/operationnels",
    "data_analyst":       "industrialiser des reportings et traduire les donnees en insights decideurs",
    "purchasing":         "analyser les categories, negocier en plusieurs langues, suivre fournisseurs",
    "key_account":        "prendre en main des comptes strategiques et structurer le plan de compte",
    "business_dev":       "ouvrir un marche ou developper un portefeuille (360 KEUR/mois actuel)",
    "sales":              "transformer des opportunites froides en deals signes (360 KEUR/mois actuel)",
    "hr":                 "piloter des process recrutement de A a Z et faire le lien RH/business",
    "generic":            "livrer des resultats concrets en autonomie a l'international",
}


def generate_short_message(offer: dict) -> str:
    titre       = offer.get("titre", "le poste")
    entreprise  = offer.get("entreprise", "votre entreprise")
    description = offer.get("description", "")
    role        = detect_sub_role(titre, description)
    pitch       = _SHORT_PITCH.get(role, _SHORT_PITCH["generic"])

    return (
        f"Bonjour,\n"
        f"Je vous adresse ma candidature pour le poste de {titre} chez {entreprise}.\n"
        f"Diplome en cours de MBA Manager de Business Unit (PSB Paris) avec experience "
        f"internationale (Lisbonne), je viens du pilotage operationnel et souhaite "
        f"mettre cette energie au service de votre equipe.\n"
        f"Concretement, je peux {pitch}.\n"
        f"Vous trouverez en piece jointe mon CV et ma lettre de motivation.\n"
        f"Disponible pour un echange a votre convenance.\n"
        f"Cordialement, {PROFILE['name']} ({PROFILE['phone']})"
    )
