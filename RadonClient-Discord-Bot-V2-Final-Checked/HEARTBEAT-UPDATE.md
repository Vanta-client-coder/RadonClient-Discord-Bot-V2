# RadonClient Bot V2 — Heartbeat & Safety Review

## Implemented
- Public `/health` now includes a `heartbeat` object that separates Discord gateway online state from status-message heartbeat state.
- Diagnostics: `state`, configured interval, last attempted/successful timestamps, age, consecutive failures and a nonsecret error type.
- A heartbeat is marked `stale` when no successful Discord status update has occurred for more than two intervals plus 120 seconds.
- Minimum heartbeat interval remains 300 seconds; maximum is 3600 seconds to avoid a misconfigured excessively slow monitor.
- Heartbeats are paused while Discord gateway is not ready or API cooldown is active.
- A Discord Forbidden response disables status-channel updates for that process (instead of repeatedly requesting a channel without permissions).
- Rate-limit and transient errors result in exponential cooldown with jitter, without frequent retries.
- The original status embed, search for previous message, ticket persistent views, giveaways, commands, and internal website API are preserved.

## Verification performed
- Compiled syntax of all Python files successfully.
- 7 dependency-free tests passed (heartbeat logic and deployment settings).
- Runtime integration tests with discord.py could not be performed in this environment because the library was unavailable and installation was blocked by network access.
- No real Discord or Render deployment was performed. No guarantee that 429 / Cloudflare 1015 can be resolved by code or by creating a new Render service.

## Setup
- Use `python -u bot.py` as Render Start Command and `pip install -r requirements.txt` as Build Command.
- Set `DISCORD_TOKEN` and `RADON_CONFIG_JSON` privately in Render Environment; configure `RADON_INTERNAL_API_KEY` only if website integration requires it.
- Keep the original Discord IDs, roles, ticket settings and existing data from your prior config. `config.example.json` contains placeholders, not a working configuration.
- Run only one instance of the bot. Disable automatic deploys during troubleshooting.
- If you see 429 / 1015 again, do not restart repeatedly; inspect the provider block and cooldown.
- For a status-channel heartbeat, ensure the bot has View Channel, Read Message History, Send Messages and Embed Links permissions.
- `online: true` and `heartbeat.state: active` provide separate indicators; a functioning `/health` alone does not prove Discord connected.
- Before switching from the old Render service, back up any existing persistent SQLite database. Render local files may not persist across deploys without an attached persistent disk.
