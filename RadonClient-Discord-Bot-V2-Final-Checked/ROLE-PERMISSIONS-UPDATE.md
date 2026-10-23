# RadonClient Discord Bot V2 — All Roles Permissions Fix

Only `core/permissions.py`, `cogs/utility.py`, and authorization tests changed versus Owner Access Fix. Login, connection retries, heartbeat, Render config and database are unchanged.

## Default permissions (when `commandAccess` is `{}`)
- Owner / Co-Owner: all commands (other Discord hierarchy and channel permission restrictions still apply).
- Developer: moderation (`ban`, `kick`, `timeout`, `untimeout`, `clear`, `warn`, `warnings`, `delwarn`).
- Team: `timeout`, `untimeout`, `warn`, `warnings`, `clear`.
- Support: `claim`, `close`, `add`, `remove`, `rename`, `warnings`.
- Auto Role and members without staff roles: public utility (`help`, `ping`, `userinfo`, `membercount`, `serverinfo`).
- Public utility is available to every role.

`!help` now shows only commands allowed to the requester. Existing `commandAccess` group entries override that group's defaults; explicit `[]` denies those extra commands. Users with several roles receive the union of allowed permissions. No new Discord permissions are granted by the bot; Discord role hierarchy and bot permissions still apply.

## Safe deployment
1. Preserve current live GitHub commit, Render variables, and database backups.
2. Upload changed code to a separate test branch. Keep working Render service unchanged.
3. Run `python -m unittest test_owner_access test_all_roles test_deploy_safety test_preflight test_heartbeat_logic tests_status` locally. Build syntax `python -m compileall -q .`.
4. Deploy just once when ready, and confirm Discord login and status heartbeat. Stop on HTTP 429 / Cloudflare 1015, do not repeatedly restart.
5. Test `!help` with each role, and a permitted and prohibited command on test accounts; do not test moderation on real users.
6. Keep the previous commit for rollback. Live Discord behavior remains unverified until tested.
