"""
Lettre de motivation et message court personnalises selon le poste exact.
- Detection de SOUS-ROLE precise (ex: chef de produit vs commercial vs sales analyst)
- Pitch adapte au sous-role (pas de '360KEUR CA' pour un poste marketing)
- Utilisation de la description de l'offre pour miroir lexical
- Angle 'jeune talent' pour compenser la seniorite limitee
- Pas de tirets cadratin (recruteur detecte sinon)
"""

import re

PROFILE = {
    "name":  "Amine Ben Mansour",
    "phone": "+33 6 60 64 57 83",
    "email": "mohamedbenpro47@gmail.com",
}

# ─── Detection de SOUS-ROLE precise ───────────────────────────────────────────

SUB_ROLES = [
    # Marketing
    ("product_marketing", ["chef de produit", "product marketing", "product manager",
                           "brand manager", "brand specialist", "global brand",
                           "category manager", "trade marketing", "shopper marketing"]),
    ("digital_marketing", ["digital marketing", "growth", "performance marketing",
                           "content marketing", "social media", "community manager",
                           "seo", "sea", "campaign", "acquisition"]),
    # Finance / Analytics
    ("financial_analyst", ["financial analyst", "controller", "controlling",
                           "fp&a", "business analyst", "controle de gestion",
                           "audit", "treasury", "tresor"]),
    ("data_analyst",      ["data analyst", "sales analyt", "business intelligence",
                           "bi analyst", "analytics specialist"]),
    ("purchasing",        ["category analyst", "purchaser", "buyer", "achat",
                           "procurement", "sourcing"]),
    # Commerce
    ("key_account",       ["key account", "key client", "grand compte",
                           "account manager", "account executive"]),
    ("business_dev",      ["business dev", "bizdev", "developpement commercial",
                           "developpement business", "sales developer", "sdr"]),
    ("sales",             ["sales", "commercial", "vente", "ventes", "closing"]),
    # HR / Operations
    ("hr",                ["talent", "recruitment", "recrutement", "hrbp",
                           "people", "human resources", "ressources humaines",
                           "early talent", "learning"]),
]


def detect_sub_role(titre: str, description: str = "") -> str:
    """Detection en 2 passes : titre prioritaire (signal fort), puis description."""
    titre_l = (titre or "").lower()
    full_l  = (titre_l + " " + (description or "")).lower()

    # Pass 1 : matcher uniquement sur le TITRE (signal le plus fiable)
    for role, keywords in SUB_ROLES:
        if any(kw in titre_l for kw in keywords):
            return role

    # Pass 2 : titre+description si rien trouve dans le titre seul
    for role, keywords in SUB_ROLES:
        if any(kw in full_l for kw in keywords):
            return role

    return "generic"


# ─── Pitches par sous-role (focus PERTINENT pour CHAQUE type de poste) ────────

def pitch_for(role: str, entreprise: str, description: str = "") -> str:
    """Pitch ciblant le sous-role precis, sans points hors-sujet."""

    # Marketing produit / brand : focus marketing, PAS B2B sales
    if role == "product_marketing":
        return (
            "Mon experience en gestion de projets digitaux pour clients internationaux "
            "depuis Lisbonne, combinee aux modules de strategie produit et d'analyse de "
            "marche de mon MBA, me permet de comprendre rapidement les enjeux de "
            "positionnement, de pricing et de cycle de vie produit. J'ai egalement "
            "collabore avec GROW 360 (Paris) sur des leviers de notoriete et "
            "d'engagement, ce qui m'a appris a transformer un brief marketing en "
            "actions mesurables."
        )

    if role == "digital_marketing":
        return (
            "Mon experience de Community Management chez GROW 360 (Paris) et de "
            "gestion de projets digitaux pour clients internationaux depuis Lisbonne "
            "m'a appris a piloter des campagnes multicanales avec des KPIs concrets : "
            "engagement, taux de conversion, ROI campagne. Je connais les outils du "
            "marketing digital moderne (analytics, automation, social listening) et "
            "sais structurer une strategie de contenu adaptee aux specificites locales."
        )

    # Finance / Analytics : focus rigueur, MBA, donnees
    if role == "financial_analyst":
        return (
            "Mon MBA Manager de Business Unit a PSB Paris School of Business inclut "
            "des modules approfondis de controle de gestion, analyse de la performance "
            "et lecture financiere strategique. En parallele, je pilote au quotidien "
            "une activite a forts enjeux operationnels (gestion de KPIs commerciaux, "
            "reporting), ce qui me donne une lecture business des chiffres au-dela "
            "de l'aspect technique. Cette double competence finance/business est un "
            "atout direct pour les sujets d'arbitrage et de partenariat avec les "
            "operationnels."
        )

    if role == "data_analyst":
        return (
            "Diplome de Business Unit avec une specialisation en pilotage par la donnee, "
            "je manipule au quotidien des indicateurs commerciaux pour orienter mes "
            "actions. Mon MBA m'a forme aux outils d'analyse, a la modelisation et au "
            "storytelling de donnees pour les decideurs. Je sais transformer un dataset "
            "brut en insight actionnable, en commencant par poser les bonnes questions "
            "business avant de plonger dans la technique."
        )

    if role == "purchasing":
        return (
            "Habitue a negocier des partenariats strategiques avec des enjeux financiers "
            "concrets, je transpose facilement cette approche cote achats : recherche "
            "de fournisseurs, comparaison TCO, negociation de conditions et structuration "
            "des contrats cadres. Mon MBA Business Unit inclut une formation aux strategies "
            "supply et procurement, et mon multilinguisme facilite les relations avec les "
            "fournisseurs internationaux."
        )

    # Commerce / Sales : ICI on peut pousser le 360K
    if role == "key_account":
        return (
            "Actuellement Business Developer B2B chez Agence 113 / DEFI GROUPE avec un "
            "portefeuille generant 360 000 EUR de CA mensuel, je gere des comptes "
            "strategiques en mode hunter-farmer. J'ai construit ma maitrise du cycle de "
            "vente long, de la prospection au closing, en passant par la gestion de la "
            "relation post-signature. Cette experience de Key Account a la francaise se "
            "transpose directement aux marches internationaux exigeants."
        )

    if role == "business_dev":
        return (
            "Actuellement Business Developer B2B chez Agence 113 / DEFI GROUPE, je pilote "
            "une activite generant 360 000 EUR de CA mensuel, en autonomie sur tout le "
            "cycle commercial : prospection, qualification, negociation, closing. Je "
            "maitrise HubSpot CRM et LinkedIn Sales Navigator au quotidien et sais "
            "structurer un pipeline de A a Z. Cette posture de developpeur d'activite "
            "est exactement celle attendue dans une mission VIE."
        )

    if role == "sales":
        return (
            "Actuellement Business Developer B2B chez Agence 113 / DEFI GROUPE avec un "
            "portefeuille de 360 000 EUR de CA mensuel, je sais transformer une opportunite "
            "froide en client signe. Maitrise du cycle de vente complet, des outils CRM "
            "(HubSpot, Sales Navigator) et de la negociation B2B sur des cibles exigeantes. "
            "Je garde une approche orientee resultat, avec une rigueur de suivi et une "
            "ecoute client qui font la difference."
        )

    # HR : focus recrutement
    if role == "hr":
        return (
            "J'ai dirige operationnellement des process de recrutement a grande echelle : "
            "organisation d'evenements regroupant plus de 300 candidats, sourcing actif, "
            "coordination du service POEI, conduite d'entretiens et reporting. Cette "
            "double experience RH/business est rare et m'a appris a parler le langage des "
            "managers comme des candidats. Mon MBA renforce ma comprehension strategique "
            "des enjeux de talent dans une organisation."
        )

    # Generic fallback
    return (
        "Mon parcours combine une experience de pilotage operationnel en France et de "
        "gestion de projets internationaux depuis Lisbonne, avec une formation en cours "
        "(MBA Manager de Business Unit, PSB Paris School of Business) qui m'a apporte les "
        "methodes et la rigueur d'une carriere structuree. J'apporte rigueur, autonomie "
        "et capacite a livrer des resultats concrets dans des contextes exigeants."
    )


def deliverables_for(role: str) -> str:
    """3 leviers concrets que j'apporte, par sous-role."""
    if role == "product_marketing":
        return (
            "Concretement, je peux contribuer des le premier mois sur trois axes : "
            "1) lecture rapide des etudes de marche et des donnees concurrentielles "
            "pour nourrir vos decisions produit, "
            "2) coordination operationnelle entre marketing, ventes et R&D pour "
            "fluidifier les lancements, "
            "3) ouverture multiculturelle pour adapter le positionnement aux specificites "
            "des marches locaux."
        )
    if role == "digital_marketing":
        return (
            "Concretement, je peux : "
            "1) prendre en main vos campagnes digitales avec une lecture KPI/ROI rigoureuse, "
            "2) produire ou superviser du contenu adapte a vos cibles internationales, "
            "3) adapter le ton et les codes selon les marches locaux grace a mon "
            "multilinguisme."
        )
    if role == "financial_analyst":
        return (
            "Concretement, je peux : "
            "1) construire des reportings clairs et actionnables pour vos decideurs, "
            "2) participer aux exercices de budget, forecast et analyse d'ecarts, "
            "3) faire le pont entre la finance et les operationnels grace a mon "
            "experience business."
        )
    if role == "data_analyst":
        return (
            "Concretement, je peux : "
            "1) industrialiser des reportings reguliers sur Excel / Power BI / Tableau, "
            "2) identifier les insights actionnables dans vos donnees commerciales, "
            "3) traduire les analyses techniques en recommandations claires pour les "
            "decideurs."
        )
    if role == "purchasing":
        return (
            "Concretement, je peux : "
            "1) construire des analyses categorielles solides pour eclairer les decisions "
            "achats, "
            "2) negocier directement avec des fournisseurs internationaux dans plusieurs "
            "langues, "
            "3) structurer le suivi de la performance fournisseurs."
        )
    if role == "key_account":
        return (
            "Concretement, je peux : "
            "1) prendre en main rapidement un portefeuille de comptes strategiques, "
            "2) deployer une approche structuree (HubSpot, plan de compte, business review), "
            "3) negocier les conditions cadres dans plusieurs langues."
        )
    if role in ("business_dev", "sales"):
        return (
            "Concretement, je peux : "
            "1) ouvrir un nouveau marche ou developper un portefeuille existant des le "
            "premier mois, "
            "2) structurer votre pipeline avec une rigueur d'execution prouvee, "
            "3) closer des deals complexes grace a mon experience B2B et a mon adaptabilite "
            "culturelle."
        )
    if role == "hr":
        return (
            "Concretement, je peux : "
            "1) prendre en charge des process de recrutement de A a Z, "
            "2) animer des evenements employeur et des sessions de sourcing, "
            "3) faire le lien entre RH et business grace a mon experience operationnelle."
        )
    return (
        "Concretement, j'apporte rigueur operationnelle, autonomie acquise a "
        "l'international, et capacite a livrer des resultats mesurables."
    )


# ─── Donnees marche pays ──────────────────────────────────────────────────────

_COUNTRY_CONTEXT = {
    "chine":     ("Shanghai et la Chine restent le 1er marche e-commerce mondial",
                  "Mes notions de chinois et ma comprehension des codes business asiatiques accelereront mon integration."),
    "japon":     ("Le Japon reste la 3e economie mondiale avec une exigence reconnue de rigueur et de long-termisme",
                  "Mon serieux et ma capacite a tisser des relations sur la duree correspondent aux codes business japonais."),
    "coree":     ("La Coree du Sud est un hub strategique pour l'innovation et l'export en Asie",
                  "Mon ouverture aux marches asiatiques et ma rigueur seront un atout immediat."),
    "singapour": ("Singapour est la porte d'entree de l'ASEAN et un hub financier mondial",
                  "Mon profil multilingue et international correspond directement a l'ecosysteme local."),
    "etats-unis":("Le marche americain reste le 1er PIB mondial et exige une approche orientee resultats",
                  "Mon experience de gestion d'objectifs CA mensuels me prepare directement a vos exigences."),
    "canada":    ("Le Canada offre un acces strategique au marche nord-americain",
                  "Mon bilinguisme francais/anglais est un avantage immediat sur ce marche."),
    "mexique":   ("Le Mexique est le 1er hub manufacturier des Ameriques",
                  "Mon espagnol intermediaire facilitera mes echanges avec les equipes et clients locaux."),
    "bresil":    ("Le Bresil represente la 1ere economie d'Amerique latine",
                  "Mon adaptabilite culturelle et mes acquis sur les marches multiculturels sont un atout direct."),
    "argentine": ("L'Argentine reste un acteur majeur du Cono Sur",
                  "Mon espagnol intermediaire facilitera mes echanges avec les partenaires locaux."),
    "chili":     ("Le Chili est le marche le plus stable d'Amerique latine et un hub regional",
                  "Mon espagnol intermediaire me permettra d'etre operationnel rapidement."),
    "colombie":  ("La Colombie represente un marche en forte croissance d'Amerique latine",
                  "Mon espagnol intermediaire sera directement utile sur ce marche hispanophone."),
    "emirats":   ("Dubai concentre les sieges regionaux Moyen-Orient et est un hub du commerce global",
                  "Arabophone natif, je maitrise les codes commerciaux essentiels pour reussir dans le Golfe."),
    "arabie":    ("L'Arabie saoudite represente 25% du PIB du Moyen-Orient et investit massivement (Vision 2030)",
                  "Mon arabe natif et ma comprehension des codes locaux sont des avantages strategiques."),
    "qatar":     ("Le Qatar reste un acteur strategique du Golfe avec un fort dynamisme",
                  "Mon arabe natif facilitera la creation de relations de confiance localement."),
    "australie": ("L'Australie est un marche mature et porte d'entree vers l'Asie Pacifique",
                  "Mon profil international et ma capacite a operer en autonomie correspondent au contexte local."),
    "inde":      ("L'Inde est la 5e economie mondiale avec un dynamisme exceptionnel",
                  "Mon ouverture culturelle et mon anglais courant correspondent au contexte business indien."),
}


def _country_context(pays: str) -> tuple:
    p = (pays or "").lower()
    for country, (market, lang) in _COUNTRY_CONTEXT.items():
        if country in p:
            return market, lang
    return ("", "")


# ─── Description-mirroring : reprendre 1 segment de la mission ────────────────

def _mirror_mission(description: str) -> str:
    if not description or len(description) < 60:
        return ""
    snippet = description.strip()
    snippet = re.sub(r"\s+", " ", snippet)
    if len(snippet) > 180:
        snippet = snippet[:180].rsplit(" ", 1)[0] + "..."
    return (
        f"La mission telle que vous la decrivez ('{snippet}') correspond precisement "
        f"a l'environnement dans lequel je souhaite construire la suite de mon parcours."
    )


# ─── Hook : XP intl + MBA + ce qu'on apporte au poste precis ──────────────────

def _hook(role: str, titre: str, entreprise: str) -> str:
    """
    Hook d'ouverture VARIABLE selon le sous-role pour eviter l'effet template.
    Pose : ce que j'apporte au poste precis, mon profil (XP intl + MBA), l'energie.
    """
    poste = (titre or "ce poste").strip()

    # Marketing : ouverture orientee strategie / contenu / produit
    if role in ("product_marketing", "digital_marketing"):
        return (
            f"C'est avec un fort interet que je postule au poste de {poste} chez {entreprise}. "
            f"Diplome en cours de MBA Manager de Business Unit a PSB Paris (soutenance juin "
            f"2026), avec une experience concrete de gestion de projets digitaux a "
            f"l'international (Lisbonne) et de community management (GROW 360, Paris), je "
            f"souhaite mettre cette double culture marketing/projets au service de votre equipe."
        )

    # Finance / Analytics : ouverture orientee rigueur + chiffres
    if role in ("financial_analyst", "data_analyst"):
        return (
            f"Je me permets de vous adresser ma candidature au poste de {poste} chez "
            f"{entreprise}. En MBA Manager de Business Unit a PSB Paris (soutenance juin "
            f"2026) et actuellement en charge du pilotage operationnel d'une activite "
            f"generant 360 KEUR de CA mensuel, je souhaite valoriser cette double "
            f"culture (gestion + analyse) au service de vos enjeux financiers."
        )

    # Achats / Procurement : ouverture orientee negociation
    if role == "purchasing":
        return (
            f"Je vous adresse ma candidature au poste de {poste} chez {entreprise}. "
            f"Forme a la negociation a la fois en pratique (Business Developer B2B, 360 KEUR "
            f"de CA mensuel) et en formation (Negotiation Business School, certifie 2025, "
            f"plus modules MBA), je souhaite transposer cette competence sur les enjeux "
            f"achats et categoriels."
        )

    # HR / Recrutement
    if role == "hr":
        return (
            f"Je suis particulierement motive par le poste de {poste} chez {entreprise}. "
            f"Recruitment Officer chez Agence 113 / DEFI GROUPE ou je gere actuellement des "
            f"sessions reunissant plus de 300 candidats, et en MBA Manager de Business Unit "
            f"(PSB Paris, juin 2026), je combine experience operationnelle RH et hauteur "
            f"strategique business."
        )

    # Commerce / Sales / Key Account / Business Dev
    return (
        f"Actuellement Business Developer B2B chez Agence 113 / DEFI GROUPE, ou je pilote "
        f"un portefeuille generant 360 KEUR de CA mensuel, et diplome en cours de MBA "
        f"Manager de Business Unit a PSB Paris (soutenance juin 2026), je souhaite mettre "
        f"mon experience commerciale et ma rigueur de pilotage au service de votre equipe "
        f"sur le poste de {poste} chez {entreprise}."
    )


# ─── Generation de la lettre complete ─────────────────────────────────────────

def generate(offer: dict) -> str:
    titre       = offer.get("titre", "le poste propose")
    entreprise  = offer.get("entreprise", "votre entreprise")
    pays        = offer.get("pays", "")
    duree       = offer.get("duree", 12)
    description = offer.get("description", "")

    role     = detect_sub_role(titre, description)
    hook     = _hook(role, titre, entreprise)
    pitch    = pitch_for(role, entreprise, description)
    deliver  = deliverables_for(role)
    mirror   = _mirror_mission(description)
    market, lang = _country_context(pays)

    pays_str  = f"en {pays}" if pays and pays not in ("N/A", "") else "a l'international"
    duree_str = f"{duree} mois" if duree else "la duree prevue"

    paras = ["Madame, Monsieur,", hook]

    if mirror:
        paras.append(mirror)

    paras.append(pitch)
    paras.append(deliver)

    if market:
        paras.append(
            f"De plus, {market}, ce qui rend cette mission particulierement strategique "
            f"pour la suite de mon parcours."
        )
    if lang:
        paras.append(lang)

    paras.append(
        f"Cette mission de {duree_str} {pays_str} represente exactement le defi dans "
        f"lequel je souhaite m'investir pleinement. Je suis disponible pour echanger "
        f"des que vous le souhaitez."
    )
    paras.append(
        f"Cordialement,\n{PROFILE['name']}\n{PROFILE['phone']} | {PROFILE['email']}"
    )

    return "\n\n".join(paras)


# ─── Message court (6 lignes) ─────────────────────────────────────────────────

_SHORT_PITCH = {
    "product_marketing":  "comprendre rapidement vos enjeux produit (etudes, positionnement, cycle de vie) et coordonner marketing/ventes/R&D",
    "digital_marketing":  "executer des campagnes digitales multicanales avec lecture ROI rigoureuse et adaptation aux marches locaux",
    "financial_analyst":  "construire des reportings actionnables et faire le pont entre finance et operationnels",
    "data_analyst":       "industrialiser des reportings, identifier les insights actionnables et les traduire pour les decideurs",
    "purchasing":         "structurer des analyses categorielles, negocier en plusieurs langues et suivre la performance fournisseurs",
    "key_account":        "prendre en main des comptes strategiques, structurer un plan de compte et negocier les conditions cadres",
    "business_dev":       "ouvrir un marche ou developper un portefeuille avec rigueur d'execution prouvee (360KEUR de CA mensuel actuel)",
    "sales":              "transformer des opportunites froides en deals signes (360KEUR de CA mensuel actuel) avec rigueur de suivi",
    "hr":                 "piloter des process de recrutement de A a Z et faire le lien RH/business",
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
        f"internationale (Lisbonne), je viens du pilotage operationnel et souhaite mettre "
        f"cette energie au service de votre equipe.\n"
        f"Concretement, je peux {pitch}.\n"
        f"Vous trouverez en piece jointe mon CV et ma lettre de motivation.\n"
        f"Disponible pour un echange a votre convenance.\n"
        f"Cordialement, {PROFILE['name']} ({PROFILE['phone']})"
    )
