import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.json"
PLACEHOLDER_WORDS = ("_ROLE_ID", "_CHANNEL_ID", "_CATEGORY_ID", "YOUR_", "CHANGE_ME")


def load_config():
    # Render environment variables keep server-specific configuration out of Git.
    raw = os.getenv("RADON_CONFIG_JSON", "").strip()
    if raw:
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError("RADON_CONFIG_JSON must contain a JSON object")
        return value
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def is_placeholder(value):
    if not isinstance(value, str):
        return False
    return not value.strip() or any(word in value for word in PLACEHOLDER_WORDS)


def validate_config(config):
    missing = []
    checks = {
        "guildId": config.get("guildId"),
        "roles.owner": config.get("roles", {}).get("owner"),
        "roles.coOwner": config.get("roles", {}).get("coOwner"),
        "roles.dev": config.get("roles", {}).get("dev"),
        "roles.team": config.get("roles", {}).get("team"),
        "roles.autoRole": config.get("roles", {}).get("autoRole"),
        "channels.moderationLogs": config.get("channels", {}).get("moderationLogs"),
        "channels.ticketLogs": config.get("channels", {}).get("ticketLogs"),
        "channels.announcements": config.get("channels", {}).get("announcements"),
        "channels.boostNotifications": config.get("channels", {}).get("boostNotifications"),
        "channels.botStatus": config.get("channels", {}).get("botStatus"),
        "channels.salesLicenseLogs": config.get("channels", {}).get("salesLicenseLogs"),
        "tickets.categoryId": config.get("tickets", {}).get("categoryId"),
    }
    for key, value in checks.items():
        if is_placeholder(value) or not str(value).isdigit():
            missing.append(key)

    support = config.get("roles", {}).get("support", [])
    if not isinstance(support, list) or not support or any(not str(x).isdigit() for x in support):
        missing.append("roles.support")
    return missing
