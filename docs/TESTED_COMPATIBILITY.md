# Tested compatibility

This record separates source-distribution checks from live agent behavior. A
successful install proves that the selected tree was fetched and placed in the
expected host directory. It does not prove every prompt, model, permission, or
runtime combination.

## Release candidate

Date: 2026-07-12  
Source commit: `04e8f7abe498b5e1cc728bb5c2f3835c1b5d4401`

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
| `gh skill preview` from the private remote | `04e8f7a` | Pass | The remote tree and instructions rendered without installation |
| `gh skill install --agent codex --scope user` in a temporary home | `04e8f7a` | Pass | Installed to `~/.codex/skills/portable-skill-doctor`; strict self-audit passed with one informational host-path note |
| `gh skill install --agent github-copilot --scope user` in a temporary home | `04e8f7a` | Pass | Installed to `~/.copilot/skills/portable-skill-doctor`; strict self-audit passed with no findings |
| Local `gh skill publish --dry-run` | `04e8f7a` | Pass with one recommendation | Required Skill metadata validated; the CLI recommends a Skill-level license field while the repository uses an MIT root license |
| Local `npx skills add . --list` discovery | pre-release tree | Pass | The CLI discovered `portable-skill-doctor`; this did not install from the public GitHub release |
| Ubuntu GitHub Actions | `04e8f7a` | Pass | Unit, adversarial, public-scope, history, compile, and distribution-contract jobs passed |

Both temporary remote installations contained the same five Skill files. The
installed auditor script was byte-identical across the Codex and Copilot
destinations. The temporary home directories were deleted after verification.

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
- release-tag installation, until the public `v0.1.0` tag is created and the
  same clean-install matrix is rerun against that tag.

The release notes record the tag-level verification performed after
publication. Re-run the matrix whenever the Skill code, installer behavior, or
documented discovery paths change.
