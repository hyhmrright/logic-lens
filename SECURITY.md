# Security Policy

## Reporting a Vulnerability

If you believe you've found a security issue in Logic-Lens (for example: a prompt that causes the skill to leak private information, a fix that corrupts target files, or an L-code detection pattern that can be weaponized against reviewers), please report it privately.

**Please do NOT open a public GitHub Issue for security concerns.**

### How to report

- GitHub Security Advisories: https://github.com/hyhmrright/logic-lens/security/advisories/new
- Email: [hyhmrright@gmail.com](mailto:hyhmrright@gmail.com) with the subject line `[SECURITY] Logic-Lens: <brief description>`

Include if possible:
- A minimal reproduction (skill invocation + input code / prompt)
- The observed vs expected behavior
- Your assessment of potential impact

### Response timeline

- Acknowledgement within 3 business days
- Initial triage and severity assessment within 7 business days
- Fix and coordinated disclosure timeline agreed with reporter (typically 30–90 days depending on severity)

### Scope

In scope:
- The six `logic-*` skills and the shared framework under `skills/_shared/`
- `scripts/` shell helpers
- CI / workflow configuration in `.github/`

Out of scope:
- Vulnerabilities in Anthropic's Claude API or the `claude` CLI itself — please report those directly to Anthropic
- Issues caused solely by third-party marketplace aggregators
