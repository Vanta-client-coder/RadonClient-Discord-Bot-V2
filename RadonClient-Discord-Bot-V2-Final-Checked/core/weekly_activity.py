"""Weekly message counts: UTC weeks, human members only, no content retained."""
from datetime import datetime, timedelta, timezone

CHANNEL_ID = 1562883723563634729
STAFF_GROUPS = ('owner', 'coOwner', 'dev', 'team', 'support')


def monday_start(dt):
    utc = dt.astimezone(timezone.utc)
    return (utc - timedelta(days=utc.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)


def is_eligible(member, config):
    if getattr(member, 'bot', True):
        return False
    permissions = getattr(member, 'guild_permissions', None)
    if permissions and (getattr(permissions, 'administrator', False) or getattr(permissions, 'manage_guild', False)):
        return False
    ids = {str(r.id) for r in getattr(member, 'roles', ())}
    roles = config.get('roles', {})
    for key in STAFF_GROUPS:
        configured = roles.get(key, ())
        if not isinstance(configured, list):
            configured = [configured]
        if ids.intersection(str(v) for v in configured if v):
            return False
    return True


def week_key(dt):
    return monday_start(dt).date().isoformat()
