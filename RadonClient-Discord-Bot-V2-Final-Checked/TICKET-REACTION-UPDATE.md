# RadonClient V2 — Ticket reaction update

- Owner or Co-Owner sends `!ticketreaction` in a channel where the bot can send messages and add reactions.
- Users click 🎫 to open a private support ticket; same category, staff overwrites, maximum ticket limit and transcripts as the existing ticket system.
- If `tickets.types` is empty, reaction tickets use a generic Support ticket. The existing select-menu `!ticketpanel` still needs configured types.
- If types are configured, the first ticket type is used by the reaction panel.
- The panel is recognized by its bot author and exact embed marker, and remains usable after a bot restart.
- Bot needs View Channel, Read Message History, Send Messages, Add Reactions, Manage Channels and ideally Manage Messages (to remove a user's reaction).
- The bot tries to DM the user with a ticket link. If user DMs are closed, the private ticket still opens.
- Caveat: two people pressing simultaneously are handled separately; same-user duplicates are serialized within one process. Restarted deployments need live testing.
- `!ticketreaction` respects owner/co-owner IDs and does not grant staff abilities to members.
- Existing status monitor, login, giveaway and ticket button interfaces were not changed.
- Do not deploy without backup; this feature has not been tested live on Discord.
