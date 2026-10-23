"""Radon weekly activity and opt-in staff recruitment, discord.py 2.x."""
import asyncio
from datetime import datetime, timedelta, timezone
import discord
from discord.ext import commands, tasks
from core.embeds import radon_embed, add_safe_field
from core.weekly_activity import CHANNEL_ID, is_eligible, monday_start, week_key
from core.permissions import is_owner_or_coowner


class InviteSelector(discord.ui.Select):
    def __init__(self, people):
        self.people = {str(uid): count for uid, count in people}
        super().__init__(placeholder='Select a member from the top 10', min_values=1, max_values=1,
                         options=[discord.SelectOption(label=f'#{i} · {uid}', description=f'{count} messages', value=str(uid))
                                  for i, (uid, count) in enumerate(people, 1)], custom_id='radon:weekly:select')

    async def callback(self, interaction):
        if not is_owner_or_coowner(interaction.user, interaction.client.config):
            return await interaction.response.send_message('Only Owner or Co-Owner may select candidates.', ephemeral=True)
        self.view.selected[interaction.user.id] = int(self.values[0])
        await interaction.response.send_message(f'Selected <@{self.values[0]}>. Click **Send Staff Invitation** to send the DM.', ephemeral=True)


class WeeklyView(discord.ui.View):
    def __init__(self, bot, week, people):
        super().__init__(timeout=None)
        self.bot = bot
        self.week = week
        self.people = people
        self.selected = {}
        if people:
            self.add_item(InviteSelector(people))

    @discord.ui.button(label='Send Staff Invitation', style=discord.ButtonStyle.primary, custom_id='radon:weekly:invite')
    async def invite(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_owner_or_coowner(interaction.user, self.bot.config):
            return await interaction.response.send_message('Owner or Co-Owner only.', ephemeral=True)
        uid = self.selected.get(interaction.user.id)
        if uid is None or uid not in [int(x) for x, _ in self.people]:
            return await interaction.response.send_message('Choose a member using the dropdown first.', ephemeral=True)
        member = interaction.guild.get_member(uid)
        if member is None:
            try:
                member = await interaction.guild.fetch_member(uid)
            except discord.HTTPException:
                return await interaction.response.send_message('Member could not be found.', ephemeral=True)
        if not is_eligible(member, self.bot.config):
            return await interaction.response.send_message('This member is now staff or otherwise ineligible.', ephemeral=True)
        if not self.bot.db.mark_weekly_invitation(interaction.guild_id, self.week, uid, interaction.user.id):
            return await interaction.response.send_message('An invitation was already sent to this member for this week.', ephemeral=True)
        try:
            await member.send(
                '**Radon Client — Staff Invitation**\n\n'
                'Hello! You have been one of our most active community members recently. '
                'Would you be interested in applying to join the Radon Client staff team?\n\n'
                'This is only an invitation to discuss the opportunity, not an automatic staff appointment. '
                'You can reply to an Owner or open a support ticket if you are interested. '
                'There is no obligation to accept. Please do not share passwords or private information.'
            )
        except (discord.Forbidden, discord.HTTPException):
            self.bot.db.clear_weekly_invitation(interaction.guild_id, self.week, uid)
            return await interaction.response.send_message('Could not send a DM. The user may have DMs disabled.', ephemeral=True)
        await interaction.response.send_message(f'Invitation sent privately to {member.mention}.', ephemeral=True)


class WeeklyActivity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.report_loop.start()

    def cog_unload(self):
        self.report_loop.cancel()

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or message.guild.id != int(self.bot.config.get('guildId', 0)):
            return
        if message.channel.id == CHANNEL_ID or not is_eligible(message.author, self.bot.config):
            return
        # Ignore commands, spammy one-character messages and ticket channels.
        if not message.content or len(message.content.strip()) < 3 or message.content.startswith(self.bot.command_prefix):
            return
        if self.bot.db.get_ticket(message.channel.id):
            return
        timestamp = message.created_at or datetime.now(timezone.utc)
        self.bot.db.record_weekly_message(message.guild.id, week_key(timestamp), message.author.id, timestamp.timestamp())

    @commands.command(name='weeklyactivity')
    async def weeklyactivity(self, ctx):
        if not is_owner_or_coowner(ctx.author, self.bot.config):
            return await ctx.send('Owner or Co-Owner only.')
        current = week_key(datetime.now(timezone.utc))
        rows = self.bot.db.weekly_top(ctx.guild.id, current, 100)
        eligible = []
        for uid, count in rows:
            member = ctx.guild.get_member(int(uid))
            if member and is_eligible(member, self.bot.config):
                eligible.append((uid, count))
            if len(eligible) >= 10:
                break
        lines = [f'{i}. <@{uid}> — {count} messages' for i, (uid, count) in enumerate(eligible, 1)]
        await ctx.send(embed=radon_embed(self.bot.config, title='Radon — Current Weekly Activity (Preview)',
                  description='\n'.join(lines) if lines else 'No eligible messages counted yet.'),
                  allowed_mentions=discord.AllowedMentions.none())

    @tasks.loop(hours=1)
    async def report_loop(self):
        now = datetime.now(timezone.utc)
        current_start = monday_start(now)
        previous = current_start - timedelta(days=7)
        week = week_key(previous)
        guild = self.bot.get_guild(int(self.bot.config['guildId']))
        if not guild or self.bot.db.get_weekly_report(guild.id, week):
            return
        channel = guild.get_channel(CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            print('[Radon Weekly] Weekly leaderboard channel missing or inaccessible.')
            return
        rows = self.bot.db.weekly_top(guild.id, week, 100)
        eligible = []
        for uid, count in rows:
            member = guild.get_member(int(uid))
            if member is None:
                try:
                    member = await guild.fetch_member(int(uid))
                except discord.HTTPException:
                    continue
            if is_eligible(member, self.bot.config):
                eligible.append((int(uid), int(count)))
            if len(eligible) >= 10:
                break
        embed = radon_embed(self.bot.config, 'Radon Client — Weekly Community Top 10', description='Most active non-staff members (UTC week starting '+week+').\n'
                              'Messages are counted in regular server channels; tickets, bot commands and very short messages are excluded.\n'
                              '**Owner/Co-Owner:** Select someone and send an optional staff invitation.')
        add_safe_field(embed, name='Leaderboard', value='\n'.join(f'**{i}.** <@{uid}> — {count} messages' for i, (uid,count) in enumerate(eligible,1)) if eligible else 'No eligible activity recorded.', inline=False)
        embed.set_footer(text='Radon Client • Activity does not guarantee staff selection')
        view = WeeklyView(self.bot, week, eligible) if eligible else None
        try:
            sent = await channel.send(embed=embed, view=view, allowed_mentions=discord.AllowedMentions.none())
        except discord.HTTPException as exc:
            print(f'[Radon Weekly] Unable to post report: {type(exc).__name__}')
            return
        self.bot.db.set_weekly_report(guild.id, week, channel.id, sent.id)
        if view:
            self.bot.add_view(view, message_id=sent.id)

    @report_loop.before_loop
    async def before_report(self):
        await self.bot.wait_until_ready()
        # Restore interactive dropdowns after a restart without creating duplicate reports.
        guild_id = int(self.bot.config['guildId'])
        for week, channel_id, message_id in self.bot.db.recent_weekly_reports(guild_id, 8):
            people = self.bot.db.weekly_top(guild_id, week, 10)
            if people:
                self.bot.add_view(WeeklyView(self.bot, week, people), message_id=int(message_id))


async def setup(bot):
    await bot.add_cog(WeeklyActivity(bot))
