# Contributing

## Setup

```bash
git clone https://github.com/jmvigueras/mcp-fortios-server.git
cd mcp-fortios-server
uv sync --dev
```

## Adding a new tool

1. Add the implementation in `app/tools.py`:

```python
@staticmethod
def your_tool(url: str, token: str, vdom: str, ...) -> Dict[str, Any]:
    connectivity = FortiOSTools._check_connectivity(url, token, vdom)
    if not connectivity["success"]:
        return connectivity
    try:
        client = FortiOSTools.create_client(url, token, vdom)
        result = client.get("cmdb/your/endpoint")
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "message": str(e)}
```

2. Register it in `app/server.py`:

```python
@mcp.tool()
def your_tool(fortigate_url: str, fortigate_token: str, ...) -> str:
    """Tool description."""
    result = FortiOSTools.your_tool(fortigate_url, fortigate_token, ...)
    return json.dumps(result, indent=2)
```

3. Add tests in `tests/`.

## Running checks

```bash
uv run pytest tests/ -v
uv run mypy app/ --ignore-missing-imports
uv run black --check app/
uv run flake8 app/ --max-line-length=127
```

## Pull requests

- Branch from `main`
- Keep changes focused
- Tests must pass
- Use conventional commits: `fix:`, `feat:`, `chore:`

## Security

Don't open public issues for vulnerabilities. Email the maintainers directly.

Never commit tokens or credentials. The server is stateless by design — credentials come from the MCP client on each call.
