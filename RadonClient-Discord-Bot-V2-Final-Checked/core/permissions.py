"""Central command authorization for the Radon guild.

Explicit commandAccess entries replace the defaults for that role. Never trust
role names: all comparisons are against configured Discord role IDs.
"""

PUBLIC_COMMANDS = frozenset({"help", "ping", "userinfo", "membercount", "serverinfo", "botinfo", "uptime"})
DEFAULT_COMMAND_ACCESS = {
    "dev": frozenset({"ban", "kick", "timeout", "untimeout", "clear", "warn", "warnings", "delwarn"}),
    "team": frozenset({"timeout", "untimeout", "warn", "warnings", "clear"}),
    "support": frozenset({"claim", "close", "add", "remove", "rename", "warnings"}),
    # Auto Role gives no staff privileges.
    "autoRole": frozenset(),
}


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
    name = str(command_name).split()[0].lower()
    if name in PUBLIC_COMMANDS:
        return True
    groups = member_groups(member, config)
    if groups & {"owner", "coOwner"}:
        return True
    configured_access = config.get("commandAccess") or {}
    if not isinstance(configured_access, dict):
        return False
    for group in groups:
        # An explicit empty list is an intentional denial for this group.
        allowed = configured_access[group] if group in configured_access else DEFAULT_COMMAND_ACCESS.get(group, ())
        if not isinstance(allowed, (list, tuple, set, frozenset)):
            continue
        normalized = {str(item).lower() for item in allowed}
        if "*" in normalized or name in normalized:
            return True
    return False


def is_owner_or_coowner(member, config):
    return bool(member_groups(member, config) & {"owner", "coOwner"})


def is_ticket_staff(member, config):
    return bool(member_groups(member, config) & {"owner", "coOwner", "support"})


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
    return [name for name, needed in permissions.items() if needed and not getattr(perms, name, False)]
