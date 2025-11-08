# FortiOS MCP Server

A containerized Model Context Protocol (MCP) server for FortiOS integration built with FastMCP.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.13+ (for local development)
- uv package manager

### Running with Docker

1. **Build and start the server:**
   ```bash
   docker-compose up --build -d
   ```

2. **Check server status:**
   ```bash
   docker logs mcp-fortios-server
   ```

3. **Test the server:**
   ```bash
   # The server will be available at http://localhost:8000/mcp
   curl -X POST http://localhost:8000/mcp \
     -H "Content-Type: application/json" \
     -H "Accept: text/event-stream" \
     -d '{"jsonrpc":"2.0","id":"test","method":"tools/list"}'
   ```

### Available Tools

The server provides comprehensive FortiOS management tools via MCP:

#### 🔥 **Firewall Policy Tools**
- **`create_firewall_policy`** - Create firewall policies with full configuration
- **`get_firewall_policies`** - Retrieve all or specific firewall policies

#### 🏠 **Address Object Tools**  
- **`create_address`** - Create address objects (ipmask, iprange, fqdn types)
- **`get_addresses`** - Retrieve all or specific address objects
- **`delete_address`** - Delete address objects

#### 👥 **Address Group Tools**
- **`create_address_group`** - Create groups containing existing address objects
- **`get_address_groups`** - Retrieve all or specific address groups  
- **`delete_address_group`** - Delete address groups

#### 🌐 **VIP (Virtual IP) Tools**
- **`create_vip`** - Create VIP objects for port forwarding/NAT
- **`get_vips`** - Retrieve all or specific VIP objects

#### 🔧 **Utility Tools**
- **`ping_fortigate`** - Test FortiOS device connectivity and responsiveness


### MCP Protocol

This server implements the Model Context Protocol (MCP) over HTTP using:
- **Endpoint:** `http://localhost:8000/mcp`
- **Protocol:** JSON-RPC 2.0 over HTTP
- **Transport:** Server-Sent Events (SSE)
- **Content-Type:** `application/json`
- **Accept:** `text/event-stream`

### Development

#### Local Development Setup

1. **Install dependencies:**
   ```bash
   uv add starlette fastmcp uvicorn
   ```

2. **Run locally:**
   ```bash
   uvicorn app.server:app --host 0.0.0.0 --port 8000 --reload
   ```

#### Docker Commands

```bash
# Build the image
docker-compose build

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the server
docker-compose down

# Rebuild and restart
docker-compose up --build -d
```

### Project Structure

```
mcp_fortios/
├── app/                     # Core application
│   ├── __init__.py         # Python package init
│   ├── server.py           # Main MCP server with all FortiOS tools
│   ├── fortios_client.py   # FortiOS API client
│   └── tools.py            # FortiOS tools implementation
├── tests/                   # Test suite
│   ├── __init__.py         # Test package init
│   ├── test_basic.py       # Unit tests
│   └── test_integration.py # Integration tests
├── examples/                # Usage examples and utilities
│   ├── __init__.py         # Examples package init
│   ├── usage_examples.py   # Comprehensive usage examples
│   └── mcp_client.py       # Advanced MCP client with session management
├── .github/workflows/       # CI/CD pipeline
│   └── ci.yml              # GitHub Actions workflow
├── Dockerfile              # Container configuration
├── docker-compose.yml      # Docker Compose setup
├── k8s-deployment.yaml     # Kubernetes deployment
├── health_check.py         # Server health check script
├── pyproject.toml          # Python dependencies and project metadata
├── uv.lock                 # Dependency lock file
├── LICENSE                 # MIT License
├── CONTRIBUTING.md         # Contributing guidelines
├── SECURITY.md             # Security policy
└── README.md               # This file
```

### Integration

To integrate this MCP server with your applications:

1. **MCP Client:** Use any MCP-compatible client
2. **API Endpoint:** `http://localhost:8000/mcp`
3. **Authentication:** Currently none (add as needed)
4. **Protocol:** Standard MCP over HTTP

### Versioning and Releases

This project follows [Semantic Versioning](https://semver.org/) using the format `v1.0.1`.

#### Making a Release

1. **Using the release script** (recommended):
   ```bash
   # Increment patch version (1.0.0 → 1.0.1)
   ./scripts/release.sh patch
   
   # Increment minor version (1.0.1 → 1.1.0)
   ./scripts/release.sh minor
   
   # Increment major version (1.1.0 → 2.0.0)
   ./scripts/release.sh major
   
   # Set specific version
   ./scripts/release.sh v1.2.3
   ```

2. **Manual process**:
   ```bash
   # Update version in pyproject.toml
   # Commit the change
   git add pyproject.toml
   git commit -m "chore: bump version to 1.0.1"
   
   # Create and push tag
   git tag -a v1.0.1 -m "Release v1.0.1"
   git push origin main
   git push origin v1.0.1
   ```

#### Docker Image Tags

When you create a version tag (e.g., `v1.0.1`), the CI/CD pipeline automatically builds and pushes Docker images with these tags:
- `your-username/mcp-fortios-server:1.0.1` (full version)
- `your-username/mcp-fortios-server:1.0` (major.minor)
- `your-username/mcp-fortios-server:1` (major)
- `your-username/mcp-fortios-server:latest` (if from main branch)

### Logs

Container logs are available via:
```bash
docker logs mcp-fortios-server
```

Logs include:
- Server startup and shutdown
- Session management
- Tool requests and responses
- Error handling

### Tool Examples

#### Create Address Object
```python
# Create subnet address
create_address(
    name="WebServers",
    address_type="ipmask", 
    subnet="192.168.100.0 255.255.255.0",
    comment="Web server subnet",
    fortigate_url="https://192.168.1.99",
    fortigate_token="your-token",
    fortigate_vdom="root"
)

# Create FQDN address  
create_address(
    name="GoogleDNS",
    address_type="fqdn",
    fqdn="dns.google.com",
    fortigate_url="https://192.168.1.99",
    fortigate_token="your-token"
)
```

#### Create Firewall Policy
```python
create_firewall_policy(
    name="Allow_Web_Access",
    srcintf=["internal"],
    dstintf=["wan1"], 
    srcaddr=["WebServers"],
    dstaddr=["all"],
    service=["HTTP", "HTTPS"],
    action="accept",
    fortigate_url="https://192.168.1.99",
    fortigate_token="your-token"
)
```

### Testing

1. **Server health check:**
   ```bash
   python health_check.py
   ```

3. **Health check:**
   ```bash
   python health_check.py
   ```

4. **Full tool examples:**
   ```bash
   python examples/usage_examples.py
   ```

5. **MCP protocol test:**
   ```bash  
   python examples/mcp_client.py
   ```

6. **Run test suite:**
   ```bash
   uv run pytest tests/ -v
   ```

### Troubleshooting

1. **Port already in use:**
   ```bash
   # Change port in docker-compose.yml
   ports:
     - "8001:8000"  # Use port 8001 instead
   ```

2. **Container not starting:**
   ```bash
   # Check logs
   docker-compose logs mcp-fortios-server
   
   # Rebuild from scratch
   docker-compose down
   docker-compose build --no-cache
   docker-compose up
   ```

3. **Connection refused:**
   - Ensure container is running: `docker-compose ps`
   - Check correct port is exposed
   - Verify no firewall blocking the port

4. **FortiOS API errors:**
   - Verify FortiGate URL is accessible
   - Check API token is valid and has required permissions
   - Ensure VDOM name is correct
   - Check FortiGate API documentation for specific error codes

### Production Usage

1. **Replace test credentials** in examples with real FortiGate details
2. **Secure API tokens** using environment variables or secrets
3. **Enable SSL verification** for production FortiGate connections
4. **Add error handling** and retry logic for network issues
5. **Implement logging** for audit trails
6. **Set up monitoring** for server health and API usage
