# RadonClient V2 — First Ticket Auto Reply

When the ticket creator sends their **first nonempty, noncommand text message** in a registered open ticket, the bot automatically replies once. It matches the message against English FAQ terms for installation, crashes, licensing, module bugs, payments, and account access. Unknown messages receive a neutral request for further information. The reply clearly states it is only an automatic suggestion; staff handles actual diagnosis and decisions.

- **Not AI**: deterministic keyword matching, no external API, no extra secrets or costs.
- **Only in registered ticket channels** and only for the original ticket creator. Other channels/messages and staff messages are ignored.
- The replied status is stored in the existing SQLite ticket table using a safe, backward-compatible migration. A concurrent second message does not trigger another reply.
- The existing 🎫 ticket-reaction panel remains enabled; it is separate from this feature.
- **Privacy**: Never echo full user messages or request tokens/passwords; responses do not tag the author.
- Configurable source: `core/ticket_auto_reply.py`, with matching categories and reply texts.
- Bot must have `Message Content Intent` in Discord Developer Portal and permission to Send Messages + Embed Links in ticket channels.
- SQLite database must be persisted through restarts to retain first-response status. Render free instances may have ephemeral storage; a lost database can also affect tickets and other features. Consult production persistence settings before deploying.

## Validation

- 33 local `unittest` cases passed, including first-message claim atomicity and topic selection.
- Python source compilation passed.
- No live Discord or Render tests were executed. The bot may still experience Discord 429/1015 on deployment.

## Safe rollout

Keep the working Render instance running until you're ready to update. Back it up and deploy in one controlled change. Verify the bot connects, open a test ticket, post a first message about a crash, confirm one reply, post a second message, confirm no second automatic reply. Check an unrelated channel receives no automatic reply. Test ticket closure, existing reaction panel, and heartbeat as normal.
