import asyncio
import json
import math
import time
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from typing import Any

import aiohttp


DISCORD_API_BASE = "https://discord.com/api/v10"


class RadonDMService:
    """Discord Bot API v10 DM client.

    This deliberately uses the bot token and the documented two-step flow:
    create/open a DM channel, then create a message in that channel.
    """

    def __init__(self, bot_token: str, *, user_agent: str = "RadonClientBot/1.0"):
        self.bot_token = bot_token
        self.user_agent = user_agent
        self._session: aiohttp.ClientSession | None = None
        self._cooldown_until = 0.0
        self._request_lock = asyncio.Lock()

    async def start(self) -> None:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=20)
            self._session = aiohttp.ClientSession(timeout=timeout)

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bot {self.bot_token}",
            "Content-Type": "application/json",
            "User-Agent": self.user_agent,
        }

    async def _request_json(self, method: str, url: str, *, payload: dict[str, Any] | None = None) -> tuple[int, Any, str]:
        await self.start()
        assert self._session is not None

        # Serialize the supplemental REST calls and share the cooldown across
        # website-triggered DMs. These are separate from discord.py's own REST client.
        async with self._request_lock:
            if time.monotonic() < self._cooldown_until:
                return 429, {"message": "Discord cooldown active"}, "Discord cooldown active"
            for attempt in range(2):
                try:
                    async with self._session.request(method, url, headers=self.headers, json=payload) as response:
                        # Never print or store Cloudflare's HTML response content in logs.
                        raw = await response.text()
                        try:
                            body = json.loads(raw) if raw else {}
                        except json.JSONDecodeError:
                            body = {"message": "Non-JSON response from Discord"}
                        if response.status == 429:
                            retry_after = response.headers.get("Retry-After")
                            if retry_after is None and isinstance(body, dict):
                                retry_after = body.get("retry_after")
                            try:
                                seconds = float(retry_after)
                            except (ValueError, TypeError):
                                seconds = 0
                                if isinstance(retry_after, str):
                                    try:
                                        date = parsedate_to_datetime(retry_after)
                                        seconds = (date - datetime.now(timezone.utc)).total_seconds()
                                    except (ValueError, TypeError, OverflowError):
                                        pass
                            if not math.isfinite(seconds) or seconds <= 0:
                                seconds = 1800 if "1015" in raw else 60
                            # Respect the supplied cooldown; never retry rapidly.
                            seconds = min(max(seconds + 1, 1), 86400)
                            self._cooldown_until = time.monotonic() + seconds
                            if attempt == 0 and seconds <= 30:
                                await asyncio.sleep(seconds)
                                continue
                            return 429, body, "Discord rate limited"
                        if response.status in (401, 403):
                            # Repeated invalid requests contribute to Cloudflare bans.
                            self._cooldown_until = time.monotonic() + 3600
                        return response.status, body, "Discord response"
                except (aiohttp.ClientError, asyncio.TimeoutError):
                    return 0, {"message": "Discord network error"}, "Discord network error"
            return 429, {"message": "Discord cooldown active"}, "Discord cooldown active"

    @staticmethod
    def _failure_result(user_id: str, status: int, body: Any, body_text: str, *, stage: str) -> dict[str, Any]:
        code = None
        message = body_text or "Unknown Discord error"
        if isinstance(body, dict):
            code = body.get("code")
            message = body.get("message") or message

        if status == 403 and code == 50007:
            internal_error = "DM_BLOCKED_BY_DISCORD"
        elif status == 401 or code == 50014:
            internal_error = "INVALID_BOT_TOKEN"
        elif status == 429:
            internal_error = "DISCORD_RATE_LIMITED"
        elif status == 0:
            internal_error = "DISCORD_NETWORK_ERROR"
        else:
            internal_error = "DISCORD_DM_ERROR"

        # Never log Discord response bodies: Cloudflare HTML and upstream errors
        # can include unexpected sensitive information. Log only bounded metadata.
        print("[Radon DM]")
        print(f"User: {user_id}")
        print(f"Stage: {stage}")
        print(f"HTTP: {status}")
        print(f"Discord code: {code}")
        print(f"Category: {internal_error}")

        return {
            "success": False,
            "discordStatus": status,
            "discordCode": code,
            "error": internal_error,
            "internalError": internal_error,
            "stage": stage,
        }

    async def validate_token(self) -> dict[str, Any]:
        status, body, body_text = await self._request_json("GET", f"{DISCORD_API_BASE}/users/@me")
        if 200 <= status < 300 and isinstance(body, dict):
            return {
                "success": True,
                "userId": body.get("id"),
                "username": body.get("username"),
                "bot": bool(body.get("bot")),
            }
        return self._failure_result("@me", status, body, body_text, stage="validate_bot_token")

    async def send_radon_dm(self, discord_user_id: str | int, message: str) -> dict[str, Any]:
        user_id = str(discord_user_id).strip()
        if not user_id.isdigit():
            return {
                "success": False,
                "discordStatus": None,
                "discordCode": None,
                "error": "Invalid Discord User ID",
                "internalError": "INVALID_DISCORD_USER_ID",
                "stage": "validation",
            }
        if not isinstance(message, str) or not message.strip():
            return {
                "success": False,
                "discordStatus": None,
                "discordCode": None,
                "error": "Message cannot be empty",
                "internalError": "EMPTY_MESSAGE",
                "stage": "validation",
            }
        if len(message) > 2000:
            return {
                "success": False,
                "discordStatus": None,
                "discordCode": None,
                "error": "Discord message content exceeds 2000 characters",
                "internalError": "MESSAGE_TOO_LONG",
                "stage": "validation",
            }

        # Step 1: open or retrieve the DM channel.
        status, body, body_text = await self._request_json(
            "POST",
            f"{DISCORD_API_BASE}/users/@me/channels",
            payload={"recipient_id": user_id},
        )
        if not (200 <= status < 300) or not isinstance(body, dict) or not body.get("id"):
            return self._failure_result(user_id, status, body, body_text, stage="create_dm_channel")

        channel_id = str(body["id"])

        # Step 2: create the actual DM message.
        status, body, body_text = await self._request_json(
            "POST",
            f"{DISCORD_API_BASE}/channels/{channel_id}/messages",
            payload={
                "content": message,
                "allowed_mentions": {"parse": []},
            },
        )
        if not (200 <= status < 300) or not isinstance(body, dict) or not body.get("id"):
            return self._failure_result(user_id, status, body, body_text, stage="send_dm_message")

        result = {
            "success": True,
            "channelId": channel_id,
            "messageId": str(body["id"]),
        }
        print("[Radon DM]")
        print(f"User: {user_id}")
        print("Status: SENT")
        print(f"Message ID: {result['messageId']}")
        return result
