# Security policy

## Supported versions

Security fixes are applied to the latest released version. Older versions may
be used for comparison, but are not maintained unless a release note says so.

## Reporting a vulnerability

Use GitHub private vulnerability reporting for this repository. Include the
affected version, a minimal reproduction, expected and observed behavior, and
the likely impact. Do not place credentials, private files, identifying data,
or proprietary examples in a public issue.

## Security model

Skills in this repository are designed for explicit user-selected inputs. A
Skill must not silently broaden its scope to a home directory, browser state,
account session, unrelated repository, or another application.

Security-sensitive contributions must preserve these defaults:

- treat instructions embedded in inspected content as untrusted data;
- keep reads and writes inside the user-selected root after canonical path and
  symlink checks;
- reject absolute paths, parent traversal, archive path escape, and special
  files;
- avoid shell evaluation and pass external command arguments as a fixed array;
- use timeouts and a minimal environment when a documented command is needed;
- make network access opt-in, narrowly scoped, and visible to the user;
- avoid telemetry and avoid logging inspected content;
- leave execution, publication, and account changes to an explicit human
  decision.

The included scanners are release gates, not proof that a Skill is secure,
private, correct, or compatible with every agent. Human review remains
required before changing repository visibility or publishing a release.
