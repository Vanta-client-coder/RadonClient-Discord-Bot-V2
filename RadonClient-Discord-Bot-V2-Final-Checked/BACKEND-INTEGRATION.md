# Radon backend -> Discord bot API

The bot exposes a small HTTP API on the same Render Web Service URL used for health checks.

All `/api/v1/*` requests require the server-side `RADON_INTERNAL_API_KEY`. Never call these endpoints directly from browser JavaScript or the Minecraft client.

## Authentication

Use one of:

```http
X-Radon-API-Key: YOUR_SECRET
```

or:

```http
Authorization: Bearer YOUR_SECRET
```

## Public health

```http
GET /health
```

## Test DM

```http
POST /api/v1/dm/test
Content-Type: application/json
X-Radon-API-Key: ...

{
  "discordUserId": "123456789"
}
```

## Generic DM

```http
POST /api/v1/dm/send
Content-Type: application/json
X-Radon-API-Key: ...

{
  "discordUserId": "123456789",
  "message": "Hello from Radon"
}
```

## OAuth welcome DM

```http
POST /api/v1/dm/welcome

{
  "discordUserId": "123456789",
  "username": "example"
}
```

The OAuth login must stay successful even when the returned `dm.success` is false.

## Personal license created

```http
POST /api/v1/license/created

{
  "discordUserId": "123456789",
  "licenseKey": "RADON-XXXX-XXXX-XXXX-XXXX",
  "plan": "Lifetime",
  "expiry": null,
  "purchaseId": "ORDER-123",
  "purchasedBy": "Example",
  "purchaserDiscordId": "123456789",
  "price": "19.99 EUR",
  "purchaseDate": "2026-10-10 09:00 UTC"
}
```

## Giveaway key created

```http
POST /api/v1/license/giveaway-created

{
  "discordUserId": "OWNER_DISCORD_ID",
  "licenseKey": "RADON-XXXX-XXXX-XXXX-XXXX",
  "plan": "Lifetime"
}
```

The owner receives the key by DM, but the license remains `UNCLAIMED` and is not assigned to the owner.

## Giveaway / unclaimed key claimed

```http
POST /api/v1/license/claimed

{
  "discordUserId": "NEW_OWNER_DISCORD_ID",
  "username": "new_owner",
  "licenseKey": "RADON-XXXX-XXXX-XXXX-XXXX",
  "plan": "Lifetime",
  "claimDate": "2026-10-10 09:15 UTC"
}
```

## Deactivate

```http
POST /api/v1/license/deactivated

{
  "discordUserId": "123456789",
  "licenseKey": "RADON-XXXX-XXXX-XXXX-XXXX"
}
```

## Reactivate

```http
POST /api/v1/license/reactivated

{
  "discordUserId": "123456789",
  "licenseKey": "RADON-XXXX-XXXX-XXXX-XXXX"
}
```

## Delete flow

Send the DM **before** deleting the database row:

```http
POST /api/v1/license/delete-notice

{
  "discordUserId": "123456789",
  "licenseKey": "RADON-XXXX-XXXX-XXXX-XXXX"
}
```

Then delete the license in your website database and mark the existing Discord sales message deleted:

```http
POST /api/v1/license/deleted

{
  "licenseKey": "RADON-XXXX-XXXX-XXXX-XXXX"
}
```

## DM diagnostic

```http
POST /api/v1/dm/diagnose

{
  "discordUserId": "123456789"
}
```

This reports whether the bot is online, which guilds are shared, whether membership screening is pending and whether the configured bot token is valid.

## Important response behavior

License event endpoints return a structure similar to:

```json
{
  "accepted": true,
  "dm": {
    "success": false,
    "discordStatus": 403,
    "discordCode": 50007,
    "internalError": "DM_BLOCKED_BY_DISCORD"
  },
  "sales": {
    "success": true
  },
  "rollbackRequired": false
}
```

`rollbackRequired` remains false because Discord DMs are notifications. A failed DM must never undo OAuth, payment, claim, deactivate, reactivate or delete operations.
