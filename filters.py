"""
Filtres d'eligibilite pour l'auto-candidature.
- Discord notifs : pas filtres (toutes les nouvelles offres notifiees)
- Auto-apply    : filtres ici (secteur + region)
Reduit naturellement le volume de candidatures et le risque de ban
tout en gardant la pertinence.
"""

import logging

logger = logging.getLogger(__name__)


# ─── Mots-cles secteurs cibles (commerce, finance, marketing) ────────────────
# Match dans titre ou secteur. Insensible a la casse.
SECTOR_KEYWORDS = [
    # Commerce / Business / Vente
    "business", "commercial", "commerce", "account", "sales", "vente",
    "developp", "bizdev", "partner", "partenariat", "client", "closing",
    "negoci", "trade", "key account",
    # Finance / Comptabilite / Audit
    "finance", "financ", "audit", "comptab", "accounting", "control", "controll",
    "tresor", "treasury", "budget", "analyst", "analytic", "reporting",
    "risk", "compliance", "purchas", "buyer", "achat", "category",
    # Marketing / Communication / Brand
    "marketing", "digital", "brand", "communication", "content", "media",
    "marque", "social", "seo", "campaign", "produit", "product",
    "trade marketing", "growth",
]

# ─── Pays/regions a EXCLURE (Afrique + Europe) ────────────────────────────────
EXCLUDED_COUNTRIES = {
    # Afrique (toutes regions)
    "afrique", "afrique du sud", "south africa", "maroc", "tunisie",
    "algerie", "algérie", "algeria", "egypte", "égypte", "egypt",
    "senegal", "sénégal", "cote d'ivoire", "côte d'ivoire", "ivory coast",
    "kenya", "ghana", "cameroun", "cameroon", "ethiopie", "éthiopie",
    "congo", "gabon", "madagascar", "mauritius", "ile maurice", "île maurice",
    "nigeria", "ouganda", "uganda", "tanzanie", "tanzania", "rwanda",
    "burkina faso", "mali", "niger", "tchad", "chad", "soudan", "sudan",
    "mozambique", "angola", "zambie", "zambia", "zimbabwe", "namibie", "namibia",
    "botswana", "lesotho", "swaziland", "eswatini", "guinee", "guinée",
    "guinee equatoriale", "guinée équatoriale", "togo", "benin", "bénin",
    "djibouti", "somalie", "somalia", "erythree", "érythrée", "eritrea",
    "libye", "libya", "mauritanie", "mauritania",
    # Europe (sauf ES/PT/CH/UK — gardes eligibles car bien payes ou avantage linguistique)
    # NOTE : Espagne + Portugal = espagnol intermediaire + experience Lisbonne
    # NOTE : Suisse + UK = VIE 2500-4000€/mois, meilleurs salaires Europe
    "france", "allemagne", "germany", "italie", "italy",
    "belgique", "belgium", "pays-bas", "pays bas", "netherlands",
    "luxembourg", "autriche", "austria",
    "danemark", "denmark", "suede", "suède", "sweden", "norvege", "norvège",
    "norway", "finlande", "finland", "irlande", "ireland",
    "pologne", "poland", "republique tcheque", "république tchèque",
    "czech republic", "tcheque", "tchèque", "czechia",
    "hongrie", "hungary", "roumanie", "romania", "bulgarie", "bulgaria",
    "grece", "grèce", "greece", "croatie", "croatia", "serbie", "serbia",
    "slovaquie", "slovakia", "slovenie", "slovénie", "slovenia",
    "ukraine", "russie", "russia", "biélorussie", "bielorussie", "belarus",
    "moldavie", "moldova", "estonie", "estonia", "lettonie", "latvia",
    "lituanie", "lithuania", "malte", "malta", "chypre", "cyprus",
    "islande", "iceland", "monaco", "andorre", "andorra", "saint-marin",
    "san marino", "vatican", "liechtenstein", "albanie", "albania",
    "bosnie", "bosnia", "macedoine", "macédoine", "macedonia",
    "montenegro", "kosovo",
}


MIN_SALARY = 1200  # indemnite minimale EUR/mois (0 = pas de filtre)


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def should_apply(offer: dict) -> tuple[bool, str]:
    """
    Decide si on postule a cette offre.
    Retourne (True, "OK") si on postule, (False, "raison") si on skip.
    """
    titre   = _norm(offer.get("titre"))
    secteur = _norm(offer.get("secteur"))
    pays    = _norm(offer.get("pays"))

    # 1. Region : skip Afrique + Europe (sauf ES/PT/CH/UK)
    if pays:
        for excluded in EXCLUDED_COUNTRIES:
            if excluded in pays:
                return False, f"pays exclu ({pays})"

    # 2. Salaire minimum
    if MIN_SALARY > 0:
        salaire = offer.get("salaire", 0) or 0
        if salaire > 0 and salaire < MIN_SALARY:
            return False, f"salaire trop bas ({salaire}€ < {MIN_SALARY}€)"

    # 3. Secteur : doit matcher commerce/finance/marketing
    haystack = f"{titre} {secteur}"
    if not any(kw in haystack for kw in SECTOR_KEYWORDS):
        return False, f"secteur hors cible (titre={titre[:60]})"

    return True, "OK"
