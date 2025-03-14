"""
This program is free software: you can redistribute it under the terms
of the GNU General Public License, v. 3.0. If a copy of the GNU General
Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.

The API endpoints referenced are from the official SimpleLogin API documentation:
https://github.com/simple-login/app/blob/master/docs/api.md
"""

import requests
from logutils import get_logger
from utils import get_env_var

SL_API_BASE_URL = get_env_var("SL_API_BASE_URL", "https://app.simplelogin.io/api")
SL_API_KEY = get_env_var("SL_API_KEY", strict=True)

logger = get_logger(__name__)


def __get_headers__(include_content_type: bool = True):
    """Generate headers for authenticating with the SimpleLogin API.

    Args:
        include_content_type (bool): Whether to include the Content-Type header.
            Defaults to True.

    Returns:
        dict: Headers containing the Authentication token and optionally Content-Type.
    """
    headers = {
        "Authentication": SL_API_KEY,
    }

    if include_content_type:
        headers["Content-Type"] = "application/json"

    return headers


def get_signed_suffix(hostname: str) -> list:
    """Generate a list of alias suffixes from the SimpleLogin API.

    Args:
        hostname (str): The primary domain name used for the alias.

    Returns:
        list: JSON response containing suffixes data if the request is successful.
        None: If the request fails.
    """
    url = f"{SL_API_BASE_URL}/v5/alias/options?hostname={hostname}"

    try:
        response = requests.get(
            url,
            headers=__get_headers__(include_content_type=False),
            timeout=30,
        )
        response.raise_for_status()
        suffixes = response.json()

        suffix = next(
            (sx for sx in suffixes["suffixes"] if sx["suffix"] == f"@{hostname}"), None
        )

        if suffix:
            logger.info("Fetched suffix for hostname %s successfully.", hostname)
            return suffix

        logger.info("No suffix found for hostname %s.", hostname)
        return None
    except requests.exceptions.RequestException as e:
        error_response = e.response.json()
        error_message = error_response.get("error") or str(e)
        logger.error("Failed to fetch suffixes: %s", e)
        logger.error("Error message: %s", error_message)
        return None


def get_aliases(query: str = None) -> list:
    """Fetch aliases from the SimpleLogin API.

    Args:
        query (str, optional): A query string to search for in alias notes.
            Defaults to None.

    Returns:
        list: JSON response containing alias data if the request is successful.
        None: If the request fails.
    """
    url = f"{SL_API_BASE_URL}/v2/aliases?enabled&page_id=0"
    data = {}

    if query:
        data["query"] = query

    try:
        response = requests.post(url, json=data, headers=__get_headers__(), timeout=30)
        response.raise_for_status()
        aliases = response.json()
        logger.info("Successfully fetched aliases.")
        logger.debug("Fetched aliases with query '%s' successfully.", query)
        return aliases["aliases"]
    except requests.exceptions.RequestException as e:
        error_response = e.response.json()
        error_message = error_response.get("error") or str(e)
        logger.error("Failed to fetch aliases: %s", e)
        logger.error("Error message: %s", error_message)
        return None


def create_alias(
    alias_prefix: str,
    mailbox_id: int,
    hostname: str,
    note: str = None,
    alias_name: str = None,
) -> dict:
    """Create a new alias using the SimpleLogin API.

    Args:
        alias_prefix (str): The prefix for the new alias email.
        mailbox_id (int): The ID of the mailbox where the alias will forward emails.
        hostname (str): The primary domain name used for the alias.
        note (str, optional): A note to attach to the alias. Defaults to None.
        alias_name (str, optional): A name to attach to the alias. Defaults to None.

    Returns:
        dict: JSON response containing the created alias data if successful.
        None: If the request fails.
    """
    url = f"{SL_API_BASE_URL}/v3/alias/custom/new"

    suffixes = get_signed_suffix(hostname)
    if suffixes is None:
        return None

    signed_suffix = suffixes["signed_suffix"]

    data = {
        "alias_prefix": alias_prefix,
        "signed_suffix": signed_suffix,
        "mailbox_ids": [mailbox_id],
        "note": note,
        "name": alias_name,
    }

    if note:
        data["note"] = note
        data["name"] = alias_name

    try:
        response = requests.post(url, json=data, headers=__get_headers__(), timeout=30)
        response.raise_for_status()
        alias = response.json()
        logger.info("Successfully created alias.")
        logger.debug("Alias %s created successfully.", alias["email"])
        return alias
    except requests.exceptions.RequestException as e:
        error_response = e.response.json()
        error_message = error_response.get("error") or str(e)
        logger.error("Failed to create alias: %s", e)
        logger.error("Error message: %s", error_message)
        return None


def delete_alias(alias_id: int) -> bool:
    """Delete an alias by its ID using the SimpleLogin API.

    Args:
        alias_id (int): The ID of the alias to be deleted.

    Returns:
        bool: True if deletion is successful, False otherwise.
    """
    url = f"{SL_API_BASE_URL}/aliases/{alias_id}"
    try:
        response = requests.delete(
            url, headers=__get_headers__(include_content_type=False), timeout=30
        )
        response.raise_for_status()
        logger.info("Successfully deleted alias.")
        logger.debug("Alias ID %s deleted successfully.", alias_id)
        return True
    except requests.exceptions.RequestException as e:
        error_response = e.response.json()
        error_message = error_response.get("error") or str(e)
        logger.error("Failed to delete alias ID %s: %s", alias_id, e)
        logger.error("Error message: %s", error_message)
        return False


def get_all_mailboxes() -> list:
    """Fetch all mailboxes from the SimpleLogin API.

    Returns:
        list: A list of all mailboxes if successful.
        None: If the request fails.
    """
    url = f"{SL_API_BASE_URL}/mailboxes"
    try:
        response = requests.get(
            url, headers=__get_headers__(include_content_type=False), timeout=30
        )
        response.raise_for_status()
        mailboxes = response.json()
        logger.info("Fetched all mailboxes successfully.")
        return mailboxes["mailboxes"]
    except requests.exceptions.RequestException as e:
        error_response = e.response.json()
        error_message = error_response.get("error") or str(e)
        logger.error("Failed to fetch all mailboxes: %s", e)
        logger.error("Error message: %s", error_message)
        return None


def get_mailbox_by_email(email: str) -> dict:
    """Get mailbox information by email address.

    Args:
        email (str): The email address to look up.

    Returns:
        dict: JSON response containing mailbox data if successful.
        None: If the request fails.
    """
    mailboxes = get_all_mailboxes()
    if mailboxes is None:
        return None

    mailbox = next((mb for mb in mailboxes if mb.get("email") == email), None)

    if mailbox:
        logger.info("Fetched mailbox for email %s successfully.", email)
        return mailbox

    logger.info("No mailbox found for email %s.", email)
    return None


def get_or_create_alias_contact(alias_id: int, email_address: str) -> dict:
    """Retrieve or Create a new contact for an alias.

    Args:
        alias_id (int): The ID of the alias who owns the contact.
        email_address (str): The recipient's email address.

    Returns:
        dict: JSON response containing contact data if successful.
        None: If the request fails.
    """
    url = f"{SL_API_BASE_URL}/aliases/{alias_id}/contacts"

    data = {"contact": f"<{email_address}>"}

    try:
        response = requests.post(url, json=data, headers=__get_headers__(), timeout=30)
        response.raise_for_status()
        contact = response.json()
        logger.info(
            "Successfully %s contact.", "retrieved" if contact["existed"] else "created"
        )
        logger.debug(
            "Contact '%s' %s successfully.",
            contact["contact"],
            "retrieved" if contact["existed"] else "created",
        )
        return contact
    except requests.exceptions.RequestException as e:
        error_response = e.response.json()
        error_message = error_response.get("error") or str(e)
        logger.error("Failed to create contact: %s", e)
        logger.error("Error message: %s", error_message)
        return None
