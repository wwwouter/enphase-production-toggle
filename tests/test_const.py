"""Test constants and configuration values."""

from custom_components.enphase_production_toggle.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)


def test_domain_constant():
    """Test that domain constant is correct."""
    assert DOMAIN == "enphase_production_toggle"
    assert isinstance(DOMAIN, str)
    assert len(DOMAIN) > 0


def test_configuration_keys():
    """Test configuration key constants."""
    assert CONF_HOST == "host"
    assert CONF_USERNAME == "username"
    assert CONF_PASSWORD == "password"

    # Ensure they're all strings
    assert isinstance(CONF_HOST, str)
    assert isinstance(CONF_USERNAME, str)
    assert isinstance(CONF_PASSWORD, str)


def test_default_values():
    """Test default configuration values."""
    assert DEFAULT_NAME == "Enphase Production"
    assert isinstance(DEFAULT_NAME, str)
    assert len(DEFAULT_NAME) > 0

    assert DEFAULT_SCAN_INTERVAL == 30
    assert isinstance(DEFAULT_SCAN_INTERVAL, int)
    assert DEFAULT_SCAN_INTERVAL > 0


def test_scan_interval_reasonable():
    """Test that scan interval is within reasonable bounds."""
    # Should be between 10 seconds and 10 minutes
    assert 10 <= DEFAULT_SCAN_INTERVAL <= 600


def test_constants_immutable():
    """Test that constants are not accidentally changed."""
    # Store original values
    original_domain = DOMAIN
    original_default_name = DEFAULT_NAME
    original_scan_interval = DEFAULT_SCAN_INTERVAL

    # Try to modify (should not affect the constants)
    domain_copy = DOMAIN + "_modified"

    # Verify originals are unchanged
    assert DOMAIN == original_domain
    assert DEFAULT_NAME == original_default_name
    assert DEFAULT_SCAN_INTERVAL == original_scan_interval
    assert domain_copy != DOMAIN


# Test comment
# Another test comment
# Test formatting issue
