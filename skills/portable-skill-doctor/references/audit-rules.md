# Audit rules

Use these categories to interpret the bundled auditor. The script output is the
source of truth for rule IDs, severities, paths, and line numbers.

## 1. Structure and specification

Check that the target is one skill directory, not an arbitrary repository or a
collection of skills. Inspect:

- a readable `SKILL.md` with valid YAML frontmatter;
- a valid `name` and a useful trigger-oriented `description`;
- agreement between the declared name and directory name where the selected
  host or open specification requires it;
- frontmatter fields that are valid for the selected host;
- a focused instruction body with explicit inputs, actions, and outputs.

Treat an open-standard violation as a specification finding. Treat a field that
is valid in one host but ignored or interpreted differently in another as a
portability finding.

## 2. Resource integrity

Check every path referenced by `SKILL.md`, including scripts, references, and
assets. Flag:

- missing or case-mismatched paths;
- absolute machine-specific paths;
- references that escape the skill directory;
- symlinks whose targets cannot be packaged safely;
- required resources that are present but never referenced;
- instructions that depend on undeclared files, tools, environment variables,
  services, or network access.

Do not load a referenced executable as a module. Static text inspection is
enough for evidence review.

## 3. Static execution risk

The presence of executable content is not automatically a defect. Identify
whether instructions or scripts can:

- execute shell commands or dynamic code;
- install packages or trigger lifecycle hooks;
- read credentials, broad environment state, or files outside user scope;
- write outside an explicit output directory;
- delete, overwrite, publish, upload, or make network requests;
- conceal behavior through generated commands, encoded payloads, or indirect
  execution.

Report suspicious behavior as static evidence, not as a malware verdict. Never
run the target to decide whether a warning is real.

## 4. Host portability

For `--target codex`, examine Codex discovery, metadata, tool, and path
assumptions. For `--target copilot`, examine GitHub Copilot discovery,
frontmatter, permission, and path assumptions. For `--target all`, report each
host independently before giving a shared conclusion.

Flag claims such as "works everywhere" when the repository provides no
host-and-version-specific installation or forward-test evidence. A portable
layout is evidence of package structure, not evidence of runtime behavior.

## 5. Evidence standard

Every human-facing finding must preserve:

- the auditor's rule ID and severity;
- the smallest relevant file path and line, when supplied;
- the observed condition;
- why it matters for the selected host;
- one bounded remediation.

Do not upgrade a heuristic warning into a confirmed exploit. Do not downgrade a
specification error because a different host may tolerate it.

## Normative references

- [Agent Skills specification](https://agentskills.io/specification)
- [OpenAI: Build skills](https://learn.chatgpt.com/docs/build-skills)
- [GitHub: About agent skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills)
- [GitHub: Adding agent skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills)
