# RadonClient Discord Bot V2 — Owner Access Fix

Fixes `!help` and other commands returning Access Denied for the configured Owner and Co-Owner roles when `commandAccess` is `{}`.

- Owner and Co-Owner roles are always permitted by the global role gate.
- `!help` is visible to server members.
- Other groups still need explicit `commandAccess` permission, avoiding unintentional privilege escalation.
- Discord login, heartbeat, Render web service and token handling were not changed.

Local tests: `python -m unittest test_owner_access -v` (no live Discord needed). Syntax also compiled. Actual Discord command behavior requires an in-server test.

## Deployment

The existing GitHub repository has the source within `RadonClient-Discord-Bot-V2-Final-Checked/`. Upload the contents of this ZIP into that same folder and commit the changed files. Keep Render's Root Directory at `RadonClient-Discord-Bot-V2-Final-Checked`. Do not change the Environment configuration or token. With Auto Deploy disabled, perform **one** manual deploy of the latest commit. Verify `!help` with Owner and a harmless Owner command, and check the heartbeat afterward.

Never upload `.env`, tokens, or private `config.json` to GitHub.
