import discord
from discord.ext import commands

from core.embeds import radon_embed


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx):
        embed = radon_embed(
            self.bot.config,
            "Radon Commands",
            "Command access is controlled by your configured Radon role. Commands not listed for a role are blocked.",
        )
        embed.add_field(
            name="Radon Owner / Radon Co-Owner",
            value=(
                "Full access: moderation, tickets, utility and management commands.\n"
                "`!lock` `!unlock` `!announce <text>` `!dm @member <text>` `!membercount`\n"
                "`!giveaway <duration> <winners> <prize>` `!giveawayend <message-id>`\n"
                "`!giveawayreroll <message-id>` `!giveawaycancel <message-id>`"
            ),
            inline=False,
        )
        embed.add_field(
            name="Radon Dev",
            value="`!ban @member [reason]`\n`!kick @member [reason]`\n`!timeout @member <duration> [reason]`",
            inline=False,
        )
        embed.add_field(
            name="Radon Team",
            value="`!timeout @member <duration> [reason]`",
            inline=False,
        )
        embed.add_field(
            name="Radon Support",
            value="`!claim` `!close` `!add @member` `!remove @member` `!rename <name>`",
            inline=False,
        )
        embed.add_field(
            name="Timeout Examples",
            value="`30s` • `10m` • `2h` • `1d` • maximum `28d`",
            inline=False,
        )
        await ctx.send(embed=embed)

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
