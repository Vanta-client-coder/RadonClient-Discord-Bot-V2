import random
from datetime import datetime, timezone

import discord
from discord.ext import commands, tasks

from core.embeds import radon_embed
from core.timeparse import parse_duration


class GiveawayView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="Enter Giveaway",
        style=discord.ButtonStyle.primary,
        custom_id="vanta:giveaway:enter",
    )
    async def enter(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            return await interaction.response.send_message("Bots cannot enter giveaways.", ephemeral=True)
        if not interaction.message:
            return await interaction.response.send_message("This giveaway could not be identified.", ephemeral=True)

        giveaway = self.bot.db.get_giveaway(interaction.message.id)
        if not giveaway or giveaway["status"] != "active":
            return await interaction.response.send_message("This giveaway is no longer active.", ephemeral=True)

        now_ts = int(datetime.now(timezone.utc).timestamp())
        if int(giveaway["ends_at"]) <= now_ts:
            cog = self.bot.get_cog("Giveaways")
            if cog:
                await cog.finish_giveaway(interaction.message.id)
            return await interaction.response.send_message("This giveaway has already ended.", ephemeral=True)

        added = self.bot.db.add_giveaway_entry(interaction.message.id, interaction.user.id)
        if not added:
            return await interaction.response.send_message("You are already entered in this giveaway.", ephemeral=True)

        count = self.bot.db.count_giveaway_entries(interaction.message.id)
        await interaction.response.send_message(
            f"You entered **{giveaway['prize']}**. Current entries: **{count}**.",
            ephemeral=True,
        )


class Giveaways(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.giveaway_watcher.start()

    def cog_unload(self):
        self.giveaway_watcher.cancel()

    @tasks.loop(seconds=15)
    async def giveaway_watcher(self):
        now_ts = int(datetime.now(timezone.utc).timestamp())
        for row in self.bot.db.get_due_giveaways(now_ts):
            try:
                await self.finish_giveaway(int(row["message_id"]))
            except Exception as exc:
                print(f"[GIVEAWAY END ERROR] {exc}")

    @giveaway_watcher.before_loop
    async def before_giveaway_watcher(self):
        await self.bot.wait_until_ready()

    def _embed(self, giveaway, *, status="active", entry_count=None):
        ends_at = datetime.fromtimestamp(int(giveaway["ends_at"]), tz=timezone.utc)
        if status == "active":
            description = (
                f"**Prize:** {giveaway['prize']}\n"
                f"**Winners:** {giveaway['winners']}\n"
                f"**Ends:** {discord.utils.format_dt(ends_at, 'R')} ({discord.utils.format_dt(ends_at, 'F')})\n"
                f"**Hosted By:** <@{giveaway['host_id']}>\n\n"
                "Click **Enter Giveaway** below to participate. One entry per member.\n"
                "Winners must use **Giveaway Claim** in the Radon ticket panel to receive their prize."
            )
            title = "Radon Giveaway"
        elif status == "cancelled":
            description = f"**Prize:** {giveaway['prize']}\n\nThis giveaway was cancelled."
            title = "Giveaway Cancelled"
        else:
            description = f"**Prize:** {giveaway['prize']}\n\nThis giveaway has ended."
            title = "Giveaway Ended"

        embed = radon_embed(self.bot.config, title, description)
        if entry_count is not None:
            embed.add_field(name="Entries", value=str(entry_count), inline=True)
        return embed

    async def _fetch_message(self, giveaway):
        channel_id = int(giveaway["channel_id"])
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                return None, None
        try:
            message = await channel.fetch_message(int(giveaway["message_id"]))
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            message = None
        return channel, message

    async def finish_giveaway(self, message_id: int, *, ended_by=None):
        giveaway = self.bot.db.get_giveaway(message_id)
        if not giveaway or giveaway["status"] != "active":
            return False

        # Claim the finish operation first so two watcher cycles cannot announce twice.
        if not self.bot.db.set_giveaway_status(message_id, "ended", only_if_active=True):
            return False

        entries = [int(row["user_id"]) for row in self.bot.db.get_giveaway_entries(message_id)]
        winner_count = min(int(giveaway["winners"]), len(entries))
        winner_ids = random.sample(entries, winner_count) if winner_count else []
        channel, message = await self._fetch_message(giveaway)

        if message:
            try:
                await message.edit(
                    embed=self._embed(giveaway, status="ended", entry_count=len(entries)),
                    view=None,
                )
            except discord.HTTPException as exc:
                print(f"[GIVEAWAY EDIT ERROR] {exc}")

        if channel:
            if winner_ids:
                mentions = ", ".join(f"<@{user_id}>" for user_id in winner_ids)
                text = (
                    f"Congratulations {mentions}! You won **{giveaway['prize']}**.\n\n"
                    "To receive your prize, open the Radon ticket panel and choose **Giveaway Claim**. "
                    "Include this giveaway message/link and the prize you won so staff can verify your claim."
                )
            else:
                text = f"The giveaway for **{giveaway['prize']}** ended with no valid entries."
            if ended_by:
                text += f"\nEnded early by {ended_by.mention}."
            try:
                await channel.send(embed=radon_embed(self.bot.config, "Giveaway Results", text))
            except discord.HTTPException as exc:
                print(f"[GIVEAWAY RESULT ERROR] {exc}")
        return True

    @commands.command()
    async def giveaway(self, ctx, duration: str, winners: int, *, prize: str):
        """Usage: !giveaway 10m 1 Nitro"""
        delta = parse_duration(duration)
        if delta is None:
            return await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Invalid Giveaway Duration",
                    "Use a duration such as `30s`, `10m`, `2h`, `1d` or up to `28d`.",
                    color=0xED4245,
                )
            )

        max_winners = int(self.bot.config.get("giveaways", {}).get("maxWinners", 10))
        if winners < 1 or winners > max_winners:
            return await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Invalid Winner Count",
                    f"Choose between **1** and **{max_winners}** winners.",
                    color=0xED4245,
                )
            )
        if len(prize.strip()) < 1 or len(prize) > 200:
            return await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Invalid Prize",
                    "The prize must be between 1 and 200 characters.",
                    color=0xED4245,
                )
            )

        ends_at = int((datetime.now(timezone.utc) + delta).timestamp())
        temp = {
            "prize": prize.strip(),
            "winners": winners,
            "host_id": str(ctx.author.id),
            "ends_at": ends_at,
        }
        message = await ctx.send(embed=self._embed(temp, status="active", entry_count=0), view=GiveawayView(self.bot))
        self.bot.db.create_giveaway(
            message.id,
            ctx.guild.id,
            ctx.channel.id,
            prize.strip(),
            winners,
            ctx.author.id,
            ends_at,
            int(datetime.now(timezone.utc).timestamp()),
        )

    @commands.command()
    async def giveawayend(self, ctx, message_id: int):
        giveaway = self.bot.db.get_giveaway(message_id)
        if not giveaway:
            return await ctx.send(
                embed=radon_embed(self.bot.config, "Giveaway Not Found", "No giveaway with that message ID exists.", color=0xED4245)
            )
        if giveaway["status"] != "active":
            return await ctx.send(
                embed=radon_embed(self.bot.config, "Giveaway Already Finished", "That giveaway is no longer active.", color=0xED4245)
            )
        await self.finish_giveaway(message_id, ended_by=ctx.author)
        await ctx.send(embed=radon_embed(self.bot.config, "Giveaway Ended", "The giveaway was ended successfully."), delete_after=6)

    @commands.command()
    async def giveawayreroll(self, ctx, message_id: int):
        giveaway = self.bot.db.get_giveaway(message_id)
        if not giveaway:
            return await ctx.send(
                embed=radon_embed(self.bot.config, "Giveaway Not Found", "No giveaway with that message ID exists.", color=0xED4245)
            )
        if giveaway["status"] == "active":
            return await ctx.send(
                embed=radon_embed(self.bot.config, "Giveaway Still Active", "End the giveaway before rerolling it.", color=0xED4245)
            )
        entries = [int(row["user_id"]) for row in self.bot.db.get_giveaway_entries(message_id)]
        if not entries:
            return await ctx.send(
                embed=radon_embed(self.bot.config, "No Entries", "This giveaway has no entries to reroll.", color=0xED4245)
            )
        winner_count = min(int(giveaway["winners"]), len(entries))
        winner_ids = random.sample(entries, winner_count)
        mentions = ", ".join(f"<@{user_id}>" for user_id in winner_ids)
        await ctx.send(
            embed=radon_embed(
                self.bot.config,
                "Giveaway Reroll",
                f"New winner(s) for **{giveaway['prize']}**: {mentions}",
            )
        )

    @commands.command()
    async def giveawaycancel(self, ctx, message_id: int):
        giveaway = self.bot.db.get_giveaway(message_id)
        if not giveaway:
            return await ctx.send(
                embed=radon_embed(self.bot.config, "Giveaway Not Found", "No giveaway with that message ID exists.", color=0xED4245)
            )
        if giveaway["status"] != "active":
            return await ctx.send(
                embed=radon_embed(self.bot.config, "Giveaway Already Finished", "That giveaway is no longer active.", color=0xED4245)
            )

        self.bot.db.set_giveaway_status(message_id, "cancelled", only_if_active=True)
        entries = self.bot.db.count_giveaway_entries(message_id)
        _, message = await self._fetch_message(giveaway)
        if message:
            try:
                await message.edit(embed=self._embed(giveaway, status="cancelled", entry_count=entries), view=None)
            except discord.HTTPException as exc:
                print(f"[GIVEAWAY CANCEL EDIT ERROR] {exc}")
        await ctx.send(embed=radon_embed(self.bot.config, "Giveaway Cancelled", "The giveaway was cancelled."), delete_after=6)


async def setup(bot):
    await bot.add_cog(Giveaways(bot))
