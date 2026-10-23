# RadonClient Discord Bot V2 — Final Candidate

## Changes
- `!help` now lists only commands registered in the running bot and available for the user's configured role.
- `!help <command>` displays its usage and details, without exposing unauthorized commands.
- New public `!botinfo` command shows connection, guild count and latency.
- New public `!uptime` command reports elapsed time since the latest Discord ready event.
- Existing ticket categories, auto-support feedback, weekly Top 10, staff invitations, giveaways, status monitor and website API retained.

## Verification
- Automated unit tests: see release response; run `python -m unittest discover -p 'test*.py'`.
- Python syntax: `python -m compileall -q .`.
- Live Discord / Render interaction **not tested** in this environment. Some integrations depend on credentials and external services.
- Render Free local SQLite data may not persist across deploy/restarts. Use permanent storage for reliable weekly counts and ticket data.

## Safe rollout
1. Back up the currently working GitHub commit and relevant persistent data.
2. Keep the same Render environment secrets. Never upload `DISCORD_TOKEN` or `RADON_CONFIG_JSON` to GitHub.
3. Upload ZIP contents to the repo directory already configured in Render, or adjust Root Directory to the new directory.
4. Deploy once and check Discord connection and `/health`.
5. In Discord: test `!help`, `!help ping`, `!botinfo`, `!uptime`, ticket buttons, owner permissions, heartbeat and weekly data on a test ticket.
6. Roll back to the known good commit if startup fails. Do not repeatedly restart upon 429/1015.
