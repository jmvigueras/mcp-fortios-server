"""
FortiOS Tools Implementation for MCP Server
"""

import ipaddress
import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from .fortios_client import FortiOSClient

logger = logging.getLogger(__name__)

# Validation patterns
# FortiGate resource names: alphanumeric, spaces, hyphens, underscores, dots
SAFE_RESOURCE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9 _.\-]+$")
VALID_ACTIONS = {"accept", "deny"}
VALID_ADDRESS_TYPES = {"ipmask", "iprange", "fqdn"}
VALID_STATUSES = {"enable", "disable"}
VALID_NAT_OPTIONS = {"enable", "disable"}
VALID_LOGTRAFFIC_OPTIONS = {"all", "utm", "disable"}
VALID_PORTFORWARD_OPTIONS = {"enable", "disable"}
VALID_PROTOCOLS = {"tcp", "udp", "sctp"}
MAX_COLOR_VALUE = 32
MIN_COLOR_VALUE = 0


class ValidationError(Exception):
    """Raised when input validation fails"""

    pass


def _validate_resource_name(name: str, field_name: str = "name") -> str:
    """
    Validate and sanitize a resource name for use in API URL paths.

    Args:
        name: The resource name to validate
        field_name: Name of the field for error messages

    Returns:
        URL-encoded resource name safe for use in paths

    Raises:
        ValidationError: If the name contains dangerous patterns
    """
    if not name or not name.strip():
        raise ValidationError(f"{field_name} cannot be empty")

    name = name.strip()

    # Block path traversal attempts
    if ".." in name or "/" in name or "\\" in name:
        raise ValidationError(
            f"{field_name} contains invalid characters (path traversal not allowed)"
        )

    # URL-encode the name for safe use in URL paths
    return quote(name, safe="")


def _validate_color(color: int) -> int:
    """Validate color value is within FortiGate's accepted range (0-32)"""
    if not isinstance(color, int) or color < MIN_COLOR_VALUE or color > MAX_COLOR_VALUE:
        raise ValidationError(
            f"color must be an integer between {MIN_COLOR_VALUE} and {MAX_COLOR_VALUE}"
        )
    return color


def _validate_action(action: str) -> str:
    """Validate firewall policy action"""
    action = action.strip().lower()
    if action not in VALID_ACTIONS:
        raise ValidationError(
            f"action must be one of: {', '.join(sorted(VALID_ACTIONS))}"
        )
    return action


def _validate_address_type(address_type: str) -> str:
    """Validate address type"""
    address_type = address_type.strip().lower()
    if address_type not in VALID_ADDRESS_TYPES:
        raise ValidationError(
            f"address_type must be one of: {', '.join(sorted(VALID_ADDRESS_TYPES))}"
        )
    return address_type


def _validate_subnet(subnet: str) -> str:
    """Validate subnet format (IP/mask or IP mask)"""
    subnet = subnet.strip()
    # FortiGate accepts "x.x.x.x y.y.y.y" (space-separated) or "x.x.x.x/prefix"
    try:
        if "/" in subnet:
            ipaddress.ip_network(subnet, strict=False)
        else:
            # Space-separated IP and mask
            parts = subnet.split()
            if len(parts) == 2:
                ipaddress.ip_address(parts[0])
                ipaddress.ip_address(parts[1])
            else:
                raise ValueError("Invalid subnet format")
    except (ValueError, TypeError) as e:
        raise ValidationError(f"Invalid subnet format '{subnet}': {e}")
    return subnet


def _validate_ip(ip: str, field_name: str = "ip") -> str:
    """Validate an IP address"""
    ip = ip.strip()
    try:
        ipaddress.ip_address(ip)
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid IP address for {field_name}: '{ip}'")
    return ip


def _validate_fqdn(fqdn: str) -> str:
    """Validate FQDN format"""
    fqdn = fqdn.strip()
    # Basic FQDN validation: labels separated by dots
    fqdn_pattern = re.compile(
        r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*\.[A-Za-z]{2,}$"
    )
    if not fqdn_pattern.match(fqdn):
        raise ValidationError(f"Invalid FQDN format: '{fqdn}'")
    return fqdn


def _validate_choice(value: str, valid_options: set, field_name: str) -> str:
    """Validate a value against a set of valid options"""
    value = value.strip().lower()
    if value not in valid_options:
        raise ValidationError(
            f"{field_name} must be one of: {', '.join(sorted(valid_options))}"
        )
    return value


class FortiOSTools:
    """FortiOS tools implementation"""

    @staticmethod
    def create_client(url: str, token: str, vdom: str = "root") -> FortiOSClient:
        """Create FortiOS client instance"""
        return FortiOSClient(url, token, vdom)

    @staticmethod
    def _check_connectivity(url: str, token: str, vdom: str = "root") -> Dict[str, Any]:
        """Check FortiGate connectivity before executing tools"""
        ping_result = FortiOSTools.ping_fortigate(url, token, vdom)
        if not ping_result["success"]:
            return {
                "success": False,
                "message": f"FortiGate not reachable: {ping_result['message']}",
                "details": ping_result["details"],
            }
        return {"success": True, "message": "Connectivity verified"}

    @staticmethod
    def ping_fortigate(url: str, token: str, vdom: str = "root") -> Dict[str, Any]:
        """Ping the FortiGate to check connectivity."""
        try:
            client = FortiOSTools.create_client(url, token, vdom)
            result = client.get("monitor/system/status")
            return {
                "success": result.get("http_status") == 200,
                "message": (
                    "FortiGate is reachable"
                    if result.get("http_status") == 200
                    else "FortiGate is unreachable"
                ),
                "details": result,
            }
        except Exception as e:
            logger.error(f"Error pinging FortiGate: {e}")
            return {
                "success": False,
                "message": f"Error pinging FortiGate: {str(e)}",
                "details": {},
            }

    @staticmethod
    def create_firewall_policy(
        url: str,
        token: str,
        vdom: str,
        name: str,
        srcintf: List[str],
        dstintf: List[str],
        srcaddr: List[str],
        dstaddr: List[str],
        service: List[str],
        action: str,
        status: str = "enable",
        nat: str = "disable",
        logtraffic: str = "utm",
    ) -> Dict[str, Any]:
        """Create a firewall policy in FortiGate"""
        # Check connectivity first
        connectivity = FortiOSTools._check_connectivity(url, token, vdom)
        if not connectivity["success"]:
            return connectivity

        try:
            # Validate inputs
            action = _validate_action(action)
            status = _validate_choice(status, VALID_STATUSES, "status")
            nat = _validate_choice(nat, VALID_NAT_OPTIONS, "nat")
            logtraffic = _validate_choice(
                logtraffic, VALID_LOGTRAFFIC_OPTIONS, "logtraffic"
            )

            client = FortiOSTools.create_client(url, token, vdom)

            policy_data = {
                "name": name,
                "srcintf": [{"name": intf} for intf in srcintf],
                "dstintf": [{"name": intf} for intf in dstintf],
                "srcaddr": [{"name": addr} for addr in srcaddr],
                "dstaddr": [{"name": addr} for addr in dstaddr],
                "service": [{"name": svc} for svc in service],
                "action": action,
                "status": status,
                "schedule": {"q_origin_key": "always"},
                "nat": nat,
                "logtraffic": logtraffic,
            }

            logger.info(f"Creating firewall policy: {name}")
            result = client.post("cmdb/firewall/policy", policy_data)

            return {
                "success": result.get("http_status") == 200,
                "message": f"Firewall policy '{name}' creation attempted",
                "details": result,
            }

        except ValidationError as e:
            return {
                "success": False,
                "message": f"Validation error: {str(e)}",
                "details": {},
            }
        except Exception as e:
            logger.error(f"Error creating firewall policy: {e}")
            return {
                "success": False,
                "message": f"Error creating firewall policy: {str(e)}",
                "details": {},
            }

    @staticmethod
    def create_address(
        url: str,
        token: str,
        vdom: str,
        name: str,
        address_type: str = "ipmask",
        subnet: Optional[str] = None,
        start_ip: Optional[str] = None,
        end_ip: Optional[str] = None,
        fqdn: Optional[str] = None,
        comment: str = "",
        color: int = 0,
    ) -> Dict[str, Any]:
        """Create an address object in FortiGate"""
        # Check connectivity first
        connectivity = FortiOSTools._check_connectivity(url, token, vdom)
        if not connectivity["success"]:
            return connectivity

        try:
            # Validate inputs
            address_type = _validate_address_type(address_type)
            color = _validate_color(color)

            client = FortiOSTools.create_client(url, token, vdom)

            address_data = {
                "name": name,
                "type": address_type,
                "color": color,
            }

            if comment:
                address_data["comment"] = comment

            if address_type == "ipmask":
                if not subnet:
                    return {
                        "success": False,
                        "message": "subnet is required for ipmask type",
                    }
                subnet = _validate_subnet(subnet)
                address_data["subnet"] = subnet
            elif address_type == "iprange":
                if not start_ip or not end_ip:
                    return {
                        "success": False,
                        "message": "start_ip and end_ip are required for iprange type",
                    }
                start_ip = _validate_ip(start_ip, "start_ip")
                end_ip = _validate_ip(end_ip, "end_ip")
                address_data["start-ip"] = start_ip
                address_data["end-ip"] = end_ip
            elif address_type == "fqdn":
                if not fqdn:
                    return {
                        "success": False,
                        "message": "fqdn is required for fqdn type",
                    }
                fqdn = _validate_fqdn(fqdn)
                address_data["fqdn"] = fqdn

            logger.info(f"Creating address object: {name}")
            result = client.post("cmdb/firewall/address", address_data)

            return {
                "success": result.get("http_status") == 200,
                "message": f"Address object '{name}' creation attempted",
                "details": result,
            }

        except ValidationError as e:
            return {
                "success": False,
                "message": f"Validation error: {str(e)}",
                "details": {},
            }
        except Exception as e:
            logger.error(f"Error creating address object: {e}")
            return {
                "success": False,
                "message": f"Error creating address object: {str(e)}",
                "details": {},
            }

    @staticmethod
    def create_address_group(
        url: str,
        token: str,
        vdom: str,
        name: str,
        members: List[str],
        comment: str = "",
        color: int = 0,
    ) -> Dict[str, Any]:
        """Create an address group in FortiGate"""
        # Check connectivity first
        connectivity = FortiOSTools._check_connectivity(url, token, vdom)
        if not connectivity["success"]:
            return connectivity

        try:
            # Validate inputs
            color = _validate_color(color)

            if not members:
                return {
                    "success": False,
                    "message": "At least one member address is required",
                }

            client = FortiOSTools.create_client(url, token, vdom)

            group_data = {
                "name": name,
                "member": [{"name": member} for member in members],
                "color": color,
            }

            if comment:
                group_data["comment"] = comment

            logger.info(f"Creating address group: {name}")
            result = client.post("cmdb/firewall/addrgrp", group_data)

            return {
                "success": result.get("http_status") == 200,
                "message": f"Address group '{name}' creation attempted",
                "details": result,
            }

        except ValidationError as e:
            return {
                "success": False,
                "message": f"Validation error: {str(e)}",
                "details": {},
            }
        except Exception as e:
            logger.error(f"Error creating address group: {e}")
            return {
                "success": False,
                "message": f"Error creating address group: {str(e)}",
                "details": {},
            }

    @staticmethod
    def create_vip(
        url: str,
        token: str,
        vdom: str,
        name: str,
        extip: str,
        mappedip: List[str],
        extintf: str = "any",
        portforward: str = "disable",
        extport: Optional[str] = None,
        mappedport: Optional[str] = None,
        protocol: str = "tcp",
        comment: str = "",
    ) -> Dict[str, Any]:
        """Create a Virtual IP (VIP) object in FortiGate"""
        # Check connectivity first
        connectivity = FortiOSTools._check_connectivity(url, token, vdom)
        if not connectivity["success"]:
            return connectivity

        try:
            # Validate inputs
            portforward = _validate_choice(
                portforward, VALID_PORTFORWARD_OPTIONS, "portforward"
            )
            protocol = _validate_choice(protocol, VALID_PROTOCOLS, "protocol")
            _validate_ip(extip, "extip")
            for ip in mappedip:
                _validate_ip(ip, "mappedip")

            client = FortiOSTools.create_client(url, token, vdom)

            vip_data = {
                "name": name,
                "extip": extip,
                "mappedip": [{"range": ip} for ip in mappedip],
                "extintf": {"q_origin_key": extintf},
                "portforward": portforward,
            }

            if portforward == "enable" and extport and mappedport:
                vip_data["extport"] = extport
                vip_data["mappedport"] = mappedport
                vip_data["protocol"] = protocol

            if comment:
                vip_data["comment"] = comment

            logger.info(f"Creating VIP object: {name}")
            result = client.post("cmdb/firewall/vip", vip_data)

            return {
                "success": result.get("http_status") == 200,
                "message": f"VIP object '{name}' creation attempted",
                "details": result,
            }

        except ValidationError as e:
            return {
                "success": False,
                "message": f"Validation error: {str(e)}",
                "details": {},
            }
        except Exception as e:
            logger.error(f"Error creating VIP object: {e}")
            return {
                "success": False,
                "message": f"Error creating VIP object: {str(e)}",
                "details": {},
            }

    @staticmethod
    def get_firewall_policies(
        url: str, token: str, vdom: str, policy_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get firewall policies from FortiGate"""
        # Check connectivity first
        connectivity = FortiOSTools._check_connectivity(url, token, vdom)
        if not connectivity["success"]:
            return connectivity

        try:
            client = FortiOSTools.create_client(url, token, vdom)

            if policy_id:
                safe_id = _validate_resource_name(policy_id, "policy_id")
                endpoint = f"cmdb/firewall/policy/{safe_id}"
                logger.info(f"Getting firewall policy: {policy_id}")
            else:
                endpoint = "cmdb/firewall/policy"
                logger.info("Getting all firewall policies")

            result = client.get(endpoint)

            return {
                "success": result.get("http_status") == 200,
                "message": "Firewall policies retrieved",
                "data": (
                    result.get("results", [])
                    if result.get("http_status") == 200
                    else []
                ),
                "details": result,
            }

        except ValidationError as e:
            return {
                "success": False,
                "message": f"Validation error: {str(e)}",
                "data": [],
                "details": {},
            }
        except Exception as e:
            logger.error(f"Error getting firewall policies: {e}")
            return {
                "success": False,
                "message": f"Error getting firewall policies: {str(e)}",
                "data": [],
                "details": {},
            }

    @staticmethod
    def get_addresses(
        url: str, token: str, vdom: str, address_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get address objects from FortiGate"""
        # Check connectivity first
        connectivity = FortiOSTools._check_connectivity(url, token, vdom)
        if not connectivity["success"]:
            return connectivity

        try:
            client = FortiOSTools.create_client(url, token, vdom)

            if address_name:
                safe_name = _validate_resource_name(address_name, "address_name")
                endpoint = f"cmdb/firewall/address/{safe_name}"
                logger.info(f"Getting address object: {address_name}")
            else:
                endpoint = "cmdb/firewall/address"
                logger.info("Getting all address objects")

            result = client.get(endpoint)

            return {
                "success": result.get("http_status") == 200,
                "message": "Address objects retrieved",
                "data": (
                    result.get("results", [])
                    if result.get("http_status") == 200
                    else []
                ),
                "details": result,
            }

        except ValidationError as e:
            return {
                "success": False,
                "message": f"Validation error: {str(e)}",
                "data": [],
                "details": {},
            }
        except Exception as e:
            logger.error(f"Error getting address objects: {e}")
            return {
                "success": False,
                "message": f"Error getting address objects: {str(e)}",
                "data": [],
                "details": {},
            }

    @staticmethod
    def get_address_groups(
        url: str, token: str, vdom: str, group_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get address groups from FortiGate"""
        # Check connectivity first
        connectivity = FortiOSTools._check_connectivity(url, token, vdom)
        if not connectivity["success"]:
            return connectivity

        try:
            client = FortiOSTools.create_client(url, token, vdom)

            if group_name:
                safe_name = _validate_resource_name(group_name, "group_name")
                endpoint = f"cmdb/firewall/addrgrp/{safe_name}"
                logger.info(f"Getting address group: {group_name}")
            else:
                endpoint = "cmdb/firewall/addrgrp"
                logger.info("Getting all address groups")

            result = client.get(endpoint)

            return {
                "success": result.get("http_status") == 200,
                "message": "Address groups retrieved",
                "data": (
                    result.get("results", [])
                    if result.get("http_status") == 200
                    else []
                ),
                "details": result,
            }

        except ValidationError as e:
            return {
                "success": False,
                "message": f"Validation error: {str(e)}",
                "data": [],
                "details": {},
            }
        except Exception as e:
            logger.error(f"Error getting address groups: {e}")
            return {
                "success": False,
                "message": f"Error getting address groups: {str(e)}",
                "data": [],
                "details": {},
            }

    @staticmethod
    def get_vips(
        url: str, token: str, vdom: str, vip_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get VIP objects from FortiGate"""
        # Check connectivity first
        connectivity = FortiOSTools._check_connectivity(url, token, vdom)
        if not connectivity["success"]:
            return connectivity

        try:
            client = FortiOSTools.create_client(url, token, vdom)

            if vip_name:
                safe_name = _validate_resource_name(vip_name, "vip_name")
                endpoint = f"cmdb/firewall/vip/{safe_name}"
                logger.info(f"Getting VIP object: {vip_name}")
            else:
                endpoint = "cmdb/firewall/vip"
                logger.info("Getting all VIP objects")

            result = client.get(endpoint)

            return {
                "success": result.get("http_status") == 200,
                "message": "VIP objects retrieved",
                "data": (
                    result.get("results", [])
                    if result.get("http_status") == 200
                    else []
                ),
                "details": result,
            }

        except ValidationError as e:
            return {
                "success": False,
                "message": f"Validation error: {str(e)}",
                "data": [],
                "details": {},
            }
        except Exception as e:
            logger.error(f"Error getting VIP objects: {e}")
            return {
                "success": False,
                "message": f"Error getting VIP objects: {str(e)}",
                "data": [],
                "details": {},
            }

    @staticmethod
    def delete_address(url: str, token: str, vdom: str, name: str) -> Dict[str, Any]:
        """Delete an address object from FortiGate"""
        # Check connectivity first
        connectivity = FortiOSTools._check_connectivity(url, token, vdom)
        if not connectivity["success"]:
            return connectivity

        try:
            safe_name = _validate_resource_name(name, "name")
            client = FortiOSTools.create_client(url, token, vdom)

            logger.info(f"Deleting address object: {name}")
            result = client.delete(f"cmdb/firewall/address/{safe_name}")

            return {
                "success": result.get("http_status") == 200,
                "message": f"Address object '{name}' deletion attempted",
                "details": result,
            }

        except ValidationError as e:
            return {
                "success": False,
                "message": f"Validation error: {str(e)}",
                "details": {},
            }
        except Exception as e:
            logger.error(f"Error deleting address object: {e}")
            return {
                "success": False,
                "message": f"Error deleting address object: {str(e)}",
                "details": {},
            }

    @staticmethod
    def delete_address_group(
        url: str, token: str, vdom: str, name: str
    ) -> Dict[str, Any]:
        """Delete an address group from FortiGate"""
        # Check connectivity first
        connectivity = FortiOSTools._check_connectivity(url, token, vdom)
        if not connectivity["success"]:
            return connectivity

        try:
            safe_name = _validate_resource_name(name, "name")
            client = FortiOSTools.create_client(url, token, vdom)

            logger.info(f"Deleting address group: {name}")
            result = client.delete(f"cmdb/firewall/addrgrp/{safe_name}")

            return {
                "success": result.get("http_status") == 200,
                "message": f"Address group '{name}' deletion attempted",
                "details": result,
            }

        except ValidationError as e:
            return {
                "success": False,
                "message": f"Validation error: {str(e)}",
                "details": {},
            }
        except Exception as e:
            logger.error(f"Error deleting address group: {e}")
            return {
                "success": False,
                "message": f"Error deleting address group: {str(e)}",
                "details": {},
            }
