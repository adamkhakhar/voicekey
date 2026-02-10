"""Tests for API key storage via keyring."""

from oai_whisper import auth
from oai_whisper.constants import KEYCHAIN_SERVICE, KEYCHAIN_USERNAME


def test_get_api_key(mocker):
    """get_api_key() delegates to keyring.get_password."""
    mock_get = mocker.patch("oai_whisper.auth.keyring.get_password", return_value="sk-test123")
    result = auth.get_api_key()
    assert result == "sk-test123"
    mock_get.assert_called_once_with(KEYCHAIN_SERVICE, KEYCHAIN_USERNAME)


def test_get_api_key_returns_none(mocker):
    """get_api_key() returns None when no key stored."""
    mocker.patch("oai_whisper.auth.keyring.get_password", return_value=None)
    assert auth.get_api_key() is None


def test_set_api_key(mocker):
    """set_api_key() delegates to keyring.set_password."""
    mock_set = mocker.patch("oai_whisper.auth.keyring.set_password")
    auth.set_api_key("sk-newkey")
    mock_set.assert_called_once_with(KEYCHAIN_SERVICE, KEYCHAIN_USERNAME, "sk-newkey")


def test_delete_api_key(mocker):
    """delete_api_key() delegates to keyring.delete_password."""
    mock_del = mocker.patch("oai_whisper.auth.keyring.delete_password")
    auth.delete_api_key()
    mock_del.assert_called_once_with(KEYCHAIN_SERVICE, KEYCHAIN_USERNAME)


def test_delete_api_key_ignores_not_found(mocker):
    """delete_api_key() silently handles PasswordDeleteError."""
    import keyring.errors
    mocker.patch(
        "oai_whisper.auth.keyring.delete_password",
        side_effect=keyring.errors.PasswordDeleteError("not found"),
    )
    # Should not raise
    auth.delete_api_key()
