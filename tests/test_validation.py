"""
Tests for input validation, path traversal protection, retry logic,
and health endpoint functionality.
"""

import json
import time
from unittest.mock import Mock, patch, MagicMock

import pytest
import requests

from app.tools import (
    FortiOSTools,
    ValidationError,
    _validate_resource_name,
    _validate_color,
    _validate_action,
    _validate_address_type,
    _validate_subnet,
    _validate_ip,
    _validate_fqdn,
    _validate_choice,
    VALID_ACTIONS,
    VALID_ADDRESS_TYPES,
    VALID_STATUSES,
    VALID_NAT_OPTIONS,
    VALID_LOGTRAFFIC_OPTIONS,
    VALID_PORTFORWARD_OPTIONS,
    VALID_PROTOCOLS,
)
from app.fortios_client import FortiOSClient


def _mock_connectivity_ok():
    """Helper: patch _check_connectivity to always pass"""
    return patch.object(
        FortiOSTools, "_check_connectivity",
        return_value={"success": True, "message": "Connectivity verified"},
    )


# ===============================
# PATH TRAVERSAL PROTECTION TESTS
# ===============================


class TestPathTraversalProtection:
    """Verify that path traversal attempts are blocked"""

    def test_blocks_dot_dot_slash(self):
        """Block ../../ path traversal"""
        with pytest.raises(ValidationError, match="path traversal"):
            _validate_resource_name("../../monitor/system/admin")

    def test_blocks_forward_slash(self):
        """Block forward slashes in resource names"""
        with pytest.raises(ValidationError, match="path traversal"):
            _validate_resource_name("foo/bar")

    def test_blocks_backslash(self):
        """Block backslashes in resource names"""
        with pytest.raises(ValidationError, match="path traversal"):
            _validate_resource_name("foo\\bar")

    def test_blocks_dot_dot_only(self):
        """Block bare .. traversal"""
        with pytest.raises(ValidationError, match="path traversal"):
            _validate_resource_name("..")

    def test_blocks_empty_name(self):
        """Block empty resource names"""
        with pytest.raises(ValidationError, match="cannot be empty"):
            _validate_resource_name("")

    def test_blocks_whitespace_only(self):
        """Block whitespace-only resource names"""
        with pytest.raises(ValidationError, match="cannot be empty"):
            _validate_resource_name("   ")

    def test_allows_normal_names(self):
        """Allow normal FortiGate resource names"""
        # These should all pass without raising
        assert _validate_resource_name("my-policy") == "my-policy"
        assert _validate_resource_name("address_group_1") == "address_group_1"
        assert _validate_resource_name("Web Server") == "Web%20Server"
        assert _validate_resource_name("10.0.0.0") == "10.0.0.0"

    def test_url_encodes_special_chars(self):
        """Ensure special characters are URL-encoded"""
        result = _validate_resource_name("name with spaces")
        assert "%20" in result
        assert "/" not in result

    def test_get_policies_blocks_traversal(self):
        """get_firewall_policies blocks path traversal in policy_id"""
        with _mock_connectivity_ok():
            mock_client = Mock()
            with patch.object(FortiOSTools, "create_client", return_value=mock_client):
                result = FortiOSTools.get_firewall_policies(
                    "https://test.com", "token", "root", "../../monitor/system/admin"
                )
        assert result["success"] is False
        assert "Validation error" in result["message"]

    def test_get_addresses_blocks_traversal(self):
        """get_addresses blocks path traversal in address_name"""
        with _mock_connectivity_ok():
            mock_client = Mock()
            with patch.object(FortiOSTools, "create_client", return_value=mock_client):
                result = FortiOSTools.get_addresses(
                    "https://test.com", "token", "root", "../secret/endpoint"
                )
        assert result["success"] is False
        assert "Validation error" in result["message"]

    def test_get_address_groups_blocks_traversal(self):
        """get_address_groups blocks path traversal in group_name"""
        with _mock_connectivity_ok():
            mock_client = Mock()
            with patch.object(FortiOSTools, "create_client", return_value=mock_client):
                result = FortiOSTools.get_address_groups(
                    "https://test.com", "token", "root", "../../admin"
                )
        assert result["success"] is False
        assert "Validation error" in result["message"]

    def test_get_vips_blocks_traversal(self):
        """get_vips blocks path traversal in vip_name"""
        with _mock_connectivity_ok():
            mock_client = Mock()
            with patch.object(FortiOSTools, "create_client", return_value=mock_client):
                result = FortiOSTools.get_vips(
                    "https://test.com", "token", "root", "../../system/config"
                )
        assert result["success"] is False
        assert "Validation error" in result["message"]

    def test_delete_address_blocks_traversal(self):
        """delete_address blocks path traversal"""
        with _mock_connectivity_ok():
            mock_client = Mock()
            with patch.object(FortiOSTools, "create_client", return_value=mock_client):
                result = FortiOSTools.delete_address(
                    "https://test.com", "token", "root", "../../../etc/passwd"
                )
        assert result["success"] is False
        assert "Validation error" in result["message"]

    def test_delete_address_group_blocks_traversal(self):
        """delete_address_group blocks path traversal"""
        with _mock_connectivity_ok():
            mock_client = Mock()
            with patch.object(FortiOSTools, "create_client", return_value=mock_client):
                result = FortiOSTools.delete_address_group(
                    "https://test.com", "token", "root", "../../admin/settings"
                )
        assert result["success"] is False
        assert "Validation error" in result["message"]


# ===============================
# INPUT VALIDATION TESTS
# ===============================


class TestColorValidation:
    """Test color value validation"""

    def test_valid_colors(self):
        assert _validate_color(0) == 0
        assert _validate_color(16) == 16
        assert _validate_color(32) == 32

    def test_invalid_color_too_high(self):
        with pytest.raises(ValidationError, match="color must be"):
            _validate_color(33)

    def test_invalid_color_negative(self):
        with pytest.raises(ValidationError, match="color must be"):
            _validate_color(-1)


class TestActionValidation:
    """Test firewall policy action validation"""

    def test_valid_actions(self):
        assert _validate_action("accept") == "accept"
        assert _validate_action("deny") == "deny"
        assert _validate_action("ACCEPT") == "accept"  # case-insensitive
        assert _validate_action(" deny ") == "deny"  # strips whitespace

    def test_invalid_action(self):
        with pytest.raises(ValidationError, match="action must be one of"):
            _validate_action("allow")

    def test_invalid_action_drop(self):
        with pytest.raises(ValidationError, match="action must be one of"):
            _validate_action("drop")


class TestAddressTypeValidation:
    """Test address type validation"""

    def test_valid_types(self):
        assert _validate_address_type("ipmask") == "ipmask"
        assert _validate_address_type("iprange") == "iprange"
        assert _validate_address_type("fqdn") == "fqdn"
        assert _validate_address_type("IPMASK") == "ipmask"

    def test_invalid_type(self):
        with pytest.raises(ValidationError, match="address_type must be one of"):
            _validate_address_type("wildcard")


class TestSubnetValidation:
    """Test subnet format validation"""

    def test_valid_cidr(self):
        assert _validate_subnet("192.168.1.0/24") == "192.168.1.0/24"
        assert _validate_subnet("10.0.0.0/8") == "10.0.0.0/8"

    def test_valid_space_separated(self):
        assert _validate_subnet("192.168.1.0 255.255.255.0") == "192.168.1.0 255.255.255.0"

    def test_invalid_subnet(self):
        with pytest.raises(ValidationError, match="Invalid subnet format"):
            _validate_subnet("not-a-subnet")

    def test_invalid_cidr_prefix(self):
        with pytest.raises(ValidationError, match="Invalid subnet format"):
            _validate_subnet("192.168.1.0/99")


class TestIPValidation:
    """Test IP address validation"""

    def test_valid_ipv4(self):
        assert _validate_ip("192.168.1.1") == "192.168.1.1"
        assert _validate_ip("10.0.0.1") == "10.0.0.1"
        assert _validate_ip("255.255.255.255") == "255.255.255.255"

    def test_valid_ipv6(self):
        assert _validate_ip("::1") == "::1"
        assert _validate_ip("fe80::1") == "fe80::1"

    def test_invalid_ip(self):
        with pytest.raises(ValidationError, match="Invalid IP address"):
            _validate_ip("999.999.999.999")

    def test_invalid_ip_string(self):
        with pytest.raises(ValidationError, match="Invalid IP address"):
            _validate_ip("not-an-ip")


class TestFQDNValidation:
    """Test FQDN format validation"""

    def test_valid_fqdns(self):
        assert _validate_fqdn("example.com") == "example.com"
        assert _validate_fqdn("sub.domain.example.com") == "sub.domain.example.com"
        assert _validate_fqdn("my-server.internal.net") == "my-server.internal.net"

    def test_invalid_fqdn_no_tld(self):
        with pytest.raises(ValidationError, match="Invalid FQDN"):
            _validate_fqdn("localhost")

    def test_invalid_fqdn_starts_with_dash(self):
        with pytest.raises(ValidationError, match="Invalid FQDN"):
            _validate_fqdn("-invalid.com")

    def test_invalid_fqdn_special_chars(self):
        with pytest.raises(ValidationError, match="Invalid FQDN"):
            _validate_fqdn("invalid!name.com")


class TestChoiceValidation:
    """Test generic choice validation"""

    def test_valid_choice(self):
        assert _validate_choice("enable", VALID_STATUSES, "status") == "enable"
        assert _validate_choice("DISABLE", VALID_STATUSES, "status") == "disable"

    def test_invalid_choice(self):
        with pytest.raises(ValidationError, match="status must be one of"):
            _validate_choice("maybe", VALID_STATUSES, "status")


# ===============================
# TOOL-LEVEL VALIDATION TESTS
# ===============================


class TestCreateFirewallPolicyValidation:
    """Test validation in create_firewall_policy"""

    def test_invalid_action_rejected(self):
        """Invalid action returns validation error without calling API"""
        with _mock_connectivity_ok():
            result = FortiOSTools.create_firewall_policy(
                "https://test.com", "token", "root",
                "test-policy", ["port1"], ["port2"],
                ["all"], ["all"], ["ALL"],
                "allow",  # invalid - should be accept or deny
            )
        assert result["success"] is False
        assert "Validation error" in result["message"]

    def test_invalid_status_rejected(self):
        with _mock_connectivity_ok():
            result = FortiOSTools.create_firewall_policy(
                "https://test.com", "token", "root",
                "test-policy", ["port1"], ["port2"],
                ["all"], ["all"], ["ALL"],
                "accept",
                status="active",  # invalid
            )
        assert result["success"] is False
        assert "Validation error" in result["message"]

    def test_invalid_nat_rejected(self):
        with _mock_connectivity_ok():
            result = FortiOSTools.create_firewall_policy(
                "https://test.com", "token", "root",
                "test-policy", ["port1"], ["port2"],
                ["all"], ["all"], ["ALL"],
                "accept",
                nat="yes",  # invalid
            )
        assert result["success"] is False
        assert "Validation error" in result["message"]

    def test_invalid_logtraffic_rejected(self):
        with _mock_connectivity_ok():
            result = FortiOSTools.create_firewall_policy(
                "https://test.com", "token", "root",
                "test-policy", ["port1"], ["port2"],
                ["all"], ["all"], ["ALL"],
                "accept",
                logtraffic="verbose",  # invalid
            )
        assert result["success"] is False
        assert "Validation error" in result["message"]

    def test_valid_policy_calls_api(self):
        """Valid inputs should proceed to API call"""
        with _mock_connectivity_ok():
            mock_client = Mock()
            mock_client.post.return_value = {"http_status": 200}
            with patch.object(FortiOSTools, "create_client", return_value=mock_client):
                result = FortiOSTools.create_firewall_policy(
                    "https://test.com", "token", "root",
                    "test-policy", ["port1"], ["port2"],
                    ["all"], ["all"], ["ALL"],
                    "accept",
                )
        assert result["success"] is True
        mock_client.post.assert_called_once()


class TestCreateAddressValidation:
    """Test validation in create_address"""

    def test_invalid_address_type_rejected(self):
        with _mock_connectivity_ok():
            result = FortiOSTools.create_address(
                "https://test.com", "token", "root",
                "test-addr", "wildcard",  # invalid type
            )
        assert result["success"] is False
        assert "Validation error" in result["message"]

    def test_invalid_color_rejected(self):
        with _mock_connectivity_ok():
            result = FortiOSTools.create_address(
                "https://test.com", "token", "root",
                "test-addr", "ipmask",
                subnet="192.168.1.0/24",
                color=99,  # invalid
            )
        assert result["success"] is False
        assert "Validation error" in result["message"]

    def test_invalid_subnet_rejected(self):
        with _mock_connectivity_ok():
            result = FortiOSTools.create_address(
                "https://test.com", "token", "root",
                "test-addr", "ipmask",
                subnet="not-a-subnet",
            )
        assert result["success"] is False
        assert "Validation error" in result["message"]

    def test_invalid_ip_range_rejected(self):
        with _mock_connectivity_ok():
            result = FortiOSTools.create_address(
                "https://test.com", "token", "root",
                "test-addr", "iprange",
                start_ip="not-an-ip",
                end_ip="192.168.1.100",
            )
        assert result["success"] is False
        assert "Validation error" in result["message"]

    def test_invalid_fqdn_rejected(self):
        with _mock_connectivity_ok():
            result = FortiOSTools.create_address(
                "https://test.com", "token", "root",
                "test-addr", "fqdn",
                fqdn="not a valid fqdn!",
            )
        assert result["success"] is False
        assert "Validation error" in result["message"]

    def test_valid_ipmask_includes_type_field(self):
        """Verify the POST body includes the 'type' field"""
        with _mock_connectivity_ok():
            mock_client = Mock()
            mock_client.post.return_value = {"http_status": 200}
            with patch.object(FortiOSTools, "create_client", return_value=mock_client):
                FortiOSTools.create_address(
                    "https://test.com", "token", "root",
                    "test-addr", "ipmask",
                    subnet="192.168.1.0/24",
                )
            call_args = mock_client.post.call_args
            post_data = call_args[0][1]
            assert post_data["type"] == "ipmask"

    def test_color_sent_as_integer(self):
        """Verify color is sent as integer, not string"""
        with _mock_connectivity_ok():
            mock_client = Mock()
            mock_client.post.return_value = {"http_status": 200}
            with patch.object(FortiOSTools, "create_client", return_value=mock_client):
                FortiOSTools.create_address(
                    "https://test.com", "token", "root",
                    "test-addr", "ipmask",
                    subnet="192.168.1.0/24",
                    color=5,
                )
            call_args = mock_client.post.call_args
            post_data = call_args[0][1]
            assert post_data["color"] == 5
            assert isinstance(post_data["color"], int)


class TestCreateVIPValidation:
    """Test validation in create_vip"""

    def test_invalid_extip_rejected(self):
        with _mock_connectivity_ok():
            result = FortiOSTools.create_vip(
                "https://test.com", "token", "root",
                "test-vip", "not-an-ip", ["192.168.1.1"],
            )
        assert result["success"] is False
        assert "Validation error" in result["message"]

    def test_invalid_mappedip_rejected(self):
        with _mock_connectivity_ok():
            result = FortiOSTools.create_vip(
                "https://test.com", "token", "root",
                "test-vip", "10.0.0.1", ["bad-ip"],
            )
        assert result["success"] is False
        assert "Validation error" in result["message"]

    def test_invalid_portforward_rejected(self):
        with _mock_connectivity_ok():
            result = FortiOSTools.create_vip(
                "https://test.com", "token", "root",
                "test-vip", "10.0.0.1", ["192.168.1.1"],
                portforward="yes",  # invalid
            )
        assert result["success"] is False
        assert "Validation error" in result["message"]

    def test_invalid_protocol_rejected(self):
        with _mock_connectivity_ok():
            result = FortiOSTools.create_vip(
                "https://test.com", "token", "root",
                "test-vip", "10.0.0.1", ["192.168.1.1"],
                protocol="icmp",  # invalid
            )
        assert result["success"] is False
        assert "Validation error" in result["message"]


# ===============================
# RETRY LOGIC TESTS
# ===============================


class TestRetryLogic:
    """Test the retry mechanism in FortiOSClient"""

    def test_retries_on_connection_error(self):
        """Client retries on ConnectionError"""
        client = FortiOSClient(
            "https://test.com", "token", "root",
            max_retries=3, retry_backoff=0.01,  # fast backoff for tests
        )

        with patch.object(client.session, "get") as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("refused")
            result = client.get("cmdb/firewall/policy")

        assert result["status"] == "error"
        assert result["http_status"] == 0
        assert "3 attempts" in result["message"]
        assert mock_get.call_count == 3

    def test_retries_on_timeout(self):
        """Client retries on Timeout"""
        client = FortiOSClient(
            "https://test.com", "token", "root",
            max_retries=2, retry_backoff=0.01,
        )

        with patch.object(client.session, "get") as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("timed out")
            result = client.get("cmdb/firewall/policy")

        assert result["status"] == "error"
        assert result["http_status"] == 0
        assert mock_get.call_count == 2

    def test_no_retry_on_other_request_errors(self):
        """Client does NOT retry on non-transient errors"""
        client = FortiOSClient(
            "https://test.com", "token", "root",
            max_retries=3, retry_backoff=0.01,
        )

        with patch.object(client.session, "get") as mock_get:
            mock_get.side_effect = requests.exceptions.InvalidURL("bad url")
            result = client.get("cmdb/firewall/policy")

        assert result["status"] == "error"
        assert mock_get.call_count == 1  # No retry

    def test_succeeds_after_transient_failure(self):
        """Client succeeds if a retry works"""
        client = FortiOSClient(
            "https://test.com", "token", "root",
            max_retries=3, retry_backoff=0.01,
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}

        with patch.object(client.session, "get") as mock_get:
            mock_get.side_effect = [
                requests.exceptions.ConnectionError("refused"),
                mock_response,
            ]
            result = client.get("cmdb/firewall/policy")

        assert result["http_status"] == 200
        assert mock_get.call_count == 2


# ===============================
# URL CONSTRUCTION TESTS
# ===============================


class TestURLConstruction:
    """Test that URLs are constructed correctly (no urljoin issues)"""

    def test_url_format(self):
        """Verify URL is built with explicit string formatting"""
        client = FortiOSClient("https://192.168.1.99", "token", "root")

        with patch.object(client.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {}
            mock_get.return_value = mock_response

            client.get("cmdb/firewall/policy")

            called_url = mock_get.call_args[0][0]
            assert called_url == "https://192.168.1.99/api/v2/cmdb/firewall/policy"

    def test_url_trailing_slash_stripped(self):
        """Trailing slash on base URL is handled"""
        client = FortiOSClient("https://192.168.1.99/", "token", "root")

        with patch.object(client.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {}
            mock_get.return_value = mock_response

            client.get("cmdb/firewall/policy")

            called_url = mock_get.call_args[0][0]
            assert called_url == "https://192.168.1.99/api/v2/cmdb/firewall/policy"
            assert "//" not in called_url.replace("https://", "")


# ===============================
# HEALTH ENDPOINT TESTS
# ===============================


class TestHealthEndpoint:
    """Test the /health endpoint"""

    @pytest.fixture
    def test_client(self):
        """Create a Starlette test client"""
        from starlette.testclient import TestClient
        from app.server import app
        return TestClient(app)

    def test_health_returns_200(self, test_client):
        """Health endpoint returns 200 OK"""
        response = test_client.get("/health")
        assert response.status_code == 200

    def test_health_returns_json(self, test_client):
        """Health endpoint returns valid JSON"""
        response = test_client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "mcp-fortios-server"


# ===============================
# LOGGING SAFETY TESTS
# ===============================


class TestLoggingSafety:
    """Verify that sensitive data is not logged"""

    def test_url_not_in_log_message(self):
        """The full URL (with host) should not appear in log output"""
        client = FortiOSClient("https://192.168.1.99", "secret-token-123", "root")

        with patch.object(client.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {}
            mock_get.return_value = mock_response

            with patch("app.fortios_client.logger") as mock_logger:
                client.get("cmdb/firewall/policy")

                # Check that the log message contains endpoint but not full URL
                log_call = mock_logger.info.call_args[0][0]
                assert "cmdb/firewall/policy" in log_call
                assert "192.168.1.99" not in log_call
                assert "secret-token-123" not in log_call


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
