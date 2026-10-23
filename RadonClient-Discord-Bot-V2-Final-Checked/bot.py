import asyncio
import os
import shutil
import random
from pathlib import Path

import discord
from discord.ext import commands

from core.config import load_config, validate_config
from core.database import Database
from core.discord_dm import RadonDMService
from core.embeds import radon_embed
from core.permissions import command_allowed
from core.sales_channel import SalesChannelService
from events import setup_events
from services.internal_api import RadonInternalAPI
from status_monitor import setup_status_monitor

ROOT = Path(__file__).resolve().parent


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def database_path() -> Path:
    if os.getenv("DATABASE_URL", "").strip():
        return ROOT / "data" / "radon.db"  # Unused when PostgreSQL is configured.
    data_dir = Path(os.getenv("RADON_DATA_DIR", str(ROOT / "data"))).expanduser()
    if not data_dir.is_absolute():
        data_dir = ROOT / data_dir
    data_dir.mkdir(parents=True, exist_ok=True)

    current = data_dir / "radon.db"
    legacy_candidates = [ROOT / "data" / "vanta.db", data_dir / "vanta.db"]
    if not current.exists():
        for legacy in legacy_candidates:
            if not legacy.exists():
                continue
            try:
                shutil.copy2(legacy, current)
                print(f"[DATABASE] Migrated existing data from {legacy} to {current}.")
                break
            except OSError as exc:
                print(f"[DATABASE WARNING] Could not migrate {legacy}: {exc}")
    return current


class RadonBot(commands.Bot):
    def __init__(self, config, token: str):
        intents = discord.Intents.none()
        intents.guilds = True
        intents.members = True
        intents.messages = True
        intents.reactions = True
        intents.message_content = True

        super().__init__(
            command_prefix=config.get("prefix", "!"),
            intents=intents,
            help_command=None,
            case_insensitive=True,
        )

        self.config = config
        self.db = Database(database_path())
        self.dm_service = RadonDMService(token)
        self.sales_service = SalesChannelService(self, self.db)
        self.internal_api = RadonInternalAPI(self)
        self._services_closed = False

    async def setup_hook(self):
        # The HTTP server is started from main(), before any Discord login request.
        await self.dm_service.start()
        await self.sales_service.start()

        extensions = (
            "cogs.moderation",
            "cogs.utility",
            "cogs.tickets",
            "cogs.admin",
            "cogs.giveaways",
            "cogs.weekly_activity",
        )
        for extension in extensions:
            await self.load_extension(extension)
            print(f"[Radon] Loaded extension: {extension}")

        from cogs.tickets import TicketActionView, TicketPanelView, AutoSupportFeedbackView
        from cogs.giveaways import GiveawayView

        # Existing component IDs intentionally remain compatible with older
        # ticket panels and giveaway messages.
        self.add_view(TicketActionView(self))
        self.add_view(AutoSupportFeedbackView(self))
        from core.ticket_categories import effective_ticket_types
        if effective_ticket_types(self.config):
            self.add_view(TicketPanelView(self))
        else:
            print("[Radon Tickets] No ticket types configured; ticket panel disabled until configured.")
        self.add_view(GiveawayView(self))
        print("[Radon] Persistent Discord views registered.")

    async def close(self):
        if not self._services_closed:
            self._services_closed = True
            try:
                await self.internal_api.close()
            except Exception as exc:
                print(f"[Radon Shutdown] Internal API close error: {exc}")
            try:
                await self.sales_service.close()
            except Exception as exc:
                print(f"[Radon Shutdown] Sales service close error: {exc}")
            try:
                await self.dm_service.close()
            except Exception as exc:
                print(f"[Radon Shutdown] DM service close error: {exc}")
        await super().close()

    async def on_ready(self):
        import time
        self._radon_ready_monotonic = time.monotonic()
        self.connection_state = "online"
        self.last_connection_error = None
        status = self.config.get("botStatus", {})
        text = status.get("text", "Radon Client")
        kind = status.get("type", "watching").lower()
        activity_type = {
            "playing": discord.ActivityType.playing,
            "listening": discord.ActivityType.listening,
            "watching": discord.ActivityType.watching,
            "competing": discord.ActivityType.competing,
        }.get(kind, discord.ActivityType.watching)

        await self.change_presence(activity=discord.Activity(type=activity_type, name=text))

        print("=" * 56)
        print(f"Radon Bot is online as {self.user}")
        print(f"[Radon] Connected guilds: {len(self.guilds)}")
        print(f"[Radon] Members Intent: {self.intents.members}")
        print(f"[Radon] Message Content Intent: {self.intents.message_content}")

        configured_guild = str(self.config.get("guildId", ""))
        for guild in self.guilds:
            marker = " (configured)" if str(guild.id) == configured_guild else ""
            print(
                f"[Radon] Guild: {guild.name} ({guild.id}){marker} | "
                f"cached members={len(guild.members)} | Discord count={guild.member_count}"
            )

        await self._startup_config_audit()

        try:
            # Login already validated the token. This is optional diagnostics;
            # avoid an unnecessary REST call immediately after gateway login.
            token_check = {"success": True, "userId": str(self.user.id)}
            if token_check.get("success"):
                rest_id = str(token_check.get("userId"))
                gateway_id = str(self.user.id) if self.user else None
                if rest_id == gateway_id:
                    print(f"[Radon DM] Bot token verified for Discord user {rest_id}.")
                else:
                    print(f"[Radon DM WARNING] REST identity={rest_id}; Gateway identity={gateway_id}")
            else:
                print(f"[Radon DM WARNING] Bot token validation failed: {token_check}")
        except Exception as exc:
            print(f"[Radon DM ERROR] Token validation failed: {exc}")

        print("=" * 56)

    async def _startup_config_audit(self):
        guild_id = str(self.config.get("guildId", "")).strip()
        if not guild_id.isdigit():
            print("[CONFIG ERROR] guildId is invalid.")
            return

        guild = self.get_guild(int(guild_id))
        if guild is None:
            print(f"[CONFIG ERROR] Bot is not connected to configured guild {guild_id}.")
            return

        roles = self.config.get("roles", {})
        role_entries = {
            "owner": roles.get("owner"),
            "coOwner": roles.get("coOwner"),
            "dev": roles.get("dev"),
            "team": roles.get("team"),
            "autoRole": roles.get("autoRole"),
        }
        for key, raw in role_entries.items():
            if str(raw).isdigit() and guild.get_role(int(raw)) is None:
                print(f"[CONFIG ERROR] Role '{key}' ({raw}) does not exist in {guild.name}.")
        for raw in roles.get("support", []):
            if str(raw).isdigit() and guild.get_role(int(raw)) is None:
                print(f"[CONFIG ERROR] Support role {raw} does not exist in {guild.name}.")

        channels = self.config.get("channels", {})
        for key in (
            "moderationLogs",
            "ticketLogs",
            "announcements",
            "boostNotifications",
            "botStatus",
            "salesLicenseLogs",
        ):
            raw = channels.get(key)
            if str(raw).isdigit() and guild.get_channel(int(raw)) is None:
                print(f"[CONFIG ERROR] Channel '{key}' ({raw}) does not exist in {guild.name}.")

        category_id = str(self.config.get("tickets", {}).get("categoryId", ""))
        category = guild.get_channel(int(category_id)) if category_id.isdigit() else None
        if not isinstance(category, discord.CategoryChannel):
            print(f"[CONFIG ERROR] Ticket category {category_id} is not a valid Discord category.")

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.CheckFailure):
            return await ctx.send(
                embed=radon_embed(
                    self.config,
                    "Access Denied",
                    "Your Radon role does not have permission to use this command.",
                    color=0xED4245,
                )
            )
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(
                embed=radon_embed(
                    self.config,
                    "Missing Information",
                    "The command is incomplete. Use `!help` from an Owner or Co-Owner account to view command usage.",
                    color=0xED4245,
                )
            )
        if isinstance(error, commands.MemberNotFound):
            return await ctx.send(
                embed=radon_embed(
                    self.config,
                    "Member Not Found",
                    "Mention a valid member and try again.",
                    color=0xED4245,
                )
            )
        if isinstance(error, commands.BadArgument):
            return await ctx.send(
                embed=radon_embed(
                    self.config,
                    "Invalid Input",
                    "Check the command arguments and try again.",
                    color=0xED4245,
                )
            )

        original = getattr(error, "original", error)
        print(f"[COMMAND ERROR] {type(original).__name__}: {original}")
        try:
            await ctx.send(
                embed=radon_embed(
                    self.config,
                    "Something Went Wrong",
                    "A technical error occurred. Details were written to the bot console.",
                    color=0xED4245,
                )
            )
        except discord.HTTPException:
            pass


async def main():
    load_env_file(ROOT / ".env")
    token = os.getenv("DISCORD_TOKEN", "").strip()
    invalid_tokens = {
        "",
        "YOUR_DISCORD_BOT_TOKEN",
        "YOUR_BOT_TOKEN_HERE",
        "YOUR_NEW_BOT_TOKEN_HERE",
        "RESET_AND_PASTE_YOUR_NEW_TOKEN_HERE",
    }
    if token in invalid_tokens:
        print("[Radon ERROR] DISCORD_TOKEN is missing.")
        print("[Radon ERROR] Set DISCORD_TOKEN in Render -> Environment.")
        return

    try:
        config = load_config()
    except (OSError, ValueError) as exc:
        print("[Radon CONFIG ERROR] Missing or invalid configuration. Set RADON_CONFIG_JSON in Render Environment using your original config.json contents; see NEW-RENDER-SETUP.md.")
        print(f"[Radon CONFIG ERROR] Type: {type(exc).__name__}")
        return
    issues = validate_config(config)
    if issues:
        print("[Radon CONFIG ERROR] Missing/invalid configuration: " + ", ".join(issues))
        print("[Radon CONFIG ERROR] Configure RADON_CONFIG_JSON privately in Render before deployment.")
        return

    bot = RadonBot(config, token)
    setup_events(bot)
    setup_status_monitor(bot)

    @bot.check
    async def radon_role_gate(ctx):
        if ctx.guild is None or not isinstance(ctx.author, discord.Member):
            return False
        return command_allowed(ctx.author, ctx.command.qualified_name, bot.config)

    # Start HTTP once. Discord login may fail before setup_hook is ever called.
    # Never restart the whole Render process in a tight loop on a Cloudflare block.
    bot.connection_state = "starting"
    bot.last_connection_error = None
    await bot.internal_api.start()
    consecutive_failures = 0
    try:
        while True:
            try:
                bot.connection_state = "connecting"
                bot.last_connection_error = None
                print("[Radon Connect] Attempting Discord connection.")
                await bot.start(token, reconnect=True)
                # A clean gateway exit is not a reason for rapid reconnection.
                print("[Radon Connect] Discord connection exited.")
                bot.connection_state = "disconnected"
                break
            except discord.LoginFailure:
                bot.connection_state = "invalid_token"
                bot.last_connection_error = "Discord rejected the configured token"
                print("[Radon ERROR] Invalid Discord bot token. Check Render DISCORD_TOKEN; no automatic retries.")
                break
            except discord.PrivilegedIntentsRequired:
                bot.connection_state = "missing_intents"
                bot.last_connection_error = "Discord privileged intents are not enabled"
                print("[Radon ERROR] Enable Server Members and Message Content intents in the Discord Developer Portal. No automatic retries.")
                break
            except (discord.HTTPException, OSError, asyncio.TimeoutError) as exc:
                consecutive_failures += 1
                status = getattr(exc, "status", None)
                description = str(exc)[:500].lower()
                is_cloudflare = "1015" in description
                is_limited = status == 429 or is_cloudflare or "rate limit" in description
                if status in (401, 403) and not is_limited:
                    bot.connection_state = "discord_denied"
                    bot.last_connection_error = f"HTTP {status}"
                    print(f"[Radon ERROR] Discord access denied (HTTP {status}); inspect token and permissions. No automatic retries.")
                    break
                bot.connection_state = "rate_limited" if is_limited else "connection_error"
                bot.last_connection_error = f"HTTP {status}" if status else type(exc).__name__
                if is_limited:
                    # Cloudflare IP restrictions cannot be bypassed in application code.
                    # Very conservative exponential cooldown with jitter.
                    delay = min(7200, 1800 * (2 ** min(consecutive_failures - 1, 2)))
                else:
                    delay = min(1800, 60 * (2 ** min(consecutive_failures - 1, 5)))
                delay += random.uniform(0, min(60, delay * 0.1))
                print(f"[Radon Connect] {bot.connection_state}, {bot.last_connection_error}; retry in {int(delay)} seconds. No token or response body logged.")
                await asyncio.sleep(delay)
                # When discord.py has already closed this instance, attempting
                # a new login on it can re-use unusable state. Instead exit and
                # let Render supervise the restart after the cooldown.
                if bot.is_closed():
                    print("[Radon Connect] Discord client is closed; automatic retry is unsafe without a fresh bot instance.")
                    bot.connection_state = "restart_required"
                    break
            except Exception as exc:
                bot.connection_state = "unexpected_error"
                bot.last_connection_error = type(exc).__name__
                print(f"[Radon ERROR] Unexpected connection failure: {type(exc).__name__}. Inspect Render logs.")
                break
        # Keep HTTP diagnostics reachable after a nonretryable failure.
        if bot.connection_state in {"invalid_token", "missing_intents", "discord_denied", "unexpected_error", "restart_required"}:
            print("[Radon] HTTP health endpoint remains available for diagnosis.")
            await asyncio.Event().wait()
    finally:
        if not bot.is_closed():
            await bot.close()
        elif bot.internal_api.runner:
            await bot.internal_api.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[Radon] Bot stopped manually.")
