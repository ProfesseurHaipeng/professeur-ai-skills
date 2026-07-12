# Changelog

All notable public changes to this repository will be documented here.

## [0.1.0] - 2026-07-12

### Added

- Initial public documentation for `portable-skill-doctor`.
- Offline Python auditor with stable finding identifiers and exit codes.
- Codex and GitHub Copilot target analysis without executing target code.
- Deterministic text, JSON, and SARIF renderers.
- Audit-first instructions for Codex and GitHub Copilot targets.
- Text, JSON, and SARIF output guidance.
- Focused audit-rule and report-contract references.
- Public-scope and independent-provenance records.
- A tested-compatibility record with explicit evidence boundaries.
- Forty-eight unit, adversarial, path, archive, and policy tests.
- Read-only CI, history scanning, and deterministic release-archive gates.

### Changed

- Replaced the generated Skill placeholder with a concise, command-driven,
  read-only workflow.
- Narrowed the repository's current public scope to one Agent Skill.
- Treated Codex's host-specific `.codex/skills` install location as an
  informational portability note instead of a strict-mode warning.
- Verified public remote preview and clean installation from an exact commit;
  release-tag verification follows tag creation.

### Security

- Prohibited running, importing, sourcing, installing, building, or testing
  code from the audited skill.
- Required bounded static-audit language instead of claims that a target is
  safe, malware-free, or universally compatible.
