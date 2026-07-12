# Inspiration and provenance

Portable Skill Doctor was designed from public specifications, official host
documentation, and documented portability requirements. Its code, rule names,
report structure, prose, examples, and tests are intended to be original to this
repository.

## Sources used

| Source | What informed this project | What was not copied |
| --- | --- | --- |
| [Agent Skills specification](https://agentskills.io/specification) and [source repository](https://github.com/agentskills/agentskills) | Required skill structure, frontmatter constraints, optional resource directories, progressive disclosure, and validation concepts | Specification prose, reference implementation code, fixtures, rule names, and examples |
| [OpenAI: Build skills](https://learn.chatgpt.com/docs/build-skills) and [OpenAI Skills catalog](https://github.com/openai/skills) | Codex discovery locations, concise trigger descriptions, progressive disclosure, and the role of `agents/openai.yaml` | Skill instructions, scripts, assets, prompts, and per-skill implementation details; licenses are evaluated per skill rather than assumed for the catalog |
| [GitHub: About agent skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills), [Adding agent skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills), and [`gh skill publish`](https://cli.github.com/manual/gh_skill_publish) | Copilot discovery locations, description-based activation, preview/install/publish interfaces, and warnings around executable permissions | Documentation prose, examples, CLI implementation, and GitHub-owned assets |
| [Vercel `skills` CLI](https://github.com/vercel-labs/skills) | Syntax for the optional `npx skills add` distribution path | Installer code, compatibility tables, README prose, telemetry implementation, and compatibility claims |

The Agent Skills specification repository identifies separate licensing for
code and documentation. This project paraphrases the public rules and links to
the source rather than copying specification text.

## Requirements evidence

The design also responds to publicly documented ecosystem problems:

- portability labels can exceed what current validation proves:
  [anthropics/skills#1156](https://github.com/anthropics/skills/issues/1156);
- missing tool requirements can fail silently:
  [anthropics/skills#1154](https://github.com/anthropics/skills/issues/1154);
- discovery paths and semantics differ across hosts:
  [anthropics/skills discussion #166](https://github.com/anthropics/skills/discussions/166).

These items are treated as problem evidence, not as specifications or sources
of implementation text.

Repository-owner requirements recorded in July 2026 additionally established
the following non-negotiable behavior:

- audit before explanation;
- never execute scripts from the audited skill;
- keep target access read-only;
- produce evidence-backed, bounded compatibility findings;
- publish only this focused skill in the current release.

## Independent implementation statement

No third-party validator code, prompt text, finding identifiers, scoring model,
report template, example, or visual asset has been copied into this project.
External projects may be used later for comparative testing only. Any future
reuse must record the exact source file, revision, license, attribution,
modifications, and reason before the reused material is committed.

The words "portable" and "audit" describe the intended workflow. They do not
claim universal host support, security certification, or runtime verification.

## Updating this record

Update this file whenever a new external source materially changes the public
workflow. Documentation links alone are not a substitute for checking the
source license and recording whether code or prose was reused.
