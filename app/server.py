"""
FastMCP server for FortiOS integration

Run with:
    uvicorn app.server:app --host 0.0.0.0 --port 8000
"""

import json
import logging

from mcp.server.fastmcp import FastMCP

from .tools import FortiOSTools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create MCP server
mcp = FastMCP("FortiOS MCP Server")

# ===============================
# FIREWALL POLICY TOOLS
# ===============================


@mcp.tool()
def create_firewall_policy(
    name: str,
    srcintf: str,
    dstintf: str,
    srcaddr: str,
    dstaddr: str,
    service: str,
    action: str,
    fortigate_url: str,
    fortigate_token: str,
    fortigate_vdom: str = "root",
    status: str = "enable",
    nat: str = "disable",
    logtraffic: str = "utm",
) -> str:
    """Create a firewall policy in FortiGate.

    Args:
        name: Policy name
        srcintf: Source interface names (comma-separated)
        dstintf: Destination interface names (comma-separated)
        srcaddr: Source address names (comma-separated)
        dstaddr: Destination address names (comma-separated)
        service: Service names (comma-separated)
        action: Policy action (accept or deny)
        fortigate_url: FortiGate URL (e.g., https://192.168.1.99)
        fortigate_token: FortiGate API token
        fortigate_vdom: FortiGate VDOM (default: root)
        status: Policy status (enable or disable)
        nat: NAT setting (enable or disable)
        logtraffic: Log traffic (all, utm, or disable)
    """
    # Convert comma-separated strings to lists
    srcintf_list = [s.strip() for s in srcintf.split(",")]
    dstintf_list = [s.strip() for s in dstintf.split(",")]
    srcaddr_list = [s.strip() for s in srcaddr.split(",")]
    dstaddr_list = [s.strip() for s in dstaddr.split(",")]
    service_list = [s.strip() for s in service.split(",")]

    result = FortiOSTools.create_firewall_policy(
        fortigate_url,
        fortigate_token,
        fortigate_vdom,
        name,
        srcintf_list,
        dstintf_list,
        srcaddr_list,
        dstaddr_list,
        service_list,
        action,
        status,
        nat,
        logtraffic,
    )
    return json.dumps(result, indent=2)


@mcp.tool()
def get_firewall_policies(
    fortigate_url: str,
    fortigate_token: str,
    fortigate_vdom: str = "root",
    policy_id: str = "",
) -> str:
    """Get firewall policies from FortiGate.

    Args:
        fortigate_url: FortiGate URL (e.g., https://192.168.1.99)
        fortigate_token: FortiGate API token
        fortigate_vdom: FortiGate VDOM (default: root)
        policy_id: Specific policy ID to retrieve (empty for all policies)
    """
    policy_id_param = policy_id if policy_id else None
    result = FortiOSTools.get_firewall_policies(
        fortigate_url, fortigate_token, fortigate_vdom, policy_id_param
    )
    return json.dumps(result, indent=2)


# ===============================
# ADDRESS OBJECT TOOLS
# ===============================


@mcp.tool()
def create_address(
    name: str,
    address_type: str,
    fortigate_url: str,
    fortigate_token: str,
    fortigate_vdom: str = "root",
    subnet: str = "",
    start_ip: str = "",
    end_ip: str = "",
    fqdn: str = "",
    comment: str = "",
    color: int = 0,
) -> str:
    """Create an address object in FortiGate

    Args:
        name: Address object name
        address_type: Type of address (ipmask, iprange, fqdn)
        subnet: IP address and netmask (for ipmask type)
        start_ip: Start IP (for iprange type)
        end_ip: End IP (for iprange type)
        fqdn: FQDN (for fqdn type)
        comment: Optional comment
        color: Color for the address object (0-32)
    """
    # Convert empty strings to None for optional parameters
    subnet_param = subnet if subnet else None
    start_ip_param = start_ip if start_ip else None
    end_ip_param = end_ip if end_ip else None
    fqdn_param = fqdn if fqdn else None

    result = FortiOSTools.create_address(
        fortigate_url,
        fortigate_token,
        fortigate_vdom,
        name,
        address_type,
        subnet_param,
        start_ip_param,
        end_ip_param,
        fqdn_param,
        comment,
        color,
    )
    return json.dumps(result, indent=2)


@mcp.tool()
def get_addresses(
    fortigate_url: str,
    fortigate_token: str,
    fortigate_vdom: str = "root",
    address_name: str = "",
) -> str:
    """Get address objects from FortiGate.

    Args:
        fortigate_url: FortiGate URL (e.g., https://192.168.1.99)
        fortigate_token: FortiGate API token
        fortigate_vdom: FortiGate VDOM (default: root)
        address_name: Specific address name to retrieve (empty for all addresses)
    """
    address_name_param = address_name if address_name else None
    result = FortiOSTools.get_addresses(
        fortigate_url, fortigate_token, fortigate_vdom, address_name_param
    )
    return json.dumps(result, indent=2)


@mcp.tool()
def delete_address(
    name: str, fortigate_url: str, fortigate_token: str, fortigate_vdom: str = "root"
) -> str:
    """Delete an address object from FortiGate"""
    result = FortiOSTools.delete_address(
        fortigate_url, fortigate_token, fortigate_vdom, name
    )
    return json.dumps(result, indent=2)


# ===============================
# ADDRESS GROUP TOOLS
# ===============================


@mcp.tool()
def create_address_group(
    name: str,
    members: str,
    fortigate_url: str,
    fortigate_token: str,
    fortigate_vdom: str = "root",
    comment: str = "",
    color: int = 0,
) -> str:
    """Create an address group in FortiGate that contains existing address objects.

    Args:
        name: Address group name
        members: Existing address object names (comma-separated)
        fortigate_url: FortiGate URL (e.g., https://192.168.1.99)
        fortigate_token: FortiGate API token
        fortigate_vdom: FortiGate VDOM (default: root)
        comment: Optional comment
        color: Color for the address group (0-32)
    """
    # Convert comma-separated string to list
    members_list = [m.strip() for m in members.split(",")]

    result = FortiOSTools.create_address_group(
        fortigate_url,
        fortigate_token,
        fortigate_vdom,
        name,
        members_list,
        comment,
        color,
    )
    return json.dumps(result, indent=2)


@mcp.tool()
def get_address_groups(
    fortigate_url: str,
    fortigate_token: str,
    fortigate_vdom: str = "root",
    group_name: str = "",
) -> str:
    """Get address groups from FortiGate.

    Args:
        fortigate_url: FortiGate URL (e.g., https://192.168.1.99)
        fortigate_token: FortiGate API token
        fortigate_vdom: FortiGate VDOM (default: root)
        group_name: Specific group name to retrieve (empty for all groups)
    """
    group_name_param = group_name if group_name else None
    result = FortiOSTools.get_address_groups(
        fortigate_url, fortigate_token, fortigate_vdom, group_name_param
    )
    return json.dumps(result, indent=2)


@mcp.tool()
def delete_address_group(
    name: str, fortigate_url: str, fortigate_token: str, fortigate_vdom: str = "root"
) -> str:
    """Delete an address group from FortiGate"""
    result = FortiOSTools.delete_address_group(
        fortigate_url, fortigate_token, fortigate_vdom, name
    )
    return json.dumps(result, indent=2)


# ===============================
# VIP (VIRTUAL IP) TOOLS
# ===============================


@mcp.tool()
def create_vip(
    name: str,
    extip: str,
    mappedip: str,
    fortigate_url: str,
    fortigate_token: str,
    fortigate_vdom: str = "root",
    extintf: str = "any",
    portforward: str = "disable",
    extport: str = "",
    mappedport: str = "",
    protocol: str = "tcp",
    comment: str = "",
) -> str:
    """Create a Virtual IP (VIP) object in FortiGate.

    Args:
        name: VIP object name
        extip: External IP address
        mappedip: Mapped IP addresses (comma-separated)
        fortigate_url: FortiGate URL (e.g., https://192.168.1.99)
        fortigate_token: FortiGate API token
        fortigate_vdom: FortiGate VDOM (default: root)
        extintf: External interface (default: any)
        portforward: Enable port forwarding (enable or disable)
        extport: External port range (empty if no port forwarding)
        mappedport: Mapped port range (empty if no port forwarding)
        protocol: Protocol (tcp, udp, sctp)
        comment: Optional comment
    """
    # Convert comma-separated string to list
    mappedip_list = [ip.strip() for ip in mappedip.split(",")]

    # Handle optional port parameters
    extport_param = extport if extport else None
    mappedport_param = mappedport if mappedport else None

    result = FortiOSTools.create_vip(
        fortigate_url,
        fortigate_token,
        fortigate_vdom,
        name,
        extip,
        mappedip_list,
        extintf,
        portforward,
        extport_param,
        mappedport_param,
        protocol,
        comment,
    )
    return json.dumps(result, indent=2)


@mcp.tool()
def get_vips(
    fortigate_url: str,
    fortigate_token: str,
    fortigate_vdom: str = "root",
    vip_name: str = "",
) -> str:
    """Get VIP objects from FortiGate.

    Args:
        fortigate_url: FortiGate URL (e.g., https://192.168.1.99)
        fortigate_token: FortiGate API token
        fortigate_vdom: FortiGate VDOM (default: root)
        vip_name: Specific VIP name to retrieve (empty for all VIPs)
    """
    vip_name_param = vip_name if vip_name else None
    result = FortiOSTools.get_vips(
        fortigate_url, fortigate_token, fortigate_vdom, vip_name_param
    )
    return json.dumps(result, indent=2)


# ===============================
# DEBUG TOOLS
# ===============================
@mcp.tool()
def ping_fortigate(fortigate_url: str, fortigate_token: str) -> str:
    """Ping the FortiGate to check connectivity."""
    result = FortiOSTools.ping_fortigate(fortigate_url, fortigate_token)
    return json.dumps(result, indent=2)


# Create the ASGI app for HTTP server using the streamable HTTP app
app = mcp.streamable_http_app()
