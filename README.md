# Bot VIE — Alertes Discord automatiques

Scrape Business France toutes les 30-60 secondes et envoie les nouvelles offres VIE dans Discord.

---

## Installation locale

```bash
pip install -r requirements.txt
python main.py
```

---

## Deploiement Railway

### 1. Pousser sur GitHub

```bash
git init
git add .
git commit -m "bot VIE v3"
git branch -M main
git remote add origin https://github.com/TON_USERNAME/vie-alert-bot.git
git push -u origin main
```

### 2. Creer le projet Railway

1. railway.app → Login with GitHub
2. New Project → Deploy from GitHub repo
3. Selectionner le repo
4. Railway detecte le Procfile automatiquement
5. Deploy Now

### 3. Verifier les logs Railway

```
[2026-04-27 13:00:00] INFO __main__ - Bot VIE demarre
[2026-04-27 13:00:02] INFO __main__ - [CYCLE #1] Debut @ 13:00:02
[2026-04-27 13:00:05] INFO __main__ - [SCRAPER] Total: 87 offres recuperees
[2026-04-27 13:00:07] INFO __main__ - [CYCLE #1] Termine en 5s | Envoyes: 3 | Total vus: 3
```

Le message "Bot VIE demarre" apparait aussi dans Discord.

---

## Structure

| Fichier | Role |
|---|---|
| config.py | Webhook, intervalle, URLs |
| scraper.py | Scraping API + fallback HTML |
| discord_notif.py | Embeds Discord + retry |
| main.py | Boucle principale + logs |
| seen_offers.json | IDs deja envoyes |
| bot.log | Logs fichier (5Mo max) |

---

## Fonctionnement

1. Scrape l'API sur 4 pages (0 a 3)
2. Parse chaque offre → ID unique = `id + "_" + date_publication`
3. Compare avec `seen_offers.json`
4. Envoie les nouvelles sur Discord
5. Sauvegarde les IDs → pas de doublons
6. Attend 30-60s (aleatoire) → recommence

---

## Depannage

**Bot tourne mais 0 offres** : l'API requiert une authentification. Voir `login.py` dans le dossier `vie-alert-bot/` pour generer un token.

**Webhook ne fonctionne pas** : verifier l'URL dans `config.py`. Recreer le webhook dans Discord → Parametres salon → Integrations → Webhooks.

**Erreur pip sur Railway** : verifier que `requirements.txt` ne contient QUE les packages (requests, beautifulsoup4, lxml).
