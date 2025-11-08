"""
FortiOS API Client for MCP Server
"""

import json
import logging
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests

logger = logging.getLogger(__name__)


class FortiOSClient:
    """FortiOS API client for MCP server"""

    def __init__(
        self, url: str, token: str, vdom: str = "root", verify_ssl: bool = False, timeout: int = 10
    ):
        """
        Initialize FortiOS API client

        Args:
            url: FortiGate URL (e.g., https://192.168.1.99)
            token: API access token
            vdom: Virtual domain (default: root)
            verify_ssl: Whether to verify SSL certificates
            timeout: Request timeout in seconds (default: 10)
        """
        self.url = url.rstrip("/")
        self.token = token
        self.vdom = vdom
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.session = requests.Session()

        # Set headers
        self.session.headers.update(
            {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        )

        # Disable SSL warnings if not verifying
        if not verify_ssl:
            import urllib3

            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _make_request(
        self, method: str, endpoint: str, data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to FortiOS API

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Request data for POST/PUT

        Returns:
            API response as dictionary
        """
        url = urljoin(f"{self.url}/api/v2/", endpoint)

        # Add vdom parameter
        params = {"vdom": self.vdom}

        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params, verify=self.verify_ssl, timeout=self.timeout)
            elif method.upper() == "POST":
                response = self.session.post(
                    url, params=params, json=data, verify=self.verify_ssl, timeout=self.timeout
                )
            elif method.upper() == "PUT":
                response = self.session.put(
                    url, params=params, json=data, verify=self.verify_ssl, timeout=self.timeout
                )
            elif method.upper() == "DELETE":
                response = self.session.delete(
                    url, params=params, verify=self.verify_ssl, timeout=self.timeout
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Log request details
            logger.info(f"{method.upper()} {url} - Status: {response.status_code}")

            # Try to parse JSON response
            try:
                result = response.json()
            except json.JSONDecodeError:
                result = {
                    "status": "error",
                    "message": "Invalid JSON response",
                    "raw_response": response.text,
                }

            # Add HTTP status code to result
            result["http_status"] = response.status_code

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return {
                "status": "error",
                "message": f"Request failed: {str(e)}",
                "http_status": 0,
            }

    def get(self, endpoint: str) -> Dict[str, Any]:
        """GET request"""
        return self._make_request("GET", endpoint)

    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """POST request"""
        return self._make_request("POST", endpoint, data)

    def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """PUT request"""
        return self._make_request("PUT", endpoint, data)

    def delete(self, endpoint: str) -> Dict[str, Any]:
        """DELETE request"""
        return self._make_request("DELETE", endpoint)
