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


def test_oauth_code_generation_different_lengths():
    """Test OAuth code generation with different lengths."""
    client = EnvoyClient("192.168.1.100", "test@example.com", "password")

    # Test different verifier lengths
    for length in [32, 40, 64, 128]:
        verifier = client._generate_code_verifier(length)
        assert isinstance(verifier, str)
        assert len(verifier) == length

        # Ensure verifier contains only valid characters (letters and digits)
        assert verifier.isalnum()


def test_oauth_code_challenge_consistency():
    """Test that OAuth code challenge is consistent for same input."""
    client = EnvoyClient("192.168.1.100", "test@example.com", "password")

    verifier = "test_verifier_123"
    challenge1 = client._generate_challenge(verifier)
    challenge2 = client._generate_challenge(verifier)

    # Same input should produce same challenge
    assert challenge1 == challenge2
    assert isinstance(challenge1, str)
    assert len(challenge1) > 0


def test_extract_session_id_edge_cases():
    """Test session ID extraction with various edge cases."""
    client = EnvoyClient("192.168.1.100", "test@example.com", "password")

    test_cases = [
        # Valid cases
        ('{"session_id":"abc123"}', "abc123"),
        ('{"other":"data","session_id":"def456","more":"stuff"}', "def456"),
        ('prefix{"session_id":"ghi789"}suffix', "ghi789"),
        # Invalid cases
        ('{"sessionid":"wrong_key"}', None),
        ('{"session_id":""}', None),  # Empty session ID
        ("{}", None),
        ("", None),
        ("not json at all", None),
        ('{"session_id":null}', None),
    ]

    for response_text, expected in test_cases:
        result = client._extract_session_id(response_text)
        assert result == expected


def test_client_initialization_edge_cases():
    """Test client initialization with various edge cases."""
    # Test with IPv6 address
    client_ipv6 = EnvoyClient("::1", "test@example.com", "password")
    assert client_ipv6.host == "::1"

    # Test with hostname
    client_hostname = EnvoyClient("envoy.local", "test@example.com", "password")
    assert client_hostname.host == "envoy.local"

    # Test with special characters in credentials
    client_special = EnvoyClient(
        "192.168.1.100", "user+test@example.com", "p@ssw0rd!#$%^&*()", "SN123456789"
    )
    assert client_special.username == "user+test@example.com"
    assert client_special.password == "p@ssw0rd!#$%^&*()"
    assert client_special.serial_number == "SN123456789"


def test_client_state_management():
    """Test client state management through various scenarios."""
    client = EnvoyClient("192.168.1.100", "test@example.com", "password")

    # Initial state
    assert client.session_id is None
    assert client.jwt_token is None
    assert client._session is None

    # Simulate state changes
    client.session_id = "test_session_123"
    client.jwt_token = "test_jwt_token_456"

    assert client.session_id == "test_session_123"
    assert client.jwt_token == "test_jwt_token_456"

    # Reset state
    client.session_id = None
    client.jwt_token = None

    assert client.session_id is None
    assert client.jwt_token is None


def test_client_debug_mode():
    """Test client debug mode functionality."""
    client = EnvoyClient("192.168.1.100", "test@example.com", "password")

    # Test debug mode property
    assert hasattr(client, "_debug_mode")
    assert client._debug_mode is False

    # Test setting debug mode
    client._debug_mode = True
    assert client._debug_mode is True

    client._debug_mode = False
    assert client._debug_mode is False
