"""
This program is free software: you can redistribute it under the terms
of the GNU General Public License, v. 3.0. If a copy of the GNU General
Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.
"""

import sys
import re
import argparse
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
BRIDGE_SMTP_SERVER = get_env_var("BRIDGE_SMTP_SERVER", strict=True)
BRIDGE_SMTP_PORT = get_env_var("BRIDGE_SMTP_PORT", 587)
BRIDGE_SMTP_USERNAME = get_env_var("BRIDGE_SMTP_USERNAME", strict=True)
BRIDGE_SMTP_PASSWORD = get_env_var("BRIDGE_SMTP_PASSWORD", strict=True)
BRIDGE_SMTP_ENABLE_TLS = get_env_var("BRIDGE_SMTP_ENABLE_TLS", True)

ALIAS_PHONE_NUMBER_PREFIX = get_env_var("ALIAS_PHONE_NUMBER_PREFIX", default_value="")
ALIAS_PHONE_NUMBER_SUFFIX = get_env_var("ALIAS_PHONE_NUMBER_SUFFIX", default_value="")


def __get_or_create_phonenumber_alias__(phone_number: str) -> dict:
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
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S (%Z)")
    note = f"Created by relaysms email bridge at {timestamp}."

    given_alias_prefix = (
        f"{ALIAS_PHONE_NUMBER_PREFIX}{cleaned_phone_number}{ALIAS_PHONE_NUMBER_SUFFIX}"
    )

    aliases = get_aliases(query=f"{given_alias_prefix}@{SL_PRIMARY_DOMAIN}")
    if aliases is None:
        return None

    if bool(aliases):
        return aliases[0]

    primary_mailbox = get_mailbox_by_email(email=SL_PRIMARY_EMAIL)
    if primary_mailbox is None:
        return None

    alias = create_alias(
        alias_prefix=given_alias_prefix,
        alias_name=f"{cleaned_phone_number} Via RelaySMS",
        hostname=SL_PRIMARY_DOMAIN,
        mailbox_id=primary_mailbox["id"],
        note=note,
    )
    if alias is None:
        return None

    return alias


def __handle_aliases__(pn_alias, to_email, cc_email, bcc_email):
    """
    Handle alias creation for email addresses.

    Args:
        pn_alias (dict): Phone number alias details.
        to_email (str): Recipient's email address.
        cc_email (str): CC email address.
        bcc_email (str): BCC email address.

    Returns:
        tuple:
            to_email_reverse_alias (str): Reverse alias for the recipient email.
            cc_email_reverse_alias (str): Reverse alias for the CC email.
            bcc_email_reverse_alias (str): Reverse alias for the BCC email.
    """
    to_email_contact = get_or_create_alias_contact(
        pn_alias["id"], email_address=to_email
    )
    cc_email_contact = (
        get_or_create_alias_contact(pn_alias["id"], email_address=cc_email)
        if cc_email
        else None
    )
    bcc_email_contact = (
        get_or_create_alias_contact(pn_alias["id"], email_address=bcc_email)
        if bcc_email
        else None
    )

    to_email_reverse_alias = (
        to_email_contact["reverse_alias"] if to_email_contact else None
    )
    cc_email_reverse_alias = (
        cc_email_contact["reverse_alias"] if cc_email_contact else None
    )
    bcc_email_reverse_alias = (
        bcc_email_contact["reverse_alias"] if bcc_email_contact else None
    )

    return to_email_reverse_alias, cc_email_reverse_alias, bcc_email_reverse_alias


def __send_email_via_smtp__(
    to_email_reverse_alias,
    subject,
    body,
    cc_email_reverse_alias,
    bcc_email_reverse_alias,
):
    """
    Send email using SMTP.

    Args:
        to_email_reverse_alias (str): The recipient's reverse alias email address.
        subject (str): The subject of the email.
        body (str): The main content or body of the email.
        cc_email_reverse_alias (str): CC reverse alias email address.
        bcc_email_reverse_alias (str): BCC reverse alias email address.
    """
    msg = MIMEMultipart()
    msg["From"] = SL_PRIMARY_EMAIL
    msg["To"] = to_email_reverse_alias
    msg["Subject"] = subject

    if cc_email_reverse_alias:
        msg["Cc"] = cc_email_reverse_alias
    if bcc_email_reverse_alias:
        msg["Bcc"] = bcc_email_reverse_alias

    msg.attach(MIMEText(body, "plain"))

    server = smtplib.SMTP(BRIDGE_SMTP_SERVER, BRIDGE_SMTP_PORT)
    if BRIDGE_SMTP_ENABLE_TLS:
        server.starttls()
    server.login(BRIDGE_SMTP_USERNAME, BRIDGE_SMTP_PASSWORD)

    recipients = [to_email_reverse_alias]
    if cc_email_reverse_alias:
        recipients.append(cc_email_reverse_alias)
    if bcc_email_reverse_alias:
        recipients.append(bcc_email_reverse_alias)

    server.sendmail(BRIDGE_SMTP_USERNAME, recipients, msg.as_string())
    server.quit()


def send_email(
    phone_number: str, to_email: str, subject: str, body: str, **kwargs
) -> tuple:
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
        tuple:
            success (bool): A boolean indicating the status of the operation. True if successful
                and False otherwise.
            message (str): A success message or an error message.
        None
    """
    cc_email = kwargs.get("cc_email")
    bcc_email = kwargs.get("bcc_email")

    try:
        pn_alias = __get_or_create_phonenumber_alias__(phone_number)
        if pn_alias is None:
            return False, "Failed to create phone number alias. Please try again later."

        to_email_reverse_alias, cc_email_reverse_alias, bcc_email_reverse_alias = (
            __handle_aliases__(pn_alias, to_email, cc_email, bcc_email)
        )

        if to_email_reverse_alias is None:
            return (
                False,
                "Failed to create to_email contact reverse alias. Please try again later.",
            )

        __send_email_via_smtp__(
            to_email_reverse_alias,
            subject,
            body,
            cc_email_reverse_alias,
            bcc_email_reverse_alias,
        )

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info("Email sent successfully at %s.", timestamp)
        return True, f"Email sent successfully at {timestamp}."

    except Exception as e:
        logger.exception(e)
        return False, "Failed to send email. Please try again later."


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="A client script for sending emails using SimpleLogin alias and reverse alias.",
        prog="SimpleLogin Client CLI.",
    )
    parser.add_argument(
        "command", choices=["send_email"], help="Command for sending emails."
    )
    parser.add_argument(
        "--phone_number",
        type=str,
        required=True,
        help="The sender's phone number, used as a prefix for the email alias.",
    )
    parser.add_argument(
        "--to", type=str, required=True, help="The recipient's email address."
    )
    parser.add_argument(
        "--body", type=str, required=True, help="The main content or body of the email."
    )
    parser.add_argument(
        "--subject", type=str, required=True, help="The subject of the email."
    )
    parser.add_argument(
        "--cc", type=str, help="The email address for CC (Carbon Copy).", default=None
    )
    parser.add_argument(
        "--bcc",
        type=str,
        help="The email address for BCC (Blind Carbon Copy).",
        default=None,
    )
    return parser.parse_args()


def main():
    """Entry function for CLI tool."""
    args = parse_arguments()

    match args.command:
        case "send_email":
            success, message = send_email(
                phone_number=args.phone_number,
                to_email=args.to,
                body=args.body,
                subject=args.subject,
                cc_email=args.cc,
                bcc_email=args.bcc,
            )
            if not success:
                logger.error(message)
                sys.exit(1)
            sys.exit(0)


if __name__ == "__main__":
    main()
