---
name: Security Audit
description: Perform thorough security assessment identifying vulnerabilities, misconfigurations, and attack vectors.
category: Security
tags: [security, audit, vulnerability, cve]
---

I'll conduct a comprehensive security audit following the Security Auditor Agent guidelines from `openspec/agents/security-auditor.md`.

**Vulnerability Detection:**

I'll identify and assess common security flaws including:
- Injection vulnerabilities (SQL, command, LDAP, XPath)
- Cross-site scripting (XSS) and CSRF
- Broken authentication & session management
- Insecure direct object references
- Security misconfigurations
- Sensitive data exposure
- Broken access control
- Insecure deserialization
- Known vulnerabilities in dependencies
- Insufficient logging & monitoring
- Exposed API keys or credentials

**Analysis Workflow:**

1. **Reconnaissance** - Map codebase structure, frameworks, dependencies
2. **Dependency Audit** - Check for known CVEs
3. **Static Analysis** - Review for security anti-patterns
4. **Configuration Review** - Examine configs, environment handling, secrets
5. **Authentication/Authorization** - Audit access control
6. **Data Handling** - Review sensitive data processing
7. **Summary Report** - Prioritized findings with remediation

**For Each Finding I'll Provide:**
- **Severity**: Critical / High / Medium / Low / Informational
- **Location**: File path and line numbers
- **Description**: Clear vulnerability explanation
- **Impact**: What an attacker could achieve
- **Proof of Concept**: Example exploit scenario
- **Remediation**: Specific fix with code examples

**Please specify:**
- What to audit (files, directories, or whole codebase)
- Threat model or specific concerns
- Technology stack/framework focus
