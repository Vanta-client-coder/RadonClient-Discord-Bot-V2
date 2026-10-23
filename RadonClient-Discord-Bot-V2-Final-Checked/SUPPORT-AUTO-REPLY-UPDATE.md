# RadonClient V2 — Automatic Ticket Support

- The bot replies **once** to the first non-command, nonempty message written by a ticket creator.
- Offline topic recognition covers 22 issue groups and many synonyms. It is a rule-based best-match, not an LLM, and may occasionally misunderstand a request.
- Every English reply includes detailed troubleshooting steps and a privacy reminder where relevant.
- The ticket owner may press **That helped** or **Didn't help — Contact Staff**.
- A ticket owner may submit feedback once. An explicit staff request pings the configured **mentionable Support role**; if unavailable, a non-pinging staff-request message is posted.
- Button handlers are persistent across bot restarts and use the ticket database to check ticket ownership.
- The original reaction ticket panel, ticket controls, role permissions, login and heartbeat are preserved.

## Before deploying

1. Back up the currently working GitHub commit and any SQLite ticket data. Do not replace `.env` or Render secrets.
2. Deploy exactly once when ready; watch Render logs for Discord 429/1015.
3. Ensure the bot has `Send Messages`, `Embed Links`, `Read Message History`, `View Channel`, and for reaction panels `Add Reactions`.
4. Set the Support role to mentionable if automatic staff pings are desired; alternatively configure the bot's role permissions appropriately with care.
5. Open a test ticket, send an issue, verify exactly one English response, press **Didn't help — Contact Staff**, confirm exactly one escalation. Test the other button in a separate ticket.
6. Existing tickets answered before this update will not automatically get new support messages. Verify `online=true` and heartbeat updates separately.

## Limitations

Live Discord, Render, real permissions and staff ping delivery have **not** been tested here. A matching category is an automated suggestion, not a confirmed diagnosis. Database records on Render Free may be ephemeral; use persistent storage or a remote DB if ticket history must survive redeploys.
