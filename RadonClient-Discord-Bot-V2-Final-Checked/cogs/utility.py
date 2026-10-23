import discord
from discord.ext import commands

from core.embeds import radon_embed, add_safe_field


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx, *, command_name: str = None):
        """Display only commands that the user can actually run, with usage guidance."""
        from core.permissions import command_allowed
        if command_name:
            command = self.bot.get_command(command_name.strip().lower())
            if command is None or command.hidden or not command_allowed(ctx.author, command.qualified_name, self.bot.config):
                return await ctx.send(embed=radon_embed(self.bot.config, "Command not available", "This command is unavailable to your role or does not exist.", kind="warning"))
            prefix = self.bot.config.get("prefix", "!")
            usage = f"{prefix}{command.qualified_name} {command.signature}".strip()
            embed = radon_embed(self.bot.config, f"Help • {command.qualified_name}", command.help or "No description is available.")
            add_safe_field(embed, "Usage", f"`{usage}`")
            return await ctx.send(embed=embed)

        categories = {
            "General": ["help", "ping", "userinfo", "membercount", "serverinfo", "botinfo", "uptime"],
            "Moderation": ["ban", "kick", "timeout", "untimeout", "clear", "warn", "warnings", "delwarn"],
            "Tickets": ["ticketpanel", "ticketreaction", "claim", "close", "add", "remove", "rename"],
            "Weekly Community": ["weeklyactivity"],
            "Giveaways": ["giveaway", "giveawayend", "giveawayreroll", "giveawaycancel"],
            "Management": ["lock", "unlock", "announce", "dm", "testdm"],
        }
        prefix = self.bot.config.get("prefix", "!")
        embed = radon_embed(self.bot.config, "Radon Client • Command Center", "Commands shown below are available to your configured roles. Use `" + prefix + "help <command>` for syntax and details.")
        found = 0
        for category, names in categories.items():
            visible = [n for n in names if self.bot.get_command(n) and command_allowed(ctx.author, n, self.bot.config)]
            if visible:
                add_safe_field(embed, category, "  ".join(f"`{prefix}{n}`" for n in visible))
                found += len(visible)
        if not found:
            add_safe_field(embed, "No available commands", "Contact support if you believe this is a mistake.")
        embed.set_footer(text="Radon Client V2 • Discord permissions and role hierarchy still apply")
        await ctx.send(embed=embed)

    @commands.command(name="botinfo", help="Show the client bot's connection and feature overview.")
    async def botinfo(self, ctx):
        embed = radon_embed(self.bot.config, "Radon Client • Bot Information", "Community management, support tickets, giveaways and scheduled activity summaries.")
        add_safe_field(embed, "Connection", "Connected to Discord" if self.bot.is_ready() else "Connecting", inline=True)
        add_safe_field(embed, "Servers", str(len(self.bot.guilds)), inline=True)
        add_safe_field(embed, "Latency", f"{max(0, round(self.bot.latency * 1000))} ms", inline=True)
        add_safe_field(embed, "Support", "Use the configured ticket panel for assistance.")
        await ctx.send(embed=embed)

    @commands.command(name="uptime", help="Display how long the bot has been connected since its latest ready event.")
    async def uptime(self, ctx):
        import time
        started = getattr(self.bot, "_radon_ready_monotonic", None)
        if started is None:
            message = "Startup duration is not available yet."
        else:
            seconds = max(0, int(time.monotonic() - started))
            days, rem = divmod(seconds, 86400)
            hours, rem = divmod(rem, 3600)
            minutes, secs = divmod(rem, 60)
            message = f"**{days}d {hours}h {minutes}m {secs}s** since the latest ready event."
        await ctx.send(embed=radon_embed(self.bot.config, "Radon Client • Uptime", message))

    @commands.command()
    async def ping(self, ctx):
        await ctx.send(
            embed=radon_embed(
                self.bot.config,
                "Pong",
                f"Gateway latency: **{round(self.bot.latency * 1000)} ms**",
            )
        )

    @commands.command()
    async def userinfo(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        roles = [role.mention for role in member.roles[1:]][-15:]
        embed = radon_embed(self.bot.config, f"User Information • {member}")
        embed.add_field(name="Username", value=str(member), inline=True)
        embed.add_field(name="Display Name", value=member.display_name, inline=True)
        embed.add_field(name="User ID", value=member.id, inline=False)
        embed.add_field(name="Account Created", value=discord.utils.format_dt(member.created_at, "F"), inline=False)
        embed.add_field(
            name="Joined Server",
            value=discord.utils.format_dt(member.joined_at, "F") if member.joined_at else "Unknown",
            inline=False,
        )
        embed.add_field(name="Roles", value=" ".join(roles) if roles else "None", inline=False)
        await ctx.send(embed=embed)


    @commands.command()
    async def membercount(self, ctx):
        guild = ctx.guild
        total = guild.member_count or len(guild.members)
        bots = sum(1 for member in guild.members if member.bot)
        humans = max(0, total - bots)
        embed = radon_embed(self.bot.config, "Member Count")
        embed.add_field(name="Total Members", value=str(total), inline=True)
        embed.add_field(name="Members", value=str(humans), inline=True)
        embed.add_field(name="Bots", value=str(bots), inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def serverinfo(self, ctx):
        guild = ctx.guild
        embed = radon_embed(self.bot.config, f"Server Information • {guild.name}")
        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(name="Channels", value=len(guild.channels), inline=True)
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="Created", value=discord.utils.format_dt(guild.created_at, "F"), inline=False)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Utility(bot))
