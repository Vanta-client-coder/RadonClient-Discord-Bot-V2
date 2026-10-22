# RadonClient Discord Bot — Render startup fix

## Wat was mis?
`discord.py` runs `setup_hook()` AFTER the Discord HTTP login. If Cloudflare blocks login with HTTP 429 / error 1015, the Render webserver started in setup_hook() never binds to `PORT`. Render reports `No open ports detected`, then the deployment fails.

## Wat is aangepast?
- `bot.py` starts `internal_api.start()` BEFORE Discord login, binding 0.0.0.0:$PORT.
- A blocked login logs short, safe diagnostic lines rather than the full Cloudflare HTML.
- On blocked login, the process waits without retrying Discord automatically. `/health` stays available with `online:false`; a successful HTTP response alone is NOT evidence the bot is online.
- Existing bot modules, config, tokens, permissions and status monitor are retained.

## Eenvoudige instructies
1. Leave Render suspended while deploying to GitHub.
2. Upload the contents of this ZIP to the SAME GitHub folder as bot.py (not an extra nested folder). Do not replace or expose config.json, .env, or any tokens.
3. Commit. In Render resume once, and verify Events shows the newest commit.
4. Check Logs and /health. If `online:false` and a 429/1015 warning appears, suspend again; this is still Discord/Cloudflare blocking the host IP. Do not rapidly redeploy or reset your token.
5. After enough cool-down, resume once, and test Discord ticket action. Resume UptimeRobot only after `online:true` is stable.

## Test status
Source syntax validated, NOT tested against the live Discord API.
A Render/Discord network restriction can persist even with correct code; contact Render or Discord support if it continues.
