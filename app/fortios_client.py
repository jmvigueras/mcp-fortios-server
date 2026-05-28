"""
FortiOS API Client for MCP Server
"""

import json
import logging
import time
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)

# Default retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BACKOFF = 1.0  # seconds


class FortiOSClient:
    """FortiOS API client for MCP server"""

    def __init__(
        self,
        url: str,
        token: str,
        vdom: str = "root",
        verify_ssl: bool = False,
        timeout: int = 10,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_backoff: float = DEFAULT_RETRY_BACKOFF,
    ):
        """
        Initialize FortiOS API client

        Args:
            url: FortiGate URL (e.g., https://192.168.1.99)
            token: API access token
            vdom: Virtual domain (default: root)
            verify_ssl: Whether to verify SSL certificates
            timeout: Request timeout in seconds (default: 10)
            max_retries: Maximum number of retries for transient failures
            retry_backoff: Base backoff time in seconds between retries
        """
        self.url = url.rstrip("/")
        self.token = token
        self.vdom = vdom
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
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
        Make HTTP request to FortiOS API with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (should not start with /)
            data: Request data for POST/PUT

        Returns:
            API response as dictionary
        """
        # Use explicit string formatting instead of urljoin to avoid path issues
        url = f"{self.url}/api/v2/{endpoint}"

        # Add vdom parameter
        params = {"vdom": self.vdom}

        last_exception = None
        for attempt in range(self.max_retries):
            try:
                if method.upper() == "GET":
                    response = self.session.get(
                        url, params=params, verify=self.verify_ssl, timeout=self.timeout
                    )
                elif method.upper() == "POST":
                    response = self.session.post(
                        url,
                        params=params,
                        json=data,
                        verify=self.verify_ssl,
                        timeout=self.timeout,
                    )
                elif method.upper() == "PUT":
                    response = self.session.put(
                        url,
                        params=params,
                        json=data,
                        verify=self.verify_ssl,
                        timeout=self.timeout,
                    )
                elif method.upper() == "DELETE":
                    response = self.session.delete(
                        url, params=params, verify=self.verify_ssl, timeout=self.timeout
                    )
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # Log request details (endpoint only, not full URL with host)
                logger.info(
                    f"{method.upper()} {endpoint} - Status: {response.status_code}"
                )

                # Try to parse JSON response
                try:
                    result = response.json()
                except json.JSONDecodeError:
                    result = {
                        "status": "error",
                        "message": "Invalid JSON response",
                        "raw_response": response.text[:500],
                    }

                # Add HTTP status code to result
                result["http_status"] = response.status_code

                return result

            except requests.exceptions.ConnectionError as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_backoff * (2**attempt)
                    logger.warning(
                        f"Connection error on attempt {attempt + 1}/{self.max_retries}, "
                        f"retrying in {wait_time}s: {e}"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"Connection failed after {self.max_retries} attempts: {e}"
                    )

            except requests.exceptions.Timeout as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_backoff * (2**attempt)
                    logger.warning(
                        f"Timeout on attempt {attempt + 1}/{self.max_retries}, "
                        f"retrying in {wait_time}s: {e}"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"Request timed out after {self.max_retries} attempts: {e}"
                    )

            except requests.exceptions.RequestException as e:
                # Non-retryable request errors
                logger.error(f"Request failed: {e}")
                return {
                    "status": "error",
                    "message": f"Request failed: {str(e)}",
                    "http_status": 0,
                }

        # All retries exhausted
        return {
            "status": "error",
            "message": f"Request failed after {self.max_retries} attempts: {str(last_exception)}",
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
