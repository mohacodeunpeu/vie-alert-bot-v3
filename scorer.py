"""
Scoring des offres VIE /100 — mode sniper.
Score = role_fit (0-40) + pays (0-30) + industrie (0-30) + mission_fit bonus (0-10), cap 100.
Seuils :
  >= 70 : auto-candidature (sniper)
  55-69 : log pour review manuelle
  <  55 : skip
"""

import logging
from offer_analyzer import detect_industry
from cover_letter import detect_sub_role

logger = logging.getLogger(__name__)

APPLY_THRESHOLD  = 70   # sniper : auto-apply
REVIEW_THRESHOLD = 55   # log only, review possible


# ─── Fit rôle ────────────────────────────────────────────────────────────────

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


# ─── Pays ────────────────────────────────────────────────────────────────────

_COUNTRY_TIERS = {
    30: ["dubai", "emirat", "singapour", "hong kong", "new york", "san francisco",
         "tokyo", "japon"],
    27: ["canada", "toronto", "montreal", "vancouver", "australie", "sydney",
         "melbourne", "seoul", "coree"],
    25: ["etats-unis", "usa", "chicago", "boston", "los angeles", "miami",
         "arabie", "qatar", "abu dhabi"],
    22: ["shanghai", "beijing", "chine", "inde", "mumbai", "bangalore",
         "new delhi", "amsterdam", "suisse"],
    18: ["mexique", "mexico", "bresil", "sao paulo", "colombie", "bogota",
         "chili", "lima", "perou", "argentine"],
    15: ["vietnam", "ho chi minh", "hanoi", "thaïlande", "bangkok",
         "malaisie", "kuala lumpur", "indonesie", "jakarta", "philippines"],
    12: ["turquie", "istanbul", "pakistan", "nigeria"],
}


def _country_score(pays: str, ville: str = "") -> int:
    text = f"{pays} {ville}".lower()
    for score, keywords in sorted(_COUNTRY_TIERS.items(), reverse=True):
        if any(kw in text for kw in keywords):
            return score
    return 10


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


# ─── Mission matching ─────────────────────────────────────────────────────────
# Missions reelles d'Amine : si l'offre les mentionne -> bonus 0-10 pts

_ROLE_MISSIONS = {
    "business_dev": [
        "prospection", "pipeline", "closing", "partenariat", "b2b",
        "portefeuille client", "cycle commercial", "negociation", "sales navigator",
        "acquisition client", "hunting", "crm", "business development",
    ],
    "key_account": [
        "compte cle", "grand compte", "key account", "portefeuille", "business review",
        "plan de compte", "upsell", "cross-sell", "fidelisation", "negociation",
        "interlocuteur decisionnaire",
    ],
    "financial_analyst": [
        "budget", "forecast", "reporting", "consolidation", "variance", "ecart",
        "kpi", "tableau de bord", "controle de gestion", "rentabilite",
        "business plan", "p&l", "analyse financiere", "suivi mensuel",
    ],
    "product_marketing": [
        "brief", "positionnement", "go-to-market", "gtm", "lancement", "pricing",
        "brand", "campagne", "strategie produit", "cycle de vie", "trade marketing",
        "coordination", "brief agence",
    ],
    "digital_marketing": [
        "sea", "seo", "acquisition", "campagne digitale", "kpi", "roas", "roi",
        "landing page", "a/b test", "analytics", "google ads", "meta ads",
        "community", "engagement", "contenu", "conversion",
    ],
    "data_analyst": [
        "sql", "python", "power bi", "tableau", "dashboard",
        "reporting", "insight", "recommandation", "visualisation",
    ],
    "purchasing": [
        "appel d'offres", "sourcing", "fournisseur", "negociation", "contrat",
        "categorie", "tco", "benchmark", "mise en concurrence",
    ],
    "sales": [
        "vente", "objectif commercial", "chiffre d'affaires", "quota",
        "prospection", "closing", "relation client", "fidelisation",
    ],
    "hr": [
        "recrutement", "sourcing", "entretien", "onboarding", "marque employeur",
        "talent", "formation", "candidat", "integration",
    ],
    "generic": [
        "autonomie", "rigueur", "resultats", "equipe", "projet", "international",
    ],
}


def _mission_score(description: str, role: str) -> tuple:
    """Bonus 0-10 + liste des missions matchees."""
    desc     = (description or "").lower()
    missions = _ROLE_MISSIONS.get(role, _ROLE_MISSIONS["generic"])
    matched  = [m for m in missions if m in desc]
    ratio    = len(matched) / max(len(missions), 1)

    if ratio >= 0.35:   score = 10
    elif ratio >= 0.20: score = 7
    elif ratio >= 0.10: score = 4
    elif ratio >= 0.05: score = 2
    else:               score = 0

    return score, matched[:5]


# ─── Fonction principale ──────────────────────────────────────────────────────

def score_offer(offer: dict) -> dict:
    """
    Retourne {
        "total": int (0-100),
        "role_fit": int,
        "country": int,
        "industry": int,
        "mission_fit": int,
        "matched_missions": list,
        "role": str,
        "industry_det": str,
        "should_apply": bool,   # >= APPLY_THRESHOLD (80)
        "should_review": bool,  # REVIEW_THRESHOLD <= total < APPLY_THRESHOLD
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

    role_pts     = _ROLE_SCORES.get(role, 16)
    country_pts  = _country_score(pays, ville)
    industry_pts = _INDUSTRY_SCORES.get(industry, 14)
    mission_pts, matched = _mission_score(description, role)

    total = min(100, role_pts + country_pts + industry_pts + mission_pts)

    result = {
        "total":            total,
        "role_fit":         role_pts,
        "country":          country_pts,
        "industry":         industry_pts,
        "mission_fit":      mission_pts,
        "matched_missions": matched,
        "role":             role,
        "industry_det":     industry,
        "should_apply":     total >= APPLY_THRESHOLD,
        "should_review":    REVIEW_THRESHOLD <= total < APPLY_THRESHOLD,
    }

    status = "APPLY" if result["should_apply"] else ("REVIEW" if result["should_review"] else "SKIP")
    logger.info(
        "[SCORE] %s | %s | %s -> %d/100 "
        "(role=%d, pays=%d, ind=%d, mission=%d [%s]) | %s",
        offer.get("titre", "?")[:40],
        pays, role, total,
        role_pts, country_pts, industry_pts, mission_pts,
        ",".join(matched[:2]) or "-",
        status,
    )

    return result
