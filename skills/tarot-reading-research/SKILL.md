---
name: tarot-reading-research
license: MIT
description: Research Tarot history, deck iconography, spreads, and reflective readings with reproducible draws, source provenance, competing traditions, and explicit uncertainty. Use when Codex is asked to explain Tarot cards, deck systems, spreads, reversals, readings, or Tarot history.
---

# Tarot Reading Research

Treat Tarot as a historical-cultural interpretive system. Card meanings and readings are symbolic traditions, not established causal predictors. Never make medical, legal, financial, safety, fertility, employment, or relationship decisions for a user.

## Runtime: Python 3.10+

The bundled helper requires Python 3.10+ and only the Python standard library. It is deterministic and does not make network requests.

## Workflow

1. Identify the deck tradition and edition; record creator, date, language, and licence.
2. Separate card imagery, historical claims, divinatory convention, and reflective interpretation.
3. Record the question, spread positions, draw order, orientation rule, and whether the draw was user-supplied or simulated. Never fabricate a random draw.
4. Compare at least two interpretive traditions when meanings differ. Make the reading reflective and conditional, with concrete next questions.
5. Finish with a reality check: what can be observed, what is metaphor, and what evidence would challenge the interpretation.

## Tools and references

Use Python 3.10+ standard library only. Run `python3 scripts/transparent_spread.py --seed <visible-seed> --count 3` for a reproducible 78-card demonstration. Read [knowledge-model.md](references/knowledge-model.md) before designing a chart or spread schema, and [evaluation.md](references/evaluation.md) before discussing accuracy.

## Calculation and interpretation rules

For Tarot, distinguish card imagery, deck-specific iconography, divinatory convention, and reader projection. Use open questions rather than deterministic claims.

## Quality questions

- Is every computed value tied to a stated input, coordinate system, and source?
- Are historical facts separated from modern esoteric practice?
- Does the reading preserve ambiguity instead of manufacturing certainty?
- Could a user mistake the output for professional advice or a scientific result?

If asked about “success rate,” explain that symbolic usefulness and predictive accuracy are different hypotheses. Propose a preregistered, blinded, outcome-based test for empirical evaluation; do not invent a percentage.

Read [sources.md](references/sources.md) when source selection or deck history matters.
