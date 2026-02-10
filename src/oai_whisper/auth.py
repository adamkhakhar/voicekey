"""API key storage via macOS Keychain (keyring)."""

import keyring

from .constants import KEYCHAIN_SERVICE, KEYCHAIN_USERNAME


def get_api_key() -> str | None:
    return keyring.get_password(KEYCHAIN_SERVICE, KEYCHAIN_USERNAME)


def set_api_key(key: str) -> None:
    keyring.set_password(KEYCHAIN_SERVICE, KEYCHAIN_USERNAME, key)


def delete_api_key() -> None:
    try:
        keyring.delete_password(KEYCHAIN_SERVICE, KEYCHAIN_USERNAME)
    except keyring.errors.PasswordDeleteError:
        pass
