# Report contract

Explain only after the bundled auditor has produced a result. Treat its output
as primary evidence and preserve machine-readable artifacts byte-for-byte when
the user requests them.

## Human report order

1. **Result** — target, selected host, strict mode, command outcome, and finding
   counts.
2. **Findings** — highest severity first; preserve original order within a
   severity.
3. **Portability** — separate Codex and GitHub Copilot results when both were
   audited.
4. **Limits** — uninspected evidence, unresolved paths, and static-analysis
   limits.

For each finding, report:

```text
[severity] rule-id — short title
Evidence: relative/path:line and the observed condition
Impact: why this matters for the selected host
Remediation: one concrete, bounded change
```

Do not quote large portions of the target. Use the smallest excerpt needed to
identify the condition.

## Formats

- `text`: return the auditor's text report, followed by a concise explanation
  only if the user asked for one.
- `json`: return valid JSON unchanged. Put commentary in a separate prose block,
  never inside or around the JSON code fence.
- `sarif`: save or return the SARIF document unchanged. Do not rewrite rule IDs,
  levels, locations, or fingerprints.

Do not synthesize a JSON or SARIF pass when the auditor failed to run.

## Verdict language

Use bounded language:

- "The static audit found ..."
- "No findings under the current static rules."
- "This pattern may reduce portability on ..."
- "Runtime behavior remains unverified."

Avoid unprovable language:

- "safe" or "malware-free";
- "fully compatible" or "works everywhere";
- "verified" without the exact test, host, version, and result;
- "clean" when files or references were not inspected.

## Failure handling

If the command cannot complete, report:

- the command stage that failed;
- the available error output;
- whether any partial findings were produced;
- the evidence that remains unaudited.

Do not execute the target skill, install its dependencies, or weaken strict mode
to manufacture a successful report.
