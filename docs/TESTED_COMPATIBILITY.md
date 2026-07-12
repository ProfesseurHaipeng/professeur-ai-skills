# Tested compatibility

This record separates source-distribution checks from live agent behavior. A
successful install proves that the selected tree was fetched and placed in the
expected host directory. It does not prove every prompt, model, permission, or
runtime combination.

## Release

- Date: 2026-07-12
- Release tag: `v0.1.0`
- Release commit: `cbe33351f47dae0dd36a9acd71c903ea90935cc7`
- Pre-release distribution commit: `8e3bf4ee3c6b0c81d62f5a0686b154e21122f8cd`

### Environment

| Component | Tested value |
| --- | --- |
| Operating system | macOS 27.0, Apple silicon |
| Python | 3.14.4 locally; 3.10, 3.12, and 3.13 on Ubuntu CI |
| GitHub CLI | 2.96.0 |
| Node.js | 24.14.1 |
| `skills` CLI | 1.5.16 |

### Distribution matrix

| Path | Exact ref | Result | Evidence boundary |
| --- | --- | --- | --- |
| Anonymous `gh skill preview` from the public remote | `8e3bf4e` | Pass | The remote tree and instructions rendered without installation or GitHub authentication |
| Anonymous `gh skill install --agent codex --scope user` in a temporary home | `8e3bf4e` | Pass | Installed to `~/.codex/skills/portable-skill-doctor`; strict self-audit passed with one informational host-path note |
| Anonymous `gh skill install --agent github-copilot --scope user` in a temporary home | `8e3bf4e` | Pass | Installed to `~/.copilot/skills/portable-skill-doctor`; strict self-audit passed with no findings |
| Local `gh skill publish --dry-run` | `8e3bf4e` | Pass with one recommendation | Required Skill metadata validated; the CLI recommends a Skill-level license field while the repository uses an MIT root license |
| Public `npx skills add` discovery and Codex project install | `main` at `8e3bf4e` | Pass | The CLI discovered and copied `portable-skill-doctor` to `.agents/skills`; strict self-audit passed |
| Ubuntu GitHub Actions | `8e3bf4e` | Pass | Unit, adversarial, public-scope, history, compile, and distribution-contract jobs passed |
| Anonymous Codex and GitHub Copilot clean installs | `v0.1.0` at `cbe3335` | Pass | Both pinned installs passed strict self-audit; installed auditor SHA-256 was `6204911da57f71c0642d49cf2076e8c552bf7807b12473808db8093c517eb390` |
| Tag-triggered Release audit | `v0.1.0` at `cbe3335` | Pass | Tests, scope gate, Skill contract, deterministic archive build, archive inspection, and checksum completed on Ubuntu |

Both temporary `gh skill` installations contained the same five Skill files.
The installed auditor script was byte-identical across the Codex and Copilot
destinations. Temporary homes and the `npx skills` project fixture were deleted
after verification.

## Behavior exercised

- 48 unit, adversarial, path, archive, and repository-policy tests;
- strict self-audit of the source Skill for both target hosts;
- a clean synthetic Skill that passes strict audit;
- an unsafe synthetic Skill that fails on name mismatch, parent traversal,
  missing resources, weak trigger metadata, and undeclared runtime assumptions;
- a marker check confirming that a target script was not executed during the
  unsafe audit;
- deterministic source-archive inspection without extraction.

## Not established by this record

- exhaustive Codex or GitHub Copilot runtime compatibility;
- implicit invocation quality across models and prompts;
- behavior on Windows or Linux desktop hosts;
- absence of every malicious or unsafe pattern;
- behavior of future installer or host versions not listed above.

The release notes also record the tag-level verification performed after
publication. Re-run the matrix whenever the Skill code, installer behavior, or
documented discovery paths change.
