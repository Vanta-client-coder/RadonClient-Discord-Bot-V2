# RadonClient Discord Bot — new GitHub and Render setup

**Important:** A new GitHub repository does not change your server-side Discord rate limit. A new Render service may also use shared egress IP addresses and may still get 429 / Cloudflare 1015. No success is guaranteed.

## Before switching
1. Keep the current repository and service as a rollback copy. Do not run two copies using the same bot token.
2. Back up the database (`data/radon.db` or your Render persistent disk), transcripts, existing environment variables, and any configuration files. Never commit secrets.
3. If the current service has a persistent disk, arrange to move or reconnect it before changing hosts. Render local files can be ephemeral. Do not assume tickets/giveaway state carries over automatically.

## New GitHub repository
1. Create a **private** repository, e.g. `RadonClient-Discord-Bot-V2`.
2. Upload the **contents of this ZIP to the repository root** (not a second nested folder).
3. Confirm `bot.py`, `requirements.txt`, `render.yaml`, `cogs`, `core`, and `services` are in the root.
4. **Required:** copy the contents of your original `config.json` into Render **Environment** as the secret environment variable `RADON_CONFIG_JSON`. Do not commit `config.json` to GitHub. This upload did not include it. `config.example.json` is only a guide. Keep your existing role/channel/ticket mappings.
5. Do not publish sensitive server configuration to a public repository; use a private repository.
4. Never upload `.env`, `data/*.db`, tokens, secrets, or license data.

## New Render web service
1. Before starting the new service, suspend/stop the old one so only one instance logs into Discord.
2. Connect your new private repository, branch `main`; leave **Root Directory blank**.
3. Use Python, build command `pip install -r requirements.txt`, start command `python -u bot.py`.
4. Set environment variables `DISCORD_TOKEN`, `RADON_INTERNAL_API_KEY`, and any others needed by your existing setup. Copy secrets privately from your own configuration, not through chat.
5. If you are using persistent storage, configure `RADON_DATA_DIR` to point to the mounted disk. Restore your existing data before running.
6. Do **one** deploy and check `/health` and Logs. Do not continually restart on 429/1015.
7. Once online, update the Website V100 server-side bot API URL and matching API secret to the new Render URL. Do not change website user data or overwrite `.env` files.

## Interpreting health
- `online: true`: Discord gateway ready, but tickets, commands and DMs still need live tests.
- `online: false, discordConnectionState: rate_limited`: do not keep redeploying; the Discord REST login is still blocked.
- `online: false, discordConnectionState: invalid_token`: check your privately stored token.
- `online: false, discordConnectionState: missing_intents`: review privileged intents on Discord Developer Portal.

## Verification
Run `python -m unittest discover -p 'test_*.py'` and `python selftest.py`. These are local checks, not proof of live Discord/Render behavior.

## Critical config deployment warning
`config.json` is ignored by Git to avoid publishing your server-specific configuration. The bot reads `RADON_CONFIG_JSON` first, falling back to local `config.json` for Windows development. Set the full original JSON in Render Environment privately; without a valid configuration the bot will not start. The example file is intentionally not a working configuration.
