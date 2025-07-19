"""Test the Enphase Envoy client."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from custom_components.enphase_production_toggle.envoy_client import EnvoyClient


@pytest.mark.asyncio
async def test_envoy_client_init():
    """Test EnvoyClient initialization."""
    client = EnvoyClient("192.168.1.100", "test@example.com", "password")
    
    assert client.host == "192.168.1.100"
    assert client.username == "test@example.com"
    assert client.password == "password"
    assert client.session_id is None
    assert client.jwt_token is None


@pytest.mark.asyncio
async def test_authenticate_success(mock_aiohttp_session):
    """Test successful authentication."""
    client = EnvoyClient("192.168.1.100", "test@example.com", "password")
    
    with patch("aiohttp.ClientSession", return_value=mock_aiohttp_session):
        await client.authenticate()
        
        # Verify session creation and authentication calls
        assert client._session is not None


@pytest.mark.asyncio
async def test_authenticate_failure():
    """Test authentication failure."""
    client = EnvoyClient("192.168.1.100", "test@example.com", "password")
    
    with patch("aiohttp.ClientSession") as mock_session_class:
        mock_session = mock_session_class.return_value
        mock_response = MagicMock()
        mock_response.status = 401
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        mock_session.post.return_value = mock_response
        
        with pytest.raises(Exception, match="Authentication failed: 401"):
            await client.authenticate()


@pytest.mark.asyncio
async def test_get_production_status_success(mock_aiohttp_session):
    """Test successful production status retrieval."""
    client = EnvoyClient("192.168.1.100", "test@example.com", "password")
    client.jwt_token = "test_token"
    client._session = mock_aiohttp_session
    
    result = await client.get_production_status()
    
    expected = {
        "is_producing": True,
        "current_power": 5000,
        "production_enabled": True,
    }
    assert result == expected


@pytest.mark.asyncio
async def test_get_production_status_failure():
    """Test production status retrieval failure."""
    client = EnvoyClient("192.168.1.100", "test@example.com", "password")
    client.jwt_token = "test_token"
    
    with patch("aiohttp.ClientSession") as mock_session_class:
        mock_session = mock_session_class.return_value
        mock_response = MagicMock()
        mock_response.status = 404
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        mock_session.get.return_value = mock_response
        
        client._session = mock_session
        
        with pytest.raises(Exception, match="Failed to get production status: 404"):
            await client.get_production_status()


@pytest.mark.asyncio
async def test_set_production_power_enable(mock_aiohttp_session):
    """Test enabling production power."""
    client = EnvoyClient("192.168.1.100", "test@example.com", "password")
    client.jwt_token = "test_token"
    
    with patch("aiohttp.ClientSession", return_value=mock_aiohttp_session):
        client._session = mock_aiohttp_session
        await client.set_production_power(True)
        
        # Verify PUT request was made with correct data
        mock_aiohttp_session.put.assert_called_once()
        call_args = mock_aiohttp_session.put.call_args
        assert "ivp/mod/603980032/mode/power" in call_args[0][0]
        assert call_args[1]["json"]["arr"] == [False]  # False = production on


@pytest.mark.asyncio
async def test_set_production_power_disable(mock_aiohttp_session):
    """Test disabling production power."""
    client = EnvoyClient("192.168.1.100", "test@example.com", "password")
    client.jwt_token = "test_token"
    
    with patch("aiohttp.ClientSession", return_value=mock_aiohttp_session):
        client._session = mock_aiohttp_session
        await client.set_production_power(False)
        
        # Verify PUT request was made with correct data
        mock_aiohttp_session.put.assert_called_once()
        call_args = mock_aiohttp_session.put.call_args
        assert call_args[1]["json"]["arr"] == [True]  # True = production off


@pytest.mark.asyncio
async def test_set_production_power_failure():
    """Test production power setting failure."""
    client = EnvoyClient("192.168.1.100", "test@example.com", "password")
    client.jwt_token = "test_token"
    
    with patch("aiohttp.ClientSession") as mock_session_class:
        mock_session = mock_session_class.return_value
        mock_response = MagicMock()
        mock_response.status = 500
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        mock_session.put.return_value = mock_response
        
        client._session = mock_session
        
        with pytest.raises(Exception, match="Failed to set production power: 500"):
            await client.set_production_power(True)


@pytest.mark.asyncio
async def test_close():
    """Test client session closing."""
    client = EnvoyClient("192.168.1.100", "test@example.com", "password")
    
    mock_session = AsyncMock()
    client._session = mock_session
    
    await client.close()
    
    mock_session.close.assert_called_once()
    assert client._session is None


def test_extract_session_id():
    """Test session ID extraction from response."""
    client = EnvoyClient("192.168.1.100", "test@example.com", "password")
    
    response_text = '{"session_id":"abc123def456","other":"data"}'
    session_id = client._extract_session_id(response_text)
    
    assert session_id == "abc123def456"


def test_extract_session_id_not_found():
    """Test session ID extraction when not found."""
    client = EnvoyClient("192.168.1.100", "test@example.com", "password")
    
    response_text = '{"other":"data"}'
    session_id = client._extract_session_id(response_text)
    
    assert session_id is None