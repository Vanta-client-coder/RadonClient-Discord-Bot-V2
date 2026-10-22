import uuid
from datetime import datetime, timezone

import discord
from discord.ext import commands

from core.embeds import radon_embed
from core.logs import send_log
from core.permissions import bot_has, can_moderate
from core.timeparse import parse_duration


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _target_check(self, ctx, member, **bot_permissions):
        allowed, reason = can_moderate(ctx, member)
        if not allowed:
            await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Action Blocked",
                    reason,
                    color=0xED4245,
                )
            )
            return False

        missing = bot_has(ctx, **bot_permissions)
        if missing:
            readable = ", ".join(name.replace("_", " ").title() for name in missing)
            await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Missing Bot Permissions",
                    f"I need the following permission(s): **{readable}**.",
                    color=0xED4245,
                )
            )
            return False
        return True

    @commands.command()
    async def ban(self, ctx, member: discord.Member, *, reason="No reason provided"):
        if not await self._target_check(ctx, member, ban_members=True):
            return
        try:
            await member.ban(reason=f"{reason} | Moderator: {ctx.author}")
        except discord.HTTPException as exc:
            print(f"[BAN ERROR] {exc}")
            return await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Ban Failed",
                    "Discord rejected the ban. Check the bot role position and permissions.",
                    color=0xED4245,
                )
            )

        await ctx.send(
            embed=radon_embed(
                self.bot.config,
                "Member Banned",
                f"{member.mention} has been banned.\n**Reason:** {reason}",
            )
        )
        await send_log(
            self.bot,
            "moderationLogs",
            "Member Banned",
            [
                ("Moderator", ctx.author.mention, True),
                ("Member", str(member), True),
                ("User ID", member.id, False),
                ("Reason", reason, False),
                ("Date / Time", discord.utils.format_dt(datetime.now(timezone.utc), "F"), False),
            ],
        )

    @commands.command()
    async def kick(self, ctx, member: discord.Member, *, reason="No reason provided"):
        if not await self._target_check(ctx, member, kick_members=True):
            return
        try:
            await member.kick(reason=f"{reason} | Moderator: {ctx.author}")
        except discord.HTTPException as exc:
            print(f"[KICK ERROR] {exc}")
            return await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Kick Failed",
                    "Discord rejected the kick. Check the bot role position and permissions.",
                    color=0xED4245,
                )
            )

        await ctx.send(
            embed=radon_embed(
                self.bot.config,
                "Member Kicked",
                f"{member.mention} has been kicked.\n**Reason:** {reason}",
            )
        )
        await send_log(
            self.bot,
            "moderationLogs",
            "Member Kicked",
            [
                ("Moderator", ctx.author.mention, True),
                ("Member", str(member), True),
                ("User ID", member.id, False),
                ("Reason", reason, False),
                ("Date / Time", discord.utils.format_dt(datetime.now(timezone.utc), "F"), False),
            ],
        )

    @commands.command()
    async def timeout(self, ctx, member: discord.Member, duration: str, *, reason="No reason provided"):
        delta = parse_duration(duration)
        if delta is None:
            return await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Invalid Duration",
                    "Use a duration such as `30s`, `10m`, `2h`, `1d` or up to `28d`.",
                    color=0xED4245,
                )
            )
        if not await self._target_check(ctx, member, moderate_members=True):
            return

        try:
            await member.timeout(delta, reason=f"{reason} | Moderator: {ctx.author}")
        except discord.HTTPException as exc:
            print(f"[TIMEOUT ERROR] {exc}")
            return await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Timeout Failed",
                    "Discord rejected the timeout. Check the bot role position and permissions.",
                    color=0xED4245,
                )
            )

        await ctx.send(
            embed=radon_embed(
                self.bot.config,
                "Timeout Applied",
                f"{member.mention} has been timed out for **{duration}**.\n**Reason:** {reason}",
            )
        )
        await send_log(
            self.bot,
            "moderationLogs",
            "Timeout Applied",
            [
                ("Moderator", ctx.author.mention, True),
                ("Member", member.mention, True),
                ("Duration", duration, True),
                ("Reason", reason, False),
                ("Date / Time", discord.utils.format_dt(datetime.now(timezone.utc), "F"), False),
            ],
        )

    @commands.command()
    async def untimeout(self, ctx, member: discord.Member, *, reason="No reason provided"):
        if not await self._target_check(ctx, member, moderate_members=True):
            return
        try:
            await member.timeout(None, reason=f"{reason} | Moderator: {ctx.author}")
        except discord.HTTPException as exc:
            print(f"[UNTIMEOUT ERROR] {exc}")
            return await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Timeout Removal Failed",
                    "Discord rejected the request. Check the bot role position and permissions.",
                    color=0xED4245,
                )
            )

        await ctx.send(
            embed=radon_embed(
                self.bot.config,
                "Timeout Removed",
                f"The timeout for {member.mention} has been removed.\n**Reason:** {reason}",
            )
        )
        await send_log(
            self.bot,
            "moderationLogs",
            "Timeout Removed",
            [
                ("Moderator", ctx.author.mention, True),
                ("Member", member.mention, True),
                ("Reason", reason, False),
                ("Date / Time", discord.utils.format_dt(datetime.now(timezone.utc), "F"), False),
            ],
        )

    @commands.command()
    async def clear(self, ctx, amount: int):
        if amount < 1 or amount > 100:
            return await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Invalid Amount",
                    "Choose a number between **1** and **100**.",
                    color=0xED4245,
                )
            )

        missing = bot_has(ctx, manage_messages=True)
        if missing:
            return await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Missing Bot Permission",
                    "I need the **Manage Messages** permission in this channel.",
                    color=0xED4245,
                )
            )

        try:
            deleted = await ctx.channel.purge(limit=amount + 1)
        except discord.HTTPException as exc:
            print(f"[CLEAR ERROR] {exc}")
            return await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Clear Failed",
                    "I could not delete the requested messages.",
                    color=0xED4245,
                )
            )

        count = max(0, len(deleted) - 1)
        message = await ctx.send(
            embed=radon_embed(
                self.bot.config,
                "Messages Cleared",
                f"Deleted **{count}** message(s).",
            )
        )
        try:
            await message.delete(delay=4)
        except Exception:
            pass

        await send_log(
            self.bot,
            "moderationLogs",
            "Messages Cleared",
            [
                ("Moderator", ctx.author.mention, True),
                ("Amount", count, True),
                ("Channel", ctx.channel.mention, False),
                ("Date / Time", discord.utils.format_dt(datetime.now(timezone.utc), "F"), False),
            ],
        )

    @commands.command()
    async def warn(self, ctx, member: discord.Member, *, reason="No reason provided"):
        if member.bot:
            return await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Action Blocked",
                    "Bots cannot receive warnings.",
                    color=0xED4245,
                )
            )

        warning_id = uuid.uuid4().hex[:8].upper()
        created = datetime.now(timezone.utc).isoformat()
        self.bot.db.add_warning(warning_id, ctx.guild.id, member.id, ctx.author.id, reason, created)

        await ctx.send(
            embed=radon_embed(
                self.bot.config,
                "Warning Added",
                f"{member.mention} received warning `{warning_id}`.\n**Reason:** {reason}",
            )
        )
        await send_log(
            self.bot,
            "moderationLogs",
            "Warning Added",
            [
                ("Moderator", ctx.author.mention, True),
                ("Member", member.mention, True),
                ("Warning ID", warning_id, True),
                ("Reason", reason, False),
                ("Date / Time", discord.utils.format_dt(datetime.now(timezone.utc), "F"), False),
            ],
        )

    @commands.command()
    async def warnings(self, ctx, member: discord.Member):
        rows = self.bot.db.get_warnings(ctx.guild.id, member.id)
        if not rows:
            return await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Warnings",
                    f"{member.mention} has no warnings.",
                )
            )

        embed = radon_embed(self.bot.config, f"Warnings • {member}")
        for row in rows[:20]:
            embed.add_field(
                name=f"Warning {row['warning_id']}",
                value=(
                    f"**Reason:** {row['reason']}\n"
                    f"**Moderator ID:** {row['moderator_id']}\n"
                    f"**Created:** {row['created_at']}"
                ),
                inline=False,
            )
        if len(rows) > 20:
            embed.description = f"Showing the newest 20 of {len(rows)} warning(s)."
        await ctx.send(embed=embed)

    @commands.command()
    async def delwarn(self, ctx, member: discord.Member, warning_id: str):
        warning_id = warning_id.upper()
        deleted = self.bot.db.delete_warning(ctx.guild.id, member.id, warning_id)
        if not deleted:
            return await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Warning Not Found",
                    "That warning ID does not exist for this member.",
                    color=0xED4245,
                )
            )

        await ctx.send(
            embed=radon_embed(
                self.bot.config,
                "Warning Deleted",
                f"Warning `{warning_id}` has been deleted.",
            )
        )
        await send_log(
            self.bot,
            "moderationLogs",
            "Warning Deleted",
            [
                ("Moderator", ctx.author.mention, True),
                ("Member", member.mention, True),
                ("Warning ID", warning_id, False),
                ("Date / Time", discord.utils.format_dt(datetime.now(timezone.utc), "F"), False),
            ],
        )


async def setup(bot):
    await bot.add_cog(Moderation(bot))
