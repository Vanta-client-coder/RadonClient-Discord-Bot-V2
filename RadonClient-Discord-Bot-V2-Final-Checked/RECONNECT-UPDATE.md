# RadonClient Discord Bot — Conservative Reconnect Update

This update preserves the original cogs, commands, ticket views, giveaway views, configuration and data schema.

## Improvements
- The Render HTTP listener starts before Discord login, as before.
- Temporary Discord HTTP/API errors use delayed login retries, with much longer cooldowns for HTTP 429 and Cloudflare 1015. There is no rapid retry loop.
- Invalid tokens and missing privileged gateway intents do **not** trigger automatic retry loops; the public health endpoint remains available for diagnosis.
- `/health` still exposes `online` and now includes `discordConnectionState` and `discordLastError` (a minimal classification, never credentials).
- The home endpoint does not falsely state Discord is online when only the HTTP listener is working.
- Separate DM HTTP requests now respect a `retry_after` up to 120 seconds and return a rate-limit response instead of retrying too early for longer durations.

## Before deployment
1. Back up any existing Render persistent disk/data, environment configuration, and GitHub repository; do not overwrite `.env` or SQLite databases.
2. Copy all ZIP contents into the existing GitHub bot repository. Preserve Render environment variables.
3. Confirm the configured Render service uses `python bot.py` and has `DISCORD_TOKEN` and other existing environment variables set.
4. In the Discord Developer Portal, ensure Server Members Intent and Message Content Intent are enabled if your existing bot relies on them.
5. Deploy once. Do not set up UptimeRobot to force repeated restarts.
6. Open `/health`: `online: true` confirms that Discord's gateway is connected; `online: false` means only the HTTP service is available. Check `discordConnectionState` and Render logs.

## Important limitations
- No code change can guarantee removal of a Discord/Cloudflare IP restriction or force flight through Discord rate limits.
- Testing here verified Python syntax, not a live Discord login, Render deployment, tickets, commands or giveaways.
- If 1015 persists across cooldowns, investigate Render egress IP reputation with Render/Discord support instead of repeatedly restarting the process.
