# RadonClient Discord Bot V2 — Embed quality update

- Centralized safer theme colors and input length validation in `core/embeds.py`.
- Existing `radon_embed()` call signatures retained, including custom colors.
- Consistent themed Weekly Top 10 embed with unchanged selection and invitation logic.
- More helpful ticket welcome embed: next steps and staff escalation explanation.
- Status monitor uses configured Radon accent color, heartbeat cadence unchanged.
- No code changes to login, reconnect, credentials, database or rate limiting.
- Discord API integration is NOT live-tested; create a test ticket and verify embeds manually.
- Local Render Free SQLite state is not durable; use persistent storage for weekly reports.
- Preserve the currently working Render deployment and configuration until controlled rollout.
