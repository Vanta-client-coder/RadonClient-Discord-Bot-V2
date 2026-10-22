"""Local, offline deployment preflight; never calls Discord or prints credentials."""
import os
import sys
from core.config import load_config, validate_config


def assess(env=None):
    env = os.environ if env is None else env
    errors, warnings = [], []
    token = env.get('DISCORD_TOKEN', '').strip()
    if not token or token.startswith('YOUR_'):
        errors.append('DISCORD_TOKEN missing or placeholder')
    if not env.get('RADON_INTERNAL_API_KEY', '').strip() or env.get('RADON_INTERNAL_API_KEY', '').strip() == 'CHANGE_ME_TO_A_LONG_RANDOM_SECRET':
        warnings.append('RADON_INTERNAL_API_KEY not configured; protected website API unavailable')
    try:
        # load_config uses process environment; isolated alternate environments are tested by patching os.environ
        config = load_config()
        issues = validate_config(config)
        if issues:
            errors.append('Invalid configuration fields: ' + ', '.join(issues))
    except (OSError, ValueError, TypeError) as exc:
        errors.append('Configuration unavailable or invalid (' + type(exc).__name__ + ')')
    return errors, warnings


if __name__ == '__main__':
    errors, warnings = assess()
    print('RadonClient V2 preflight — offline checks only; no Discord login')
    for msg in errors:
        print('ERROR: ' + msg)
    for msg in warnings:
        print('WARNING: ' + msg)
    if not errors:
        print('PASS: Local configuration checks complete. Live connectivity NOT verified.')
    sys.exit(1 if errors else 0)
