"""
Lettre de motivation et message court personnalises par offre.
- Detection sous-role precise (2 passes)
- 8 hooks d'ouverture varies, rotation par hash de l'offre
- 2-3 éléments spécifiques de l'offre references
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
    ("business_dev",      ["business dev", "bizdev", "développement commercial",
                           "développement business", "sales developer", "sdr"]),
    ("sales",             ["sales", "commercial", "vente", "ventes", "closing"]),
    ("hr",                ["talent", "recruitment", "recrutement", "hrbp",
                           "people", "human resources", "ressources humaines",
                           "early talent", "learning"]),
]


# « Talent Acquisition » contient « acquisition », mot-clé du marketing digital :
# sans cette garde, une offre de recrutement — son métier le plus solide — partait
# avec un CV et une lettre de community manager.
_HR_TITLE = ("talent acquisition", "recrut", "recruit")


def detect_sub_role(titre: str, description: str = "") -> str:
    titre_l = (titre or "").lower()
    full_l  = (titre_l + " " + (description or "")).lower()
    if any(kw in titre_l for kw in _HR_TITLE):
        return "hr"
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


# ─── Pool de hooks par role ───────────────────────────────────────────────────
#
# Faits autorisés (profil.json, statut « verifie ») : Bachelor REM (Bac+3, Paris
# Nord Business School, 2026), BTS NTC, chargé d'affaires chez PROMAN Group
# (2026), chargé de recrutement & commercial chez DEFI GROUPE (2025 - juil.
# 2026), Website Builder chez Wix à Lisbonne (2025), conseiller premium
# horlogerie au Printemps Haussmann (2023-2024), Grow 360 (2022-2024), TOEIC
# 915/990, arabe natif, espagnol notions, disponible immédiatement.
#
# Retirés le 06/10/2026 : « MBA Manager de Business Unit (PSB Paris) », « 360
# k€/mois », « 30 deals », « 300+ candidats », « deux ans de B2B », HubSpot,
# Sales Navigator, « Negotiation Business School », « actuellement » — aucun
# n'est dans son profil vérifié, et ils sont partis chez des recruteurs qui
# l'ont rappelé dessus.

def _hook(role: str, titre: str, entreprise: str, offer: dict) -> str:
    poste = (titre or "ce poste").strip()
    idx   = _hook_index(offer, 3)

    if role in ("product_marketing", "digital_marketing"):
        variants = [
            (
                f"C'est avec un fort intérêt que je postule au poste de {poste} "
                f"chez {entreprise}. Titulaire d'un Bachelor REM (Bac+3), j'ai "
                f"travaillé comme Website Builder chez Wix à Lisbonne, en "
                f"environnement anglophone, et comme community manager & "
                f"événementiel chez Grow 360 à Paris. Je souhaite mettre cette "
                f"double culture digitale et terrain au service de votre équipe."
            ),
            (
                f"Mon parcours croise le digital et le terrain : projets web "
                f"clients chez Wix à Lisbonne, réseaux sociaux et événements chez "
                f"Grow 360 à Paris, vente premium au Printemps Haussmann. Le poste "
                f"de {poste} chez {entreprise} réunit ces trois dimensions, et "
                f"je suis disponible immédiatement."
            ),
            (
                f"Ce que j'ai appris à Lisbonne comme à Paris, c'est qu'un projet "
                f"digital commence par l'écoute du besoin client. C'est l'approche "
                f"que je veux apporter au poste de {poste} chez {entreprise}, "
                f"avec un Bachelor REM (Bac+3) et un anglais courant (TOEIC 915/990)."
            ),
        ]
        return variants[idx % len(variants)]

    if role in ("financial_analyst", "data_analyst"):
        variants = [
            (
                f"Je me permets de vous adresser ma candidature au poste de "
                f"{poste} chez {entreprise}. Titulaire d'un Bachelor REM (Bac+3), "
                f"je viens du terrain commercial — chargé d'affaires chez PROMAN "
                f"Group, chargé de recrutement & commercial chez DEFI GROUPE — et "
                f"je souhaite mettre cette lecture business au service de vos "
                f"analyses."
            ),
            (
                f"Les chiffres sont plus utiles quand on connaît le terrain qu'ils "
                f"décrivent. C'est ce que m'ont appris la prospection et le suivi "
                f"de portefeuille clients chez PROMAN Group et DEFI GROUPE, et "
                f"c'est l'angle que je veux apporter au poste de {poste} chez "
                f"{entreprise}."
            ),
            (
                f"Le poste de {poste} chez {entreprise} est l'occasion de joindre "
                f"une expérience commerciale réelle (PROMAN Group, DEFI GROUPE, "
                f"Printemps Haussmann) à la rigueur du suivi et du reporting. "
                f"Bachelor REM (Bac+3), anglais courant (TOEIC 915/990), "
                f"disponible immédiatement."
            ),
        ]
        return variants[idx % len(variants)]

    if role == "purchasing":
        variants = [
            (
                f"Je vous adresse ma candidature au poste de {poste} chez "
                f"{entreprise}. Côté vente, chez PROMAN Group et DEFI GROUPE, "
                f"j'ai appris à identifier le besoin réel d'une entreprise avant "
                f"de proposer une solution ; je souhaite transposer cette écoute "
                f"de l'autre côté de la table."
            ),
            (
                f"Négocier, c'est d'abord comprendre ce que l'autre partie veut "
                f"vraiment, pas seulement son prix. C'est l'approche que j'ai "
                f"pratiquée en prospection B2B chez PROMAN Group et DEFI GROUPE, "
                f"et que je souhaite mettre au service du poste de {poste} chez "
                f"{entreprise}."
            ),
            (
                f"Après une expérience commerciale B2B (PROMAN Group, DEFI GROUPE) "
                f"et un Bachelor REM (Bac+3), je souhaite rejoindre {entreprise} "
                f"sur le poste de {poste} pour travailler la relation "
                f"fournisseurs avec la même exigence d'écoute et de suivi."
            ),
        ]
        return variants[idx % len(variants)]

    if role == "hr":
        variants = [
            (
                f"Je suis particulièrement motivé par le poste de {poste} chez "
                f"{entreprise}. Pendant un an chez DEFI GROUPE, j'ai été chargé de "
                f"recrutement et commercial : sourcing, présélection et entretiens "
                f"candidats d'un côté, analyse du besoin des entreprises de l'autre. "
                f"Titulaire d'un Bachelor REM (Bac+3), je suis disponible immédiatement."
            ),
            (
                f"Un recrutement réussi tient à une chose : comprendre l'entreprise "
                f"autant que le candidat. C'est ce que j'ai pratiqué chez DEFI "
                f"GROUPE, seul interlocuteur des deux côtés jusqu'à l'aboutissement "
                f"du dossier, et c'est pourquoi le poste de {poste} chez "
                f"{entreprise} me correspond."
            ),
            (
                f"Chargé de recrutement & commercial chez DEFI GROUPE, puis chargé "
                f"d'affaires chez PROMAN Group : j'ai travaillé le recrutement avec "
                f"un regard business. C'est cette double lecture que je souhaite "
                f"apporter au poste de {poste} chez {entreprise}."
            ),
        ]
        return variants[idx % len(variants)]

    # Commerce / Sales / Key Account / Business Dev / generic
    variants = [
        (
            f"Chargé d'affaires chez PROMAN Group en 2026, après un an comme chargé "
            f"de recrutement et commercial chez DEFI GROUPE, je souhaite mettre "
            f"mon expérience de la prospection et du développement de portefeuille "
            f"au service du poste de {poste} chez {entreprise}. Titulaire d'un "
            f"Bachelor REM (Bac+3), je suis disponible immédiatement."
        ),
        (
            f"Partir en V.I.E., c'est une décision réfléchie. C'est avec cet état "
            f"d'esprit que je postule au poste de {poste} chez {entreprise} : "
            f"prospection B2B chez PROMAN Group et DEFI GROUPE, vente premium au "
            f"Printemps Haussmann auprès d'une clientèle internationale, et un "
            f"anglais courant (TOEIC 915/990)."
        ),
        (
            f"J'ai construit mon expérience commerciale sur le terrain : "
            f"prospection et fidélisation de clients chez PROMAN Group, besoins "
            f"des entreprises et suivi des dossiers chez DEFI GROUPE, conseil à une "
            f"clientèle internationale au Printemps Haussmann. Le poste de {poste} "
            f"chez {entreprise} est la prochaine étape logique."
        ),
        (
            f"Sur le poste de {poste} chez {entreprise}, mon objectif est clair : "
            f"être opérationnel dès les premières semaines. J'arrive avec une "
            f"pratique réelle de la prospection B2B (PROMAN Group, DEFI GROUPE), "
            f"un Bachelor REM (Bac+3) et une disponibilité immédiate."
        ),
    ]
    return variants[idx % len(variants)]


# ─── Pitch par role ───────────────────────────────────────────────────────────

def pitch_for(role: str, entreprise: str, description: str = "") -> str:
    if role == "product_marketing":
        return (
            "Chez Wix à Lisbonne, j'ai accompagné des clients dans leurs projets "
            "de sites web, de l'analyse du besoin au suivi du projet, en anglais "
            "au quotidien. Chez Grow 360 à Paris, j'ai géré les réseaux sociaux "
            "de restaurants et organisé des événements. Ces deux expériences "
            "m'ont appris à partir du besoin réel du client pour construire une "
            "proposition qui lui parle."
        )
    if role == "digital_marketing":
        return (
            "Mon expérience de community manager & événementiel chez Grow 360 "
            "(réseaux sociaux de restaurants, événements) et de Website Builder "
            "chez Wix à Lisbonne m'a donné une pratique concrète du contenu et du "
            "web : HTML/CSS/JavaScript, Wix/Velo, WordPress, Webflow. J'utilise "
            "aussi l'IA et l'automatisation pour gagner du temps sur la "
            "production."
        )
    if role == "financial_analyst":
        return (
            "Mon atout est la lecture business : chez PROMAN Group et DEFI "
            "GROUPE, j'ai prospecté, suivi un portefeuille clients et des "
            "dossiers jusqu'à leur aboutissement. Je sais ce que les chiffres "
            "représentent sur le terrain, et je travaille avec rigueur sur les "
            "outils de suivi et de reporting."
        )
    if role == "data_analyst":
        return (
            "Je travaille avec les outils de suivi et de reporting (Pack Office), "
            "j'ai des bases web (HTML/CSS/JavaScript) et j'utilise l'IA et "
            "l'automatisation au quotidien. Mon expérience commerciale chez "
            "PROMAN Group et DEFI GROUPE m'aide à poser les bonnes questions "
            "business avant de plonger dans les données."
        )
    if role == "purchasing":
        return (
            "Chez PROMAN Group et DEFI GROUPE, j'ai identifié les besoins des "
            "entreprises, proposé des solutions adaptées et suivi chaque dossier "
            "jusqu'à son aboutissement. Mon arabe natif et mon anglais courant "
            "(TOEIC 915/990) facilitent les échanges avec des partenaires "
            "internationaux."
        )
    if role == "key_account":
        return (
            "Chez PROMAN Group, j'ai développé et fidélisé un portefeuille "
            "clients et développé des partenariats ; chez DEFI GROUPE, j'ai "
            "identifié les besoins des entreprises et suivi leurs dossiers "
            "jusqu'au bout. Ce suivi dans la durée est le cœur d'un poste Key "
            "Account, et je souhaite l'exercer sur des marchés internationaux."
        )
    if role == "business_dev":
        return (
            "Chargé d'affaires chez PROMAN Group, j'ai prospecté de nouveaux "
            "clients, géré et fidélisé un portefeuille et développé des "
            "partenariats. Chez DEFI GROUPE, j'ai prospecté des entreprises, "
            "analysé leurs besoins et proposé des solutions adaptées. Je me forme "
            "aussi à Salesforce (certificat Sales and CRM Overview, Coursera, 2026)."
        )
    if role == "sales":
        return (
            "Ma pratique de la vente couvre le B2B et le B2C : prospection et "
            "développement de portefeuille chez PROMAN Group et DEFI GROUPE, "
            "conseil et vente en horlogerie premium au Printemps Haussmann, "
            "auprès d'une clientèle internationale. J'y ai appris à écouter le "
            "besoin avant d'argumenter, et à suivre le client dans la durée."
        )
    if role == "hr":
        return (
            "Chez DEFI GROUPE, j'étais l'interlocuteur des deux côtés : "
            "prospection d'entreprises et analyse de leur besoin, sourcing, "
            "présélection téléphonique et entretiens candidats, puis suivi des "
            "recrutements jusqu'à leur aboutissement. Cette double expérience "
            "RH et commerciale m'a appris à parler le langage des managers comme "
            "celui des candidats."
        )
    return (
        "Mon parcours combine une expérience commerciale en France (PROMAN "
        "Group, DEFI GROUPE, Printemps Haussmann) et une expérience "
        "professionnelle à Lisbonne, en anglais. J'apporte autonomie, écoute du "
        "client et adaptabilité culturelle, avec un Bachelor REM (Bac+3)."
    )


def deliverables_for(role: str) -> str:
    if role == "product_marketing":
        return (
            "Concrètement, je peux contribuer dès le premier mois : "
            "1) lecture rapide des études de marché pour nourrir les decisions "
            "produit, "
            "2) coordination opérationnelle entre marketing, ventes et R&D, "
            "3) adaptation du positionnement aux specificites des marchés locaux "
            "grâce à mon ouverture multiculturelle."
        )
    if role == "digital_marketing":
        return (
            "Concrètement, je peux : "
            "1) prendre en main vos campagnes digitales avec lecture KPI/ROI rigoureuse, "
            "2) produire du contenu adapte a vos cibles internationales, "
            "3) adapter le ton selon les marchés locaux grâce à mon multilinguisme."
        )
    if role == "financial_analyst":
        return (
            "Concrètement, je peux : "
            "1) construire des reportings clairs et actionnables pour vos décideurs, "
            "2) participer aux exercices de budget, forecast et analyse d'écarts, "
            "3) faire le pont finance/opérationnels grâce à mon expérience business."
        )
    if role == "data_analyst":
        return (
            "Concrètement, je peux : "
            "1) fiabiliser des reportings réguliers avec les outils de l'équipe, "
            "2) identifier les insights actionnables dans vos données commerciales, "
            "3) traduire les analyses en recommandations claires pour les décideurs."
        )
    if role == "purchasing":
        return (
            "Concrètement, je peux : "
            "1) construire des analyses catégorielles pour éclairer les décisions achats, "
            "2) négocier directement avec des fournisseurs internationaux en plusieurs "
            "langues, "
            "3) structurer le suivi de la performance fournisseurs."
        )
    if role == "key_account":
        return (
            "Concrètement, je peux : "
            "1) prendre en main rapidement un portefeuille de comptes stratégiques, "
            "2) déployer une approche structurée (plan de compte, business review), "
            "3) négocier les conditions cadres dans plusieurs langues."
        )
    if role in ("business_dev", "sales"):
        return (
            "Concrètement, je peux : "
            "1) prospecter et développer un portefeuille dès les premières semaines, "
            "2) suivre chaque opportunité avec rigueur jusqu'à sa conclusion, "
            "3) créer une relation de confiance avec des clients internationaux "
            "grâce à mon anglais courant et mon adaptabilité culturelle."
        )
    if role == "hr":
        return (
            "Concrètement, je peux : "
            "1) prendre en charge des process de recrutement de A à Z, "
            "2) animer des événements employeur et des sessions de sourcing, "
            "3) faire le lien RH/business grâce à mon expérience opérationnelle."
        )
    return "Concrètement, j'apporte rigueur, autonomie et écoute du client, en France comme à l'international."


# ─── Contexte pays ────────────────────────────────────────────────────────────

_COUNTRY_CONTEXT = {
    "chine":      ("Shanghai et la Chine sont le 1er marché e-commerce mondial",
                   "Mon anglais courant (TOEIC 915/990) et mon adaptabilité "
                   "accéléreront mon intégration."),
    "japon":      ("Le Japon reste la 3e economie mondiale avec une exigence "
                   "reconnue de rigueur et de long-termisme",
                   "Mon serieux et ma capacite a tisser des relations sur la duree "
                   "correspondent aux codes business japonais."),
    "coree":      ("La Coree du Sud est un hub stratégique pour l'innovation en Asie",
                   "Mon ouverture aux marchés asiatiques et ma rigueur seront un "
                   "atout immédiat."),
    "singapour":  ("Singapour est la porte d'entree de l'ASEAN et un hub financier",
                   "Mon profil multilingue et international correspond directement "
                   "a l'ecosysteme local."),
    "etats-unis": ("Le marché americain reste le 1er PIB mondial avec des exigences "
                   "elevees de performance",
                   "Mon anglais courant (TOEIC 915/990) et mon expérience "
                   "commerciale me préparent à ces standards."),
    "canada":     ("Le Canada offre un acces stratégique au marché nord-americain",
                   "Mon bilinguisme français/anglais est un avantage immédiat sur ce marché."),
    "mexique":    ("Le Mexique est le 1er hub manufacturier des Ameriques",
                   "Mes notions d'espagnol et mon adaptabilité faciliteront mon intégration."),
    "bresil":     ("Le Bresil représente la 1ere economie d'Amerique latine",
                   "Mon adaptabilité culturelle et mes acquis multiculturels sont un atout direct."),
    "argentine":  ("L'Argentine reste un acteur majeur du Cono Sur",
                   "Mes notions d'espagnol et mon adaptabilité faciliteront mon intégration."),
    "chili":      ("Le Chili est le marché le plus stable d'Amerique latine",
                   "Mes notions d'espagnol, que je continue de travailler, m'aideront à m'intégrer vite."),
    "colombie":   ("La Colombie est un marché en forte croissance d'Amerique latine",
                   "Mes notions d'espagnol, que je continue de travailler, seront utiles sur ce marché."),
    "emirats":    ("Dubai concentre les sieges regionaux Moyen-Orient et est un hub du "
                   "commerce global",
                   "Arabophone natif, je maîtrise les codes commerciaux du Golfe."),
    "arabie":     ("L'Arabie saoudite représente 25% du PIB Moyen-Orient et investit "
                   "massivement (Vision 2030)",
                   "Mon arabe natif et ma compréhension des codes locaux sont des "
                   "avantages stratégiques."),
    "qatar":      ("Le Qatar reste un acteur stratégique du Golfe avec un fort dynamisme",
                   "Mon arabe natif facilitera la création de relations de confiance locales."),
    "australie":  ("L'Australie est un marché mature et porte d'entree vers l'Asie Pacifique",
                   "Mon profil international et mon autonomie correspondent au contexte local."),
    "inde":       ("L'Inde est la 5e economie mondiale avec un dynamisme exceptionnel",
                   "Mon anglais courant et mon ouverture culturelle correspondent au "
                   "contexte business indien."),
    "turquie":    ("La Turquie est un hub stratégique entre Europe et Asie",
                   "Mon profil multilingue et ma culture du commerce international "
                   "sont directement applicables."),
    "vietnam":    ("Le Vietnam est l'une des economies les plus dynamiques d'Asie du Sud-Est",
                   "Mon ouverture aux marchés asiatiques et mon adaptabilité sont "
                   "des atouts directs."),
    "indonesie":  ("L'Indonesie représente la plus grande economie de l'ASEAN",
                   "Mon profil international et ma capacite a operer en contexte "
                   "multiculturel seront immédiatement utiles."),
    "thaïlande":  ("La Thaïlande est le 2e marché d'Asie du Sud-Est",
                   "Mon expérience à l'international et mon adaptabilité correspondent "
                   "aux exigences locales."),
    "malaisie":   ("La Malaisie est un hub stratégique pour l'Asie du Sud-Est",
                   "Mon profil multilingue et mon expérience internationale sont "
                   "directement valorisables."),
}


def _country_context(pays: str) -> tuple:
    p = (pays or "").lower()
    for country, (market, lang) in _COUNTRY_CONTEXT.items():
        if country in p:
            return market, lang
    return ("", "")


# ─── Pont offre<->expérience : connexion naturelle, sans dump brut ─────────────

def _offer_bridge(offer: dict, analysis: dict, role: str) -> str:
    """
    Connecte les enjeux de l'offre a l'expérience concrete d'Amine.
    Reformule intelligemment — jamais de copie brute du texte de l'offre.
    """
    actions  = analysis.get("actions", [])
    industry = analysis.get("industry", "generic")
    pays     = offer.get("pays", "")
    a1       = actions[0] if len(actions) >= 1 else ""
    a2       = actions[1] if len(actions) >= 2 else ""

    # Bridges role-spécifiques : connectent DIRECTEMENT l'expérience au besoin
    if role == "financial_analyst":
        if a1 and a2:
            return (
                f"La dimension {a1} / {a2} au cœur de cette mission demande de "
                f"comprendre ce que les chiffres racontent du terrain : c'est ce "
                f"que m'a appris le suivi de portefeuille clients chez PROMAN "
                f"Group et DEFI GROUPE."
            )
        return (
            "Le pilotage que vous portez demande de comprendre ce que les chiffres "
            "racontent du terrain : c'est ce que m'a appris le suivi de "
            "portefeuille clients chez PROMAN Group et DEFI GROUPE."
        )

    if role == "data_analyst":
        if a1:
            return (
                f"L'enjeu {a1} que vous portez rejoint ma façon de travailler : "
                f"partir de la question business avant de produire un tableau, "
                f"pour que l'analyse serve vraiment la décision."
            )
        return (
            "Ma façon de travailler : partir de la question business avant de "
            "produire un tableau, pour que l'analyse serve vraiment la décision."
        )

    if role in ("product_marketing", "digital_marketing"):
        if a1 and a2:
            return (
                f"Les dimensions {a1} et {a2} que vous portez rejoignent ce que "
                f"j'ai pratiqué : à Lisbonne, l'accompagnement de projets web "
                f"clients chez Wix ; à Paris, les réseaux sociaux et les "
                f"événements chez Grow 360."
            )
        return (
            "Le marketing que vous décrivez rejoint ce que j'ai pratiqué : à "
            "Lisbonne, l'accompagnement de projets web clients chez Wix ; à Paris, "
            "les réseaux sociaux et les événements chez Grow 360."
        )

    if role in ("business_dev", "sales", "key_account"):
        # Ne pas utiliser des keywords generiques (reporting, analyse) pour un pont commercial
        _GENERIC_KWS = {"reporting", "analyse", "budget", "forecast", "dashboard", "kpi"}
        commercial_kw = next((a for a in actions if a not in _GENERIC_KWS), "")
        if commercial_kw:
            return (
                f"La dimension {commercial_kw} au cœur de ce poste correspond au "
                f"travail que j'ai mené chez PROMAN Group et DEFI GROUPE : "
                f"prospecter, identifier le besoin du client et suivre chaque "
                f"dossier jusqu'à son aboutissement."
            )
        return (
            "Le développement commercial que vous portez correspond au travail que "
            "j'ai mené chez PROMAN Group et DEFI GROUPE : prospecter, identifier "
            "le besoin du client et suivre chaque dossier jusqu'à son aboutissement."
        )

    if role == "purchasing":
        return (
            "La logique achats — comprendre ce que l'autre partie veut vraiment "
            "avant de défendre ses positions — est l'approche que j'ai pratiquée "
            "en B2B et que je veux transposer à votre catégorie."
        )

    if role == "hr":
        return (
            "Le recrutement qui fonctionne, c'est celui qui comprend le business. "
            "Chargé de recrutement et commercial à la fois chez DEFI GROUPE, j'ai "
            "appris à tenir les deux bouts du dossier."
        )

    # Fallback : secteur ou pays
    _INDUSTRY_BRIDGES = {
        "luxe":    "La culture de l'exigence et du détail que vous incarnez rejoint ce que j'ai pratiqué au Printemps Haussmann, auprès d'une clientèle internationale premium.",
        "énergie": "Les enjeux d'envergure et la transformation que vous portez correspondent à ce que je recherche délibérément pour mon premier poste international.",
        "conseil": "La culture du résultat et l'orientation client de votre environnement correspondent à ce que j'apporte.",
        "retail":  "La dynamique commerciale de votre secteur est l'environnement dans lequel je progresse le mieux, comme au Printemps Haussmann.",
        "finance": "Les enjeux analytiques de votre secteur demandent rigueur et sens du suivi, deux qualités que mon expérience commerciale m'a imposées.",
    }
    if industry in _INDUSTRY_BRIDGES:
        return _INDUSTRY_BRIDGES[industry]

    if pays and pays not in ("N/A", ""):
        return (
            f"Ce poste en {pays} correspond au niveau de complexite et d'exigence "
            f"que je recherche deliberement pour ma première mission internationale."
        )

    return ""


# ─── Generation lettre complète ───────────────────────────────────────────────

def generate(offer: dict) -> str:
    titre       = offer.get("titre", "le poste propose")
    entreprise  = offer.get("entreprise", "votre entreprise")
    pays        = offer.get("pays", "")
    duree       = offer.get("duree", 12)
    description = offer.get("description", "")

    role        = detect_sub_role(titre, description)
    analysis    = oa.analyze(offer)

    hook        = _hook(role, titre, entreprise, offer)
    bridge      = _offer_bridge(offer, analysis, role)
    pitch       = pitch_for(role, entreprise, description)
    deliver     = deliverables_for(role)
    market, lang_line = _country_context(pays)

    pays_str  = f"en {pays.title()}" if pays and pays not in ("N/A", "") else "à l'international"
    duree_str = f"{duree} mois" if duree else "la durée prévue"

    paras = ["Madame, Monsieur,", hook]

    if bridge:
        paras.append(bridge)

    paras.append(pitch)
    paras.append(deliver)

    if market:
        paras.append(
            f"De plus, {market}, ce qui rend cette mission particulièrement "
            f"stratégique pour la suite de mon parcours."
        )
    if lang_line:
        paras.append(lang_line)

    paras.append(
        f"Cette mission de {duree_str} {pays_str} représente exactement le "
        f"défi dans lequel je souhaite m'investir pleinement. Je suis disponible "
        f"pour un échange à votre convenance."
    )
    paras.append(
        f"Cordialement,\n{PROFILE['name']}\n{PROFILE['phone']} | {PROFILE['email']}"
    )

    return "\n\n".join(paras)


# ─── Message court (candidature email) ───────────────────────────────────────

_SHORT_PITCH = {
    "product_marketing":  "structurer votre démarche produit et coordonner marketing/ventes/R&D",
    "digital_marketing":  "piloter des campagnes digitales multicanales avec lecture ROI rigoureuse",
    "financial_analyst":  "construire des reportings actionnables et partenaire finance/opérationnels",
    "data_analyst":       "industrialiser des reportings et traduire les données en décisions pour les décideurs",
    "purchasing":         "analyser les categories, négocier en plusieurs langues, suivre fournisseurs",
    "key_account":        "prendre en main des comptes stratégiques et structurer le plan de compte",
    "business_dev":       "prospecter, développer et fidéliser un portefeuille clients",
    "sales":              "prospecter, conseiller et suivre vos clients jusqu'à la signature",
    "hr":                 "piloter des process recrutement de A à Z et faire le lien RH/business",
    "generic":            "livrer des résultats concrets en autonomie à l'international",
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
        f"Titulaire d'un Bachelor REM (Bac+3), j'ai été chargé d'affaires chez "
        f"PROMAN Group et chargé de recrutement & commercial chez DEFI GROUPE, "
        f"avec une expérience à Lisbonne (Wix) et un anglais courant (TOEIC "
        f"915/990). Je suis disponible immédiatement.\n"
        f"Concrètement, je peux {pitch}.\n"
        f"Vous trouverez ci-joint mon CV et ma lettre de motivation.\n"
        f"Disponible pour un échange à votre convenance.\n"
        f"Cordialement, {PROFILE['name']} ({PROFILE['phone']})"
    )
