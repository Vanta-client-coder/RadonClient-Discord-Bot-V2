# Radon Discord Bot — API rate limit fix

The uploaded logs show Discord/Cloudflare HTTP 429 and error 1015 when the status monitor repeatedly fetches history and edits an embed. This patch:
- Changes the heartbeat to at least 5 minutes (default 10 minutes).
- Reads message history only once per process, not on every update.
- Avoids immediate duplicate API operations on ready/resume.
- Uses a cooldown (starting at 30 minutes for HTTP 429) and exponential backoff.
- Logs short errors rather than entire Cloudflare HTML pages.

## Deploy to GitHub/Render
1. Back up the current repository and Render environment variable names.
2. In GitHub, find `status_monitor.py` next to `bot.py` and replace it with the new file from this ZIP; commit the update. Alternatively upload the ZIP's contents, preserving folders. Do NOT upload tokens, `.env` or credentials.
3. Ensure your existing `config.json` remains in the same directory as `bot.py` (the user had previously created it in GitHub; it is intentionally NOT included in this ZIP).
4. In Render, keep existing environment secrets unchanged. Resume/redeploy the service once the Discord restriction has cleared.
5. Verify `/health`, Render logs, a single status update, and ticket actions. Avoid repeatedly restarting or flooding Discord with test messages.
6. Resume UptimeRobot when the service is healthy.

Important: this reduces traffic and handles Discord rate limits, but does not guarantee Cloudflare won't block Render's shared egress IP. Discord may continue to restrict a shared IP; if it does, contact Render/Discord support or consider a different legitimate hosting IP. Do not use proxies to evade rate limits.

Note: No live Discord API calls were made during testing. A 429 may also be triggered by OTHER services using the same token or shared IP. Check that the old bot service is stopped.
