# RadonClient Discord Bot V2 — Embed Quality Review

## Changes
- Shared Radon embed helper now validates color and branding input safely.
- Enforces Discord's 256-character title, 4096-character description, 256-character field names, 1024-character field values, maximum 25 fields, and 6000 total embed-character budget.
- The ticket creation/closure embeds and ticket administration embeds use safe fields.
- Moderation/ticket logs use safe fields.
- Sales/license embeds preserve their status colors and fields and now use the common brand footer and safe field bounds.
- Weekly activity preview uses Radon branding, while the scheduled report retains its existing staff-selection controls.
- The existing ticket responses, 11 categories, auto replies, weekly activity tracking, giveaways, roles, login and heartbeat are retained in source.

## Testing
- `python -m compileall -q .`: passed.
- `python -m unittest discover -p 'test_*.py' -q`: 46 tests passed.
- `python verify_embed_quality.py`: 6 checks passed.
- ZIP checked via Python ZipFile.testzip.

## Not validated
- No live Discord connection or Render deployment was run here.
- Visual appearance is subject to Discord rendering; buttons, sales messages and all third-party API integrations need live smoke tests.
- Render Free local SQLite storage remains ephemeral. This release does not fix persistent storage.

## Release safety
- Back up currently running repo and data. Do not place tokens or secret JSON in GitHub.
- New ZIP is a complete source update, not a guarantee of live Discord behavior.
- Preserve current Render environment settings, prevent concurrent bot instances, and review logs after a single controlled deployment.
