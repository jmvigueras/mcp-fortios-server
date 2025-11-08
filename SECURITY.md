# Security Policy

## 🔒 Supported Versions

We provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## 🚨 Reporting a Vulnerability

### Where to Report
**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them responsibly:
- **Email**: Send details to the project maintainers
- **Include**: Detailed description of the vulnerability
- **Response**: We will respond within 48 hours

### What to Include
When reporting a vulnerability, please provide:

1. **Description** of the vulnerability
2. **Steps to reproduce** the issue
3. **Potential impact** assessment
4. **Suggested fix** (if you have one)
5. **Your contact information**

### Response Process
1. **Acknowledgment**: We'll confirm receipt within 48 hours
2. **Assessment**: We'll assess the severity and impact
3. **Fix Development**: We'll work on a fix
4. **Disclosure**: Coordinated disclosure after fix is ready
5. **Credit**: We'll credit you in the security advisory (if desired)

## 🛡️ Security Best Practices

### For Users
1. **Secure API Tokens**:
   - Never commit tokens to version control
   - Use environment variables or secure secret management
   - Rotate tokens regularly

2. **Network Security**:
   - Use HTTPS for FortiGate connections in production
   - Implement proper firewall rules
   - Consider VPN access for management

3. **Container Security**:
   - Keep base images updated
   - Run containers as non-root user (already implemented)
   - Use security scanning tools

4. **Access Control**:
   - Limit MCP server access to authorized clients
   - Implement proper authentication if needed
   - Monitor API usage and logs

### For Developers
1. **Input Validation**:
   - Validate all user inputs
   - Sanitize data before FortiOS API calls
   - Use parameterized queries

2. **Error Handling**:
   - Don't expose sensitive information in error messages
   - Log security events appropriately
   - Implement proper rate limiting

3. **Dependencies**:
   - Keep dependencies updated
   - Use security scanning tools
   - Review third-party packages

## 🔍 Known Security Considerations

### Current Security Measures
- ✅ **Non-root container execution**
- ✅ **Input validation for FortiOS API calls**
- ✅ **SSL certificate verification support**
- ✅ **No hardcoded credentials**
- ✅ **Structured error handling**

### Areas for Enhancement
- 🔧 **Authentication/Authorization**: Currently no built-in auth
- 🔧 **Rate Limiting**: No built-in request rate limiting
- 🔧 **Audit Logging**: Basic logging, could be enhanced
- 🔧 **API Key Management**: Left to deployment environment

## 🚀 Deployment Security

### Production Checklist
- [ ] Use HTTPS for all FortiGate connections
- [ ] Implement proper secret management
- [ ] Enable container security scanning
- [ ] Set up monitoring and alerting
- [ ] Regular security updates
- [ ] Network segmentation
- [ ] Access control implementation

### Kubernetes Security (if applicable)
```yaml
# Example security context
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  readOnlyRootFilesystem: true
  capabilities:
    drop:
    - ALL
```

## 📊 Security Scanning

We recommend using these tools:

### Container Scanning
- **Trivy**: `trivy image mcp-fortios-server:latest`
- **Snyk**: Container vulnerability scanning
- **Docker Scout**: Built-into Docker Desktop

### Dependency Scanning
- **Safety**: `uv run safety check`
- **Bandit**: `uv run bandit -r app/`
- **Semgrep**: Static analysis for security issues

### Code Quality
- **SonarQube**: Comprehensive code analysis
- **CodeQL**: GitHub's semantic code analysis

## 🔄 Security Updates

### Update Process
1. **Monitor** for security advisories
2. **Assess** impact on this project
3. **Test** updates in development environment
4. **Deploy** to production after validation
5. **Document** security changes

### Notifications
- Watch this repository for security updates
- Subscribe to security advisories for dependencies
- Monitor FortiOS security bulletins

## 📚 Additional Resources

### FortiOS Security
- [FortiOS Administration Guide](https://docs.fortinet.com/)
- [FortiGate REST API Documentation](https://fndn.fortinet.net/)
- [Fortinet Security Advisories](https://www.fortiguard.com/psirt)

### Container Security
- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
- [Kubernetes Security](https://kubernetes.io/docs/concepts/security/)
- [OWASP Container Security](https://owasp.org/www-project-container-security/)

### Python Security
- [Python Security Guide](https://python-security.readthedocs.io/)
- [OWASP Python Security](https://owasp.org/www-project-python-security/)

---

**Remember**: Security is a shared responsibility. While we strive to make this software secure, proper deployment and configuration are crucial for maintaining security in production environments.