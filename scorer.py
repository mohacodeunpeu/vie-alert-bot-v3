"""
Scoring des offres VIE /100.
Score = fit_role (40 pts) + pays_strategique (30 pts) + industrie (30 pts)
Seuil candidature : 70
"""

import logging
from offer_analyzer import detect_industry
from cover_letter import detect_sub_role

logger = logging.getLogger(__name__)

APPLY_THRESHOLD = 70


# ─── Fit rôle ────────────────────────────────────────────────────────────────
# Scores calibrés sur le profil Amine (commerce/finance/marketing Bac+5)

_ROLE_SCORES = {
    "business_dev":      40,
    "key_account":       38,
    "financial_analyst": 37,
    "product_marketing": 35,
    "digital_marketing": 30,
    "data_analyst":      28,
    "purchasing":        27,
    "sales":             26,
    "hr":                18,
    "generic":           16,
}


# ─── Pays stratégiques ───────────────────────────────────────────────────────
# Critères : hub économique, emploi/visa, salaire VIE, réseau

_COUNTRY_TIERS = {
    # Tier 1 — meilleurs hubs mondiau (hub financier, marché +++, forte valeur CV)
    30: ["dubai", "emirat", "singapour", "hong kong", "new york", "san francisco",
         "tokyo", "japon"],
    27: ["canada", "toronto", "montreal", "vancouver", "australie", "sydney",
         "melbourne", "seoul", "coree"],
    25: ["etats-unis", "usa", "chicago", "boston", "los angeles", "miami",
         "arabie", "qatar", "abu dhabi"],
    22: ["shanghai", "beijing", "chine", "inde", "mumbai", "bangalore",
         "new delhi", "amsterdam", "suisse"],  # Suisse incluse (pas dans EXCLUDED)
    18: ["mexique", "mexico", "bresil", "sao paulo", "colombie", "bogota",
         "chili", "lima", "perou", "argentine"],
    15: ["vietnam", "ho chi minh", "hanoi", "thaïlande", "bangkok",
         "malaisie", "kuala lumpur", "indonesie", "jakarta", "philippines"],
    12: ["turquie", "istanbul", "pakistan", "nigeria"],  # Marches moins strategiques
}


def _country_score(pays: str, ville: str = "") -> int:
    text = f"{pays} {ville}".lower()
    for score, keywords in sorted(_COUNTRY_TIERS.items(), reverse=True):
        if any(kw in text for kw in keywords):
            return score
    return 10  # Défaut : pays non répertorié mais éligible


# ─── Industrie ───────────────────────────────────────────────────────────────

_INDUSTRY_SCORES = {
    "luxe":        30,
    "finance":     28,
    "conseil":     26,
    "pharma":      25,
    "tech":        24,
    "energie":     23,
    "agroalim":    22,
    "automotive":  21,
    "retail":      20,
    "telecom":     19,
    "industrie":   18,
    "construction":16,
    "generic":     14,
}


# ─── Fonction principale ─────────────────────────────────────────────────────

def score_offer(offer: dict) -> dict:
    """
    Retourne {
        "total": int (0-100),
        "role_fit": int,
        "country": int,
        "industry": int,
        "role": str,
        "should_apply": bool,
    }
    """
    titre       = offer.get("titre", "")
    description = offer.get("description", "")
    secteur     = offer.get("secteur", "")
    entreprise  = offer.get("entreprise", "")
    pays        = offer.get("pays", "")
    ville       = offer.get("ville", "")

    role     = detect_sub_role(titre, description)
    industry = detect_industry(entreprise, secteur, description)

    role_pts    = _ROLE_SCORES.get(role, 16)
    country_pts = _country_score(pays, ville)
    industry_pts= _INDUSTRY_SCORES.get(industry, 14)

    total = role_pts + country_pts + industry_pts

    result = {
        "total":        total,
        "role_fit":     role_pts,
        "country":      country_pts,
        "industry":     industry_pts,
        "role":         role,
        "industry_det": industry,
        "should_apply": total >= APPLY_THRESHOLD,
    }

    logger.info(
        "[SCORE] %s | %s | %s -> %d/100 (role=%d, pays=%d, ind=%d) | %s",
        offer.get("titre", "?")[:50],
        pays,
        role,
        total,
        role_pts,
        country_pts,
        industry_pts,
        "APPLY" if result["should_apply"] else "SKIP",
    )

    return result
