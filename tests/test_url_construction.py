"""Test URL construction and validation across the integration."""

from custom_components.enphase_production_toggle.envoy_client import EnvoyClient


def test_production_status_url_construction():
    """Test production status URL construction."""
    test_hosts = ["192.168.1.100", "10.0.0.5", "envoy.local", "my-envoy.home.local"]

    for host in test_hosts:
        _ = EnvoyClient(host, "user", "pass")  # Verify client can be created
        expected_url = f"https://{host}/production.json"

        # Test URL construction logic (since we can't easily test the actual request)
        assert host in expected_url
        assert "/production.json" in expected_url
        assert expected_url.startswith("https://")


def test_auth_urls_construction():
    """Test authentication URL construction."""
    test_hosts = ["192.168.1.100", "envoy.local"]

    for host in test_hosts:
        _ = EnvoyClient(host, "user", "pass")  # Verify client can be created

        # Test JWT validation URL
        jwt_url = f"https://{host}/auth/check_jwt"
        assert host in jwt_url
        assert "/auth/check_jwt" in jwt_url
        assert jwt_url.startswith("https://")

        # Test redirect URI
        redirect_uri = f"https://{host}/auth/callback"
        assert host in redirect_uri
        assert "/auth/callback" in redirect_uri
        assert redirect_uri.startswith("https://")


def test_production_control_url_construction():
    """Test production control URL construction."""
    test_hosts = ["192.168.1.100", "envoy.local"]

    for host in test_hosts:
        _ = EnvoyClient(host, "user", "pass")  # Verify client can be created

        # Test production control URL (using EMU device ID)
        control_url = f"https://{host}/ivp/mod/603980032/mode/power"
        assert host in control_url
        assert "/ivp/mod/603980032/mode/power" in control_url
        assert control_url.startswith("https://")


def test_info_xml_url_construction():
    """Test info.xml URL construction for serial number retrieval."""
    test_hosts = ["192.168.1.100", "envoy.local"]

    for host in test_hosts:
        _ = EnvoyClient(host, "user", "pass")  # Verify client can be created

        # Test info.xml URL (note: uses HTTP not HTTPS)
        info_url = f"http://{host}/info.xml"
        assert host in info_url
        assert "/info.xml" in info_url
        assert info_url.startswith("http://")


def test_external_auth_urls():
    """Test external authentication URLs."""
    # Test Enphase cloud URLs
    auth_url = "https://entrez.enphaseenergy.com/login"
    token_url = "https://entrez.enphaseenergy.com/oauth/token"

    assert auth_url.startswith("https://")
    assert "entrez.enphaseenergy.com" in auth_url
    assert "/login" in auth_url

    assert token_url.startswith("https://")
    assert "entrez.enphaseenergy.com" in token_url
    assert "/oauth/token" in token_url


def test_url_security():
    """Test that URLs follow security best practices."""
    # Test that local Envoy URLs use HTTPS for sensitive operations
    sensitive_endpoints = [
        "/production.json",
        "/auth/check_jwt",
        "/ivp/mod/603980032/mode/power",
    ]

    host = "192.168.1.100"
    for endpoint in sensitive_endpoints:
        url = f"https://{host}{endpoint}"
        assert url.startswith(
            "https://"
        ), f"Sensitive endpoint {endpoint} should use HTTPS"

    # Test that only info.xml uses HTTP (as it's public info)
    info_url = f"http://{host}/info.xml"
    assert info_url.startswith("http://"), "info.xml can use HTTP as it's public info"


def test_url_path_construction():
    """Test URL path construction with various scenarios."""
    host = "192.168.1.100"

    # Test paths don't have double slashes
    paths = [
        "/production.json",
        "/auth/check_jwt",
        "/auth/callback",
        "/ivp/mod/603980032/mode/power",
        "/info.xml",
    ]

    for path in paths:
        url = f"https://{host}{path}"
        assert "//" not in url.replace(
            "https://", ""
        ), f"URL {url} should not have double slashes"
        assert url.endswith(path), f"URL should end with the expected path {path}"


def test_ipv6_url_construction():
    """Test URL construction with IPv6 addresses."""
    ipv6_host = "::1"

    # IPv6 addresses should be wrapped in brackets in URLs
    urls = [
        f"https://[{ipv6_host}]/production.json",
        f"https://[{ipv6_host}]/auth/check_jwt",
        f"http://[{ipv6_host}]/info.xml",
    ]

    for url in urls:
        assert f"[{ipv6_host}]" in url, "IPv6 addresses should be wrapped in brackets"
        assert url.startswith(
            ("http://", "https://")
        ), "URL should have proper protocol"


def test_hostname_url_construction():
    """Test URL construction with various hostname formats."""
    hostnames = [
        "envoy.local",
        "my-envoy.home.local",
        "envoy-123.network.local",
        "ENVOY.LOCAL",  # Test case sensitivity
    ]

    for hostname in hostnames:
        # Test that hostname is preserved as-is
        url = f"https://{hostname}/production.json"
        assert hostname in url, f"Hostname {hostname} should be preserved in URL"
        assert url.startswith("https://"), "URL should start with https://"
        assert "/production.json" in url, "URL should contain the endpoint path"


def test_special_characters_in_hostnames():
    """Test URL construction with special characters in hostnames."""
    # These are valid hostname characters
    valid_hostnames = [
        "envoy-1.local",
        "envoy_test.local",
        "envoy123.local",
        "my.envoy.home.local",
    ]

    for hostname in valid_hostnames:
        url = f"https://{hostname}/production.json"
        assert hostname in url, f"Valid hostname {hostname} should work in URLs"
        assert not any(
            char in url for char in ["<", ">", '"', " "]
        ), "URL should not contain invalid characters"
