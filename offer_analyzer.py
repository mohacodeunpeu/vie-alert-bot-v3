"""
Analyseur d'offre VIE.
Extrait : mots-cles ATS, secteur d'industrie, seniorite, profil ideal.
Utilise par cv_generator et cover_letter pour personnaliser profondement.
"""

import re


# ─── Mots-cles techniques / outils / frameworks reconnus ──────────────────────
# Si match dans la description, ils valent la peine d'etre reflectes.
TECH_TOOLS = [
    "hubspot", "salesforce", "pipedrive", "sap", "oracle", "workday",
    "tableau", "power bi", "powerbi", "looker", "qlik", "metabase",
    "excel", "google sheets", "google analytics", "ga4", "tag manager",
    "tmall", "jd.com", "alibaba", "wechat", "weibo", "tiktok",
    "shopify", "magento", "wordpress", "wix", "webflow",
    "facebook ads", "google ads", "linkedin ads", "meta ads",
    "hubspot crm", "linkedin sales navigator", "sales navigator",
    "sql", "python", "vba",
    "canva", "figma", "adobe", "photoshop", "illustrator", "indesign",
    "notion", "asana", "trello", "jira", "monday",
    "slack", "teams", "zoom",
    "zendesk", "freshdesk", "intercom",
    "stripe", "paypal",
    "klaviyo", "mailchimp", "sendgrid",
]

# Secteurs d'industrie (detectes via mots-cles dans l'entreprise / description)
INDUSTRIES = {
    "luxe":       ["luxe", "luxury", "haute couture", "joaillerie", "horlogerie",
                   "skincare", "fragrance", "cosmetics", "premium", "lvmh", "kering",
                   "hermes", "chanel", "dior", "richemont", "loreal", "l'oreal"],
    "pharma":     ["pharma", "pharmaceutic", "laboratoire", "medical", "clinical",
                   "drug", "therapy", "therapeutic", "servier", "sanofi",
                   "novartis", "pfizer", "bayer", "boiron", "ipsen"],
    "automotive": ["automotive", "automobile", "vehicule", "vehicle", "renault",
                   "stellantis", "peugeot", "michelin", "valeo", "faurecia",
                   "plastic omnium", "alstom"],
    "energy":     ["energy", "energie", "petrol", "gaz", "renewable", "solar",
                   "wind", "totalenergies", "engie", "edf", "schneider",
                   "veolia", "suez"],
    "tech":       ["software", "saas", "cloud", "ai", "data center", "fintech",
                   "platform", "engineer", "developer", "developpeur"],
    "retail":     ["retail", "magasin", "store", "boutique", "decathlon",
                   "carrefour", "auchan", "leroy merlin", "fnac", "ikea",
                   "sport", "consumer goods"],
    "finance":    ["bank", "banque", "asset management", "investment", "credit",
                   "bnp", "societe generale", "credit agricole", "axa", "allianz",
                   "amundi", "lazard"],
    "agroalim":   ["food", "beverage", "danone", "nestle", "lactalis", "pernod",
                   "moet", "champagne", "wine", "agroalimentaire"],
    "conseil":    ["consulting", "conseil", "audit", "advisory", "strategy",
                   "deloitte", "kpmg", "ey", "pwc", "mazars", "capgemini",
                   "accenture", "boston consulting", "mckinsey", "bain"],
    "industrie":  ["manufacturing", "production", "factory", "usine", "industrial",
                   "thales", "safran", "airbus", "dassault"],
    "construction":["construction", "btp", "vinci", "bouygues", "eiffage", "spie"],
    "telecom":    ["telecom", "orange", "sfr", "bouygues telecom", "operator"],
}


def detect_industry(entreprise: str, secteur: str, description: str) -> str:
    """Renvoie le secteur d'industrie detecte ou 'generic'."""
    txt = f"{entreprise} {secteur} {description}".lower()
    # Score chaque industrie par nombre de matches
    best = ("generic", 0)
    for ind, kws in INDUSTRIES.items():
        score = sum(1 for kw in kws if kw in txt)
        if score > best[1]:
            best = (ind, score)
    return best[0]


def extract_tools(description: str) -> list:
    """Extrait les outils techniques mentionnes dans l'offre."""
    if not description:
        return []
    txt = description.lower()
    found = []
    for tool in TECH_TOOLS:
        if tool in txt and tool not in found:
            found.append(tool)
    return found


# ─── Mots-cles 'metier' a extraire (verbes d'action + concepts) ───────────────
# Termes specifiques qui valent la peine d'etre reflectes dans le CV/lettre.
ACTION_KEYWORDS = [
    # Marketing
    "lancement", "positionnement", "pricing", "branding", "campagne", "campaign",
    "trade marketing", "shopper", "go-to-market", "gtm", "content", "seo", "sea",
    "social media", "community", "influence", "ugc", "newsletter",
    # Commerce / Sales
    "prospection", "negociation", "closing", "key account", "kam", "partenariat",
    "channel", "indirect", "direct sales", "b2b", "b2c", "saas",
    "cold calling", "outbound", "inbound", "lead", "pipeline",
    # Finance / Analytics
    "budget", "forecast", "p&l", "ebitda", "roi", "cashflow", "kpi",
    "reporting", "dashboard", "modeling", "analyse",
    "controle de gestion", "audit", "cloture", "consolidation",
    # Achats / Ops
    "sourcing", "rfp", "rfq", "supplier", "fournisseur", "tco",
    "procurement", "categorie", "category management",
    # Pharma / Med
    "regulatory", "compliance", "clinical", "essai", "amm",
    # General
    "stakeholder", "cross-functional", "agile", "scrum", "transformation",
]


def extract_action_keywords(description: str) -> list:
    """Extrait les mots-cles d'action mentionnes."""
    if not description:
        return []
    txt = description.lower()
    found = []
    for kw in ACTION_KEYWORDS:
        if kw in txt and kw not in found:
            found.append(kw)
    return found[:6]


# ─── Detection de seniorite demandee ──────────────────────────────────────────

def detect_seniority(description: str) -> str:
    """junior / mid / senior selon les annees d'experience demandees."""
    if not description:
        return "junior"
    txt = description.lower()
    # Recherche "X annees d'experience" / "X years"
    m = re.search(r"(\d+)\s*(?:a|ans|annees|years)", txt)
    if m:
        n = int(m.group(1))
        if n >= 5:
            return "senior"
        if n >= 3:
            return "mid"
        return "junior"
    if any(w in txt for w in ["senior", "experimente", "confirme"]):
        return "mid"
    if any(w in txt for w in ["junior", "graduate", "debutant", "premier emploi", "vie"]):
        return "junior"
    return "junior"


# ─── Bullet enrichi : injecte un mot-cle dans un bullet existant ──────────────

def enrich_bullet(bullet: str, keywords: list) -> str:
    """
    Si un mot-cle de l'offre est lie au sens du bullet, l'ajoute en parenthese.
    Ne MENT PAS : ajoute uniquement si coherent.
    """
    if not keywords:
        return bullet
    bl = bullet.lower()

    # Mapping coherent : si le bullet mentionne X et l'offre demande Y similaire,
    # on enrichit. Regles simples mais efficaces.
    enrich_map = [
        (["crm", "hubspot"],            ["hubspot", "salesforce", "pipedrive"]),
        (["pipeline", "prospection"],   ["pipeline", "outbound", "inbound", "lead"]),
        (["negociation", "closing"],    ["negociation", "closing"]),
        (["reporting", "dashboard"],    ["dashboard", "reporting", "kpi"]),
        (["evenement", "evenements"],   ["sourcing", "stakeholder"]),
        (["digital", "ux"],             ["seo", "sea", "campaign", "campagne", "social media"]),
        (["reseaux sociaux"],           ["community", "social media", "content"]),
    ]

    for triggers, candidates in enrich_map:
        if any(t in bl for t in triggers):
            for k in keywords:
                if any(c in k.lower() for c in candidates) and k.lower() not in bl:
                    return bullet.rstrip(".") + f" (incl. {k})."
    return bullet


def analyze(offer: dict) -> dict:
    """Analyse complete de l'offre. Renvoie un dict d'attributs utiles."""
    titre       = offer.get("titre", "")
    entreprise  = offer.get("entreprise", "")
    secteur     = offer.get("secteur", "")
    description = offer.get("description", "")
    pays        = offer.get("pays", "")

    return {
        "industry":     detect_industry(entreprise, secteur, description),
        "tools":        extract_tools(description),
        "actions":      extract_action_keywords(description),
        "seniority":    detect_seniority(description),
        "titre":        titre,
        "entreprise":   entreprise,
        "pays":         pays,
        "secteur":      secteur,
        "description":  description,
    }
