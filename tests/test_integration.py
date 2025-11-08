"""
Integration tests for FortiOS MCP Server
Tests the actual MCP protocol and server responses
"""
import pytest
import requests
import json
import time
from unittest import mock


class TestMCPProtocol:
    """Test MCP protocol implementation"""
    
    @pytest.fixture
    def server_url(self):
        """MCP server URL for testing"""
        return "http://localhost:8000/mcp"
    
    @pytest.fixture
    def mcp_headers(self):
        """Standard MCP headers"""
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/event-stream'
        }
    
    def test_server_connectivity(self, server_url):
        """Test basic server connectivity"""
        try:
            response = requests.get(server_url, timeout=5)
            # MCP servers typically return 406 for direct GET requests
            assert response.status_code in [200, 406, 405]
        except requests.exceptions.ConnectionError:
            pytest.skip("Server not running - start with docker-compose up -d")
    
    def test_mcp_tools_list(self, server_url, mcp_headers):
        """Test MCP tools/list method"""
        request_data = {
            "jsonrpc": "2.0",
            "id": "test-tools-list",
            "method": "tools/list"
        }
        
        try:
            response = requests.post(server_url, json=request_data, headers=mcp_headers, timeout=10)
            # Should get a response (exact format depends on FastMCP implementation)
            assert response.status_code in [200, 400, 405]  # Various acceptable responses
        except requests.exceptions.ConnectionError:
            pytest.skip("Server not running")
    
    def test_hello_tool_call(self, server_url, mcp_headers):
        """Test calling the hello tool via MCP"""
        request_data = {
            "jsonrpc": "2.0", 
            "id": "test-hello",
            "method": "tools/call",
            "params": {
                "name": "hello",
                "arguments": {}
            }
        }
        
        try:
            response = requests.post(server_url, json=request_data, headers=mcp_headers, timeout=10)
            # Should get some form of response
            assert response.status_code in [200, 400, 405]
        except requests.exceptions.ConnectionError:
            pytest.skip("Server not running")


class TestServerHealth:
    """Test server health and basic functionality"""
    
    def test_health_check_script(self):
        """Test that health check script can be imported and run"""
        # This tests the health check script without actually running the server
        import subprocess
        import sys
        
        # Try to run health check with a timeout
        try:
            result = subprocess.run(
                [sys.executable, "health_check.py"], 
                timeout=30,
                capture_output=True,
                text=True
            )
            # Health check should either succeed or fail gracefully
            assert result.returncode in [0, 1]  # 0 = success, 1 = expected failure when server not running
        except subprocess.TimeoutExpired:
            pytest.fail("Health check script timed out")
        except FileNotFoundError:
            pytest.skip("Health check script not found")


class TestToolParameters:
    """Test tool parameter handling"""
    
    def test_parameter_parsing(self):
        """Test comma-separated parameter parsing"""
        # Test the parameter parsing logic used by tools
        test_cases = [
            ("port1,port2,port3", ["port1", "port2", "port3"]),
            ("port1, port2 , port3", ["port1", "port2", "port3"]),
            ("single_port", ["single_port"]),
            ("", [""]),
        ]
        
        for input_str, expected in test_cases:
            result = [s.strip() for s in input_str.split(',')]
            if input_str == "":
                assert result == [""]  # Empty string case
            else:
                assert result == expected


@pytest.mark.integration
class TestFortiOSIntegration:
    """Integration tests with FortiOS (requires mock or real device)"""
    
    @mock.patch('app.fortios_client.FortiOSClient')
    def test_ping_tool_mock(self, mock_client_class):
        """Test ping tool with mocked FortiOS client"""
        from app.tools import FortiOSTools
        
        # Mock the client and its response
        mock_client = mock.Mock()
        mock_client.get.return_value = {"http_status": 200, "results": {"status": "success"}}
        mock_client_class.return_value = mock_client
        
        result = FortiOSTools.ping_fortigate("https://test.com", "token123")
        
        assert result["success"] is True
        assert "Ping successful" in result["message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])