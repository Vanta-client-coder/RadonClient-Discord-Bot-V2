import asyncio
import json
import tempfile
from pathlib import Path

from aiohttp import web

import core.discord_dm as dm_module
from core.config import load_config, validate_config
from core.database import Database
from core.discord_dm import RadonDMService


EXPECTED_IDS = {
    "guildId": "1554520979886047315",
    "owner": "1555224034902278214",
    "coOwner": "1555224142792491128",
    "dev": "1555223821227917343",
    "team": "1554869329684725812",
    "autoRole": "1555309234776711168",
    "moderationLogs": "1556710051417296907",
    "ticketLogs": "1556710107310596218",
    "announcements": "1557060383288729632",
    "boostNotifications": "1558164536429645894",
    "botStatus": "1558196796059291658",
    "salesLicenseLogs": "1557419606992224407",
    "ticketCategory": "1557054511682429018",
}


def run_config_test():
    config = load_config()
    assert validate_config(config) == [], validate_config(config)
    assert config["guildId"] == EXPECTED_IDS["guildId"]
    for key in ("owner", "coOwner", "dev", "team", "autoRole"):
        assert config["roles"][key] == EXPECTED_IDS[key]
    for key in ("moderationLogs", "ticketLogs", "announcements", "boostNotifications", "botStatus", "salesLicenseLogs"):
        assert config["channels"][key] == EXPECTED_IDS[key]
    assert config["tickets"]["categoryId"] == EXPECTED_IDS["ticketCategory"]
    assert config["branding"]["product"] == "Radon Client"
    assert config["branding"]["premium"] == "Radon+"


def run_database_test():
    with tempfile.TemporaryDirectory() as tmp:
        db = Database(Path(tmp) / "test.db")
        db.set_sales_state("RADON-TEST", "123", json.dumps({"status": "ACTIVE"}))
        assert db.get_sales_message_id("RADON-TEST") == "123"
        assert json.loads(db.get_sales_metadata_json("RADON-TEST"))["status"] == "ACTIVE"
        assert db.add_giveaway_entry("1", "10") is True
        assert db.add_giveaway_entry("1", "10") is False


async def run_dm_success_test():
    async def create_dm(request):
        body = await request.json()
        assert body["recipient_id"] == "123456789"
        return web.json_response({"id": "987654321"})

    async def create_message(request):
        body = await request.json()
        assert body["content"] == "hello"
        return web.json_response({"id": "555555555"})

    app = web.Application()
    app.router.add_post("/users/@me/channels", create_dm)
    app.router.add_post("/channels/{channel_id}/messages", create_message)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]

    old = dm_module.DISCORD_API_BASE
    dm_module.DISCORD_API_BASE = f"http://127.0.0.1:{port}"
    service = RadonDMService("test-token")
    try:
        result = await service.send_radon_dm("123456789", "hello")
        assert result == {"success": True, "channelId": "987654321", "messageId": "555555555"}
    finally:
        await service.close()
        dm_module.DISCORD_API_BASE = old
        await runner.cleanup()


async def run_dm_50007_test():
    async def create_dm(request):
        return web.json_response({"code": 50007, "message": "Cannot send messages to this user"}, status=403)

    app = web.Application()
    app.router.add_post("/users/@me/channels", create_dm)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]

    old = dm_module.DISCORD_API_BASE
    dm_module.DISCORD_API_BASE = f"http://127.0.0.1:{port}"
    service = RadonDMService("test-token")
    try:
        result = await service.send_radon_dm("123456789", "hello")
        assert result["success"] is False
        assert result["discordStatus"] == 403
        assert result["discordCode"] == 50007
        assert result["internalError"] == "DM_BLOCKED_BY_DISCORD"
    finally:
        await service.close()
        dm_module.DISCORD_API_BASE = old
        await runner.cleanup()


async def main():
    run_config_test()
    print("[PASS] Config and supplied Discord IDs")
    run_database_test()
    print("[PASS] SQLite persistence primitives")
    await run_dm_success_test()
    print("[PASS] Discord REST API v10 two-step DM")
    await run_dm_50007_test()
    print("[PASS] Discord 403 / 50007 mapping")
    print("Offline self-test completed successfully.")


if __name__ == "__main__":
    asyncio.run(main())
