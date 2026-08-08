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
import scorer
import apply_log

AUTO_APPLY_ENABLED = os.environ.get("AUTO_APPLY", "true").lower() == "true"
MAX_DAILY_APPLIES  = 15  # 15 candidatures max / jour
# Budget temps d'un run (GitHub Actions). 0 = boucle infinie (worker classique).
MAX_RUNTIME_SEC    = int(os.environ.get("MAX_RUNTIME_SEC", "0"))
_START_TS = time.time()


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


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _can_apply_today(daily_applies: dict) -> bool:
    return daily_applies.get(_today(), 0) < MAX_DAILY_APPLIES


def _increment_daily(daily_applies: dict) -> None:
    today = _today()
    daily_applies[today] = daily_applies.get(today, 0) + 1


def run() -> None:
    setup_logging()
    logger.info("=" * 55)
    logger.info("Bot VIE demarre — mode SNIPER")
    logger.info("Seuil auto-apply: %d | Review: %d-%d | Max/jour: %d",
                scorer.APPLY_THRESHOLD, scorer.REVIEW_THRESHOLD,
                scorer.APPLY_THRESHOLD - 1, MAX_DAILY_APPLIES)
    logger.info("Intervalle: %d-%ds | Auto-candidature: %s",
                config.MIN_INTERVAL, config.MAX_INTERVAL,
                "ACTIVE" if AUTO_APPLY_ENABLED else "DESACTIVEE")
    logger.info("=" * 55)

    logger.info("[DISCORD] Demarrage silencieux (pas de notif)")

    seen_ids: set    = load_seen()
    timestamps: dict = {k: "" for k in seen_ids}
    logger.info("[SEEN] %d IDs deja connus", len(seen_ids))

    first_run      = len(seen_ids) == 0
    cycle          = 0
    daily_applies: dict = {}   # {"2026-05-01": 2, ...}

    while True:
        cycle += 1
        t0 = time.time()
        logger.info("[CYCLE #%d] Debut @ %s | Applies aujourd'hui: %d/%d",
                    cycle, datetime.now().strftime("%H:%M:%S"),
                    daily_applies.get(_today(), 0), MAX_DAILY_APPLIES)

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

            sent    = 0
            applied = 0
            reviewed = 0
            skipped  = 0

            for offer in new_offers:
                # 1. Notifier sur Discord (TOUTES les offres, sans filtre)
                if discord_notif.send_offer(offer):
                    cid = offer["composite_id"]
                    seen_ids.add(cid)
                    timestamps[cid] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    sent += 1
                    save_seen(seen_ids, timestamps)

                # 2. Filtrer + scorer + postuler
                if not AUTO_APPLY_ENABLED:
                    continue

                ok, reason = filters.should_apply(offer)
                if not ok:
                    skipped += 1
                    logger.info("[FILTER] Skip: %s | %s",
                                reason, offer.get("titre", "")[:60])
                    continue

                score_result = scorer.score_offer(offer)
                total = score_result["total"]

                # Score trop bas : skip complet
                if total < scorer.REVIEW_THRESHOLD:
                    skipped += 1
                    continue

                # Score en zone review (68-79) : log sans postuler
                if score_result["should_review"]:
                    apply_log.log_pending(offer, score_result)
                    reviewed += 1
                    logger.info("[SNIPER] Review (score=%d) | %s | %s | missions=%s",
                                total, offer.get("pays", ""),
                                offer.get("titre", "")[:45],
                                ",".join(score_result.get("matched_missions", [])[:2]) or "-")
                    continue

                # Score >= 80 : candidature sniper
                if not _can_apply_today(daily_applies):
                    apply_log.log_pending(offer, score_result)
                    logger.info("[SNIPER] Limite jour atteinte (%d/%d), queued | score=%d | %s",
                                daily_applies.get(_today(), 0), MAX_DAILY_APPLIES,
                                total, offer.get("titre", "")[:45])
                    continue

                success = auto_apply.apply_offer(offer)
                apply_log.log_application(offer, score_result, success)
                _increment_daily(daily_applies)
                if success:
                    applied += 1

            elapsed = round(time.time() - t0, 1)
            logger.info(
                "[CYCLE #%d] %ss | Discord: %d | Applied: %d | Review: %d | Skip: %d | Vu total: %d",
                cycle, elapsed, sent, applied, reviewed, skipped, len(seen_ids)
            )

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
    if MAX_RUNTIME_SEC and (time.time() - _START_TS) >= MAX_RUNTIME_SEC:
        logger.info("[EXIT] Budget de %ds atteint - fin du run (relance par cron)",
                    MAX_RUNTIME_SEC)
        raise SystemExit(0)
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
