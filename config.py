import os

# Webhook Discord : priorite a la variable d'environnement DISCORD_WEBHOOK_URL
# (secret GitHub Actions). Le fallback est l'ancien webhook, a regenerer car
# il a ete expose en clair dans un repo public.
DISCORD_WEBHOOK_URL = os.environ.get(
    "DISCORD_WEBHOOK_URL",
    "https://discord.com/api/webhooks/1498293144863903886/tYUYXnNqqB7Myc9nZ_6fnjcAHiazgijciPJFzCYH6oszhb31yfp1F1H-1WyXMD0cdyYp",
)

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
