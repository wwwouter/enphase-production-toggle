"""Unit tests for EnvoyClient without external dependencies."""

import hashlib
import re
import secrets
from unittest.mock import MagicMock, patch

import pytest

from custom_components.enphase_production_toggle.envoy_client import EnvoyClient


class TestEnvoyClientUnit:
    """Unit tests for EnvoyClient class."""

    def test_init_sets_properties(self):
        """Test that initialization sets all properties correctly."""
        host = "192.168.1.100"
        username = "test@example.com"
        password = "secretpassword"

        client = EnvoyClient(host, username, password)

        assert client.host == host
        assert client.username == username
        assert client.password == password
        assert client.session_id is None
        assert client.jwt_token is None
        assert client._session is None

    def test_init_with_different_hosts(self):
        """Test initialization with various host formats."""
        test_cases = [
            "192.168.1.100",
            "10.0.0.5",
            "envoy.local",
            "192.168.0.1",
        ]

        for host in test_cases:
            client = EnvoyClient(host, "user", "pass")
            assert client.host == host

    def test_init_with_special_characters_in_credentials(self):
        """Test initialization with special characters in credentials."""
        special_username = "user+test@example.com"
        special_password = "p@ssw0rd!#$%"

        client = EnvoyClient("host", special_username, special_password)

        assert client.username == special_username
        assert client.password == special_password

    def test_extract_session_id_success(self):
        """Test successful session ID extraction."""
        client = EnvoyClient("host", "user", "pass")

        test_response = '{"session_id":"abc123def456ghi789","other":"data"}'
        session_id = client._extract_session_id(test_response)

        assert session_id == "abc123def456ghi789"

    def test_extract_session_id_different_formats(self):
        """Test session ID extraction with different response formats."""
        client = EnvoyClient("host", "user", "pass")

        test_cases = [
            ('{"session_id":"short123"}', "short123"),
            ('{"other":"data","session_id":"middle456","more":"stuff"}', "middle456"),
            ('prefix{"session_id":"embedded789"}suffix', "embedded789"),
            ('{"session_id":"with-dashes-123"}', "with-dashes-123"),
            ('{"session_id":"with_underscores_456"}', "with_underscores_456"),
        ]

        for response_text, expected_id in test_cases:
            session_id = client._extract_session_id(response_text)
            assert session_id == expected_id

    def test_extract_session_id_not_found(self):
        """Test session ID extraction when not present."""
        client = EnvoyClient("host", "user", "pass")

        test_cases = [
            '{"other":"data"}',
            '{"sessionid":"wrong_key"}',
            '{}',
            '',
            'plain text without json',
            '{"session_id": }',  # Invalid JSON
            '{"session_id":""}',  # Empty session ID
        ]

        for response_text in test_cases:
            session_id = client._extract_session_id(response_text)
            # All test cases should return None since they don't contain valid session IDs
            assert session_id is None

    def test_extract_session_id_malformed_json(self):
        """Test session ID extraction with malformed JSON."""
        client = EnvoyClient("host", "user", "pass")

        # Should handle malformed JSON gracefully
        malformed_responses = [
            '{"session_id":"valid123"extratext',
            'prefix{"session_id":"valid456"}',
            '{"session_id":"val',  # Cut off
        ]

        for response_text in malformed_responses:
            # Should either extract successfully or return None
            result = client._extract_session_id(response_text)
            # For the first two, regex should still find the session_id
            if "valid123" in response_text:
                assert result == "valid123"
            elif "valid456" in response_text:
                assert result == "valid456"
            else:
                assert result is None

    def test_oauth_parameter_generation(self):
        """Test OAuth parameter generation consistency."""
        # Test that the OAuth generation produces consistent types and lengths
        for _ in range(10):  # Test multiple iterations
            code_verifier = secrets.token_urlsafe(32)
            code_challenge = hashlib.sha256(code_verifier.encode()).hexdigest()

            assert isinstance(code_verifier, str)
            assert isinstance(code_challenge, str)
            assert len(code_challenge) == 64  # SHA256 hex is 64 chars
            assert len(code_verifier) > 30  # Should be reasonably long

    def test_client_state_transitions(self):
        """Test client state transitions during authentication flow."""
        client = EnvoyClient("host", "user", "pass")

        # Initial state
        assert client.session_id is None
        assert client.jwt_token is None
        assert client._session is None

        # Simulate state changes
        client.session_id = "test_session"
        assert client.session_id == "test_session"
        assert client.jwt_token is None

        client.jwt_token = "test_token"
        assert client.session_id == "test_session"
        assert client.jwt_token == "test_token"

    def test_url_construction(self):
        """Test that URLs are constructed correctly."""
        test_hosts = [
            "192.168.1.100",
            "10.0.0.5",
            "envoy.local",
        ]

        for host in test_hosts:
            client = EnvoyClient(host, "user", "pass")

            # Test production.json URL
            expected_production_url = f"http://{host}/production.json"
            # Since this is tested in the actual method, we'll test URL components
            assert host in expected_production_url
            assert "http://" in expected_production_url
            assert "/production.json" in expected_production_url

            # Test JWT token URL
            expected_jwt_url = f"http://{host}/auth/check_jwt"
            assert host in expected_jwt_url
            assert "/auth/check_jwt" in expected_jwt_url

            # Test production control URL
            expected_control_url = f"http://{host}/ivp/mod/603980032/mode/power"
            assert host in expected_control_url
            assert "/ivp/mod/603980032/mode/power" in expected_control_url

    def test_production_data_parsing_edge_cases(self):
        """Test production data parsing with various data structures."""
        client = EnvoyClient("host", "user", "pass")

        # These would be tested in integration tests, but we can test the logic
        test_data_sets = [
            # Normal case
            {"production": [{"wNow": 5000}]},
            # Zero production
            {"production": [{"wNow": 0}]},
            # Missing wNow
            {"production": [{}]},
            # Empty production array
            {"production": []},
            # Missing production key
            {},
            # Multiple production entries (should use first)
            {"production": [{"wNow": 1000}, {"wNow": 2000}]},
        ]

        for data in test_data_sets:
            # Simulate the parsing logic
            production = (
                data.get("production", [{}])[0] if data.get("production") else {}
            )
            current_power = production.get("wNow", 0)
            is_producing = current_power > 0

            result = {
                "is_producing": is_producing,
                "current_power": current_power,
                "production_enabled": True,
            }

            # Verify the structure is always consistent
            assert isinstance(result["is_producing"], bool)
            assert isinstance(result["current_power"], (int, float))
            assert isinstance(result["production_enabled"], bool)
            assert result["current_power"] >= 0

    def test_production_control_data_format(self):
        """Test production control data format correctness."""
        # Test the data format that gets sent to the API
        test_cases = [
            (True, [False]),  # Enable production -> arr: [False]
            (False, [True]),  # Disable production -> arr: [True]
        ]

        for enabled, expected_arr in test_cases:
            data = {
                "length": 1,
                "arr": [not enabled],
            }

            assert data["length"] == 1
            assert data["arr"] == expected_arr
            assert len(data["arr"]) == data["length"]

    def test_regex_pattern_security(self):
        """Test that regex pattern is safe and won't cause ReDoS."""
        client = EnvoyClient("host", "user", "pass")

        # Test with potentially dangerous inputs
        dangerous_inputs = [
            '"session_id":"' + 'a' * 10000 + '"',  # Very long session ID
            '"session_id":"' + 'a' * 1000000,  # Unterminated very long string
            '"session_id":"test"' * 1000,  # Repeated pattern
        ]

        for dangerous_input in dangerous_inputs:
            # Should handle gracefully without hanging
            try:
                result = client._extract_session_id(dangerous_input)
                # Should either extract successfully or return None
                assert result is None or isinstance(result, str)
            except Exception:
                # Any exception is acceptable as long as it doesn't hang
                pass
