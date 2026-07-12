# Professeur AI Skills

A focused public repository for small, inspectable Agent Skills. The current
public scope contains one skill: **Portable Skill Doctor**, an offline-first
static auditor for Agent Skill structure and portability.

It audits before it explains. It never executes scripts from the skill being
audited.

## Portable Skill Doctor

`portable-skill-doctor` checks a target skill for:

- Agent Skills structure and frontmatter problems;
- broken, escaping, or machine-specific resource paths;
- undeclared runtime, tool, permission, and network assumptions;
- suspicious script behavior through static inspection only;
- portability risks for Codex, GitHub Copilot, or both;
- unsupported compatibility claims.

The auditor can emit text, JSON, or SARIF. A report is evidence from a bounded
static rule set, not a malware verdict or proof that a skill will run correctly.

## Install

### `npx skills`

The intended repository install command is:

```bash
npx skills add ProfesseurHaipeng/professeur-ai-skills \
  --skill portable-skill-doctor
```

**Verification status:** this exact remote command must not be described as
tested until the public repository and release tag exist and a clean install has
been completed against that tag. The command follows the interface documented
by the third-party [`skills` CLI](https://github.com/vercel-labs/skills); it is
not itself evidence of compatibility with a particular agent version.

`npx skills` downloads code and writes to an agent skill directory. Its project
documents anonymous telemetry and the `DISABLE_TELEMETRY=1` opt-out. Preview the
source and understand the installer before using it.

### Manual copy

Clone the repository, inspect the skill, then copy it into the user skill
directory documented by your agent:

```bash
git clone https://github.com/ProfesseurHaipeng/professeur-ai-skills.git
cd professeur-ai-skills
mkdir -p "$HOME/.agents/skills"
cp -R skills/portable-skill-doctor "$HOME/.agents/skills/"
```

Both current Codex and GitHub Copilot documentation describe
`~/.agents/skills` as a user-level discovery location. Host behavior can change;
verify discovery with the exact version you run.

## Minimal use

Invoke the installed skill:

```text
Use $portable-skill-doctor to audit ./skills/example-skill for Codex and
GitHub Copilot. Run the audit first and never execute the target's scripts.
```

Or run the bundled auditor directly from this repository:

```bash
python3 skills/portable-skill-doctor/scripts/skill_doctor.py \
  audit ./skills/example-skill \
  --target all \
  --format text \
  --strict
```

Choose `--target codex`, `--target copilot`, or `--target all`. Choose
`--format text`, `--format json`, or `--format sarif`.

## Network and permissions

| Operation | Network | Target-skill access | Writes |
| --- | --- | --- | --- |
| Bundled static audit | Not required | Read-only | Standard output only unless the caller redirects it |
| Manual evidence review | Not required | Read-only text inspection | None |
| `npx skills add` | Required for remote install | Installer-controlled | Agent skill directory and installer metadata |
| `git clone` + manual copy | Required only for clone | Read source before copying | Chosen skill directory |

The audit workflow does not need credentials and should not be given any. It
must not run, import, source, install, build, or test code from the target skill.

## Output

- **Text** for direct review.
- **JSON** for deterministic downstream processing.
- **SARIF** for compatible code-scanning and CI consumers.

Strict mode is intended for pre-install and pre-publish gates. Preserve the
auditor's exit status and machine output in automation.

## Limits

- Static rules can produce false positives and false negatives.
- The auditor cannot prove that code is benign, correct, or sandbox-safe.
- It does not execute target code, tests, installers, hooks, or dependencies.
- It does not validate external services, credentials, remote URLs, or live
  model behavior.
- Portability analysis is currently scoped to Codex and GitHub Copilot.
- A structurally portable package can still behave differently across host and
  version combinations.
- Compatibility is claimed only after a named host/version and installation
  path have been tested and recorded.

See [public scope](docs/PUBLIC_SCOPE.md) and
[inspiration and provenance](docs/INSPIRATION_AND_PROVENANCE.md).
