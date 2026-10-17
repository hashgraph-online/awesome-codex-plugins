# Security Policy

Agent Harness Skills is a documentation and skills repository. It should not contain credentials, private URLs, account identifiers, customer data, or environment-specific secrets.

## Supported Versions

Security fixes are handled on the default branch. If releases are introduced later, this section should list supported release lines.

## Reporting A Vulnerability

Do not open a public issue containing secrets, exploit details, or sensitive repository information.

Use the repository host's private vulnerability reporting feature if it is enabled. If no private route is available, open a minimal public issue asking maintainers to provide a private disclosure channel, without including sensitive details.

When reporting, include:

- A concise description of the issue.
- The affected file or installation path.
- Whether any private data or credentials are exposed.
- Steps maintainers can use to confirm the problem safely.

## Scope

Relevant issues include:

- Committed secrets, credentials, private URLs, or account identifiers.
- Install instructions that could cause unsafe execution or credential exposure.
- Plugin or extension metadata that grants broader capabilities than documented.
- Skill text that instructs agents to collect, expose, or commit sensitive data.

Out of scope:

- Product vulnerabilities in repositories that use these skills.
- General questions about agent behavior without a concrete security impact.
- Reports that require access to private systems not controlled by this project.
