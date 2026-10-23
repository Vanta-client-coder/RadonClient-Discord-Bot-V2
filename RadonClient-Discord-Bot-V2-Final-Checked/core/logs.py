from .embeds import radon_embed, add_safe_field


async def send_log(bot, channel_key, title, fields):
    channel_id = bot.config.get("channels", {}).get(channel_key)
    if not channel_id or not str(channel_id).isdigit():
        return

    channel = bot.get_channel(int(channel_id))
    if channel is None:
        try:
            channel = await bot.fetch_channel(int(channel_id))
        except Exception as exc:
            print(f"[LOG ERROR] Could not find channel '{channel_key}': {exc}")
            return

    embed = radon_embed(bot.config, title=title)
    for name, value, inline in fields:
        add_safe_field(embed, name, value, inline=inline)

    try:
        await channel.send(embed=embed)
    except Exception as exc:
        print(f"[LOG ERROR] Could not send log message: {exc}")
