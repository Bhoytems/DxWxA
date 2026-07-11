"""
GitHub Actions entry point (repo-only version — no external host).

Runs ONE pass: reads config.json (engine on/off, enabled assets, channels),
scans each enabled asset for a signal, sends any signal to Telegram and
appends it to data/signals.json, then resolves any signal whose 5-minute
expiry has elapsed and posts the result. The workflow commits the updated
data/signals.json back to the repo after each run.

To change settings, edit config.json and commit/push — there's no live
dashboard in this version.
"""
import sys
from datetime import datetime, timezone

import data_store as store
import data_feed
import strategy
import telegram_bot
from config import ASSETS, EXPIRY_MINUTES, SIGNAL_COOLDOWN_SECONDS


def scan_and_signal(asset_key, channels, signals, expiry_minutes):
    asset = ASSETS[asset_key]

    last = store.last_signal_time(signals, asset_key)
    if last is not None:
        elapsed = (datetime.now(timezone.utc) - last).total_seconds()
        if elapsed < SIGNAL_COOLDOWN_SECONDS:
            return

    try:
        candles = data_feed.fetch_all_timeframes(asset["feed_symbol"])
    except Exception as e:
        print(f"[runner] data fetch failed for {asset_key}: {e}")
        return

    try:
        direction = strategy.generate_signal(candles)
    except Exception as e:
        print(f"[runner] strategy error for {asset_key}: {e}")
        return

    if direction is None:
        return

    tf1m = candles.get("1m")
    entry_price = float(tf1m["close"].iloc[-1]) if tf1m is not None and len(tf1m) else None

    if not channels:
        print(f"[runner] signal for {asset_key} ({direction}) but no channels configured")
        return

    record = store.create_signal(signals, asset_key, direction, entry_price, expiry_minutes)
    text = telegram_bot.format_signal_message(
        record["id"], asset["label"], direction, expiry_minutes, record["sent_at_wat"]
    )
    telegram_bot.broadcast([c["chat_id"] for c in channels], text)
    print(f"[runner] signal sent: {asset_key} {direction} id={record['id']}")


def resolve_due(signals, channels):
    for record in store.due_pending(signals):
        asset = ASSETS.get(record["asset_key"])
        if asset is None:
            continue
        try:
            exit_price = data_feed.latest_price(asset["feed_symbol"])
        except Exception as e:
            print(f"[runner] exit price fetch failed for {record['id']}: {e}")
            continue
        if exit_price is None or record["entry_price"] is None:
            continue

        if record["direction"] == "CALL":
            result = "WIN" if exit_price > record["entry_price"] else ("LOSS" if exit_price < record["entry_price"] else "TIE")
        else:
            result = "WIN" if exit_price < record["entry_price"] else ("LOSS" if exit_price > record["entry_price"] else "TIE")

        store.resolve(record, result, exit_price)

        text = telegram_bot.format_result_message(
            record["id"], asset["label"], record["direction"], result, record["entry_price"], exit_price
        )
        telegram_bot.broadcast([c["chat_id"] for c in channels], text)
        print(f"[runner] result posted: {record['id']} -> {result}")


def main():
    config = store.load_config()

    if not config.get("engine_running"):
        print("[runner] engine is OFF in config.json — skipping this pass")
        sys.exit(0)

    signals = store.load_signals()
    channels = config.get("channels", [])
    expiry_minutes = config.get("expiry_minutes", EXPIRY_MINUTES)

    for asset_key, enabled in config.get("assets", {}).items():
        if enabled and asset_key in ASSETS:
            scan_and_signal(asset_key, channels, signals, expiry_minutes)

    resolve_due(signals, channels)
    store.save_signals(signals)
    print("[runner] pass complete")


if __name__ == "__main__":
    main()
