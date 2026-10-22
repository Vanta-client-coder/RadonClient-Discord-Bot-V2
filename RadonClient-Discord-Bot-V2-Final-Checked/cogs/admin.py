from datetime import datetime, timezone

import discord
from discord.ext import commands

from core.embeds import radon_embed
from core.logs import send_log


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _require_manage_channels(self, ctx):
        me = ctx.guild.me
        if me is None or not ctx.channel.permissions_for(me).manage_channels:
            await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Missing Bot Permission",
                    "I need the **Manage Channels** permission in this channel.",
                    color=0xED4245,
                )
            )
            return False
        return True

    @commands.command()
    async def lock(self, ctx):
        """Lock the current text channel for @everyone."""
        if not isinstance(ctx.channel, discord.TextChannel):
            return await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Unsupported Channel",
                    "This command can only be used in a server text channel.",
                    color=0xED4245,
                )
            )
        if not await self._require_manage_channels(ctx):
            return

        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        if overwrite.send_messages is False:
            return await ctx.send(
                embed=radon_embed(self.bot.config, "Channel Already Locked", "This channel is already locked.")
            )

        overwrite.send_messages = False
        try:
            await ctx.channel.set_permissions(
                ctx.guild.default_role,
                overwrite=overwrite,
                reason=f"Radon Client channel lock by {ctx.author}",
            )
        except discord.HTTPException as exc:
            print(f"[LOCK ERROR] {exc}")
            return await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Lock Failed",
                    "Discord rejected the channel permission update.",
                    color=0xED4245,
                )
            )

        await ctx.send(
            embed=radon_embed(
                self.bot.config,
                "Channel Locked",
                f"{ctx.channel.mention} has been locked. Regular members can no longer send messages here.",
            )
        )
        await send_log(
            self.bot,
            "moderationLogs",
            "Channel Locked",
            [
                ("Channel", ctx.channel.mention, True),
                ("Locked By", ctx.author.mention, True),
                ("Date / Time", discord.utils.format_dt(datetime.now(timezone.utc), "F"), False),
            ],
        )

    @commands.command()
    async def unlock(self, ctx):
        """Remove the bot's @everyone send-message lock from the current channel."""
        if not isinstance(ctx.channel, discord.TextChannel):
            return await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Unsupported Channel",
                    "This command can only be used in a server text channel.",
                    color=0xED4245,
                )
            )
        if not await self._require_manage_channels(ctx):
            return

        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        try:
            await ctx.channel.set_permissions(
                ctx.guild.default_role,
                overwrite=overwrite,
                reason=f"Radon Client channel unlock by {ctx.author}",
            )
        except discord.HTTPException as exc:
            print(f"[UNLOCK ERROR] {exc}")
            return await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Unlock Failed",
                    "Discord rejected the channel permission update.",
                    color=0xED4245,
                )
            )

        await ctx.send(
            embed=radon_embed(
                self.bot.config,
                "Channel Unlocked",
                f"{ctx.channel.mention} now uses its normal inherited send-message permissions again.",
            )
        )
        await send_log(
            self.bot,
            "moderationLogs",
            "Channel Unlocked",
            [
                ("Channel", ctx.channel.mention, True),
                ("Unlocked By", ctx.author.mention, True),
                ("Date / Time", discord.utils.format_dt(datetime.now(timezone.utc), "F"), False),
            ],
        )

    @commands.command()
    async def announce(self, ctx, *, text: str):
        """Delete the command message and publish a branded announcement in the configured channel."""
        channels_cfg = self.bot.config.get("channels", {})
        raw_channel_id = channels_cfg.get("announcements")
        channel = None

        # Prefer the configured channel ID. If it is missing/outdated, fall back to
        # a channel name so setup stays friendly for non-technical server owners.
        try:
            channel_id = int(raw_channel_id)
        except (TypeError, ValueError):
            channel_id = None

        if ctx.guild and channel_id is not None:
            channel = ctx.guild.get_channel(channel_id)
            if channel is None:
                try:
                    channel = await ctx.guild.fetch_channel(channel_id)
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    channel = None

        if ctx.guild and not isinstance(channel, discord.TextChannel):
            fallback_name = str(channels_cfg.get("announcementChannelName", "announcements")).strip().casefold()
            channel = next(
                (item for item in ctx.guild.text_channels if item.name.strip().casefold() == fallback_name),
                None,
            )

        if not isinstance(channel, discord.TextChannel):
            return await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Announcement Channel Not Found",
                    "Set `channels.announcements` in `config.json` to the announcement channel ID, or create a text channel named `#announcements`.",
                    color=0xED4245,
                ),
                delete_after=10,
            )

        me = ctx.guild.me
        perms = channel.permissions_for(me) if me else None
        if not perms or not perms.view_channel or not perms.send_messages or not perms.embed_links:
            return await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Missing Announcement Permissions",
                    f"I need **View Channel**, **Send Messages** and **Embed Links** in {channel.mention}.",
                    color=0xED4245,
                ),
                delete_after=10,
            )

        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            pass

        embed = radon_embed(self.bot.config, "Radon Announcement", text)
        embed.add_field(name="Published By", value=ctx.author.mention, inline=False)
        embed.timestamp = datetime.now(timezone.utc)

        try:
            await channel.send(embed=embed)
        except discord.HTTPException as exc:
            print(f"[ANNOUNCEMENT ERROR] {exc}")
            return await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Announcement Failed",
                    "Discord returned an error while publishing the announcement.",
                    color=0xED4245,
                ),
                delete_after=10,
            )

        if channel.id != ctx.channel.id:
            await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Announcement Published",
                    f"The announcement was posted in {channel.mention}.",
                ),
                delete_after=5,
            )

    @commands.command()
    async def dm(self, ctx, member: discord.Member, *, message: str):
        """Send a direct message through the same Discord Bot API v10 service used by the backend."""
        if member.bot:
            return await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "DM Blocked",
                    "This command is intended for server members, not bots.",
                    color=0xED4245,
                )
            )

        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            pass

        content = f"**RADON**\n\n{message}\n\nSent by: {ctx.author}"
        result = await self.bot.dm_service.send_radon_dm(member.id, content)
        if not result.get("success"):
            internal = result.get("internalError")
            if internal == "DM_BLOCKED_BY_DISCORD":
                detail = (
                    f"Discord blocked the DM to {member.mention} (`50007`). The member may have DMs disabled, "
                    "may have blocked the bot, may not share an eligible server with the bot, or may still be pending membership screening."
                )
            else:
                detail = (
                    f"Discord rejected the DM to {member.mention}. "
                    f"HTTP: `{result.get('discordStatus')}` • Code: `{result.get('discordCode')}`."
                )
            return await ctx.send(
                embed=radon_embed(self.bot.config, "DM Failed", detail, color=0xED4245),
                delete_after=12,
            )

        await ctx.send(
            embed=radon_embed(
                self.bot.config,
                "DM Sent",
                f"A direct message was sent to {member.mention}. Message ID: `{result.get('messageId')}`",
            ),
            delete_after=8,
        )

    @commands.command()
    async def testdm(self, ctx, member: discord.Member = None):
        """Owner DM diagnostic using the real Radon Bot API DM flow."""
        from core.radon_messages import test_dm

        member = member or ctx.author
        result = await self.bot.dm_service.send_radon_dm(member.id, test_dm())
        if result.get("success"):
            description = (
                f"DM test succeeded for {member.mention}.\n"
                f"Channel ID: `{result.get('channelId')}`\n"
                f"Message ID: `{result.get('messageId')}`"
            )
            return await ctx.send(embed=radon_embed(self.bot.config, "Radon DM Test • SENT", description))

        description = (
            f"DM test failed for {member.mention}.\n"
            f"HTTP: `{result.get('discordStatus')}`\n"
            f"Discord code: `{result.get('discordCode')}`\n"
            f"Internal result: `{result.get('internalError')}`\n"
            f"Discord message: `{result.get('error')}`"
        )
        await ctx.send(embed=radon_embed(self.bot.config, "Radon DM Test • FAILED", description, color=0xED4245))



async def setup(bot):
    await bot.add_cog(Admin(bot))
