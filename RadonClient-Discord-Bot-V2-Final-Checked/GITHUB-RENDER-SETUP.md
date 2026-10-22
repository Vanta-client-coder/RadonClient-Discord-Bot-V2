# Radon Discord Bot — New GitHub repository and Render deployment

## Security first
The original uploaded ZIP contained a real `.env` file. It was deliberately excluded from this package.
**Regenerate your Discord bot token** in Discord Developer Portal > Applications > Bot > Reset Token, then update Render > Environment > `DISCORD_TOKEN`.
If `DISCORD_CLIENT_SECRET` or `RADON_INTERNAL_API_KEY` in that ZIP were real, rotate those too and update the corresponding website/backend environments.
Do not upload `.env`, `.env.local`, database files, transcripts, tokens or `node_modules`.

## Move to the new private GitHub repository
1. Extract this ZIP. Upload the **contents of the folder**, not the original ZIP, into your newly created private GitHub repository.
2. Confirm `bot.py`, `render.yaml`, `requirements.txt`, `config.json`, `cogs/`, `core/` and `services/` are at repository root.
3. Check that `.env` is **not** present on GitHub.
4. In Render, create a **separate test Web Service** from the new repo first. Don't disconnect your existing working service.
5. Select Python; Build Command: `pip install -r requirements.txt`; Start Command: `python bot.py`.
6. Render environment variables: `DISCORD_TOKEN`, `RADON_INTERNAL_API_KEY`, and optionally `RADON_DATA_DIR=/var/data` if a persistent disk is attached.
7. The Discord application must enable Server Members Intent and Message Content Intent if the existing bot features need them.
8. Read Render logs. The HTTP service listening is NOT proof that the Discord connection succeeded. Look for `Radon Bot is online as` and correct guild ID.
9. Visit `https://YOUR-RENDER-SERVICE/health`. `online: true` means the Discord bot is ready; HTTP 200 alone does not.
10. Update UptimeBot only after you confirm the new service is healthy. Uptime checks cannot replace Discord connection checks.

**Do not run two copies of this bot with the same token in production** if they update the same status, ticket or giveaway messages. Stop the test instance once it is verified, or stop the old instance before starting the replacement.

## Website V85 connection
The Python bot has a protected internal API at `/api/v1/license/*` that accepts `RADON_INTERNAL_API_KEY` on requests. The V85 website's audit webhook implementation may use Discord directly instead of these endpoints. The integration is **not automatically connected** by uploading this repo. Confirm the website's endpoint protocol, key name and event payload match before enabling production events. Never expose the API key in browser JavaScript.

## Checks performed here
The package was cleaned of local secrets; Python files were syntax-checked. Live Discord login and Render deployment require your actual environment and are not verified here.
