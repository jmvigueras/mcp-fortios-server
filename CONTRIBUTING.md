# Contributing to FortiOS MCP Server

Thank you for your interest in contributing to the FortiOS MCP Server! This document provides guidelines for contributing to this project.

## 🚀 Getting Started

### Prerequisites
- Python 3.13+
- Docker and Docker Compose
- uv package manager
- Access to a FortiGate device for testing (or FortiGate VM)

### Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/yourusername/fortios-mcp-server.git
   cd fortios-mcp-server
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Start the development server:**
   ```bash
   docker-compose up --build
   ```

## 🛠️ Development Guidelines

### Code Style
- Follow PEP 8 Python style guidelines
- Use type hints where possible
- Add docstrings to all functions and classes
- Keep functions focused and single-purpose

### Project Structure
```
app/
├── server.py         # Main MCP server with tool definitions
├── fortios_client.py # FortiOS API client
├── tools.py          # Tool implementation functions
└── tests/           # Test files
```

### Adding New Tools

1. **Add the tool function to `app/tools.py`:**
   ```python
   @staticmethod
   def your_new_tool(url: str, token: str, vdom: str = "root", **kwargs) -> Dict[str, Any]:
       """Tool description"""
       try:
           client = FortiOSTools.create_client(url, token, vdom)
           # Tool implementation
           return {"success": True, "data": result}
       except Exception as e:
           logger.error(f"Error in tool: {e}")
           return {"success": False, "error": str(e)}
   ```

2. **Add the MCP tool endpoint to `app/server.py`:**
   ```python
   @mcp.tool()
   def your_new_tool(
       fortigate_url: str,
       fortigate_token: str,
       fortigate_vdom: str = "root",
       # ... other parameters
   ) -> str:
       """Tool description for MCP clients"""
       result = FortiOSTools.your_new_tool(
           fortigate_url, fortigate_token, fortigate_vdom, **kwargs
       )
       return json.dumps(result, indent=2)
   ```

3. **Add tests for your tool**

### Testing

1. **Run the test suite:**
   ```bash
   uv run python -m pytest
   ```

2. **Test with a real FortiGate:**
   ```bash
   # Update examples with your FortiGate details
   uv run python app/examples.py
   ```

3. **Test MCP protocol:**
   ```bash
   uv run python app/simple_test.py
   ```

## 📝 Pull Request Process

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Add your feature/fix
   - Add or update tests
   - Update documentation if needed

3. **Test your changes:**
   ```bash
   # Run tests
   uv run python -m pytest
   
   # Test Docker build
   docker-compose build
   
   # Test MCP server
   docker-compose up -d
   uv run python app/simple_test.py
   ```

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: add new FortiOS tool for X"
   ```

5. **Push and create PR:**
   ```bash
   git push origin feature/your-feature-name
   ```

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment information:**
   - Python version
   - Docker version
   - FortiOS version
   - Operating system

2. **Steps to reproduce:**
   - Exact commands used
   - Expected vs actual behavior
   - Error messages/logs

3. **Minimal example:**
   - Simplified code that reproduces the issue
   - Remove sensitive information (tokens, IPs)

## 💡 Feature Requests

For new features:

1. **Check existing issues** to avoid duplicates
2. **Describe the use case** and why it's valuable
3. **Propose the API** if you have ideas
4. **Consider implementation complexity**

## 🔒 Security

### Reporting Security Issues
- **Do not** open public issues for security vulnerabilities
- Email security issues to: [maintainer-email]
- Include detailed information about the vulnerability

### Security Guidelines
- Never commit API tokens, passwords, or sensitive data
- Use environment variables for sensitive configuration
- Follow security best practices in code

## 📚 Documentation

When contributing:

1. **Update README.md** if you add new features
2. **Add docstrings** to new functions
3. **Update examples** if APIs change
4. **Keep documentation current**

## 🏷️ Versioning

We use Semantic Versioning (SemVer):
- **MAJOR.MINOR.PATCH**
- Major: Breaking changes
- Minor: New features (backward compatible)
- Patch: Bug fixes

## 📜 Code of Conduct

### Our Standards
- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Maintain professionalism

### Unacceptable Behavior
- Harassment or discrimination
- Offensive comments or personal attacks
- Spam or off-topic discussions
- Sharing private information without permission

## ❓ Questions

If you have questions:

1. **Check the documentation** first
2. **Search existing issues**
3. **Ask in discussions** for general questions
4. **Open an issue** for specific problems

## 🙏 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions
- Project documentation

Thank you for contributing to FortiOS MCP Server! 🚀