"""
FortiOS Tools Implementation for MCP Server
"""

import logging
from typing import Any, Dict, List, Optional

from .fortios_client import FortiOSClient

logger = logging.getLogger(__name__)


class FortiOSTools:
    """FortiOS tools implementation"""

    @staticmethod
    def create_client(url: str, token: str, vdom: str = "root") -> FortiOSClient:
        """Create FortiOS client instance"""
        return FortiOSClient(url, token, vdom)

    @staticmethod
    def ping_fortigate(url: str, token: str, vdom: str = "root") -> Dict[str, Any]:
        """Ping the FortiGate to check connectivity."""
        try:
            client = FortiOSTools.create_client(url, token, vdom)
            result = client.get("monitor/system/ping")
            return {
                "success": result.get("http_status") == 200,
                "message": (
                    "Ping successful"
                    if result.get("http_status") == 200
                    else "Ping failed"
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
        try:
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
        try:
            client = FortiOSTools.create_client(url, token, vdom)

            address_data = {"name": name, "color": str(color)}

            if comment:
                address_data["comment"] = comment

            if address_type == "ipmask":
                if not subnet:
                    return {
                        "success": False,
                        "message": "subnet is required for ipmask type",
                    }
                address_data["subnet"] = subnet
            elif address_type == "iprange":
                if not start_ip or not end_ip:
                    return {
                        "success": False,
                        "message": "start_ip and end_ip are required for iprange type",
                    }
                address_data["start-ip"] = start_ip
                address_data["end-ip"] = end_ip
            elif address_type == "fqdn":
                if not fqdn:
                    return {
                        "success": False,
                        "message": "fqdn is required for fqdn type",
                    }
                address_data["fqdn"] = fqdn
            else:
                return {
                    "success": False,
                    "message": f"Unsupported address type: {address_type}",
                }

            logger.info(f"Creating address object: {name}")
            result = client.post("cmdb/firewall/address", address_data)

            return {
                "success": result.get("http_status") == 200,
                "message": f"Address object '{name}' creation attempted",
                "details": result,
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
        try:
            client = FortiOSTools.create_client(url, token, vdom)

            if not members:
                return {
                    "success": False,
                    "message": "At least one member address is required",
                }

            group_data = {
                "name": name,
                "member": [{"name": member} for member in members],
                "color": str(color),
            }

            if comment:
                group_data["comment"] = comment

            logger.info(f"Creating address group: {name} with members: {members}")
            result = client.post("cmdb/firewall/addrgrp", group_data)

            return {
                "success": result.get("http_status") == 200,
                "message": f"Address group '{name}' creation attempted",
                "details": result,
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
        try:
            client = FortiOSTools.create_client(url, token, vdom)

            vip_data = {
                "name": name,
                "extip": extip,
                "mappedip": [{"range": ip} for ip in mappedip],
                "extintf": {"q_origin_key": extintf},
                "portforward": portforward,
            }

            if extport and mappedport:
                vip_data["extport"] = extport
                vip_data["mappedport"] = mappedport

            if comment:
                vip_data["comment"] = comment

            logger.info(f"Creating VIP object: {name}")
            result = client.post("cmdb/firewall/vip", vip_data)

            return {
                "success": result.get("http_status") == 200,
                "message": f"VIP object '{name}' creation attempted",
                "details": result,
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
        try:
            client = FortiOSTools.create_client(url, token, vdom)

            if policy_id:
                endpoint = f"cmdb/firewall/policy/{policy_id}"
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
        try:
            client = FortiOSTools.create_client(url, token, vdom)

            if address_name:
                endpoint = f"cmdb/firewall/address/{address_name}"
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
        try:
            client = FortiOSTools.create_client(url, token, vdom)

            if group_name:
                endpoint = f"cmdb/firewall/addrgrp/{group_name}"
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
        try:
            client = FortiOSTools.create_client(url, token, vdom)

            if vip_name:
                endpoint = f"cmdb/firewall/vip/{vip_name}"
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
        try:
            client = FortiOSTools.create_client(url, token, vdom)

            logger.info(f"Deleting address object: {name}")
            result = client.delete(f"cmdb/firewall/address/{name}")

            return {
                "success": result.get("http_status") == 200,
                "message": f"Address object '{name}' deletion attempted",
                "details": result,
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
        try:
            client = FortiOSTools.create_client(url, token, vdom)

            logger.info(f"Deleting address group: {name}")
            result = client.delete(f"cmdb/firewall/addrgrp/{name}")

            return {
                "success": result.get("http_status") == 200,
                "message": f"Address group '{name}' deletion attempted",
                "details": result,
            }

        except Exception as e:
            logger.error(f"Error deleting address group: {e}")
            return {
                "success": False,
                "message": f"Error deleting address group: {str(e)}",
                "details": {},
            }
