---
name: iching-research
license: MIT
description: Research the I Ching and Zhouyi as textual and symbolic systems with reproducible hexagram casting, primary-text provenance, competing interpretations, and explicit uncertainty. Use when Codex is asked to explain, compare, cast, or design an educational workflow for 易经、周易、六十四卦、爻辞 or related traditions.
---

# I Ching Research

Treat this as humanities research plus transparent line-generation arithmetic, not supernatural prediction. Separate (1) cast inputs and reproducible computation, (2) historical/textual evidence, and (3) symbolic reflection.

## Runtime: Python 3.10+

The bundled helper requires Python 3.10+ and only the Python standard library. It is deterministic and does not make network requests.

Never provide medical, legal, financial, safety, fertility, employment, or major-life decisions from a divination result. For high-stakes questions, convert the request into decision criteria, evidence gathering, and professional advice.

## Workflow

1. Clarify the question and whether the user supplied a cast. Do not silently mix Zhouyi line interpretation, later commentary, and folk fortune-telling.
2. Record coin method, seed, line order, changing-line rule, edition, and translation.
3. Compute only what is mechanically defined. Show six line values, trigram decomposition, changing lines, and relating hexagram step by step.
4. Establish provenance. Prefer the Zhouyi text and dated commentaries; label later interpretive layers. Read [sources.md](references/sources.md).
5. Give a layered reading: textual observation, historical interpretation, symbolic reflection, alternative readings, and uncertainty. Ask the user to test reflections against lived evidence.
6. End with falsifiable next actions: what to verify, what would change the interpretation, and what is outside the method's scope.

## Tools and references

Use Python 3.10+ standard library only. Run `python3 scripts/transparent_cast.py --seed <visible-seed> --method three-coins` for an inspectable six-line demonstration. Read [knowledge-model.md](references/knowledge-model.md) before designing data or UI, and [reading-grid.md](references/reading-grid.md) before producing an interpretation.

## Method notes

### I Ching / Zhouyi

State whether the task is textual exegesis, a simulated cast, or analysis of a user-supplied cast. For a simulated cast, label the seed and procedure; never pretend to have physically tossed coins. Keep changing lines, relating hexagram, judgment, image, and line text distinct. Compare interpretations instead of collapsing them into one answer.

## Quality questions

- Could another researcher reproduce the same input normalization and computation?
- Which claim comes from a primary text, which from a commentator, and which is synthesis?
- What plausible alternative school would read this differently?
- Is the output being used as reflection, entertainment, or a high-stakes decision proxy?

Do not use “scientific,” “proven,” “accurate prediction,” or “success rate” for symbolic interpretations. If asked whether the method works, discuss construct validity, reproducibility, confirmation bias, cultural meaning, and the difference between useful reflection and predictive validity. Never invent a percentage.
