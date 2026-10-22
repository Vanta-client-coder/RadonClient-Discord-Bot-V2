import discord


def _role_ids(member):
    return {str(role.id) for role in getattr(member, "roles", [])}


def _configured_ids(value):
    if isinstance(value, list):
        return {str(v) for v in value if v}
    if value:
        return {str(value)}
    return set()


def member_groups(member, config):
    ids = _role_ids(member)
    groups = set()
    for group, configured in config.get("roles", {}).items():
        if ids & _configured_ids(configured):
            groups.add(group)
    return groups


def command_allowed(member, command_name, config):
    name = command_name.split()[0].lower()
    groups = member_groups(member, config)
    access = config.get("commandAccess", {})
    for group in groups:
        allowed = access.get(group, [])
        normalized = {str(item).lower() for item in allowed}
        if "*" in normalized or name in normalized:
            return True
    return False


def is_owner_or_coowner(member, config):
    groups = member_groups(member, config)
    return bool(groups & {"owner", "coOwner"})


def is_ticket_staff(member, config):
    groups = member_groups(member, config)
    return bool(groups & {"owner", "coOwner", "support"})


def can_moderate(ctx, target):
    if target.id == ctx.author.id:
        return False, "You cannot moderate yourself."
    if target.id == ctx.guild.owner_id:
        return False, "The server owner cannot be moderated by the bot."
    if target.id == ctx.bot.user.id:
        return False, "You cannot moderate the bot."

    me = ctx.guild.me
    if me is None or me.top_role <= target.top_role:
        return False, "My bot role must be higher than the target member's highest role."
    if ctx.author.id != ctx.guild.owner_id and ctx.author.top_role <= target.top_role:
        return False, "Your highest Discord role must be above the target member's highest role."
    return True, None


def bot_has(ctx, **permissions):
    perms = ctx.channel.permissions_for(ctx.guild.me)
    return [
        name
        for name, needed in permissions.items()
        if needed and not getattr(perms, name, False)
    ]
