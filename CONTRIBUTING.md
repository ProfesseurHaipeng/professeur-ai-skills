# Contributing

Contributions should improve a reusable, general-purpose AI Skill without
bringing private project material into the repository.

## Public scope

- Start from original, synthetic, or explicitly licensed material.
- Keep private product domains, operational records, commercial work,
  identifying data, credentials, and account history outside the repository.
- Do not add exact private project names to public deny rules or fixtures.
- Keep examples generic and synthetic. Anonymization is not a substitute for
  permission when the underlying material is private.

Use the repository's issue forms for a minimal synthetic portability case or a
new deterministic rule proposal. Security vulnerabilities belong in a private
security advisory, not a public issue.

## Skill quality

A contribution should add more than a reusable paragraph. Define when the
Skill triggers, its input and output contract, its workflow, stop conditions,
failure behavior, and a forward-evaluation case that demonstrates a material
benefit over an ordinary prompt.

Do not claim broad compatibility, privacy, safety, or offline behavior without
a reproducible test for the exact claim. State tested versions and limitations.

## Provenance and licensing

Do not copy code, prose, prompts, templates, or assets from installed Skills,
private repositories, websites, or other projects unless their license permits
the intended use. Update `THIRD_PARTY_NOTICES.md` before adding adapted
material, including the exact upstream revision and affected files.

## Local checks

Run from the repository root:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/check_public_scope.py .
python3 -m compileall -q scripts tests
```

For a release archive, run:

```bash
python3 scripts/audit_release_archive.py path/to/source.zip
```

Every error must be fixed. A passing scanner remains a structural check and
does not replace review of privacy, safety, or licensing claims.
