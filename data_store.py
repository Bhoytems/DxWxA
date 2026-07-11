import json
import os
import uuid
from datetime import datetime, timezone, timedelta

from config import WAT_OFFSET_HOURS

CONFIG_PATH = "config.json"
SIGNALS_PATH = "data/signals.json"


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def load_signals():
    if not os.path.exists(SIGNALS_PATH):
        return []
    with open(SIGNALS_PATH) as f:
        return json.load(f)


def save_signals(signals):
    os.makedirs(os.path.dirname(SIGNALS_PATH), exist_ok=True)
    with open(SIGNALS_PATH, "w") as f:
        json.dump(signals, f, indent=2)


def to_wat(dt_utc_iso):
    dt = datetime.fromisoformat(dt_utc_iso)
    wat = dt + timedelta(hours=WAT_OFFSET_HOURS)
    return wat.strftime("%Y-%m-%d %H:%M WAT")


def create_signal(signals, asset_key, direction, entry_price, expiry_minutes):
    sid = str(uuid.uuid4())[:8].upper()
    now = datetime.now(timezone.utc)
    record = {
        "id": sid,
        "asset_key": asset_key,
        "direction": direction,
        "entry_price": entry_price,
        "sent_at_utc": now.isoformat(),
        "sent_at_wat": to_wat(now.isoformat()),
        "expiry_minutes": expiry_minutes,
        "result": "PENDING",
        "exit_price": None,
        "resolved_at_utc": None,
        "resolved_at_wat": None,
    }
    signals.append(record)
    return record


def last_signal_time(signals, asset_key):
    times = [s["sent_at_utc"] for s in signals if s["asset_key"] == asset_key]
    if not times:
        return None
    return max(datetime.fromisoformat(t) for t in times)


def due_pending(signals):
    due = []
    now = datetime.now(timezone.utc)
    for s in signals:
        if s["result"] != "PENDING":
            continue
        sent = datetime.fromisoformat(s["sent_at_utc"])
        if now >= sent + timedelta(minutes=s["expiry_minutes"]):
            due.append(s)
    return due


def resolve(record, result, exit_price):
    record["result"] = result
    record["exit_price"] = exit_price
    now = datetime.now(timezone.utc)
    record["resolved_at_utc"] = now.isoformat()
    record["resolved_at_wat"] = to_wat(now.isoformat())
