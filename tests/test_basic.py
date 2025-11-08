"""
Basic tests for FortiOS MCP Server
"""
import pytest
import json
from unittest.mock import Mock, patch
from app.tools import FortiOSTools
from app.fortios_client import FortiOSClient


class TestFortiOSTools:
    """Test FortiOS tools functionality"""
    
    def test_create_client(self):
        """Test client creation"""
        client = FortiOSTools.create_client("https://test.com", "token123", "root")
        assert isinstance(client, FortiOSClient)
        assert client.url == "https://test.com"
        assert client.token == "token123"
        assert client.vdom == "root"
    
    @patch('app.tools.FortiOSTools.create_client')
    def test_ping_fortigate_success(self, mock_create_client):
        """Test successful FortiGate ping"""
        # Mock client and response
        mock_client = Mock()
        mock_client.get.return_value = {"http_status": 200, "results": {"status": "success"}}
        mock_create_client.return_value = mock_client
        
        result = FortiOSTools.ping_fortigate("https://test.com", "token123")
        
        assert result["success"] is True
        assert "Ping successful" in result["message"]
        mock_client.get.assert_called_once_with("monitor/system/ping")
    
    @patch('app.tools.FortiOSTools.create_client')
    def test_ping_fortigate_failure(self, mock_create_client):
        """Test FortiGate ping failure"""
        # Mock client exception
        mock_create_client.side_effect = Exception("Connection failed")
        
        result = FortiOSTools.ping_fortigate("https://test.com", "token123")
        
        assert result["success"] is False
        assert "Connection failed" in result["message"]


class TestFortiOSClient:
    """Test FortiOS client functionality"""
    
    def test_client_initialization(self):
        """Test client initialization"""
        client = FortiOSClient("https://test.com", "token123", "root")
        
        assert client.url == "https://test.com"
        assert client.token == "token123"
        assert client.vdom == "root"
        assert client.verify_ssl is False  # Default is False for FortiOS self-signed certs
    
    def test_client_initialization_no_ssl(self):
        """Test client initialization without SSL verification"""
        client = FortiOSClient("https://test.com", "token123", "root", verify_ssl=False)
        
        assert client.verify_ssl is False


class TestToolParameters:
    """Test tool parameter validation"""
    
    def test_comma_separated_parsing(self):
        """Test comma-separated string parsing"""
        # Test normal case
        test_string = "port1,port2,port3"
        result = [s.strip() for s in test_string.split(',')]
        expected = ["port1", "port2", "port3"]
        assert result == expected
        
        # Test with spaces
        test_string = "port1, port2 , port3"
        result = [s.strip() for s in test_string.split(',')]
        expected = ["port1", "port2", "port3"]
        assert result == expected
        
        # Test single item
        test_string = "port1"
        result = [s.strip() for s in test_string.split(',')]
        expected = ["port1"]
        assert result == expected


class TestJSONSerialization:
    """Test JSON serialization for MCP responses"""
    
    def test_json_serialization(self):
        """Test that responses can be serialized to JSON"""
        test_data = {
            "success": True,
            "data": {
                "name": "test_policy",
                "status": "enabled"
            },
            "message": "Policy created successfully"
        }
        
        # Should not raise exception
        json_str = json.dumps(test_data, indent=2)
        assert isinstance(json_str, str)
        
        # Should be deserializable
        parsed = json.loads(json_str)
        assert parsed == test_data


def test_basic_imports():
    """Test that all modules can be imported"""
    from app import server
    from app import tools
    from app import fortios_client
    
    assert server is not None
    assert tools is not None
    assert fortios_client is not None


if __name__ == "__main__":
    pytest.main([__file__])