"""
Generateur de lettres de motivation et messages courts personnalises.
- Hook court et orient resultats (XP internationale + MBA + ce qu'on apporte)
- Paragraphe entreprise base sur secteur, pays, description de l'offre
- Pas de tirets cadratin (recruteur voit que c'est genere sinon)
"""

PROFILE = {
    "name":         "Amine Ben Mansour",
    "phone":        "+33 6 60 64 57 83",
    "email":        "mohamedbenpro47@gmail.com",
    "degree":       "MBA Manager de Business Unit, PSB Paris School of Business",
    "current_role": "Business Developer & Recruitment Officer B2B chez Agence 113 / DEFI GROUPE",
    "ca":           "360 000 EUR de CA mensuel",
    "events":       "300+ candidats",
}

_ROLE = {
    "commercial": ["business", "commercial", "account", "sales", "vente", "developp",
                   "bizdev", "partner", "partenariat", "client", "closing", "negoci"],
    "marketing":  ["marketing", "digital", "communication", "brand", "content", "media",
                   "marque", "social", "seo", "campaign"],
    "finance":    ["finance", "tresor", "comptab", "audit", "control", "gestion", "budget",
                   "analyst", "reporting", "risk", "compliance"],
    "hr":         ["rh", "ressources humaines", "recrutement", "hr", "people", "talent",
                   "recruitment", "formation"],
    "supply":     ["supply", "logistique", "achats", "procurement", "operations", "planning"],
    "tech":       ["data", "it", "tech", "informatique", "systeme", "engineer", "developpeur",
                   "software", "erp"],
}

# Donnees marche pays (pour personnaliser le contexte)
_COUNTRY_CONTEXT = {
    "chine":     ("Shanghai et la Chine restent le 1er marche e-commerce mondial avec 3 trillions USD",
                  "Mes notions de chinois et ma comprehension des codes business asiatiques accelereront mon integration."),
    "japon":     ("Le Japon, 3e economie mondiale, exige rigueur et long-termisme dans la relation client",
                  "Mon serieux et ma capacite a construire des relations sur la duree correspondent a la culture business locale."),
    "coree":     ("La Coree du Sud est un hub strategique pour l'innovation et l'export en Asie",
                  "Mon ouverture aux marches asiatiques et ma rigueur seront un atout immediat."),
    "singapour": ("Singapour est la porte d'entree de l'ASEAN et un hub financier mondial",
                  "Mon profil multilingue et international correspond directement a l'ecosysteme local."),
    "etats-unis":("Le marche americain reste le 1er PIB mondial et exige une approche orientee resultats",
                  "Mon experience de gestion d'objectifs CA mensuels me prepare directement a vos exigences."),
    "canada":    ("Le Canada offre un acces strategique au marche nord-americain",
                  "Mon bilinguisme francais/anglais est un avantage immediat sur ce marche."),
    "mexique":   ("Le Mexique est le 1er hub manufacturier des Ameriques et 2e marche d'Amerique latine",
                  "Mon espagnol intermediaire facilitera mes echanges avec les equipes et clients locaux."),
    "bresil":    ("Le Bresil represente la 1ere economie d'Amerique latine, marche cle pour la francophonie",
                  "Mon adaptabilite culturelle et mes acquis sur les marches multiculturels sont un atout direct."),
    "emirats":   ("Dubai concentre les sieges regionaux Moyen-Orient et est un hub du commerce global",
                  "Arabophone natif, je maitrise les codes commerciaux essentiels pour reussir dans le Golfe."),
    "arabie":    ("L'Arabie saoudite represente 25% du PIB du Moyen-Orient et investit massivement (Vision 2030)",
                  "Mon arabe natif et ma comprehension des codes locaux sont des avantages strategiques."),
    "qatar":     ("Le Qatar reste un acteur strategique du Golfe avec un fort dynamisme post-2022",
                  "Mon arabe natif facilitera la creation de relations de confiance avec vos partenaires locaux."),
    "espagne":   ("L'Espagne est la 4e economie europeenne et un pivot vers l'Amerique latine",
                  "Mon espagnol intermediaire me permettra d'etre operationnel des le premier jour."),
    "australie": ("L'Australie est un marche mature et porte d'entree vers l'Asie Pacifique",
                  "Mon profil international et ma capacite a operer en autonomie correspondent au contexte local."),
}


def _role_type(titre: str) -> str:
    t = titre.lower()
    for role, kw in _ROLE.items():
        if any(k in t for k in kw):
            return role
    return "commercial"


def _country_context(pays: str) -> tuple:
    p = pays.lower()
    for country, (market, lang) in _COUNTRY_CONTEXT.items():
        if country in p:
            return market, lang
    return ("", "")


def _what_i_bring(role: str, titre: str, entreprise: str) -> str:
    """Ce que je vais apporter concretement, par type de poste."""
    if role == "commercial":
        return (
            f"Concretement, je vous apporte trois leviers immediats : 1) une capacite a closer "
            f"des deals B2B prouvee par {PROFILE['ca']} en cours, 2) la maitrise des outils CRM "
            f"(HubSpot, Sales Navigator) pour structurer votre pipeline des le premier mois, "
            f"3) une approche multiculturelle pour adapter votre discours commercial aux specificites "
            f"locales."
        )
    if role == "marketing":
        return (
            f"Concretement, je vous apporte : 1) une experience de gestion de projets digitaux "
            f"pour clients internationaux depuis Lisbonne, 2) la maitrise des leviers de visibilite "
            f"et de conversion (Community Management chez GROW 360), 3) une capacite a operer dans "
            f"des environnements multiculturels avec resultats mesurables."
        )
    if role == "finance":
        return (
            f"Concretement, je vous apporte : 1) une rigueur analytique formee en MBA et appliquee "
            f"a la gestion d'une activite a 360KEUR/mois, 2) la capacite a structurer du reporting "
            f"clair pour les decideurs, 3) un sens commercial qui complete utilement les profils finance "
            f"purs sur les sujets d'arbitrage."
        )
    if role == "hr":
        return (
            f"Concretement, je vous apporte : 1) une experience operationnelle de recrutement "
            f"({PROFILE['events']} candidats geres), 2) une double competence RH/business rare "
            f"qui facilite le dialogue avec les managers, 3) une capacite a operer en autonomie sur "
            f"des process complets de A a Z."
        )
    return (
        f"Concretement, je vous apporte rigueur operationnelle, autonomie acquise a l'international "
        f"(Lisbonne) et capacite a livrer des resultats mesurables dans des environnements exigeants."
    )


def _company_para(entreprise: str, secteur: str, pays: str, description: str) -> str:
    """Phrase qui montre que j'ai compris le contexte de l'entreprise et de l'offre."""
    pieces = []

    secteur_clean = secteur.strip() if secteur and secteur not in ("N/A", "") else ""
    if secteur_clean:
        pieces.append(f"votre positionnement sur le secteur {secteur_clean.lower()}")

    market, _ = _country_context(pays)
    if market:
        pieces.append(market.lower())

    if not pieces and description:
        # Fallback : utiliser les premiers mots de la description
        snippet = description.strip()[:140].rsplit(" ", 1)[0]
        if snippet:
            return (
                f"Votre mission, telle que vous la decrivez ('{snippet}...'), correspond "
                f"directement a mon ambition : creer de la valeur dans un environnement international exigeant."
            )

    if pieces:
        ctx = " et ".join(pieces)
        return (
            f"Votre developpement chez {entreprise}, dans un contexte ou {ctx}, correspond "
            f"precisement a l'experience que je cherche a construire pour la suite de ma carriere."
        )

    return (
        f"Votre presence chez {entreprise} et le contexte international de cette mission "
        f"correspondent precisement au type d'environnement ou je cree le plus de valeur."
    )


def _hook(role: str, titre: str, entreprise: str) -> str:
    """Hook d'accroche : court, pose XP intl + MBA, dit ce que j'apporte au poste."""
    poste = titre.strip() or "ce poste"
    return (
        f"Apres une experience de Business Development B2B en France ({PROFILE['ca']}) "
        f"et de gestion de projets internationaux depuis Lisbonne, je termine actuellement mon "
        f"MBA Manager de Business Unit a PSB Paris School of Business avec d'excellents retours "
        f"de mes encadrants. C'est dans cette continuite que je postule au poste de {poste} "
        f"chez {entreprise}, ou je suis convaincu de pouvoir creer de la valeur des le premier mois."
    )


def generate(offer: dict) -> str:
    """Lettre de motivation complete (texte brut, mise en page geree par le PDF)."""
    titre       = offer.get("titre", "le poste propose")
    entreprise  = offer.get("entreprise", "votre entreprise")
    pays        = offer.get("pays", "")
    duree       = offer.get("duree", 12)
    secteur     = offer.get("secteur", "")
    description = offer.get("description", "")

    role        = _role_type(titre)
    hook        = _hook(role, titre, entreprise)
    company     = _company_para(entreprise, secteur, pays, description)
    bring       = _what_i_bring(role, titre, entreprise)
    _, lang     = _country_context(pays)

    pays_str  = f"en {pays}" if pays and pays not in ("N/A", "") else "a l'international"
    duree_str = f"{duree} mois" if duree else "la duree prevue"

    paras = [
        "Madame, Monsieur,",
        hook,
        company,
        bring,
    ]
    if lang:
        paras.append(lang)

    paras.append(
        f"Cette mission de {duree_str} {pays_str} represente exactement le type de defi "
        f"dans lequel j'investis pleinement. Je suis disponible pour echanger des que vous le souhaiterez."
    )
    paras.append(
        f"Cordialement,\n{PROFILE['name']}\n{PROFILE['phone']} | {PROFILE['email']}"
    )

    return "\n\n".join(paras)


def generate_short_message(offer: dict) -> str:
    """Message court (6 lignes max) accompagnant la candidature."""
    titre      = offer.get("titre", "le poste")
    entreprise = offer.get("entreprise", "votre entreprise")
    role       = _role_type(titre)

    if role == "commercial":
        bring = "closer des deals B2B (360KEUR de CA mensuel actuellement)"
    elif role == "marketing":
        bring = "executer des campagnes digitales multiculturelles avec ROI mesurable"
    elif role == "finance":
        bring = "structurer du reporting financier clair et orient business"
    elif role == "hr":
        bring = "piloter des process de recrutement de A a Z (300+ candidats geres)"
    else:
        bring = "livrer des resultats concrets en autonomie a l'international"

    return (
        f"Bonjour,\n"
        f"Je vous adresse ma candidature pour le poste de {titre} chez {entreprise}.\n"
        f"Diplome MBA Business Unit (PSB Paris) avec experience internationale (Lisbonne) et "
        f"actuellement Business Developer B2B en France.\n"
        f"Je peux vous apporter immediatement la capacite a {bring}.\n"
        f"Vous trouverez en piece jointe mon CV et ma lettre de motivation.\n"
        f"Disponible pour un echange a votre convenance.\n"
        f"Cordialement, {PROFILE['name']} ({PROFILE['phone']})"
    )
