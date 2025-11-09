"""
Simple tests for FortiOS MCP Server
"""
import pytest
from unittest.mock import Mock, patch
from app.tools import FortiOSTools
from app.fortios_client import FortiOSClient


def test_imports():
    """Test basic imports work"""
    from app import server, tools, fortios_client
    assert all([server, tools, fortios_client])


def test_client_creation():
    """Test client creation"""
    client = FortiOSTools.create_client("https://test.com", "token123", "root")
    assert isinstance(client, FortiOSClient)
    assert client.url == "https://test.com"


@patch('app.tools.FortiOSTools.create_client')
def test_ping_success(mock_create_client):
    """Test successful ping"""
    mock_client = Mock()
    mock_client.get.return_value = {"http_status": 200}
    mock_create_client.return_value = mock_client
    
    result = FortiOSTools.ping_fortigate("https://test.com", "token123")
    
    assert result["success"] is True
    mock_client.get.assert_called_once_with("monitor/system/status")


@patch('app.tools.FortiOSTools.create_client')
def test_ping_failure(mock_create_client):
    """Test ping failure"""
    mock_create_client.side_effect = Exception("Connection failed")
    
    result = FortiOSTools.ping_fortigate("https://test.com", "token123")
    
    assert result["success"] is False


if __name__ == "__main__":
    pytest.main([__file__])