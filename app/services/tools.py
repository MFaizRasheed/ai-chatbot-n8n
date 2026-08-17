"""Tools available to the LangGraph agent."""

import logging
import smtplib
from email.mime.text import MIMEText

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from app.config import get_settings

logger = logging.getLogger(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def _send_email(user: str, password: str, to: str, subject: str, body: str) -> str:
    """Core send logic (separated so it can be tested without the tool wrapper)."""
    configured = bool(user and password)
    logger.info(
        "send_email tool invoked: from=%s to=%s subject=%s configured=%s",
        user or "<unset>",
        to,
        subject,
        configured,
    )
    if not configured:
        return (
            "Gmail is not configured. The app admin must set GMAIL_USER and "
            "GMAIL_APP_PASSWORD (a Gmail App Password) in the environment."
        )

    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = user
        msg["To"] = to

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(user, [to], msg.as_string())

        logger.info("send_email tool succeeded: from=%s to=%s", user, to)
        return f"Email sent successfully from {user} to {to}."
    except Exception as exc:  # noqa: BLE001 - report failure to the model
        logger.warning("send_email tool failed from %s to %s: %s", user, to, exc)
        return f"Failed to send email: {exc}"


def accounts() -> dict[str, tuple[str, str]]:
    """Configured sender accounts: label -> (email, app password)."""
    settings = get_settings()
    result: dict[str, tuple[str, str]] = {}
    if settings.gmail_user and settings.gmail_app_password:
        result["primary"] = (settings.gmail_user, settings.gmail_app_password)
    if settings.gmail_user_2 and settings.gmail_app_password_2:
        result["second"] = (settings.gmail_user_2, settings.gmail_app_password_2)
    return result


def resolve_account(
    accs: dict[str, tuple[str, str]], from_account: str
) -> tuple[str, str] | None:
    """Match a from_account request (label or email) to a (user, password)."""
    query = from_account.strip().lower()
    if not query:
        return next(iter(accs.values())) if accs else None

    # Match account labels: "primary", "second", "the primary account", ...
    for label, creds in accs.items():
        if query == label or query in (
            f"the {label} account",
            f"the {label} email",
            f"{label} account",
            f"{label} email",
        ):
            return creds

    # Match by email address.
    for user, password in accs.values():
        if query == user.lower():
            return user, password

    return None


def send_email_from(
    accs: dict[str, tuple[str, str]], to: str, subject: str, body: str, from_account: str = ""
) -> str:
    """Send using the requested sender account."""
    if not accs:
        return (
            "Gmail is not configured. The app admin must set GMAIL_USER and "
            "GMAIL_APP_PASSWORD (a Gmail App Password) in the environment."
        )

    creds = resolve_account(accs, from_account)
    if creds is None:
        labels = ", ".join(f"'{label}' ({user})" for label, (user, _) in accs.items())
        return (
            f"Could not find a sender account matching '{from_account}'. "
            f"Available sender accounts: {labels}."
        )

    user, password = creds
    return _send_email(user, password, to, subject, body)


class SendEmailInput(BaseModel):
    to: str = Field(..., description="Recipient email address.")
    subject: str = Field(..., description="Email subject line.")
    body: str = Field(..., description="Email body text.")
    from_account: str = Field(
        "",
        description=(
            "Which sender account to use: an account label ('primary', 'second') "
            "or the sender's email address. Leave empty to use the default "
            "(primary) account. Set this when the user asks to send from a "
            "specific account."
        ),
    )


def build_send_email_tool() -> StructuredTool:
    """Build the send_email tool with the configured accounts in its description."""
    accs = accounts()
    labels = ", ".join(f"'{label}' ({user})" for label, (user, _) in accs.items())
    labels = labels or "none configured"

    def _tool_send_email(to: str, subject: str, body: str, from_account: str = "") -> str:
        return send_email_from(accounts(), to, subject, body, from_account)

    return StructuredTool.from_function(
        func=_tool_send_email,
        name="send_email",
        description=(
            "Send an email from one of the assistant's Gmail accounts to a "
            "recipient. Use this tool whenever the user asks to send, email, "
            "or share something by email — for example 'send the summary to "
            "example@gmail.com' or 'send it from my second email'. "
            f"Configured sender accounts: {labels}. Set 'from_account' to the "
            "account label or email address when the user specifies a sender; "
            "leave it empty for the default account."
        ),
        args_schema=SendEmailInput,
    )
