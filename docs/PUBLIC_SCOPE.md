# Public scope

## Current release

This repository currently publishes one narrowly scoped artifact:

- `skills/portable-skill-doctor/` — a read-only static audit workflow for one
  Agent Skill directory at a time.

The public value proposition is compatibility evidence, resource-path review,
and safer pre-install inspection for Codex and GitHub Copilot. It is not a broad
collection of unrelated prompts or projects.

## Included

- the skill instructions and UI metadata;
- the deterministic bundled auditor;
- focused audit-rule and report-contract references;
- synthetic fixtures and tests needed to verify the public behavior;
- CI and release documentation for this skill only.

## Excluded

- private work, customer material, credentials, personal data, and unpublished
  research;
- domain-specific product content or proprietary workflows;
- third-party skills, copied prompts, copied documentation, or repackaged
  validators;
- autonomous installation, execution, repair, publication, or account actions;
- claims of malware detection, universal compatibility, or runtime proof.

## Publication gate

Before any public release:

1. Confirm every tracked file belongs to the scope above.
2. Confirm examples and fixtures are fully synthetic.
3. Run the repository's tests and public-scope checks.
4. Run the auditor against its positive and negative fixtures.
5. Inspect the release archive before upload.
6. Test each documented install command against the exact release tag before
   changing its status from intended to verified.
7. Record the tested host, host version, operating system, command, and result.

Passing these gates does not prove a third-party skill is safe. It establishes
only that this repository's release is within scope and that its documented
behavior was exercised under the recorded conditions.
