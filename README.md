# Professeur AI Skills

[![CI](https://github.com/ProfesseurHaipeng/professeur-ai-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/ProfesseurHaipeng/professeur-ai-skills/actions/workflows/ci.yml)
[![Security gates](https://github.com/ProfesseurHaipeng/professeur-ai-skills/actions/workflows/security.yml/badge.svg)](https://github.com/ProfesseurHaipeng/professeur-ai-skills/actions/workflows/security.yml)
[![Latest release](https://img.shields.io/github/v/release/ProfesseurHaipeng/professeur-ai-skills)](https://github.com/ProfesseurHaipeng/professeur-ai-skills/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Small, inspectable Agent Skills with explicit limits and reproducible tests.

The first release is **Portable Skill Doctor**: a read-only static auditor that
finds broken resources, unsafe path assumptions, undeclared requirements, and
host-portability risks before an Agent Skill is installed or published.

It audits before it explains. It never executes scripts from the skill being
audited.

## Why this exists

An Agent Skill can have valid-looking instructions and still fail after
installation because a file is missing, a path escapes the package, a runtime
is undeclared, or one host discovers it differently from another. Portable
Skill Doctor turns those problems into deterministic findings with evidence,
severity, and a bounded remediation.

| It checks | It deliberately does not do |
| --- | --- |
| `SKILL.md` structure, name, and trigger description | Execute, import, source, build, or test target code |
| Referenced scripts, references, assets, and symlinks | Install dependencies or call external services |
| Absolute, escaping, encoded, and machine-specific paths | Claim that a package is malware-free or safe |
| Runtime, tool, permission, and network assumptions | Rewrite the target without a separate request |
| Codex and GitHub Copilot discovery layouts | Claim compatibility beyond the tested matrix |
| Conservative static execution-risk patterns | Replace sandboxing or human source review |

The auditor emits text, JSON, or SARIF and uses exit codes suitable for CI.

## Preview, then install

Requirements: GitHub CLI 2.90.0 or newer with `gh skill`, plus Python 3.10 or
newer to run the bundled auditor.

Inspect the exact release before installation:

```bash
gh skill preview ProfesseurHaipeng/professeur-ai-skills \
  portable-skill-doctor@v0.1.0
```

Install for Codex at user scope:

```bash
gh skill install ProfesseurHaipeng/professeur-ai-skills \
  portable-skill-doctor@v0.1.0 \
  --agent codex \
  --scope user
```

Install for GitHub Copilot at user scope:

```bash
gh skill install ProfesseurHaipeng/professeur-ai-skills \
  portable-skill-doctor@v0.1.0 \
  --agent github-copilot \
  --scope user
```

GitHub warns that third-party skills are not verified. Preview the tree and
instructions before installing, even when a release is pinned.

### Optional `npx skills` path

```bash
DISABLE_TELEMETRY=1 npx --yes skills add \
  ProfesseurHaipeng/professeur-ai-skills \
  --skill portable-skill-doctor
```

This alternative uses the third-party
[`skills` CLI](https://github.com/vercel-labs/skills). Review its installer and
telemetry documentation before use.

See the exact environments and bounded results in
[Tested compatibility](docs/TESTED_COMPATIBILITY.md).

## Use it

Invoke the installed skill:

```text
Use $portable-skill-doctor to audit ./skills/example-skill for Codex and
GitHub Copilot. Run the audit first and never execute the target's scripts.
```

Or run the deterministic auditor directly:

```bash
python3 skills/portable-skill-doctor/scripts/skill_doctor.py \
  audit ./skills/example-skill \
  --target all \
  --format text \
  --strict
```

Choose `--target codex`, `--target copilot`, or `--target all`. Choose
`--format text`, `--format json`, or `--format sarif`.

## Example finding set

```text
portable-skill-doctor 0.1.0
Target: all | Strict: yes | Result: FAIL
Findings: 2 error, 1 warning, 0 info
ERROR   PSD-PATH-003 SKILL.md:12 - Parent traversal is not allowed.
ERROR   PSD-RESOURCE-001 SKILL.md:11 - Referenced resource does not exist.
WARNING PSD-SCRIPT-001 SKILL.md - Bundled scripts have no declared runtime.
```

Finding IDs, severities, paths, and line numbers are stable machine evidence.
The report is not a verdict about whether a target is trustworthy.

## Network and permissions

| Operation | Network | Target-skill access | Writes |
| --- | --- | --- | --- |
| Bundled static audit | Not required | Read-only | Standard output only unless redirected |
| Manual evidence review | Not required | Read-only text inspection | None |
| `gh skill preview` | Required for remote source | Read-only remote fetch | None to the skill directory |
| `gh skill install` | Required for remote source | Installer-controlled | Selected agent skill directory and install metadata |
| `npx skills add` | Required for remote source | Installer-controlled | Selected agent skill directory and installer metadata |

The audit workflow does not need credentials and should not be given any. It
must not run, import, source, install, build, or test code from the target skill.

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | No errors; in strict mode, no warnings |
| `1` | Findings failed the selected policy |
| `2` | Input or audit failure |
| `3` | Command-line usage error |

Preserve the exit status and machine output in automation.

## Limits

- Static rules can produce false positives and false negatives.
- The auditor cannot prove that code is benign, correct, or sandbox-safe.
- It does not validate credentials, remote URLs, external services, or live
  model behavior.
- A structurally portable package can still behave differently across host and
  version combinations.
- Compatibility is claimed only for the named environments in the test record.

## Project records

- [Public scope](docs/PUBLIC_SCOPE.md)
- [Tested compatibility](docs/TESTED_COMPATIBILITY.md)
- [Inspiration and provenance](docs/INSPIRATION_AND_PROVENANCE.md)
- [Security policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)

If the auditor misses a reproducible structural or portability failure, use the
[Portable Skill case form](https://github.com/ProfesseurHaipeng/professeur-ai-skills/issues/new?template=portable-skill-case.yml).
If the example is not minimal yet, reduce it with the community in the
[broken synthetic Skill challenge](https://github.com/ProfesseurHaipeng/professeur-ai-skills/discussions/4).
