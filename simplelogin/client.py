"""
A client script for sending emails using a SimpleLogin alias and reverse alias.
"""

import re
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from logutils import get_logger
from utils import get_env_var
from simplelogin.api import (
    get_aliases,
    create_alias,
    get_mailbox_by_email,
    get_or_create_alias_contact,
)

logger = get_logger(__name__)

SL_PRIMARY_EMAIL = get_env_var("SL_PRIMARY_EMAIL", strict=True)
SL_PRIMARY_DOMAIN = get_env_var("SL_PRIMARY_DOMAIN", strict=True)
SMTP_SERVER = get_env_var("SMTP_SERVER", strict=True)
SMTP_PORT = get_env_var("SMTP_PORT", 587)
SMTP_USERNAME = get_env_var("SMTP_USERNAME", strict=True)
SMTP_PASSWORD = get_env_var("SMTP_PASSWORD", strict=True)
SMTP_ENABLE_TLS = get_env_var("SMTP_ENABLE_TLS", True)


def get_or_create_phonenumber_alias(phone_number: str) -> dict:
    """
    Retrieve or create an email alias for a given phone number.

    This function checks if an email alias exists for the provided phone number.
    If not, it creates a new one using the phone number as a prefix.

    Args:
        phone_number (str): The phone number used to generate or retrieve the alias.

    Returns:
        dict: A dictionary of the alias associated with the phone number.
    """
    cleaned_phone_number = re.sub(r"\D", "", phone_number)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    note = f"Created by relaysms email bridge at {timestamp}."

    aliases = get_aliases(query=f"{cleaned_phone_number}@{SL_PRIMARY_DOMAIN}")
    if aliases is None:
        return None

    if bool(aliases):
        return aliases[0]

    primary_mailbox = get_mailbox_by_email(email=SL_PRIMARY_EMAIL)
    if primary_mailbox is None:
        return None

    alias = create_alias(
        alias_prefix=cleaned_phone_number,
        alias_name=f"{cleaned_phone_number} From RelaySMS",
        hostname=SL_PRIMARY_DOMAIN,
        mailbox_id=primary_mailbox["id"],
        note=note,
    )
    if alias is None:
        return None

    return alias


def send_email(
    phone_number: str, to_email: str, subject: str, body: str, **kwargs
) -> None:
    """
    Send an email using the phone number alias as the sender.

    Args:
        phone_number (str): The sender's phone number, used as a prefix for the email alias.
        to_email (str): The recipient's email address.
        subject (str): The subject of the email.
        body (str): The main content or body of the email.
        cc_email (str, optional): The email address for CC (Carbon Copy). Defaults to None.
        bcc_email (str, optional): The email address for BCC (Blind Carbon Copy). Defaults to None.

    Returns:
        None
    """
    cc_email = kwargs.get("cc_email")
    bcc_email = kwargs.get("bcc_email")

    try:
        msg = MIMEMultipart()
        msg["From"] = SL_PRIMARY_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject

        if cc_email:
            msg["Cc"] = cc_email
        if bcc_email:
            msg["Bcc"] = bcc_email

        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)

        if SMTP_ENABLE_TLS:
            server.starttls()

        server.login(SMTP_USERNAME, SMTP_PASSWORD)

        recipients = [to_email]
        if cc_email:
            recipients.append(cc_email)
        if bcc_email:
            recipients.append(bcc_email)

        server.sendmail(SMTP_USERNAME, recipients, msg.as_string())
        server.quit()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info("Email sent successfully to %s at %s", to_email, timestamp)

    except Exception as e:
        logger.exception(e)


if __name__ == "__main__":
    pn_alias = get_or_create_phonenumber_alias("+237123456789")
    print(">>>>>>", pn_alias)
    contact = get_or_create_alias_contact(pn_alias["id"], email_address="")
    print(">>>>>>", contact)
    send_email(
        phone_number="",
        to_email=contact["reverse_alias"],
        subject="Hello There Again.",
        body="Hey there this is a sample mail from bridge.",
    )
