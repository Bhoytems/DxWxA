# --- Assets ---
# key -> (display name, data feed symbol)
# OTC pairs are IQ Option's synthetic weekend/after-hours instruments; they track
# the underlying live market closely, so the live symbol is used as the price proxy.
ASSETS = {
    "gbpusd_otc": {"label": "GBPUSD OTC", "feed_symbol": "GBPUSD=X", "kind": "forex"},
    "xauusd_otc": {"label": "XAUUSD OTC", "feed_symbol": "GC=F", "kind": "forex"},
    "btc_otc":    {"label": "Bitcoin OTC", "feed_symbol": "BTC-USD", "kind": "crypto"},
}

# --- Timeframes monitored internally ---
TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h"]

# --- Signal behaviour ---
EXPIRY_MINUTES = 5
SIGNAL_COOLDOWN_SECONDS = 60 * 4  # min gap between two signals on the same asset

# --- Timezone ---
WAT_OFFSET_HOURS = 1  # West Africa Time = UTC+1, no DST
