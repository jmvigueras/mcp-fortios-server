#!/usr/bin/env python3
"""
FortiOS MCP Server Examples
Demonstrates how to use all available FortiOS tools
"""

import requests
import json

class FortiOSMCPClient:
    """Simple client for FortiOS MCP Server"""
    
    def __init__(self, server_url="http://localhost:8000/mcp"):
        self.server_url = server_url
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/event-stream'
        }
    
    def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Call a tool on the MCP server"""
        request_data = {
            "jsonrpc": "2.0",
            "id": f"test-{tool_name}",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        try:
            response = requests.post(self.server_url, 
                                   headers=self.headers, 
                                   json=request_data,
                                   stream=True)
            
            # Parse SSE response (simplified)
            response_text = response.text
            return {
                "status_code": response.status_code,
                "response": response_text
            }
        except Exception as e:
            return {
                "status_code": 0,
                "error": str(e)
            }

def main():
    """Demonstrate FortiOS MCP tools"""
    print("🚀 FortiOS MCP Server Tool Examples")
    print("="*60)
    
    client = FortiOSMCPClient()
    
    # Example FortiGate connection details (replace with your values)
    fortigate_config = {
        "fortigate_url": "https://192.168.1.99",
        "fortigate_token": "your-api-token-here",
        "fortigate_vdom": "root"
    }
    
    print("⚠️  Note: Replace the FortiGate connection details before running actual tests")
    print("   Current config is for demonstration purposes only\n")
    
    # 1. Test connectivity
    print("1️⃣  Testing Server Connectivity")
    result = client.call_tool("hello", {})
    print(f"   Status: {result['status_code']}")
    print(f"   Response preview: {result.get('response', '')[:100]}...\n")
    
    # 2. List available tools
    print("2️⃣  Listing Available Tools")
    result = client.call_tool("list_available_tools", {})
    print(f"   Status: {result['status_code']}")
    print(f"   Response preview: {result.get('response', '')[:200]}...\n")
    
    # 3. Address Object Examples
    print("3️⃣  Address Object Examples")
    
    # Create subnet address
    print("   📍 Creating subnet address object...")
    subnet_args = {
        "name": "Server_Subnet",
        "address_type": "ipmask",
        "subnet": "192.168.100.0 255.255.255.0",
        "comment": "Internal server subnet",
        **fortigate_config
    }
    result = client.call_tool("create_address", subnet_args)
    print(f"      Status: {result['status_code']}")
    
    # Create FQDN address
    print("   🌐 Creating FQDN address object...")
    fqdn_args = {
        "name": "Google_DNS",
        "address_type": "fqdn",
        "fqdn": "dns.google.com",
        "comment": "Google public DNS",
        **fortigate_config
    }
    result = client.call_tool("create_address", fqdn_args)
    print(f"      Status: {result['status_code']}")
    
    # Create IP range address
    print("   📏 Creating IP range address object...")
    range_args = {
        "name": "DHCP_Range",
        "address_type": "iprange", 
        "start_ip": "192.168.1.100",
        "end_ip": "192.168.1.200",
        "comment": "DHCP address range",
        **fortigate_config
    }
    result = client.call_tool("create_address", range_args)
    print(f"      Status: {result['status_code']}\n")
    
    # 4. Address Group Example
    print("4️⃣  Address Group Example")
    print("   👥 Creating address group...")
    group_args = {
        "name": "Internal_Networks",
        "members": ["Server_Subnet", "DHCP_Range"],
        "comment": "All internal network segments",
        **fortigate_config
    }
    result = client.call_tool("create_address_group", group_args)
    print(f"      Status: {result['status_code']}\n")
    
    # 5. VIP Object Example
    print("5️⃣  VIP Object Example")
    print("   🌐 Creating VIP object...")
    vip_args = {
        "name": "WebServer_VIP",
        "extip": "203.0.113.10",
        "mappedip": ["192.168.100.10"],
        "extintf": "wan1",
        "portforward": "enable",
        "extport": "80",
        "mappedport": "8080",
        "comment": "Web server port forwarding",
        **fortigate_config
    }
    result = client.call_tool("create_vip", vip_args)
    print(f"      Status: {result['status_code']}\n")
    
    # 6. Firewall Policy Example  
    print("6️⃣  Firewall Policy Example")
    print("   🛡️  Creating firewall policy...")
    policy_args = {
        "name": "Allow_Internal_to_Internet",
        "srcintf": ["internal"],
        "dstintf": ["wan1"],
        "srcaddr": ["Internal_Networks"],
        "dstaddr": ["all"],
        "service": ["HTTP", "HTTPS", "DNS"],
        "action": "accept",
        "status": "enable",
        "nat": "enable",
        "logtraffic": "utm",
        **fortigate_config
    }
    result = client.call_tool("create_firewall_policy", policy_args)
    print(f"      Status: {result['status_code']}\n")
    
    # 7. Retrieval Examples
    print("7️⃣  Data Retrieval Examples")
    
    # Get addresses
    print("   📋 Getting address objects...")
    result = client.call_tool("get_addresses", fortigate_config)
    print(f"      Status: {result['status_code']}")
    
    # Get firewall policies
    print("   📋 Getting firewall policies...")
    result = client.call_tool("get_firewall_policies", fortigate_config)
    print(f"      Status: {result['status_code']}")
    
    # Get VIPs
    print("   📋 Getting VIP objects...")
    result = client.call_tool("get_vips", fortigate_config)
    print(f"      Status: {result['status_code']}\n")
    
    print("✅ All examples completed!")
    print("   Replace FortiGate connection details to test with real device")
    print("   Check server logs for detailed API interaction information")

if __name__ == "__main__":
    main()