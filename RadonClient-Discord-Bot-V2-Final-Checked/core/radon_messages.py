from typing import Any


def _value(value: Any, fallback: str = "Unknown") -> str:
    if value is None or value == "":
        return fallback
    return str(value)


def welcome_dm(username: str) -> str:
    return (
        "**RADON**\n\n"
        "Welcome to Radon.\n\n"
        "Your Discord account has been successfully linked to Radon Client.\n"
        "You can now manage your Radon+ licenses through your Radon account.\n\n"
        f"Discord:\n{_value(username)}"
    )


def license_created_dm(license_key: str, plan: str, expires_at: str | None = None) -> str:
    expiry = _value(expires_at, "Never" if str(plan).lower() == "lifetime" else "Unknown")
    return (
        "**RADON+ LICENSE CREATED**\n\n"
        "Your Radon+ license has been created.\n\n"
        f"License:\n{license_key}\n\n"
        f"Plan:\n{_value(plan)}\n\n"
        "Status:\nACTIVE\n\n"
        f"Expires:\n{expiry}\n\n"
        "Keep this key private."
    )


def giveaway_created_dm(license_key: str, plan: str = "Lifetime") -> str:
    return (
        "**RADON GIVEAWAY KEY CREATED**\n\n"
        f"License:\n{license_key}\n\n"
        f"Plan:\n{_value(plan)}\n\n"
        "Status:\nUNCLAIMED\n\n"
        "This key is not linked to a Discord account yet.\n"
        "The first eligible user who activates it becomes the owner."
    )


def license_claimed_dm(license_key: str, plan: str, username: str, expires_at: str | None = None) -> str:
    expiry = _value(expires_at, "Never" if str(plan).lower() == "lifetime" else "Unknown")
    return (
        "**RADON+ LICENSE ACTIVATED**\n\n"
        "You successfully claimed a Radon+ license.\n\n"
        f"License:\n{license_key}\n\n"
        f"Plan:\n{_value(plan)}\n\n"
        "Status:\nACTIVE\n\n"
        f"Expires:\n{expiry}\n\n"
        f"Discord:\n{_value(username)}"
    )


def license_deactivated_dm(license_key: str) -> str:
    return (
        "**RADON+ LICENSE DEACTIVATED**\n\n"
        "Your Radon+ license has been deactivated.\n\n"
        f"License:\n{license_key}\n\n"
        "Status:\nINACTIVE\n\n"
        "Access to Radon Client is currently disabled for this license."
    )


def license_reactivated_dm(license_key: str) -> str:
    return (
        "**RADON+ LICENSE REACTIVATED**\n\n"
        "Your Radon+ license is active again.\n\n"
        f"License:\n{license_key}\n\n"
        "Status:\nACTIVE\n\n"
        "You can use Radon Client again."
    )


def license_deleted_dm(license_key: str) -> str:
    return (
        "**RADON+ LICENSE DELETED**\n\n"
        "Your Radon+ license has been permanently removed.\n\n"
        f"License:\n{license_key}\n\n"
        "Status:\nDELETED"
    )


def test_dm() -> str:
    return (
        "**RADON DM TEST**\n\n"
        "The Radon bot can successfully send private messages to this Discord account."
    )
