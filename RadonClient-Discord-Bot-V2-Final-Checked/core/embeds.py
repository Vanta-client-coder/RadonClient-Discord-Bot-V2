"""Reusable Radon Discord embeds with conservative Discord API limits."""
import re
import discord

DEFAULT_COLOR = 0x20D5DD
STATUS_COLORS = {"success": 0x35C88A, "warning": 0xF2B84B, "error": 0xEB5865, "info": DEFAULT_COLOR}
MAX_EMBED_CHARS = 6000


def clean_text(value, limit, *, fallback="—"):
    text = str(value if value is not None else "").replace("\x00", "").strip()
    if not text:
        text = fallback
    return text if len(text) <= limit else text[:limit - 1] + "…"


def color_from_config(config):
    branding = (config or {}).get("branding") or {}
    if not isinstance(branding, dict):
        return DEFAULT_COLOR
    raw = str(branding.get("color", "#20D5DD")).strip()
    return int(raw.lstrip("#"), 16) if re.fullmatch(r"#?[0-9a-fA-F]{6}", raw) else DEFAULT_COLOR


def radon_embed(config, title=None, description=None, *, color=None, kind=None):
    branding = (config or {}).get("branding") or {}
    if not isinstance(branding, dict):
        branding = {}
    accent = STATUS_COLORS.get(kind, color_from_config(config)) if color is None else color
    footer = clean_text(branding.get("name") or branding.get("product") or "Radon Client", 2048)
    title = clean_text(title, 256) if title is not None else None
    # Leave space for the footer within the 6000-character Discord embed limit.
    room = max(1, min(4096, MAX_EMBED_CHARS - len(title or "") - len(footer)))
    description = clean_text(description, room) if description is not None else None
    embed = discord.Embed(title=title, description=description, color=accent)
    embed.set_footer(text=footer)
    logo = branding.get("logo")
    if isinstance(logo, str) and re.fullmatch(r"https://[^\s]{1,2040}", logo):
        embed.set_thumbnail(url=logo)
    return embed


def embed_character_count(embed):
    footer = getattr(embed, "footer", None)
    foot = getattr(footer, "text", "") if footer else ""
    return (len(getattr(embed, "title", "") or "")
            + len(getattr(embed, "description", "") or "")
            + len(foot or "")
            + sum(len(str(field.name)) + len(str(field.value)) for field in embed.fields))


def add_safe_field(embed, name, value, *, inline=False):
    """Apply per-field, field-count, and 6000-character aggregate limits."""
    if len(embed.fields) >= 25:
        return embed
    name = clean_text(name, 256)
    remaining = min(1024, MAX_EMBED_CHARS - embed_character_count(embed) - len(name))
    if remaining < 1:
        return embed
    embed.add_field(name=name, value=clean_text(value, remaining), inline=inline)
    return embed
