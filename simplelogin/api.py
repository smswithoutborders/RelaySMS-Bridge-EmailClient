"""A module for interacting with the SimpleLogin API."""

import requests
from logutils import get_logger
from utils import get_env_var

SL_API_BASE_URL = get_env_var("SL_API_BASE_URL", "https://app.simplelogin.io/api")
SL_API_KEY = get_env_var("SL_API_KEY", strict=True)

logger = get_logger(__name__)


def get_headers(include_content_type=True):
    """Generate headers for authenticating with the SimpleLogin API.

    Args:
        include_content_type (bool): Whether to include the Content-Type header.
            Defaults to True.

    Returns:
        dict: Headers containing the Authorization token and optionally Content-Type.
    """
    headers = {
        "Authorization": SL_API_KEY,
    }

    if include_content_type:
        headers["Content-Type"] = "application/json"

    return headers


def get_aliases():
    """Fetch all aliases from the SimpleLogin API.

    Returns:
        dict: JSON response containing alias data if the request is successful.
        None: If the request fails.
    """
    url = f"{SL_API_BASE_URL}/aliases"
    try:
        response = requests.get(
            url, headers=get_headers(include_content_type=False), timeout=30
        )
        response.raise_for_status()
        aliases = response.json()
        logger.info("Fetched aliases successfully.")
        return aliases
    except requests.exceptions.RequestException as e:
        logger.error("Failed to fetch aliases: %s", e)
        return None


def create_alias(email_prefix, mailbox_id):
    """Create a new alias using the SimpleLogin API.

    Args:
        email_prefix (str): The prefix for the new alias email.
        mailbox_id (int): The ID of the mailbox where the alias will forward emails.

    Returns:
        dict: JSON response containing the created alias data if successful.
        None: If the request fails.
    """
    url = f"{SL_API_BASE_URL}/aliases"
    data = {
        "email_prefix": email_prefix,
        "mailbox_id": mailbox_id,
    }
    try:
        response = requests.post(url, json=data, headers=get_headers(), timeout=30)
        response.raise_for_status()
        alias = response.json()
        logger.info("Alias %s created successfully.", alias["email"])
        return alias
    except requests.exceptions.RequestException as e:
        logger.error("Failed to create alias: %s", e)
        return None


def delete_alias(alias_id):
    """Delete an alias by its ID using the SimpleLogin API.

    Args:
        alias_id (str): The ID of the alias to be deleted.

    Returns:
        bool: True if deletion is successful, False otherwise.
    """
    url = f"{SL_API_BASE_URL}/aliases/{alias_id}"
    try:
        response = requests.delete(
            url, headers=get_headers(include_content_type=False), timeout=30
        )
        response.raise_for_status()
        logger.info("Alias ID %s deleted successfully.", alias_id)
        return True
    except requests.exceptions.RequestException as e:
        logger.error("Failed to delete alias ID %s: %s", alias_id, e)
        return False
