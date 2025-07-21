"""Simple tests for EnvoyClient that avoid Home Assistant test framework issues."""

from custom_components.enphase_production_toggle.envoy_client import EnvoyClient


def test_envoy_client_init():
    """Test EnvoyClient initialization."""
    client = EnvoyClient("192.168.1.100", "test@example.com", "password")

    assert client.host == "192.168.1.100"
    assert client.username == "test@example.com"
    assert client.password == "password"
    assert client.session_id is None
    assert client.jwt_token is None


def test_envoy_client_with_serial():
    """Test EnvoyClient initialization with serial number."""
    client = EnvoyClient("192.168.1.100", "test@example.com", "password", "123456")

    assert client.host == "192.168.1.100"
    assert client.username == "test@example.com"
    assert client.password == "password"
    assert client.serial_number == "123456"
    assert client.session_id is None
    assert client.jwt_token is None


def test_authenticate_method_exists():
    """Test that authenticate method exists and is callable."""
    client = EnvoyClient("192.168.1.100", "test@example.com", "password")

    assert hasattr(client, "authenticate")
    assert callable(client.authenticate)


def test_get_production_status_method_exists():
    """Test that get_production_status method exists and is callable."""
    client = EnvoyClient("192.168.1.100", "test@example.com", "password")

    assert hasattr(client, "get_production_status")
    assert callable(client.get_production_status)


def test_set_production_power_method_exists():
    """Test that set_production_power method exists and is callable."""
    client = EnvoyClient("192.168.1.100", "test@example.com", "password")

    assert hasattr(client, "set_production_power")
    assert callable(client.set_production_power)


def test_close_method_exists():
    """Test that close method exists and is callable."""
    client = EnvoyClient("192.168.1.100", "test@example.com", "password")

    assert hasattr(client, "close")
    assert callable(client.close)


def test_extract_session_id():
    """Test session ID extraction from response."""
    client = EnvoyClient("192.168.1.100", "test@example.com", "password")

    # Test valid session ID
    response_with_session = '{"session_id":"abc123def456"}'
    session_id = client._extract_session_id(response_with_session)
    assert session_id == "abc123def456"

    # Test invalid response
    response_without_session = '{"other":"data"}'
    session_id = client._extract_session_id(response_without_session)
    assert session_id is None


def test_oauth_code_generation_methods():
    """Test OAuth code generation helper methods."""
    client = EnvoyClient("192.168.1.100", "test@example.com", "password")

    # Test code verifier generation
    verifier = client._generate_code_verifier(40)
    assert isinstance(verifier, str)
    assert len(verifier) == 40

    # Test challenge generation
    challenge = client._generate_challenge(verifier)
    assert isinstance(challenge, str)
    assert len(challenge) > 0
