import asyncio

import discord


def setup_events(bot: discord.Client) -> None:
    """Register auto-role and server-boost events without replacing bot.on_ready."""

    async def give_auto_role(member: discord.Member) -> None:
        if member.bot:
            return

        role_id = str(bot.config.get("roles", {}).get("autoRole", "")).strip()
        if not role_id.isdigit():
            print("[Radon AutoRole] Invalid roles.autoRole in config.json.")
            return

        role = member.guild.get_role(int(role_id))
        if role is None:
            print(
                f"[Radon AutoRole] Role {role_id} not found in "
                f"{member.guild.name} ({member.guild.id})."
            )
            return

        if role in member.roles:
            return

        me = member.guild.me
        if me is None:
            print("[Radon AutoRole] Bot member object is not available yet.")
            return

        if not me.guild_permissions.manage_roles:
            print("[Radon AutoRole] Missing Manage Roles permission.")
            return

        if me.top_role <= role:
            print(
                f"[Radon AutoRole] Bot role is not above auto-role '{role.name}'. "
                "Move the Radon bot role higher in Server Settings -> Roles."
            )
            return

        try:
            await member.add_roles(role, reason="Radon automatic member role")
            print(f"[Radon AutoRole] Added {role.name} to {member} ({member.id}).")
        except discord.Forbidden:
            print(
                f"[Radon AutoRole] Forbidden while giving {role.name} to "
                f"{member} ({member.id}). Check role hierarchy and Manage Roles."
            )
        except discord.HTTPException as exc:
            print(f"[Radon AutoRole] Discord error for {member} ({member.id}): {exc}")
        except Exception as exc:
            print(f"[Radon AutoRole] Unexpected error for {member} ({member.id}): {exc}")

    async def startup_auto_role_scan() -> None:
        await bot.wait_until_ready()

        if not bot.intents.members:
            print("[Radon AutoRole] Members Intent is disabled in Python.")
            return

        configured_guild_id = str(bot.config.get("guildId", "")).strip()
        print("[Radon AutoRole] Startup scan started.")

        for guild in bot.guilds:
            if configured_guild_id.isdigit() and guild.id != int(configured_guild_id):
                continue

            role_id = str(bot.config.get("roles", {}).get("autoRole", "")).strip()
            role = guild.get_role(int(role_id)) if role_id.isdigit() else None
            if role is None:
                print(f"[Radon AutoRole] Configured auto-role not found in {guild.name}.")
                continue

            try:
                members = [member async for member in guild.fetch_members(limit=None)]
                print(f"[Radon AutoRole] Fetched {len(members)} members from {guild.name}.")
            except discord.Forbidden:
                print(
                    f"[Radon AutoRole] Discord refused the member list for {guild.name}. "
                    "Enable Server Members Intent in the Developer Portal."
                )
                continue
            except discord.HTTPException as exc:
                print(f"[Radon AutoRole] Could not fetch members from {guild.name}: {exc}")
                continue

            for member in members:
                if bot.is_closed():
                    return
                if member.bot or role in member.roles:
                    continue
                await give_auto_role(member)
                await asyncio.sleep(0.25)

        print("[Radon AutoRole] Startup scan completed.")

    async def on_member_join(member: discord.Member) -> None:
        configured_guild_id = str(bot.config.get("guildId", "")).strip()
        if configured_guild_id.isdigit() and member.guild.id != int(configured_guild_id):
            return
        print(f"[Radon AutoRole] Member joined: {member} ({member.id}).")
        await give_auto_role(member)

    async def on_member_update(before: discord.Member, after: discord.Member) -> None:
        if before.premium_since is not None or after.premium_since is None:
            return

        channel_id = str(bot.config.get("channels", {}).get("boostNotifications", "")).strip()
        if not channel_id.isdigit():
            print("[Radon Boost] Invalid channels.boostNotifications in config.json.")
            return

        channel = after.guild.get_channel(int(channel_id))
        if channel is None:
            try:
                channel = await bot.fetch_channel(int(channel_id))
            except (discord.NotFound, discord.Forbidden, discord.HTTPException) as exc:
                print(f"[Radon Boost] Could not resolve boost channel {channel_id}: {exc}")
                return

        if not isinstance(channel, discord.abc.Messageable):
            print(f"[Radon Boost] Channel {channel_id} cannot receive messages.")
            return

        total_boosts = after.guild.premium_subscription_count or 0
        embed = discord.Embed(
            title="🚀 Server Boost!",
            description=(
                f"Thank you {after.mention} for boosting the server!\n\n"
                "Your support helps make **Radon Client** even better."
            ),
            color=0x20D5DD,
        )
        embed.set_thumbnail(url=after.display_avatar.url)
        embed.set_footer(text=f"Radon • Total Server Boosts: {total_boosts}")

        try:
            await channel.send(embed=embed)
            print(f"[Radon Boost] Notification sent for {after} ({after.id}).")
        except discord.Forbidden:
            print("[Radon Boost] Missing permission to send in the boost channel.")
        except discord.HTTPException as exc:
            print(f"[Radon Boost] Discord error while sending notification: {exc}")

    def start_scan_once() -> None:
        if getattr(bot, "_radon_auto_role_scan_started", False):
            return
        bot._radon_auto_role_scan_started = True
        bot._radon_auto_role_scan_task = asyncio.create_task(
            startup_auto_role_scan(),
            name="radon-auto-role-startup-scan",
        )

    async def on_connect() -> None:
        start_scan_once()

    bot.add_listener(on_connect, "on_connect")
    bot.add_listener(on_member_join, "on_member_join")
    bot.add_listener(on_member_update, "on_member_update")
