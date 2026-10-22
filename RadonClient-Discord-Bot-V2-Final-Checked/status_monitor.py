"""Conservative Discord status heartbeat. Avoids excessive API traffic."""
import asyncio
import random
import re
import time
from datetime import datetime, timezone

import discord
from discord.ext import tasks

STATUS_EMBED_TITLE = "Radon Bot Status"


def _now_ts():
    return int(datetime.now(timezone.utc).timestamp())


def _duration(seconds):
    seconds = max(0, int(seconds))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return " ".join(f"{v}{unit}" for v, unit in ((days, "d"), (hours, "h"), (minutes, "m"), (seconds, "s")) if v or unit == "s")


def _extract_timestamp(text):
    match = re.search(r"<t:(\d+)(?::[A-Za-z])?>", text or "")
    return int(match.group(1)) if match else None


def _is_limited(exc):
    return isinstance(exc, discord.HTTPException) and (
        exc.status == 429 or "1015" in str(exc)[:220] or "rate limit" in str(exc)[:220].lower()
    )


class RadonStatusMonitor:
    def __init__(self, bot):
        self.bot = bot
        self.online_since = None
        self.status_message_id = None
        self._message = None
        self._initialized = False
        self._lock = asyncio.Lock()
        self._pause_until = 0.0
        self._failures = 0
        self._last_warning = 0.0
        self.last_success_ts = None
        self.last_attempt_ts = None
        self.last_failure_type = None
        self.disabled_reason = None
        configured = bot.config.get("monitor", {}).get("heartbeatSeconds", 600)
        try:
            self.heartbeat_seconds = max(300, min(3600, int(configured)))
        except (ValueError, TypeError):
            self.heartbeat_seconds = 600
        self.heartbeat.change_interval(seconds=self.heartbeat_seconds)

    def diagnostics(self):
        age = max(0, _now_ts() - self.last_success_ts) if self.last_success_ts else None
        return {
            "state": "disabled" if self.disabled_reason else (
                "offline" if not self.bot.is_ready() else (
                    "cooldown" if time.monotonic() < self._pause_until else (
                        "stale" if age is not None and age > 2 * self.heartbeat_seconds + 120 else (
                            "active" if age is not None else "pending"
                        )
                    )
                )
            ),
            "intervalSeconds": self.heartbeat_seconds,
            "lastSuccessfulHeartbeat": self.last_success_ts,
            "lastAttempt": self.last_attempt_ts,
            "lastSuccessfulAgeSeconds": age,
            "consecutiveFailures": self._failures,
            "lastFailureType": self.last_failure_type,
            "disabledReason": self.disabled_reason,
        }

    def _failure(self, operation, exc):
        self._failures += 1
        self.last_failure_type = type(exc).__name__
        if isinstance(exc, discord.Forbidden):
            # Missing channel permissions cannot be fixed by repeated requests.
            self.disabled_reason = "missing_discord_channel_permissions"
            print("[Radon Status] Missing Discord status-channel permission; monitor disabled until next service start.")
            return
        base = 1800 if _is_limited(exc) else 180
        cooldown = min(7200, base * (2 ** min(self._failures - 1, 3)))
        cooldown += random.uniform(0, min(60, cooldown * 0.1))
        self._pause_until = time.monotonic() + cooldown
        if time.monotonic() - self._last_warning > 300:
            print(f"[Radon Status] {operation} failed ({type(exc).__name__}, HTTP {getattr(exc, 'status', 'n/a')}); retry paused for {int(cooldown)}s.")
            self._last_warning = time.monotonic()

    async def _channel(self):
        raw = str(self.bot.config.get("channels", {}).get("botStatus", "")).strip()
        if not raw.isdigit():
            self.disabled_reason = "invalid_status_channel_config"
            print("[Radon Status] Invalid channels.botStatus configuration; monitor disabled.")
            return None
        channel = self.bot.get_channel(int(raw))
        if channel is None:
            channel = await self.bot.fetch_channel(int(raw))
        if not isinstance(channel, discord.TextChannel):
            self.disabled_reason = "status_channel_not_text"
            print("[Radon Status] botStatus is not a text channel; monitor disabled.")
            return None
        return channel

    async def _find_message_once(self, channel):
        async for message in channel.history(limit=15):
            if self.bot.user and message.author.id == self.bot.user.id and message.embeds:
                if message.embeds[0].title == STATUS_EMBED_TITLE:
                    self.status_message_id = message.id
                    self._message = message
                    return message
        return None

    def _embed(self):
        now = _now_ts()
        started = self.online_since or now
        embed = discord.Embed(
            title=STATUS_EMBED_TITLE,
            description="🟢 **ONLINE**\n\nStatus refreshes periodically. An old heartbeat may indicate interrupted connectivity.",
            color=0x20D5DD,
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="Online since", value=f"<t:{started}:F>\n<t:{started}:R>", inline=False)
        embed.add_field(name="Last heartbeat", value=f"<t:{now}:F>\n<t:{now}:R>", inline=False)
        embed.add_field(name="Current uptime", value=_duration(now - started), inline=True)
        embed.add_field(name="Heartbeat interval", value=f"{self.heartbeat_seconds} seconds", inline=True)
        embed.set_footer(text="Radon • Status can become stale if Discord API access is limited")
        return embed

    async def refresh(self):
        if self.disabled_reason or time.monotonic() < self._pause_until or not self.bot.is_ready():
            return
        async with self._lock:
            if self.disabled_reason or time.monotonic() < self._pause_until or not self.bot.is_ready():
                return
            self.last_attempt_ts = _now_ts()
            try:
                channel = await self._channel()
                if channel is None:
                    return
                if not self._initialized:
                    self._initialized = True
                    await self._find_message_once(channel)
                if self._message:
                    await self._message.edit(embed=self._embed())
                else:
                    self._message = await channel.send(embed=self._embed())
                    self.status_message_id = self._message.id
                self.last_success_ts = _now_ts()
                if self._failures:
                    print("[Radon Status] Discord heartbeat recovered.")
                self._failures = 0
                self.last_failure_type = None
            except discord.NotFound:
                self._message = None
                self.status_message_id = None
                self._pause_until = time.monotonic() + self.heartbeat_seconds
            except (discord.Forbidden, discord.HTTPException, OSError, asyncio.TimeoutError) as exc:
                self._failure("Heartbeat", exc)
            except Exception as exc:
                self._failure("Unexpected heartbeat error", exc)

    @tasks.loop(seconds=600)
    async def heartbeat(self):
        await self.refresh()

    @heartbeat.before_loop
    async def before_heartbeat(self):
        await self.bot.wait_until_ready()

    async def on_ready(self):
        if self.online_since is None:
            self.online_since = _now_ts()
        if not self.heartbeat.is_running():
            self.heartbeat.start()
        print(f"[Radon Status] Monitor active; interval {self.heartbeat_seconds}s.")

    async def on_resumed(self):
        print("[Radon Status] Gateway resumed; scheduled heartbeat continues.")

    async def on_disconnect(self):
        print("[Radon Status] Gateway disconnected; heartbeat pauses until ready.")


def setup_status_monitor(bot):
    monitor = RadonStatusMonitor(bot)
    bot.add_listener(monitor.on_ready, "on_ready")
    bot.add_listener(monitor.on_resumed, "on_resumed")
    bot.add_listener(monitor.on_disconnect, "on_disconnect")
    bot.radon_status_monitor = monitor
    return monitor
