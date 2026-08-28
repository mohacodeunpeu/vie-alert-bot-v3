import os

# Webhook Discord : UNIQUEMENT via variable d'environnement / secret GitHub.
# L'ancien webhook code en dur a ete retire (repo public = webhook compromis).
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

MIN_INTERVAL = int(os.environ.get("MIN_INTERVAL", "30"))
MAX_INTERVAL = int(os.environ.get("MAX_INTERVAL", "60"))

SEEN_FILE = "seen_offers.json"
LOG_FILE  = "bot.log"

BASE_URL = "https://mon-vie-via.businessfrance.fr"
API_URL  = "https://mon-vie-via.businessfrance.fr/api/offres/recherche"
HTML_URL = "https://mon-vie-via.businessfrance.fr/offres/recherche"

API_PARAMS = {
    "missionsTypesIds": "VIE",
    "size": 100,
}

MAX_PAGES = 4
