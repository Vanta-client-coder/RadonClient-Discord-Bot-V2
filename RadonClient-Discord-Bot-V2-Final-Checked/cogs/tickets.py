import re
import asyncio
from datetime import datetime, timezone

import discord
from discord.ext import commands

from core.config import is_placeholder
from core.embeds import radon_embed, add_safe_field
from core.logs import send_log
from core.permissions import is_owner_or_coowner, is_ticket_staff
from core.transcript import create_html_transcript
from core.ticket_auto_reply import match_ticket_issue
from core.ticket_categories import effective_ticket_types


def safe_channel_name(text):
    text = re.sub(r"[^a-z0-9-]", "-", text.lower())
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:80] or "user"


def ticket_type_from_config(bot, type_id):
    if type_id == "support" and not bot.config.get("tickets", {}).get("types"):
        return {"id": "support", "label": "Support", "openingPrompt": "Describe how our team can help you."}
    return next(
        (item for item in effective_ticket_types(bot.config) if item.get("id") == type_id),
        None,
    )


async def resolve_ticket_category(guild, category_id, category_name=None):
    channel = None
    if not is_placeholder(category_id) and str(category_id).isdigit():
        channel = guild.get_channel(int(category_id))
        if channel is None:
            try:
                channel = await guild.fetch_channel(int(category_id))
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                channel = None
        if isinstance(channel, discord.CategoryChannel):
            return channel

    # Friendly fallback: if an old/wrong ID is still configured, use the named category.
    if category_name:
        wanted = str(category_name).strip().casefold()
        for category in guild.categories:
            if category.name.strip().casefold() == wanted:
                return category
    return None


class TicketSelect(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot
        options = [
            discord.SelectOption(
                label=item["label"][:100],
                value=item["id"][:100],
                description=item.get("description", "")[:100],
            )
            for item in effective_ticket_types(bot.config)
        ]
        super().__init__(
            placeholder="Select a support category...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="vanta:ticket:create",
        )

    async def callback(self, interaction):
        await create_ticket(self.bot, interaction, self.values[0])


class TicketPanelView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.add_item(TicketSelect(bot))


class ConfirmCloseView(discord.ui.View):
    def __init__(self, bot, requester_id):
        super().__init__(timeout=60)
        self.bot = bot
        self.requester_id = requester_id

    @discord.ui.button(label="Confirm Close", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction, button):
        if interaction.user.id != self.requester_id:
            return await interaction.response.send_message(
                "Only the person who opened this confirmation can use it.",
                ephemeral=True,
            )
        await interaction.response.defer(ephemeral=True)
        await close_ticket(self.bot, interaction.channel, interaction.user)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction, button):
        if interaction.user.id != self.requester_id:
            return await interaction.response.send_message(
                "This confirmation does not belong to you.",
                ephemeral=True,
            )
        await interaction.response.edit_message(content="Ticket closure cancelled.", view=None)


class TicketActionView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="Claim Ticket",
        style=discord.ButtonStyle.primary,
        custom_id="vanta:ticket:claim",
    )
    async def claim(self, interaction, button):
        ticket = self.bot.db.get_ticket(interaction.channel_id)
        if not ticket:
            return await interaction.response.send_message(
                "This channel is not registered as an open ticket.",
                ephemeral=True,
            )
        if not is_ticket_staff(interaction.user, self.bot.config):
            return await interaction.response.send_message(
                "You are not a Radon ticket staff member.",
                ephemeral=True,
            )

        current = ticket["claimed_by"]
        if current and int(current) == interaction.user.id:
            return await interaction.response.send_message(
                "You have already claimed this ticket.",
                ephemeral=True,
            )
        if current and not is_owner_or_coowner(interaction.user, self.bot.config):
            return await interaction.response.send_message(
                f"This ticket is already claimed by <@{current}>.",
                ephemeral=True,
            )

        self.bot.db.claim_ticket(interaction.channel_id, interaction.user.id)
        await interaction.response.send_message(f"Ticket claimed by {interaction.user.mention}.")
        await send_log(
            self.bot,
            "ticketLogs",
            "Ticket Claimed",
            [
                ("Ticket", interaction.channel.mention, True),
                ("Claimed By", interaction.user.mention, True),
                ("Date / Time", discord.utils.format_dt(datetime.now(timezone.utc), "F"), False),
            ],
        )

    @discord.ui.button(
        label="Close Ticket",
        style=discord.ButtonStyle.danger,
        custom_id="vanta:ticket:close",
    )
    async def close(self, interaction, button):
        ticket = self.bot.db.get_ticket(interaction.channel_id)
        if not ticket:
            return await interaction.response.send_message(
                "This is not an open ticket.",
                ephemeral=True,
            )

        owner_can_close = int(ticket["owner_id"]) == interaction.user.id
        if not owner_can_close and not is_ticket_staff(interaction.user, self.bot.config):
            return await interaction.response.send_message(
                "You do not have permission to close this ticket.",
                ephemeral=True,
            )

        await interaction.response.send_message(
            "Are you sure you want to close this ticket? A transcript will be saved to the ticket log channel.",
            view=ConfirmCloseView(self.bot, interaction.user.id),
            ephemeral=True,
        )


async def create_ticket(bot, interaction, type_id):
    if not interaction.guild:
        return await interaction.response.send_message(
            "Tickets can only be created inside a server.",
            ephemeral=True,
        )

    tickets_cfg = bot.config.get("tickets", {})
    category_id = tickets_cfg.get("categoryId")
    category = await resolve_ticket_category(interaction.guild, category_id, tickets_cfg.get("categoryName", "TICKETS"))
    if category is None:
        return await interaction.response.send_message(
            "The configured ticket category could not be found. Check `tickets.categoryId` or create a category named `TICKETS`.",
            ephemeral=True,
        )

    existing = bot.db.get_open_tickets_for_user(interaction.guild.id, interaction.user.id)
    valid = []
    for row in existing:
        channel = interaction.guild.get_channel(int(row["channel_id"]))
        if channel is not None:
            valid.append(row)
        else:
            bot.db.close_ticket(row["channel_id"], datetime.now(timezone.utc).isoformat())

    maximum = max(1, int(tickets_cfg.get("maxTicketsPerUser", 1)))
    if len(valid) >= maximum:
        return await interaction.response.send_message(
            f"You already have the maximum number of open tickets (**{maximum}**). Please use your existing ticket instead of opening a duplicate.",
            ephemeral=True,
        )

    ticket_type = ticket_type_from_config(bot, type_id)
    if not ticket_type:
        return await interaction.response.send_message(
            "That ticket category is no longer available. Please refresh the panel and try again.",
            ephemeral=True,
        )

    await interaction.response.defer(ephemeral=True, thinking=True)

    bot_member = interaction.guild.me
    overwrites = {
        interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.user: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            attach_files=True,
            embed_links=True,
        ),
    }
    if bot_member:
        overwrites[bot_member] = discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            manage_channels=True,
            manage_messages=True,
            read_message_history=True,
            attach_files=True,
            embed_links=True,
        )

    role_cfg = bot.config.get("roles", {})
    role_ids = [role_cfg.get("owner"), role_cfg.get("coOwner")] + list(role_cfg.get("support", []))
    for role_id in role_ids:
        if role_id and str(role_id).isdigit():
            role = interaction.guild.get_role(int(role_id))
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                    embed_links=True,
                )

    channel_name = f"{safe_channel_name(type_id)}-{safe_channel_name(interaction.user.name)}"
    try:
        channel = await interaction.guild.create_text_channel(
            channel_name,
            category=category,
            overwrites=overwrites,
            reason=f"Radon Client ticket opened by {interaction.user}",
        )
    except discord.Forbidden:
        return await interaction.followup.send(
            "I do not have permission to create ticket channels in the configured category.",
            ephemeral=True,
        )
    except discord.HTTPException as exc:
        print(f"[TICKET CREATE ERROR] {exc}")
        return await interaction.followup.send(
            "The ticket could not be created because Discord returned an error. Please contact a Radon Owner.",
            ephemeral=True,
        )

    opened_at = datetime.now(timezone.utc).isoformat()
    bot.db.create_ticket(channel.id, interaction.guild.id, interaction.user.id, type_id, opened_at)

    welcome = tickets_cfg.get(
        "welcomeText",
        "Thank you for contacting Radon Support. Please describe your issue clearly.",
    )
    prompt = ticket_type.get("openingPrompt", "Please explain your request clearly.")
    embed = radon_embed(
        bot.config,
        f"Radon • {ticket_type['label']}",
        f"Welcome {interaction.user.mention}.\n\n{welcome}",
    )
    add_safe_field(embed, name="Ticket Type", value=ticket_type["label"], inline=True)
    add_safe_field(embed, name="Opened By", value=interaction.user.mention, inline=True)
    add_safe_field(embed, name="What to Include", value=prompt, inline=False)
    ticket_rule_text = (
        "No prank/test tickets, no spam, no duplicate tickets and no unnecessary staff pings. "
        "Please remain respectful."
    )
    if type_id == "giveaway-claim":
        ticket_rule_text += (
            " Giveaway claims are verified against the giveaway record. Fake claims or edited proof are not allowed."
        )
    add_safe_field(embed, name="Ticket Rules", value=ticket_rule_text, inline=False)
    add_safe_field(embed, name="Next Step", value="Describe your issue in your first message. Radon Auto Support can suggest a solution, and you can request staff help if needed.", inline=False)

    await channel.send(content=interaction.user.mention, embed=embed, view=TicketActionView(bot))
    await interaction.followup.send(
        f"Your **{ticket_type['label']}** ticket has been created: {channel.mention}",
        ephemeral=True,
    )
    await send_log(
        bot,
        "ticketLogs",
        "Ticket Opened",
        [
            ("Ticket", channel.mention, True),
            ("Owner", interaction.user.mention, True),
            ("Type", ticket_type["label"], True),
            ("Opened", discord.utils.format_dt(datetime.now(timezone.utc), "F"), False),
        ],
    )


async def close_ticket(bot, channel, closed_by):
    ticket = bot.db.get_ticket(channel.id)
    if not ticket:
        return

    closed_at = datetime.now(timezone.utc).isoformat()
    transcript = None
    try:
        transcript = await create_html_transcript(channel, ticket, closed_by)
    except Exception as exc:
        print(f"[TRANSCRIPT ERROR] {exc}")

    ticket_type = ticket_type_from_config(bot, ticket["type_id"])
    type_label = ticket_type.get("label", ticket["type_id"]) if ticket_type else ticket["type_id"]

    log_id = bot.config.get("channels", {}).get("ticketLogs")
    log_channel = bot.get_channel(int(log_id)) if str(log_id).isdigit() else None
    if log_channel is None and str(log_id).isdigit():
        try:
            log_channel = await bot.fetch_channel(int(log_id))
        except Exception:
            log_channel = None

    if log_channel:
        embed = radon_embed(bot.config, "Ticket Closed")
        add_safe_field(embed, name="Ticket Owner", value=f"<@{ticket['owner_id']}>", inline=True)
        add_safe_field(embed, name="Ticket Type", value=type_label, inline=True)
        add_safe_field(embed, name="Closed By", value=closed_by.mention, inline=True)
        add_safe_field(embed, 
            name="Claimed By",
            value=f"<@{ticket['claimed_by']}>" if ticket["claimed_by"] else "Not claimed",
            inline=True,
        )
        add_safe_field(embed, name="Opened At", value=ticket["opened_at"], inline=False)
        add_safe_field(embed, name="Closed At", value=closed_at, inline=False)

        kwargs = {"embed": embed}
        if transcript and transcript.exists():
            kwargs["file"] = discord.File(transcript, filename=transcript.name)
        try:
            await log_channel.send(**kwargs)
        except Exception as exc:
            print(f"[TICKET LOG ERROR] {exc}")

    bot.db.close_ticket(channel.id, closed_at)
    try:
        await channel.delete(reason=f"Radon Client ticket closed by {closed_by}")
    except discord.HTTPException as exc:
        print(f"[TICKET DELETE ERROR] {exc}")


REACTION_EMOJI = "🎫"
REACTION_PANEL_MARKER = "Radon Ticket Reaction Panel"


class ReactionResponse:
    async def defer(self, **kwargs):
        return None

    def __init__(self, user):
        self.user = user

    async def send_message(self, message, **kwargs):
        await ReactionFollowup(self.user).send(message, **kwargs)


class ReactionFollowup:
    def __init__(self, user):
        self.user = user

    async def send(self, message, **kwargs):
        try:
            await self.user.send(message)
        except (discord.Forbidden, discord.HTTPException):
            print("[Radon Tickets] Ticket feedback could not be delivered via DM.")


class ReactionTicketContext:
    def __init__(self, guild, member):
        self.guild = guild
        self.user = member
        self.response = ReactionResponse(member)
        self.followup = ReactionFollowup(member)


class AutoSupportFeedbackView(discord.ui.View):
    """Persistent, single-use feedback controls on automatic ticket answers."""
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    async def _handle(self, interaction, choice):
        ticket = self.bot.db.get_ticket(interaction.channel_id)
        if not ticket or str(ticket["owner_id"]) != str(interaction.user.id):
            return await interaction.response.send_message(
                "Only the person who opened this ticket can answer this question while the ticket is open.", ephemeral=True)
        if not self.bot.db.set_auto_support_feedback(interaction.channel_id, interaction.user.id, choice):
            return await interaction.response.send_message(
                "You have already responded, or the automatic support response is no longer active.", ephemeral=True)
        if choice == "helped":
            return await interaction.response.send_message(
                "Glad the suggestions helped! You can close your ticket when you're ready."
            )
        await interaction.response.send_message("A staff member has been requested. Please describe any extra details here.")
        cfg = self.bot.config.get("roles", {})
        role_values = cfg.get("support") or []
        if not isinstance(role_values, (list, tuple)):
            role_values = [role_values]
        # Ping Support only after an explicit user click; never @everyone.
        roles = [interaction.guild.get_role(int(x)) for x in role_values if str(x).isdigit()]
        roles = [r for r in roles if r is not None and r.mentionable]
        try:
            if roles:
                await interaction.channel.send(
                    " ".join(role.mention for role in roles) + " • Support requested by " + interaction.user.display_name,
                    allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=roles),
                )
            else:
                await interaction.channel.send(
                    "**Staff assistance requested.** A support team member can review this ticket. "
                    "(No mentionable Support role was configured.)",
                    allowed_mentions=discord.AllowedMentions.none(),
                )
        except (discord.Forbidden, discord.HTTPException):
            print("[Radon Tickets] Could not post the staff escalation message.")

    @discord.ui.button(label="That helped", style=discord.ButtonStyle.success,
                       custom_id="radon:auto_support:helped")
    async def helped(self, interaction, button):
        await self._handle(interaction, "helped")

    @discord.ui.button(label="Didn't help — Contact Staff", style=discord.ButtonStyle.primary,
                       custom_id="radon:auto_support:staff")
    async def staff(self, interaction, button):
        await self._handle(interaction, "staff")


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._reaction_locks = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        """Reply once to the first text message written by the ticket creator."""
        if not message.guild or message.author.bot or not isinstance(message.channel, discord.TextChannel):
            return
        content = (message.content or "").strip()
        if not content or content.startswith(self.bot.config.get("prefix", "!")):
            return
        # Avoid API lookups on messages in ordinary channels.
        ticket = self.bot.db.get_ticket(message.channel.id)
        if not ticket or str(message.author.id) != str(ticket["owner_id"]):
            return
        if not self.bot.db.claim_first_ticket_auto_reply(message.channel.id, message.author.id):
            return
        topic, reply = match_ticket_issue(content)
        try:
            await message.reply(
                embed=radon_embed(
                    self.bot.config,
                    f"Radon Auto Support • {topic}",
                    reply + "\n\n*This is an automatic suggestion based on your first message. "
                    "It may not match your issue exactly. If the steps helped, choose **That helped**. "
                    "Otherwise select **Didn't help — Contact Staff** and we will ask staff to assist.*",
                ),
                view=AutoSupportFeedbackView(self.bot),
                mention_author=False,
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except (discord.Forbidden, discord.HTTPException) as exc:
            print(f"[Radon Tickets] Auto reply could not be delivered ({type(exc).__name__}).")

    @commands.command(name="ticketreaction")
    async def ticketreaction(self, ctx):
        """Post a ticket panel where members react with 🎫 to create a support ticket."""
        if not ctx.guild or not is_owner_or_coowner(ctx.author, self.bot.config):
            return await ctx.send("Only a Radon Owner or Co-Owner can create a reaction ticket panel.")
        embed = radon_embed(
            self.bot.config, "Radon Support Tickets",
            "React with 🎫 below to open a private support ticket. "
            "You can only have the configured number of open tickets at once."
        )
        embed.set_footer(text=REACTION_PANEL_MARKER)
        try:
            message = await ctx.send(embed=embed)
            await message.add_reaction(REACTION_EMOJI)
        except discord.Forbidden:
            return await ctx.send("I need Send Messages, Embed Links and Add Reactions permissions.")
        except discord.HTTPException:
            return await ctx.send("Discord could not create the reaction ticket panel. Please retry later.")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.guild_id is None or str(payload.emoji) != REACTION_EMOJI:
            return
        if self.bot.user and payload.user_id == self.bot.user.id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return
        channel = guild.get_channel(payload.channel_id)
        if not isinstance(channel, discord.TextChannel):
            return
        try:
            message = await channel.fetch_message(payload.message_id)
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            return
        if not self.bot.user or message.author.id != self.bot.user.id:
            return
        if not message.embeds or not message.embeds[0].footer or message.embeds[0].footer.text != REACTION_PANEL_MARKER:
            return
        member = payload.member or guild.get_member(payload.user_id)
        if member is None:
            try:
                member = await guild.fetch_member(payload.user_id)
            except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                return
        if member.bot:
            return
        # Avoid duplicate channels from repeated reactions by the same user.
        key = (guild.id, member.id)
        lock = self._reaction_locks.setdefault(key, asyncio.Lock())
        try:
            async with lock:
                types = effective_ticket_types(self.bot.config)
                default_type = (types[0].get("id") if self.bot.config.get("tickets", {}).get("types") else "support")
                if default_type:
                    try:
                        await create_ticket(self.bot, ReactionTicketContext(guild, member), default_type)
                    except Exception as exc:
                        print(f"[Radon Tickets] Reaction ticket failed ({type(exc).__name__}).")
        finally:
            # Keep the lock registered: removing it while another event waits
            # could let a third event bypass the per-member queue.
            pass
        # Clearing the user's reaction lets them use the panel again later.
        try:
            await message.remove_reaction(payload.emoji, member)
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.command()
    async def ticketpanel(self, ctx):
        tickets_cfg = self.bot.config.get("tickets", {})
        panel = tickets_cfg.get("panel", {})
        embed = radon_embed(
            self.bot.config,
            panel.get("title", "Radon Support"),
            panel.get(
                "description",
                "Need help with Radon Client? Select the category that best matches your issue.",
            ),
        )

        category_lines = []
        for item in effective_ticket_types(self.bot.config):
            category_lines.append(f"**{item.get('label', item.get('id', 'Ticket'))}** — {item.get('details', item.get('description', 'Support request'))}")
        if category_lines:
            # Discord embed fields cap at 1024 characters. Avoid listing only some choices.
            preview = "\n".join(category_lines[:7])
            add_safe_field(embed, 
                name=panel.get("categoryTitle", "Choose the Right Category"),
                value=(preview[:900] + "\n**And more categories in the menu below.**")[:1024],
                inline=False,
            )

        rules = panel.get("rules", [])
        if rules:
            rules_text = "\n".join(f"• {rule}" for rule in rules)
            add_safe_field(embed, 
                name=panel.get("rulesTitle", "Ticket Rules"),
                value=rules_text[:1024],
                inline=False,
            )

        footer_note = panel.get("footerNote")
        if footer_note:
            add_safe_field(embed, name="Important", value=footer_note[:1024], inline=False)

        await ctx.send(embed=embed, view=TicketPanelView(self.bot))

    @commands.command()
    async def claim(self, ctx):
        ticket = self.bot.db.get_ticket(ctx.channel.id)
        if not ticket:
            return await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Not a Ticket",
                    "This command can only be used inside an open ticket.",
                    color=0xED4245,
                )
            )

        if ticket["claimed_by"] and int(ticket["claimed_by"]) == ctx.author.id:
            return await ctx.send(
                embed=radon_embed(self.bot.config, "Already Claimed", "You have already claimed this ticket.")
            )
        if ticket["claimed_by"] and not is_owner_or_coowner(ctx.author, self.bot.config):
            return await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Already Claimed",
                    f"This ticket is already claimed by <@{ticket['claimed_by']}>.",
                    color=0xED4245,
                )
            )

        self.bot.db.claim_ticket(ctx.channel.id, ctx.author.id)
        await ctx.send(
            embed=radon_embed(
                self.bot.config,
                "Ticket Claimed",
                f"This ticket is now claimed by {ctx.author.mention}.",
            )
        )
        await send_log(
            self.bot,
            "ticketLogs",
            "Ticket Claimed",
            [("Ticket", ctx.channel.mention, True), ("Claimed By", ctx.author.mention, True)],
        )

    @commands.command()
    async def close(self, ctx):
        if not self.bot.db.get_ticket(ctx.channel.id):
            return await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Not a Ticket",
                    "This command can only be used inside an open ticket.",
                    color=0xED4245,
                )
            )
        await ctx.send(
            "Are you sure you want to close this ticket? A transcript will be saved.",
            view=ConfirmCloseView(self.bot, ctx.author.id),
        )

    @commands.command()
    async def add(self, ctx, member: discord.Member):
        if not self.bot.db.get_ticket(ctx.channel.id):
            return await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Not a Ticket",
                    "This command can only be used inside an open ticket.",
                    color=0xED4245,
                )
            )

        await ctx.channel.set_permissions(
            member,
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            attach_files=True,
            embed_links=True,
            reason=f"Added to Radon Client ticket by {ctx.author}",
        )
        await ctx.send(
            embed=radon_embed(
                self.bot.config,
                "Member Added",
                f"{member.mention} can now access this ticket.",
            )
        )
        await send_log(
            self.bot,
            "ticketLogs",
            "Member Added to Ticket",
            [
                ("Ticket", ctx.channel.mention, True),
                ("Member", member.mention, True),
                ("Added By", ctx.author.mention, True),
            ],
        )

    @commands.command()
    async def remove(self, ctx, member: discord.Member):
        ticket = self.bot.db.get_ticket(ctx.channel.id)
        if not ticket:
            return await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Not a Ticket",
                    "This command can only be used inside an open ticket.",
                    color=0xED4245,
                )
            )
        if member.id == int(ticket["owner_id"]):
            return await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Action Blocked",
                    "The ticket owner cannot be removed from their own ticket.",
                    color=0xED4245,
                )
            )

        await ctx.channel.set_permissions(
            member,
            overwrite=None,
            reason=f"Removed from Radon Client ticket by {ctx.author}",
        )
        await ctx.send(
            embed=radon_embed(
                self.bot.config,
                "Member Removed",
                f"{member.mention} can no longer access this ticket.",
            )
        )
        await send_log(
            self.bot,
            "ticketLogs",
            "Member Removed from Ticket",
            [
                ("Ticket", ctx.channel.mention, True),
                ("Member", member.mention, True),
                ("Removed By", ctx.author.mention, True),
            ],
        )

    @commands.command()
    async def rename(self, ctx, *, new_name: str):
        if not self.bot.db.get_ticket(ctx.channel.id):
            return await ctx.send(
                embed=radon_embed(
                    self.bot.config,
                    "Not a Ticket",
                    "This command can only be used inside an open ticket.",
                    color=0xED4245,
                )
            )

        cleaned = safe_channel_name(new_name)
        await ctx.channel.edit(name=cleaned, reason=f"Radon Client ticket renamed by {ctx.author}")
        await ctx.send(
            embed=radon_embed(
                self.bot.config,
                "Ticket Renamed",
                f"This ticket has been renamed to `{cleaned}`.",
            )
        )
        await send_log(
            self.bot,
            "ticketLogs",
            "Ticket Renamed",
            [
                ("Ticket", ctx.channel.mention, True),
                ("New Name", cleaned, True),
                ("Renamed By", ctx.author.mention, True),
            ],
        )


async def setup(bot):
    await bot.add_cog(Tickets(bot))
