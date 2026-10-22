import hmac
import os
from typing import Any

from aiohttp import web

from core.radon_messages import (
    giveaway_created_dm,
    license_claimed_dm,
    license_created_dm,
    license_deactivated_dm,
    license_deleted_dm,
    license_reactivated_dm,
    test_dm,
    welcome_dm,
)


class RadonInternalAPI:
    """Render HTTP service + private Radon backend API.

    Public endpoints: GET / and GET /health.
    All /api/v1/* endpoints require X-Radon-API-Key or Bearer auth.
    The API key must only exist server-side.
    """

    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.getenv("RADON_INTERNAL_API_KEY", "").strip()
        self.host = "0.0.0.0"
        try:
            self.port = int(os.getenv("PORT", os.getenv("RADON_API_PORT", "8080")))
        except ValueError:
            self.port = 8080
        self.runner: web.AppRunner | None = None
        self.site: web.TCPSite | None = None

    @property
    def enabled(self) -> bool:
        return bool(self.api_key and self.api_key != "CHANGE_ME_TO_A_LONG_RANDOM_SECRET")

    def _authorized(self, request: web.Request) -> bool:
        supplied = request.headers.get("X-Radon-API-Key", "")
        if not supplied:
            auth = request.headers.get("Authorization", "")
            if auth.startswith("Bearer "):
                supplied = auth[7:].strip()
        return self.enabled and bool(supplied) and hmac.compare_digest(supplied, self.api_key)

    @web.middleware
    async def auth_middleware(self, request: web.Request, handler):
        if request.path in {"/", "/health"}:
            return await handler(request)
        if not self.enabled:
            return web.json_response(
                {"success": False, "error": "Radon internal API is disabled."},
                status=503,
            )
        if not self._authorized(request):
            return web.json_response({"success": False, "error": "Unauthorized"}, status=401)
        return await handler(request)

    async def start(self):
        app = web.Application(middlewares=[self.auth_middleware], client_max_size=128 * 1024)
        app.add_routes([
            web.get("/", self.home),
            web.get("/health", self.health),
            web.post("/api/v1/dm/send", self.dm_send),
            web.post("/api/v1/dm/test", self.dm_test),
            web.post("/api/v1/dm/welcome", self.dm_welcome),
            web.post("/api/v1/license/created", self.license_created),
            web.post("/api/v1/license/giveaway-created", self.giveaway_created),
            web.post("/api/v1/license/claimed", self.license_claimed),
            web.post("/api/v1/license/deactivated", self.license_deactivated),
            web.post("/api/v1/license/reactivated", self.license_reactivated),
            web.post("/api/v1/license/delete-notice", self.license_delete_notice),
            web.post("/api/v1/license/deleted", self.license_deleted),
            web.post("/api/v1/dm/diagnose", self.dm_diagnose),
        ])

        self.runner = web.AppRunner(app, access_log=None)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        try:
            await self.site.start()
        except OSError as exc:
            print(f"[Radon API ERROR] Could not bind {self.host}:{self.port}: {exc}")
            await self.runner.cleanup()
            self.runner = None
            self.site = None
            raise

        print(f"[Radon API] Render HTTP service listening on {self.host}:{self.port}")
        if self.enabled:
            print("[Radon API] Protected backend endpoints are enabled.")
        else:
            print("[Radon API] Backend endpoints disabled until RADON_INTERNAL_API_KEY is configured.")

    async def close(self):
        if self.runner:
            await self.runner.cleanup()
            self.runner = None
            self.site = None

    async def home(self, request):
        return web.Response(text="Radon HTTP service is running. Check /health for Discord status.", status=200)

    async def health(self, request):
        return web.json_response({
            "service": "Radon Discord Bot",
            "online": bool(self.bot.is_ready()),
            "discordConnectionState": "online" if self.bot.is_ready() else getattr(self.bot, "connection_state", "offline"),
            "discordLastError": None if self.bot.is_ready() else getattr(self.bot, "last_connection_error", None),
            "discordUserId": str(self.bot.user.id) if self.bot.user else None,
            "guildCount": len(self.bot.guilds),
            "backendApiEnabled": self.enabled,
            "heartbeat": (self.bot.radon_status_monitor.diagnostics()
                          if hasattr(self.bot, "radon_status_monitor") else None),
        })

    async def _json(self, request: web.Request) -> dict[str, Any] | None:
        try:
            payload = await request.json()
        except Exception:
            return None
        return payload if isinstance(payload, dict) else None

    @staticmethod
    def _user_id(payload: dict[str, Any]) -> str:
        return str(payload.get("discordUserId", "")).strip()

    @staticmethod
    def _license_key(payload: dict[str, Any]) -> str:
        return str(payload.get("licenseKey", "")).strip()

    @staticmethod
    def _bad_request(message: str):
        return web.json_response({"success": False, "error": message}, status=400)

    async def _send(self, user_id: str, message: str):
        # DM delivery is a notification only. Failure must never imply rollback.
        return await self.bot.dm_service.send_radon_dm(user_id, message)

    @staticmethod
    async def _event_response(dm_result: dict[str, Any] | None, sales_result: dict[str, Any] | None = None):
        return web.json_response({
            "accepted": True,
            "dm": dm_result,
            "sales": sales_result,
            "rollbackRequired": False,
        })

    async def dm_send(self, request):
        payload = await self._json(request)
        if payload is None:
            return self._bad_request("JSON body required.")
        user_id = self._user_id(payload)
        message = str(payload.get("message", ""))
        if not user_id or not message.strip():
            return self._bad_request("discordUserId and message are required.")
        return await self._event_response(await self._send(user_id, message))

    async def dm_test(self, request):
        payload = await self._json(request)
        if payload is None or not self._user_id(payload):
            return self._bad_request("discordUserId is required.")
        return await self._event_response(await self._send(self._user_id(payload), test_dm()))

    async def dm_welcome(self, request):
        payload = await self._json(request)
        if payload is None or not self._user_id(payload):
            return self._bad_request("discordUserId is required.")
        user_id = self._user_id(payload)
        username = str(payload.get("username", "")).strip() or await self._resolve_username(user_id)
        return await self._event_response(await self._send(user_id, welcome_dm(username)))

    async def license_created(self, request):
        payload = await self._json(request)
        if payload is None or not self._user_id(payload) or not self._license_key(payload):
            return self._bad_request("discordUserId and licenseKey are required.")
        dm_result = await self._send(
            self._user_id(payload),
            license_created_dm(
                self._license_key(payload),
                str(payload.get("plan", "Unknown")),
                payload.get("expiry"),
            ),
        )
        sales = await self._sales(payload, default_status="ACTIVE")
        return await self._event_response(dm_result, sales)

    async def giveaway_created(self, request):
        payload = await self._json(request)
        if payload is None or not self._user_id(payload) or not self._license_key(payload):
            return self._bad_request("discordUserId (owner) and licenseKey are required.")
        dm_result = await self._send(
            self._user_id(payload),
            giveaway_created_dm(self._license_key(payload), str(payload.get("plan", "Lifetime"))),
        )
        sales_payload = dict(payload)
        sales_payload["claimedBy"] = None
        sales_payload["claimedDiscordId"] = None
        sales = await self._sales(sales_payload, default_status="UNCLAIMED")
        return await self._event_response(dm_result, sales)

    async def license_claimed(self, request):
        payload = await self._json(request)
        if payload is None or not self._user_id(payload) or not self._license_key(payload):
            return self._bad_request("discordUserId and licenseKey are required.")
        user_id = self._user_id(payload)
        username = str(payload.get("username", "")).strip() or await self._resolve_username(user_id)
        dm_result = await self._send(
            user_id,
            license_claimed_dm(
                self._license_key(payload),
                str(payload.get("plan", "Unknown")),
                username,
                payload.get("expiry"),
            ),
        )
        sales_payload = dict(payload)
        sales_payload.setdefault("claimedBy", username)
        sales_payload.setdefault("claimedDiscordId", user_id)
        sales = await self._sales(sales_payload, default_status="ACTIVE")
        return await self._event_response(dm_result, sales)

    async def license_deactivated(self, request):
        return await self._status_event(request, "INACTIVE", license_deactivated_dm)

    async def license_reactivated(self, request):
        return await self._status_event(request, "ACTIVE AGAIN", license_reactivated_dm)

    async def license_delete_notice(self, request):
        payload = await self._json(request)
        if payload is None or not self._user_id(payload) or not self._license_key(payload):
            return self._bad_request("discordUserId and licenseKey are required.")
        dm_result = await self._send(self._user_id(payload), license_deleted_dm(self._license_key(payload)))
        return await self._event_response(dm_result, None)

    async def license_deleted(self, request):
        payload = await self._json(request)
        if payload is None or not self._license_key(payload):
            return self._bad_request("licenseKey is required.")
        sales = await self._sales(payload, default_status="DELETED")
        return await self._event_response(None, sales)

    async def _status_event(self, request, status: str, builder):
        payload = await self._json(request)
        if payload is None or not self._user_id(payload) or not self._license_key(payload):
            return self._bad_request("discordUserId and licenseKey are required.")
        dm_result = await self._send(self._user_id(payload), builder(self._license_key(payload)))
        sales = await self._sales(payload, default_status=status)
        return await self._event_response(dm_result, sales)

    async def _sales(self, payload: dict[str, Any], *, default_status: str):
        sales_payload = dict(payload)
        sales_payload["status"] = str(payload.get("status", default_status)).upper()
        return await self.bot.sales_service.upsert(sales_payload)

    async def _resolve_username(self, user_id: str) -> str:
        try:
            user = self.bot.get_user(int(user_id)) or await self.bot.fetch_user(int(user_id))
            return str(user)
        except Exception:
            return user_id

    async def dm_diagnose(self, request):
        payload = await self._json(request)
        if payload is None or not self._user_id(payload):
            return self._bad_request("discordUserId is required.")

        user_id = self._user_id(payload)
        diagnostic: dict[str, Any] = {
            "discordUserId": user_id,
            "botOnline": self.bot.is_ready(),
            "botUserId": str(self.bot.user.id) if self.bot.user else None,
            "guildCount": len(self.bot.guilds),
            "sharedGuilds": [],
        }

        if user_id.isdigit():
            for guild in self.bot.guilds:
                member = guild.get_member(int(user_id))
                if member is None:
                    try:
                        member = await guild.fetch_member(int(user_id))
                    except Exception:
                        member = None
                if member is not None:
                    diagnostic["sharedGuilds"].append({
                        "guildId": str(guild.id),
                        "guildName": guild.name,
                        "membershipScreeningPending": bool(getattr(member, "pending", False)),
                    })

        diagnostic["botTokenCheck"] = await self.bot.dm_service.validate_token()
        return web.json_response({"success": True, "diagnostic": diagnostic})
