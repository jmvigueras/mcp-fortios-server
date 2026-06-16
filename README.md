# FortiOS MCP Server

MCP server for managing FortiGate firewalls via AI agents. Built with FastMCP, deployed as a container.

**Public endpoint:** `https://mcp-fortios.fortidemoscloud.com/mcp`

## Tools

| Tool | Description |
|------|-------------|
| `ping_fortigate` | Test connectivity to a FortiGate |
| `create_firewall_policy` | Create a firewall policy |
| `get_firewall_policies` | List firewall policies |
| `create_address` | Create address object (ipmask, iprange, fqdn) |
| `get_addresses` | List address objects |
| `delete_address` | Delete an address object |
| `create_address_group` | Create address group |
| `get_address_groups` | List address groups |
| `delete_address_group` | Delete an address group |
| `create_vip` | Create Virtual IP (NAT/port forwarding) |
| `get_vips` | List VIP objects |

Every tool requires `fortigate_url` and `fortigate_token` as parameters. The server is stateless — it doesn't store credentials.

## Connect from Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "fortios": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://mcp-fortios.fortidemoscloud.com/mcp"
      ],
      "env": {
        "NODE_TLS_REJECT_UNAUTHORIZED": "0"
      }
    }
  }
}
```

## Connect from Gemini CLI

Add to your Gemini settings (`~/.gemini/settings.json`):

```json
{
  "mcpServers": {
    "fortios": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://mcp-fortios.fortidemoscloud.com/mcp"
      ],
      "env": {
        "NODE_TLS_REJECT_UNAUTHORIZED": "0"
      }
    }
  }
}
```

## Connect from Kiro / VS Code

Add to `.kiro/settings/mcp.json` or equivalent:

```json
{
  "mcpServers": {
    "fortios": {
      "url": "https://mcp-fortios.fortidemoscloud.com/mcp"
    }
  }
}
```

## Test with curl

```bash
# 1. Initialize session and capture Mcp-Session-Id from headers
export SESSION_ID=$(curl -s -i -X POST https://mcp-fortios.fortidemoscloud.com/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test-curl","version":"1.0"}}}' \
  | grep -i "mcp-session-id" | awk '{print $2}' | tr -d '\r')

echo "Session ID: $SESSION_ID"

# 2. List tools using the captured Session ID
curl -s -X POST https://mcp-fortios.fortidemoscloud.com/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

## Run locally

```bash
# Docker
docker-compose up --build -d

# Or directly
uv sync
uv run uvicorn app.server:app --host 0.0.0.0 --port 8000
```

Server available at `http://localhost:8000/mcp` with health check at `/health`.

## Deploy to Kubernetes

```bash
kubectl apply -f k8s-deployment.yaml
```

Exposes on NodePort 30081. Image: `jviguerasfortinet/mcp-fortios-server:v1.0.8`

## Release

```bash
./scripts/release.sh patch   # 1.0.8 → 1.0.9
```

Pushing a `v*.*.*` tag triggers the GitHub Actions pipeline to build and push the Docker image to Docker Hub.

## License

MIT
