import json
from typing import Any

import discord


STATUS_COLORS = {
    "UNCLAIMED": 0x747F8D,
    "ACTIVE": 0x20D5DD,
    "ACTIVE AGAIN": 0x20D5DD,
    "INACTIVE": 0xED4245,
    "DELETED": 0x8B0000,
}


class SalesChannelService:
    """Keep exactly one Discord sales/license message per license key."""

    def __init__(self, bot, database):
        self.bot = bot
        self.db = database

    async def start(self):
        return None

    async def close(self):
        return None

    async def _channel(self) -> discord.TextChannel | None:
        raw = str(self.bot.config.get("channels", {}).get("salesLicenseLogs", "")).strip()
        if not raw.isdigit():
            return None
        channel = self.bot.get_channel(int(raw))
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(int(raw))
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                return None
        return channel if isinstance(channel, discord.TextChannel) else None

    @staticmethod
    def _display(value: Any) -> str:
        if value is None or value == "":
            return "—"
        return str(value)[:1024]

    def _embed(self, data: dict[str, Any]) -> discord.Embed:
        status = str(data.get("status", "UNKNOWN")).upper()
        embed = discord.Embed(
            title="Radon+ License",
            color=STATUS_COLORS.get(status, 0x20D5DD),
        )
        fields = [
            ("License Key", data.get("licenseKey"), False),
            ("Purchase ID", data.get("purchaseId"), True),
            ("Purchased By", data.get("purchasedBy"), True),
            ("Purchaser Discord ID", data.get("purchaserDiscordId"), False),
            ("Claimed By", data.get("claimedBy"), True),
            ("Claimed Discord ID", data.get("claimedDiscordId"), False),
            ("Plan", data.get("plan"), True),
            ("Price", data.get("price"), True),
            ("Purchase Date", data.get("purchaseDate"), False),
            ("Claim Date", data.get("claimDate"), False),
            ("Expiry", data.get("expiry"), False),
            ("Current Status", status, False),
        ]
        for name, value, inline in fields:
            embed.add_field(name=name, value=self._display(value), inline=inline)
        embed.set_footer(text="Radon")
        return embed

    async def upsert(self, data: dict[str, Any]) -> dict[str, Any]:
        channel = await self._channel()
        if channel is None:
            return {
                "success": False,
                "skipped": True,
                "error": "Configured sales/license log channel was not found or is not accessible.",
            }

        license_key = str(data.get("licenseKey", "")).strip()
        if not license_key:
            return {"success": False, "error": "licenseKey is required."}

        allowed = {
            "licenseKey", "purchaseId", "purchasedBy", "purchaserDiscordId",
            "claimedBy", "claimedDiscordId", "plan", "price", "purchaseDate",
            "claimDate", "expiry", "status", "salesMessageId",
        }
        try:
            previous = json.loads(self.db.get_sales_metadata_json(license_key) or "{}")
            if not isinstance(previous, dict):
                previous = {}
        except json.JSONDecodeError:
            previous = {}

        merged = dict(previous)
        for key, value in data.items():
            if key in allowed and value is not None:
                merged[key] = value
        merged["licenseKey"] = license_key

        message_id = str(merged.get("salesMessageId", "")).strip() or self.db.get_sales_message_id(license_key)
        embed = self._embed(merged)

        if message_id and message_id.isdigit():
            try:
                message = await channel.fetch_message(int(message_id))
                if str(merged.get("status", "")).upper() == "DELETED":
                    await message.edit(embed=embed, view=None)
                else:
                    await message.edit(embed=embed)
                self.db.set_sales_state(license_key, str(message.id), json.dumps(merged, ensure_ascii=False))
                return {"success": True, "messageId": str(message.id), "updated": True}
            except discord.NotFound:
                pass
            except discord.Forbidden:
                return {"success": False, "error": "Bot cannot edit the existing sales message."}
            except discord.HTTPException as exc:
                print(f"[Radon Sales] Edit failed: {exc}")
                return {"success": False, "error": str(exc)}

        try:
            message = await channel.send(embed=embed)
            self.db.set_sales_state(license_key, str(message.id), json.dumps(merged, ensure_ascii=False))
            return {"success": True, "messageId": str(message.id), "updated": False}
        except discord.Forbidden:
            return {"success": False, "error": "Bot cannot send messages in the sales/license channel."}
        except discord.HTTPException as exc:
            print(f"[Radon Sales] Send failed: {exc}")
            return {"success": False, "error": str(exc)}
