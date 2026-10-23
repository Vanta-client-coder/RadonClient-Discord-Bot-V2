# RadonClient Discord Bot V2 — Weekly member leaderboard

## What happens
- Every Monday UTC, the bot posts the **previous completed week's** top 10 eligible non-staff message senders in channel `1562883723563634729`.
- Counts only messages received while V2 is running, from deployment onward; does not scan Discord history.
- Excludes all bots; configured Owner, Co-Owner, Developer, Team and Support roles; and members with Administrator or Manage Server permissions.
- Excludes messages in ticket channels, commands and messages shorter than 3 characters; counts at most one message per user each 15 seconds to reduce spam incentives.
- The Owner or Co-Owner can choose one of the top ten using the dropdown, then click **Send Staff Invitation**.
- The invitation DM is in English, friendly and optional. It does **not** give staff permissions or roles. A member can receive at most one invite per completed week.
- If the member has DMs disabled, the bot reports this privately to the owner. No automatic mass DM campaigns.
- The view is registered again after bot restart if the database is retained.

## Crucial Render Free storage warning
The database (`data/radon.db` or RADON_DATA_DIR) must persist for accurate weekly counts, duplicate-report prevention and invitation history. Render free web services have ephemeral filesystem storage. **Deploys/restarts may erase database data**. This feature cannot reliably survive redeploys or restarts on Render Free without persistent external storage. Do not claim weekly reporting is reliable until database persistence is configured and tested. Do not try to use UptimeRobot as a database persistence fix.

## Discord permissions
Bot needs View Channel, Send Messages, Embed Links in the weekly channel and message content intent enabled. DMs may be refused by member privacy settings. Owner/Co-Owner permission is verified with the configured role IDs.

## Safe update
- Before uploading to your GitHub V2 repo, save a backup of the currently working commit and Render configuration.
- Existing `RADON_CONFIG_JSON` stays unchanged. The new channel ID is built into `core/weekly_activity.py`.
- Existing GitHub repository uses root directory `RadonClient-Discord-Bot-V2-Final-Checked`: upload updated files inside that folder, or change Render Root Directory carefully.
- Keep old bot service suspended. Turn auto deploy off. Update one time, check logs, `!help`, bot status, heartbeat, ticket feedback buttons.
- This package passes local tests, **not live Discord tests**.

## Expanded ticket auto support
Additional English topics: downloads, bot command issues, ticket panel issues, beta applications, premium access, Auto Totem, Shulker Preview, Block Picker, UI Sounds and Deep Player Finder. Existing one-time ticket first reply and staff escalation buttons remain.
