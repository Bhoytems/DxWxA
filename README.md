# Signal Engine (GitHub-only version)

Everything runs inside this one repo — no external host, no dashboard server.
GitHub Actions runs the engine on a schedule (default every 5 minutes),
and a static page (GitHub Pages) shows the results.

## ⚠️ Trade-offs vs. the hosted-dashboard version
- No live toggle switches or passcode — you edit `config.json` and commit to
  change settings (which assets are on, which Telegram channels, START/STOP)
- No true 24/7 real-time monitoring — GitHub Actions cron is best-effort and
  can lag a few minutes during busy periods
- The results page is read-only and public if your repo is public (see
  "Public vs private" below)

## Setup

### 1. Telegram bot
Message **@BotFather** → `/newbot` → copy the token. Add the bot as admin to
your channel(s). Get each channel's chat ID by forwarding a channel message
to **@userinfobot**, or via `getUpdates` on the Bot API.

### 2. Push this to GitHub
Create a repo, push this folder's contents to it.

### 3. Add the one secret
Repo → Settings → Secrets and variables → Actions → New repository secret:
- `TELEGRAM_BOT_TOKEN`

That's the only secret needed — there's no dashboard to authenticate against
anymore.

### 4. Turn the engine on
Edit `config.json`:
```json
{
  "engine_running": true,
  "assets": { "gbpusd_otc": true, "xauusd_otc": true, "btc_otc": true },
  "channels": [ { "chat_id": "-100xxxxxxxxxx", "label": "My channel" } ]
}
```
Commit and push. The next scheduled run (within 5 minutes) will pick it up,
or trigger one immediately from the repo's **Actions** tab → "Signal Engine"
→ "Run workflow".

### 5. (Optional) Turn on the results page
Repo → Settings → Pages → Source: **Deploy from a branch** → Branch: `main`,
folder `/ (root)`. Your results page will be live at
`https://<your-username>.github.io/<repo-name>/` within a minute or two.

## Public vs private repo
- **Public repo**: GitHub Pages is free. `config.json` (including your
  Telegram channel IDs) and `data/signals.json` (signal history) are visible
  to anyone. The bot token itself stays safe as a secret either way.
- **Private repo**: hides everything, but GitHub Pages requires a paid plan
  (GitHub Pro/Team) to publish from a private repo. Actions still runs free
  either way (2,000 min/month on private, unlimited on public).

If you'd rather keep channel IDs private, go with a private repo and skip
Pages — you can still read `data/signals.json` directly from the repo.

## How results are tracked

Every signal gets a short ID (e.g. `A1B2C3D4`), included in the Telegram
message and stored in `data/signals.json`. On a later run, once 5 minutes
have passed, the runner checks the price again and posts a follow-up
WIN/LOSS/TIE message tagged with that ID, then commits the updated file.

## Project layout

```
runner.py              GitHub Actions entry point — one pass per run
strategy.py             <-- swap your signal logic in here
data_feed.py           Market data (yfinance, multi-timeframe)
telegram_bot.py         Telegram send + message formatting
data_store.py           JSON file read/write (replaces the old SQLite storage)
config.py               Assets, timeframes, timing
config.json              <-- edit this to change settings (assets, channels, on/off)
data/signals.json        Signal history (auto-updated by the Action)
index.html               Static results page (for GitHub Pages)
.github/workflows/       engine.yml — the cron schedule
requirements.txt
```
