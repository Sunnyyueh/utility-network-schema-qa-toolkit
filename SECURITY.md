# Security Policy

## Supported versions

Security fixes are applied to the latest V1.x release. Upgrade to the newest patch before reporting behavior that may already be fixed.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting feature for this repository. Do not open a public issue containing exploit details, credentials, sensitive infrastructure records, or restricted file contents.

Include:

- affected version and operating system;
- minimal reproduction using synthetic data;
- expected and observed behavior;
- security impact; and
- any suggested mitigation.

## Data handling

Do not place credentials, tokens, secured URLs, connection strings, authentication profiles, restricted workbooks, or sensitive infrastructure data in project manifests, examples, logs, issue attachments, or generated reports. Review reports before sharing and store them according to their data classification.

The toolkit performs no network requests and does not execute SQL, Arcade, Python, or template expressions supplied through project inputs. HTML reports use automatic escaping and contain no external scripts. Report files are atomically replaced using fixed names inside the chosen output directory.

Third-party dependencies should be updated through reviewed changes with the full quality suite.

