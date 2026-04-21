from __future__ import annotations

from django.conf import settings
from django.core.mail import EmailMessage


CC_EMAIL = "tower2372@gmail.com"  # ✅ keep hardcoded exactly


def _subject_for(action: str) -> str:
    action = (action or "").upper()
    if action == "ADDED":
        return "Control Tower: You have been added"
    if action == "EDITED":
        return "Control Tower: Your details were updated"
    if action == "DELETED":
        return "Control Tower: You have been removed"
    if action == "DISABLED":
        return "Control Tower: Your access was disabled"
    if action == "ENABLED":
        return "Control Tower: Your access was enabled"
    return "Control Tower Update"


def _body_for(action: str, first_name: str, last_name: str) -> str:
    action = (action or "").upper()
    first_name = first_name or ""
    last_name = last_name or ""

    greeting = f"Hi {first_name},\n\n"

    if action == "ADDED":
        return (
            f"{greeting}"
            "You have been added as a Team Member in Control Tower.\n\n"
            "Thank you,\n"
            "Control Tower"
        )

    if action == "EDITED":
        return (
            f"{greeting}"
            "Your  details have been updated in Control Tower.\n\n"
            "Thank you,\n"
            "Control Tower"
        )

    if action == "DELETED":
        return (
            f"{greeting}"
            "You have been removed from Team Members list in Control Tower.\n\n"
            "Thank you,\n"
            "Control Tower"
        )

    if action == "DISABLED":
        return (
            f"{greeting}"
            "Your  Member access has been disabled in Control Tower.\n\n"
            "Thank you,\n"
            "Control Tower"
        )

    if action == "ENABLED":
        return (
            f"{greeting}"
            "Your Team  access has been enabled again in Control Tower.\n\n"
            "Thank you,\n"
            "Control Tower"
        )

    return (
        f"{greeting}"
        "There is an update regarding your Team Member status in Control Tower.\n\n"
        "Thank you,\n"
        "Control Tower"
    )


def send_team_member_email(
    action: str,
    first_name: str,
    last_name: str,
    to_email: str,
) -> None:
    """
    Sends email TO the member + CC tower2372@gmail.com
    Raises error if SMTP fails.
    """
    to_email = (to_email or "").strip()
    if not to_email:
        return

    subject = _subject_for(action)
    body = _body_for(action, first_name, last_name)

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or None

    msg = EmailMessage(
        subject=subject,
        body=body,
        from_email=from_email,
        to=[to_email],
        cc=[CC_EMAIL],
    )
    msg.send(fail_silently=False)
