import json
import logging
import logging.handlers
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path

import config
import discord_notif
import scraper
import auto_apply
import filters

AUTO_APPLY_ENABLED = os.environ.get("AUTO_APPLY", "true").lower() == "true"


def setup_logging() -> None:
    fmt = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s - %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S")
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.handlers.RotatingFileHandler(
            config.LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
        ),
    ]
    for h in handlers:
        h.setFormatter(fmt)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    for h in handlers:
        root.addHandler(h)


logger = logging.getLogger(__name__)


def load_seen() -> set:
    path = Path(config.SEEN_FILE)
    if not path.exists():
        path.write_text("{}", encoding="utf-8")
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return set(data.keys())
        if isinstance(data, list):
            return set(data)
        return set()
    except Exception as e:
        logger.warning("[SEEN] Impossible de lire %s: %s — demarrage a vide", config.SEEN_FILE, e)
        return set()


def save_seen(seen: set, timestamps: dict) -> None:
    try:
        Path(config.SEEN_FILE).write_text(
            json.dumps(timestamps, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as e:
        logger.error("[SEEN] Impossible de sauvegarder: %s", e)


def run() -> None:
    setup_logging()
    logger.info("=" * 55)
    logger.info("Bot VIE demarre")
    logger.info("Intervalle: %d-%ds | Auto-candidature: %s",
                config.MIN_INTERVAL, config.MAX_INTERVAL,
                "ACTIVE" if AUTO_APPLY_ENABLED else "DESACTIVEE")
    logger.info("=" * 55)

    # Pas de spam Discord a chaque restart Railway — on log seulement
    logger.info("[DISCORD] Demarrage silencieux (pas de notif)")

    seen_ids: set    = load_seen()
    timestamps: dict = {k: "" for k in seen_ids}
    logger.info("[SEEN] %d IDs deja connus", len(seen_ids))

    first_run = len(seen_ids) == 0
    cycle = 0

    while True:
        cycle += 1
        t0 = time.time()
        logger.info("[CYCLE #%d] Debut @ %s", cycle, datetime.now().strftime("%H:%M:%S"))

        try:
            offers     = scraper.fetch_offers()
            new_offers = [o for o in offers if o["composite_id"] not in seen_ids]

            logger.info("[CYCLE #%d] %d offres recuperees, %d nouvelles",
                        cycle, len(offers), len(new_offers))

            # Premier demarrage : marquer tout comme vu sans notifier ni postuler
            if first_run and new_offers:
                for offer in new_offers:
                    cid = offer["composite_id"]
                    seen_ids.add(cid)
                    timestamps[cid] = "init"
                save_seen(seen_ids, timestamps)
                first_run = False
                elapsed = round(time.time() - t0, 1)
                logger.info("[CYCLE #%d] Init silencieuse — %d offres existantes marquees | %ss",
                            cycle, len(new_offers), elapsed)
                _wait_next(cycle)
                continue

            sent     = 0
            applied  = 0
            skipped  = 0

            for offer in new_offers:
                # 1. Notifier sur Discord (TOUTES les offres, sans filtre)
                if discord_notif.send_offer(offer):
                    cid = offer["composite_id"]
                    seen_ids.add(cid)
                    timestamps[cid] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    sent += 1
                    save_seen(seen_ids, timestamps)

                # 2. Postuler uniquement si offre cible (filtre intelligent)
                if AUTO_APPLY_ENABLED:
                    ok, reason = filters.should_apply(offer)
                    if not ok:
                        skipped += 1
                        logger.info("[FILTER] Skip apply: %s | %s",
                                    reason, offer.get("titre", "")[:60])
                        continue
                    if auto_apply.apply_offer(offer):
                        applied += 1

            elapsed = round(time.time() - t0, 1)
            logger.info("[CYCLE #%d] Termine en %ss | Discord: %d | Candidatures: %d | Skips: %d | Total vus: %d",
                        cycle, elapsed, sent, applied, skipped, len(seen_ids))

        except KeyboardInterrupt:
            logger.info("Arret demande")
            break
        except Exception as e:
            logger.error("[CYCLE #%d] Erreur inattendue: %s", cycle, e, exc_info=True)
            logger.info("Attente 60s avant de reprendre...")
            try:
                time.sleep(60)
            except KeyboardInterrupt:
                break
            continue

        _wait_next(cycle)

    logger.info("Bot arrete proprement.")


def _wait_next(cycle: int) -> None:
    wait = random.uniform(config.MIN_INTERVAL, config.MAX_INTERVAL)
    logger.info("[CYCLE #%d] Prochain cycle dans %.0fs", cycle, wait)
    try:
        time.sleep(wait)
    except KeyboardInterrupt:
        logger.info("Arret demande")
        raise


def main():
    """Wrapper qui relance run() en cas de crash inattendu."""
    while True:
        try:
            run()
            break  # Sortie propre
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error("[FATAL] Crash inattendu: %s — relance dans 30s", e, exc_info=True)
            time.sleep(30)


if __name__ == "__main__":
    main()
