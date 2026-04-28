"""
Generateur de lettres de motivation personnalisees pour les VIE.
S'adapte automatiquement au secteur, pays, et type de poste.
"""

PROFILE = {
    "name":         "Amine Ben Mansour",
    "phone":        "+33 6 60 64 57 83",
    "email":        "mohamedbenpro47@gmail.com",
    "degree":       "MBA Manager de Business Unit — PSB Paris School of Business",
    "current_role": "Business Developer & Recruitment Officer B2B chez Agence 113 / DEFI GROUPE",
    "ca":           "~360 000€ CA mensuel",
    "events":       "300+ candidats",
    "languages":    "français, anglais, arabe (natifs/courant), espagnol (intermédiaire), notions de chinois",
}

_ROLE = {
    "commercial": ["business", "commercial", "account", "sales", "vente", "développ", "bizdev",
                   "partner", "partenariat", "client", "closing", "négoci"],
    "marketing":  ["marketing", "digital", "communication", "brand", "content", "média", "marque",
                   "social", "seo", "campaign"],
    "finance":    ["finance", "trésor", "comptab", "audit", "control", "gestion", "budget",
                   "analyst", "reporting", "risk", "compliance"],
    "hr":         ["rh", "ressources humaines", "recrutement", "hr", "people", "talent",
                   "recruitment", "formation"],
    "supply":     ["supply", "logistique", "achats", "procurement", "opérations", "planning",
                   "warehouse", "entrepôt"],
    "tech":       ["data", "it", "tech", "informatique", "système", "engineer", "développeur",
                   "software", "erp", "crm analyst"],
}

_LANG_COUNTRY = {
    "espagne":   "Mon espagnol intermédiaire facilitera dès le premier jour mes échanges avec les équipes locales.",
    "mexique":   "Mon espagnol intermédiaire et ma capacité d'adaptation seront des atouts concrets sur ce marché.",
    "colombie":  "Mon espagnol intermédiaire sera directement utile pour opérer sur ce marché hispanophone.",
    "chili":     "Mon espagnol intermédiaire me permettra de m'intégrer rapidement dans l'environnement local.",
    "argentine": "Mon espagnol intermédiaire facilitera mes relations avec les partenaires et clients argentins.",
    "maroc":     "Arabophone natif, je comprends les codes culturels et commerciaux du marché marocain.",
    "tunisie":   "Mon arabe natif et ma familiarité avec le monde maghrébin sont un avantage immédiat.",
    "algérie":   "Arabophone natif, je saurai naviguer dans les codes culturels et commerciaux algériens.",
    "émirats":   "Mon arabe natif est un atout stratégique pour tisser des relations de confiance dans le Golfe.",
    "arabie":    "Arabophone natif, je maîtrise les codes culturels essentiels à la réussite sur ce marché.",
    "qatar":     "Mon arabe natif facilitera les échanges avec les partenaires locaux dès mon arrivée.",
    "liban":     "Arabophone natif, je m'intègrerai naturellement dans l'environnement libanais.",
    "chine":     "Mes notions de chinois et mon ouverture aux marchés asiatiques complèteront mon adaptation.",
}


def _role_type(titre: str) -> str:
    t = titre.lower()
    for role, kw in _ROLE.items():
        if any(k in t for k in kw):
            return role
    return "commercial"


def _role_para(role: str, entreprise: str) -> str:
    if role == "commercial":
        return (
            f"Mon expérience actuelle en Business Development B2B chez Agence 113 / DEFI GROUPE — "
            f"où je gère des partenariats stratégiques, conduis des négociations complexes et close des accords "
            f"avec un CA mensuel de {PROFILE['ca']} — correspond directement aux missions que vous décrivez. "
            f"Je pilote mon activité via HubSpot CRM et LinkedIn Sales Navigator au quotidien."
        )
    if role == "marketing":
        return (
            f"Mon expérience en Community Management (GROW 360, Paris) et en gestion de projets digitaux "
            f"pour clients internationaux depuis Lisbonne m'a permis de maîtriser les leviers de visibilité, "
            f"d'engagement et de conversion dans des contextes multiculturels — applicable immédiatement chez {entreprise}."
        )
    if role == "finance":
        return (
            f"Formé au pilotage de business unit et à l'analyse de la performance financière dans le cadre de mon MBA, "
            f"j'ai développé une rigueur analytique ancrée dans la pratique terrain. Mon expérience de gestion "
            f"opérationnelle avec des indicateurs à fort enjeu me prépare à contribuer efficacement à vos équipes finance."
        )
    if role == "hr":
        return (
            f"J'ai orchestré des processus de recrutement à grande échelle : organisation d'événements réunissant "
            f"{PROFILE['events']}, animation de sessions de sourcing, coordination du service POEI. "
            f"Cette double compétence RH / business est rare et directement applicable dans le contexte de {entreprise}."
        )
    return (
        f"Mes expériences en développement commercial B2B, gestion de projets internationaux (Lisbonne) "
        f"et management d'événements à grande échelle ({PROFILE['events']}) m'ont appris à opérer "
        f"avec autonomie et orientation résultats dans des environnements exigeants."
    )


def _lang_angle(pays: str) -> str:
    p = pays.lower()
    for country, phrase in _LANG_COUNTRY.items():
        if country in p:
            return f"\n\n{phrase}"
    return ""


def generate(offer: dict) -> str:
    titre     = offer.get("titre", "le poste proposé")
    entreprise = offer.get("entreprise", "votre entreprise")
    pays      = offer.get("pays", "")
    duree     = offer.get("duree", 12)

    role      = _role_type(titre)
    role_para = _role_para(role, entreprise)
    lang      = _lang_angle(pays)

    pays_str  = f"en {pays}" if pays and pays not in ("N/A", "") else "à l'international"
    duree_str = f"{duree} mois" if duree else "la durée prévue"

    return (
        f"Madame, Monsieur,\n\n"
        f"Diplômé d'un MBA Manager de Business Unit (PSB Paris School of Business), "
        f"je vous adresse ma candidature pour le poste de {titre} en VIE au sein de {entreprise}.\n\n"
        f"{role_para}{lang}\n\n"
        f"En parallèle, j'ai géré des projets digitaux pour des clients internationaux depuis Lisbonne — "
        f"une expérience qui m'a appris à m'adapter rapidement, à travailler en autonomie totale et à livrer "
        f"des résultats concrets. C'est exactement l'état d'esprit que j'apporte à cette mission "
        f"de {duree_str} {pays_str}.\n\n"
        f"Je maîtrise les outils qui permettent d'être opérationnel immédiatement : HubSpot CRM, "
        f"LinkedIn Sales Navigator, Google Suite. Mes 5 langues ({PROFILE['languages']}) renforcent "
        f"ma capacité à créer de la valeur dans des marchés internationaux.\n\n"
        f"Disponible dès que nécessaire, je reste à votre disposition pour tout échange.\n\n"
        f"Cordialement,\n"
        f"{PROFILE['name']}\n"
        f"{PROFILE['phone']} | {PROFILE['email']}"
    )
