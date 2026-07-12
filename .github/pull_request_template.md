## Scope

- What single behavior or document does this change improve?
- Which synthetic case demonstrates the change?

## Evidence

- [ ] `python3 -m unittest discover -s tests -v`
- [ ] `python3 scripts/check_public_scope.py .`
- [ ] `python3 -m compileall -q scripts skills tests`
- [ ] No target Skill code was executed during audit testing.
- [ ] New public material is original, synthetic, or attribution is recorded.

## Limits

State what this change does not establish, including host or version boundaries.
