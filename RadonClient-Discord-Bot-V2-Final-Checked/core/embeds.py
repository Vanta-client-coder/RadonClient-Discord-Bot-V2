import discord


def color_from_config(config):
    raw = config.get("branding", {}).get("color", "#20D5DD").lstrip("#")
    try:
        return int(raw, 16)
    except ValueError:
        return 0x20D5DD


def radon_embed(config, title=None, description=None, *, color=None):
    embed = discord.Embed(
        title=title,
        description=description,
        color=color if color is not None else color_from_config(config),
    )
    branding = config.get("branding", {})
    embed.set_footer(text=branding.get("name", "Radon"))
    logo = branding.get("logo")
    if logo and logo.startswith(("http://", "https://")):
        embed.set_thumbnail(url=logo)
    return embed
