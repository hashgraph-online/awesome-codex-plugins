# Security Policy

## Reporting a Vulnerability

The AxonFlow team takes security vulnerabilities seriously. We appreciate your efforts to responsibly disclose your findings.

### How to Report

**Please DO NOT report security vulnerabilities through public GitHub issues.**

Instead, please report security vulnerabilities by emailing:

**security@getaxonflow.com**

You should receive a response within **48 hours**. If for some reason you do not, please follow up via email to ensure we received your original message.

### What to Include

Please include the following information in your report:

- Type of vulnerability (e.g., SQL injection, XSS, authentication bypass)
- Full paths of source file(s) related to the manifestation of the vulnerability
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the vulnerability
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

This information will help us triage your report more quickly.

### Response Timeline

- **Initial Response:** Within 48 hours of report
- **Triage:** Within 5 business days, we will confirm the vulnerability and determine severity
- **Fix Development:** Depends on severity (Critical: 7 days, High: 14 days, Medium: 30 days)
- **Public Disclosure:** After fix is deployed and users have time to update (typically 30-90 days)

### Severity Classification

We use the following severity levels:

- **Critical:** Vulnerabilities that allow remote code execution, complete system compromise, or unauthorized data access at scale
- **High:** Vulnerabilities that allow significant unauthorized access to data or system functionality
- **Medium:** Vulnerabilities that allow limited unauthorized access or minor information disclosure
- **Low:** Vulnerabilities with minimal security impact

### Coordinated Disclosure

We follow responsible disclosure practices:

1. We will acknowledge your email within 48 hours
2. We will confirm the vulnerability and determine its severity
3. We will work on a fix and keep you updated on progress
4. Once a fix is ready, we will coordinate the release timeline with you
5. We will publicly acknowledge your contribution (unless you prefer to remain anonymous)

### Bug Bounty

We currently do not have a formal bug bounty program. However, we deeply appreciate security researchers' efforts and will:

- Publicly acknowledge security researchers who report valid vulnerabilities (with permission)
- Consider offering rewards for critical vulnerabilities on a case-by-case basis
- Provide AxonFlow swag and extended trial licenses to researchers who help improve our security

### Scope

The following are **in scope** for security reports:

- AxonFlow Agent (API gateway component)
- AxonFlow Orchestrator (routing and policy enforcement)
- AxonFlow SDKs (Go, Python, TypeScript, Java)
- Customer Portal (backend and frontend)
- MCP Connectors (PostgreSQL, Redis, Salesforce, Snowflake, Amadeus, etc.)
- AWS Marketplace CloudFormation templates
- Docker images and deployment configurations

The following are **out of scope**:

- Denial of Service (DoS) attacks
- Social engineering attacks
- Physical attacks against AxonFlow infrastructure
- Issues in third-party dependencies (report these to the upstream project)
- Issues requiring physical access to user devices

---

## Security Architecture

### Overview

AxonFlow implements a **prevention-first security architecture** with sub-10ms inline governance. Unlike passive monitoring tools that detect issues after damage is done, AxonFlow provides active prevention through real-time intervention.

For detailed information, see:
- [Threat Model and Data Flow Analysis](technical-docs/THREAT_MODEL_AND_DATA_FLOW.md)
- [Security Architecture Overview](technical-docs/ARCHITECTURE.md)

### Core Security Principles

1. **Defense in Depth**: Multiple layers of security controls
2. **Least Privilege**: Minimal permissions by default
3. **Zero Trust**: Verify every request, never assume trust
4. **Encryption Everywhere**: Data protected at rest and in transit
5. **Audit Everything**: Immutable logs for compliance
6. **Fail Secure**: System defaults to secure state on errors

### Trust Boundaries

- **External → Agent**: Public internet to API gateway (TLS 1.3)
- **Agent → Orchestrator**: Internal network (mutual TLS optional)
- **Orchestrator → Database**: Encrypted connections (SSL required)
- **Orchestrator → LLM Providers**: HTTPS with API key rotation

---

## Security Features

AxonFlow includes comprehensive security features by default:

### 1. Authentication & Authorization

- **License Key Authentication**: HMAC-SHA256 signed keys with expiration
- **Service Identity System**: Granular permissions for MCP connector access
- **RBAC/ABAC Enforcement**: Role and attribute-based access control
- **API Key Rotation**: Automated key rotation with zero downtime

### 2. Data Protection

- **Row-Level Security (RLS)**: Database-level multi-tenant isolation
- **PII Detection & Redaction**: Real-time content filtering to prevent data leakage
- **Credential Encryption**: AES-256-GCM encryption for connector credentials (v4.1.0+)
- **Encryption at Rest**: AES-256 encryption for all stored data
- **Encryption in Transit**: TLS 1.3 for all network communication
- **Multi-Tenant Isolation**: Complete logical separation between tenants

### 3. Policy Enforcement

- **System Policies (Agent)**: Sub-10ms enforcement at the edge
- **Tenant Policies (Orchestrator)**: Context-aware policy evaluation
- **Content Filtering**: SQL injection, XSS, and malicious prompt prevention
- **Rate Limiting**: Redis-backed distributed rate limiting per tenant

### 4. Audit & Compliance

- **Immutable Audit Logs**: Append-only logs with cryptographic verification
- **Compliance Mode**: Synchronous audit logging for regulated industries
- **Retention Policies**: Configurable log retention (7-365 days)
- **GDPR Compliance**: Data residency, right to deletion, data portability

### 5. Network Security

- **VPC Isolation**: Private subnets for all internal components
- **Security Groups**: Least-privilege firewall rules
- **Network ACLs**: Additional network-level protection
- **VPC Endpoints**: Private connectivity to AWS services (no internet exposure)
- **WAF Integration**: Web Application Firewall for edge protection (optional)

### 6. Infrastructure Security

- **Secrets Management**: AWS Secrets Manager for all credentials
- **Parameter Store**: Encrypted configuration with versioning
- **IAM Roles**: Instance roles instead of long-lived credentials
- **CloudTrail Logging**: All API calls logged for audit
- **GuardDuty**: Threat detection and continuous monitoring

---

## Encryption Standards

### Data at Rest

- **Database**: AES-256 encryption via AWS RDS encryption
- **S3 Storage**: AES-256 server-side encryption (SSE-S3 or SSE-KMS)
- **Secrets**: AES-256 encryption via AWS Secrets Manager
- **EBS Volumes**: AES-256 encryption for all attached volumes

### Data in Transit

- **External APIs**: TLS 1.3 with strong cipher suites only
- **Internal Communication**: TLS 1.2+ (configurable to mutual TLS)
- **Database Connections**: SSL/TLS required for PostgreSQL
- **Redis**: TLS encryption for cache connections

### Key Management

- **License Keys**: HMAC-SHA256 with Ed25519 signatures
- **Secrets Rotation**: Automated rotation via AWS Secrets Manager
- **KMS Integration**: AWS KMS for envelope encryption
- **HSM Support**: CloudHSM for regulated industries (optional)

---

## Compliance & Certifications

### Current Compliance Status

- **GDPR Ready**: Data residency controls, right to deletion, data portability
- **EU AI Act Ready**: Risk classification, transparency, audit trails
- **SOC 2 Type II**: In progress (target: Q3 2026)
- **HIPAA**: Architecture supports HIPAA compliance (BAA available)
- **ISO 27001**: In progress (target: Q4 2026)

### Compliance Features

- **Data Residency**: Deploy in EU (Frankfurt) or US regions
- **Audit Trails**: Immutable logs with cryptographic verification
- **Access Controls**: RBAC with separation of duties
- **Retention Policies**: Configurable retention for compliance requirements
- **Compliance Reporting**: Automated reports for auditors

---

## Secure Development Lifecycle

### Code Security Practices

1. **Code Review**: All changes require peer review before merge
2. **Static Analysis**: Automated linting (golangci-lint, gosec)
3. **Dependency Scanning**: Automated vulnerability scanning (Trivy, Dependabot)
4. **Secret Scanning**: Pre-commit hooks to prevent credential leaks
5. **Security Testing**: Dedicated security test suites

### CI/CD Security

- **Automated Testing**: All tests must pass before merge
- **Security Scanning**: Trivy scans on every build
- **Code Coverage**: Minimum 76% coverage enforced
- **Signed Commits**: GPG signing for releases (recommended)
- **Immutable Builds**: Docker images tagged with git commit SHA

### Dependency Management

- **Minimal Dependencies**: Reduce attack surface with fewer dependencies
- **Pinned Versions**: Exact version pinning in go.mod
- **Vulnerability Scanning**: Automated CVE detection via Dependabot
- **Update Policy**: Security updates applied within 7 days of disclosure
- **License Compliance**: Automated license checking (go-licenses)

---

## Deployment Security

### CloudFormation Security

- **Least Privilege IAM**: Minimal permissions for each component
- **Encrypted Storage**: All RDS, EBS, S3 encrypted by default
- **Private Subnets**: All compute resources in private subnets
- **Security Groups**: Whitelist-only ingress rules
- **Secrets Management**: No hardcoded secrets in templates

### Container Security

- **Minimal Base Images**: Alpine Linux for reduced attack surface
- **Non-Root User**: Containers run as non-root by default
- **Image Scanning**: Trivy scanning on all Docker images
- **Signed Images**: Docker Content Trust for production images
- **Immutable Tags**: Images tagged with git SHA, never `latest`

### Multi-AZ High Availability

- **RDS Multi-AZ**: Automatic failover for database
- **ECS Multi-AZ**: Services deployed across multiple availability zones
- **Load Balancer**: Application Load Balancer with health checks
- **Auto-Healing**: Automatic replacement of unhealthy containers

---

## Security Best Practices for Users

If you're deploying AxonFlow:

### Critical Security Controls

1. **Use Strong Secrets**
   - Generate cryptographically secure JWT secrets (minimum 32 bytes)
   - Use AWS Secrets Manager random password generation
   - Never commit secrets to version control

2. **Enable HTTPS**
   - Always use TLS/SSL in production (CloudFormation templates enforce this)
   - Use AWS Certificate Manager for free SSL certificates
   - Enable HTTP to HTTPS redirect

3. **Rotate Credentials**
   - Rotate license keys at least annually
   - Enable AWS Secrets Manager automatic rotation
   - Rotate database passwords every 90 days

4. **Monitor Audit Logs**
   - Review audit logs regularly for suspicious activity
   - Set up CloudWatch alarms for anomalies
   - Export logs to SIEM for long-term analysis

5. **Update Regularly**
   - Keep AxonFlow updated to the latest stable version
   - Subscribe to security advisories
   - Test updates in staging before production

6. **Restrict Network Access**
   - Use VPC configurations to limit access to internal networks only
   - Use security groups to whitelist specific IP ranges
   - Enable VPC endpoints to avoid internet exposure

7. **Enable Compliance Mode**
   - Use synchronous audit logging for regulated industries
   - Configure appropriate log retention periods
   - Enable PII redaction for sensitive data

### Network Security Checklist

- [ ] All resources deployed in private subnets
- [ ] Security groups configured with least privilege
- [ ] VPC endpoints enabled for AWS services
- [ ] Load balancer scheme set to `internal` for same-VPC deployments
- [ ] CloudTrail enabled for API audit logging
- [ ] VPC Flow Logs enabled for network monitoring

---

## Security Updates

Security updates will be released as follows:

- **Critical vulnerabilities**: Immediate patch release
- **High severity vulnerabilities**: Patch within 14 days
- **Medium/Low severity vulnerabilities**: Included in next regular release

Security advisories will be published at:
- GitHub Security Advisories: https://github.com/getaxonflow/axonflow/security/advisories
- Email notifications to registered users
- Blog post at https://getaxonflow.com/blog

---

## Incident Response

### Detection

- **Automated Monitoring**: CloudWatch alarms for anomalies
- **Audit Log Analysis**: Continuous scanning for suspicious patterns
- **Health Checks**: Automated health monitoring every 30 seconds
- **GuardDuty**: AWS threat detection service

### Response Procedures

In the event of a security incident:

1. **Immediate Containment**
   - Isolate affected systems
   - Disable compromised credentials
   - Enable additional logging

2. **Investigation**
   - Preserve evidence (logs, snapshots)
   - Determine scope and impact
   - Identify root cause

3. **Remediation**
   - Apply security patches
   - Rotate all potentially compromised credentials
   - Update security controls

4. **Recovery**
   - Restore services from known-good backups
   - Verify system integrity
   - Resume normal operations

5. **Post-Incident Review**
   - Document lessons learned
   - Update security controls
   - Notify affected parties (if required)

### Customer Responsibilities

If you operate AxonFlow:

- Monitor CloudWatch logs and alarms
- Review audit logs regularly
- Maintain incident response plan
- Keep emergency contact list updated
- Test backup and recovery procedures

---

## Contact

For security-related questions or concerns:

- **Email:** security@getaxonflow.com
- **Public inquiries:** GitHub Discussions (for non-sensitive security topics)

---

## Hall of Fame

We would like to thank the following security researchers for responsibly disclosing vulnerabilities:

*(List will be updated as researchers report issues)*

---

## Additional Resources

- [Contributing Guide](./CONTRIBUTING.md) - How to contribute securely
- [Changelog](./CHANGELOG.md) - Security updates and fixes
- [AxonFlow Security Architecture](technical-docs/THREAT_MODEL_AND_DATA_FLOW.md)
- [Deployment Security Guide](technical-docs/DEPLOYMENT_SCRIPTS_REFERENCE.md)
- [Enterprise Security Configuration](ee/docs/ENTERPRISE_SECURITY.md) - HMAC secrets, self-hosted mode
- [RLS Architecture](technical-docs/RLS_ARCHITECTURE.md)
- [Audit Logging Architecture](technical-docs/AUDIT_LOGGING_ARCHITECTURE.md)
- [Service Identity Architecture](technical-docs/SERVICE_IDENTITY_ARCHITECTURE.md)

---

**Last Updated:** April 2026

**Version:** 2.2
