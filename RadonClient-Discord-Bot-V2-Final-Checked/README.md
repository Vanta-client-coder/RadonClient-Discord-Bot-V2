# Radon Discord Bot v2

Complete `discord.py` 2.x bot for the Radon Client Discord server. This build is configured for Render and already contains the Discord server, role, channel and ticket-category IDs supplied for the Radon server.

## Included

- Prefix commands with `!`
- Role-based command access
- Moderation: ban, kick, timeout, untimeout, clear, warnings
- Tickets with Support, Purchase Support, Bug Report, Giveaway Claim and Other
- Ticket claim/close/add/remove/rename + HTML transcripts
- Giveaways with persistent entries and automatic winner selection
- Fixed announcement channel
- `!dm` and `!testdm` through Discord REST API v10 using the bot token
- `!membercount`, `!userinfo`, `!serverinfo`, `!ping`
- `!lock` / `!unlock`
- Auto-role for existing members at startup and new members on join
- Server-boost notification embed
- Bot uptime/heartbeat channel
- Radon website/backend HTTP API
- Radon+ license DMs
- One persistent Discord sales/license message per license key
- SQLite persistence
- Render Web Service health endpoint

## Configured role permissions

- **Radon Owner**: all commands
- **Radon Co-Owner**: all commands
- **Radon Dev**: `!ban`, `!kick`, `!timeout`
- **Radon Team**: `!timeout`
- **Radon Support**: `!claim`, `!close`, `!add`, `!remove`, `!rename`

The configured auto-role is automatically assigned to every non-bot member that does not already have it.

## Main commands

```text
!help
!ping
!userinfo [@member]
!serverinfo
!membercount

!ban @member [reason]
!kick @member [reason]
!timeout @member 10m [reason]
!untimeout @member [reason]
!clear 20
!warn @member [reason]
!warnings @member
!delwarn @member WARNING_ID

!ticketpanel
!claim
!close
!add @member
!remove @member
!rename new-name

!lock
!unlock
!announce text
!dm @member text
!testdm [@member]

!giveaway 10m 1 Radon+ License
!giveawayend MESSAGE_ID
!giveawayreroll MESSAGE_ID
!giveawaycancel MESSAGE_ID
```

## Discord Developer Portal

Under **Bot -> Privileged Gateway Intents**, enable:

- **Server Members Intent**
- **Message Content Intent**

Presence Intent is not required.

The bot role must be above the configured auto-role and above any members it needs to moderate. Give the bot the permissions required by the commands you use; Administrator is the simplest setup for your own private bot.

## Render setup

Create a **Web Service** from the GitHub repository.

Build command:

```text
pip install -r requirements.txt
```

Start command:

```text
python bot.py
```

The bot itself starts an `aiohttp` HTTP server on Render's `$PORT`, so no Flask keep-alive file is needed.

### Required Render Environment Variables

```text
DISCORD_TOKEN=<your current Discord bot token>
RADON_INTERNAL_API_KEY=<a long random secret>
```

### Optional / website variables

```text
DISCORD_CLIENT_ID=<Discord application ID>
DISCORD_CLIENT_SECRET=<Discord OAuth client secret>
RADON_DATA_DIR=data
```

`DISCORD_CLIENT_ID` and `DISCORD_CLIENT_SECRET` are for the Radon website/backend OAuth flow. The bot does **not** use an OAuth token as a bot token.

Never commit the real token, client secret or internal API key to GitHub.

## Discord API token / DMs

There is no separate Discord API key required for bot DMs. `DISCORD_TOKEN` is the Discord **bot token** and is used server-side with Discord REST API v10.

The DM implementation performs:

1. `POST /users/@me/channels` with the target Discord user ID.
2. `POST /channels/{dm_channel_id}/messages`.

Discord error bodies are logged. `403` + Discord code `50007` is returned internally as `DM_BLOCKED_BY_DISCORD`. DM failure never tells the website to roll back a license action.

## Backend API on Render

If your Render URL is:

```text
https://discord-bot-radon.onrender.com
```

health is available at:

```text
GET /health
```

Protected routes use either:

```text
X-Radon-API-Key: <RADON_INTERNAL_API_KEY>
```

or:

```text
Authorization: Bearer <RADON_INTERNAL_API_KEY>
```

See `BACKEND-INTEGRATION.md` for routes and payloads.

## Auto-role behavior

At startup the bot fetches all members from the configured guild. Every non-bot member missing the auto-role receives it. New joins receive the same role through `on_member_join`.

If this does not work, check Render logs for `[Radon AutoRole]` lines and verify:

- Server Members Intent is enabled.
- Bot has Manage Roles.
- Bot role is above the auto-role.
- The configured role ID still exists.

## Bot status / uptime

The configured bot-status channel gets:

- an online/restart report;
- one status embed that updates its heartbeat every 60 seconds;
- online-since time and current uptime.

A bot cannot send a Discord message at the exact moment it has already crashed. Therefore the last heartbeat is used as the closest estimate of when it stopped responding.

## Sales / license logs

The configured sales/license channel receives one Radon+ license embed per license key. The bot stores the Discord message ID in SQLite and edits that same message when status changes to `UNCLAIMED`, `ACTIVE`, `INACTIVE`, `ACTIVE AGAIN` or `DELETED`.

## SQLite on Render

By default the database is stored under `data/radon.db`. Render's normal filesystem can be ephemeral across deploys. If you need guaranteed persistence across deploys/restarts, attach a Render Persistent Disk and set:

```text
RADON_DATA_DIR=/var/data
```

(or the mount path you chose).

## Local start

Python 3.12+ is recommended.

```powershell
.\start.ps1
```

For local use, copy `.env.example` to `.env` and fill in your local values. `.env` is ignored by Git.
