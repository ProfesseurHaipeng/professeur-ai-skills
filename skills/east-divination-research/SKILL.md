---
name: east-divination-research
license: MIT
description: Research I Ching, Chinese calendrical cycles, and BaZi as cultural systems with reproducible calendar calculations, primary-text provenance, competing interpretations, and explicit uncertainty. Use when Codex is asked to explain, compare, calculate, or design an educational workflow for 易经、周易、卦象、干支、四柱八字 or related Chinese divination traditions.
---

# Eastern Divination Research

Treat this as humanities research plus transparent calendar arithmetic, not supernatural prediction. Separate (1) input normalization and reproducible computation, (2) historical/textual evidence, and (3) symbolic reflection.

Never provide medical, legal, financial, safety, fertility, employment, or major-life decisions from a divination result. For high-stakes questions, convert the request into decision criteria, evidence gathering, and professional advice.

## Workflow

1. Clarify the tradition and question. Do not silently mix Zhouyi line interpretation, later commentary, folk fortune-telling, and modern BaZi practice.
2. Normalize inputs. Record timezone, calendar type, location, precision, and whether the date is certain. For BaZi, state the year-boundary convention, solar-term source, true-solar-time rule, and day-boundary rule.
3. Compute only what is mechanically defined. Show sexagenary-cycle mapping, solar-term lookup, or line-generation method step by step. If a reliable calendar/ephemeris source is unavailable, explain the method instead of inventing a pillar.
4. Establish provenance. Prefer the Zhouyi text and dated commentaries; label later interpretive layers. Read [sources.md](references/sources.md).
5. Give a layered reading: textual observation, historical interpretation, symbolic reflection, alternative readings, and uncertainty. Ask the user to test reflections against lived evidence.
6. End with falsifiable next actions: what to verify, what would change the interpretation, and what is outside the method's scope.

## Method notes

### I Ching / Zhouyi

State whether the task is textual exegesis, a simulated cast, or analysis of a user-supplied cast. For a simulated cast, label the seed and procedure; never pretend to have physically tossed coins. Keep changing lines, relating hexagram, judgment, image, and line text distinct. Compare interpretations instead of collapsing them into one answer.

### BaZi / 四柱

Treat the four pillars as labels derived from a stated calendar convention. Do not infer personality, health, lifespan, wealth, or compatibility as fact. Preserve the raw civil timestamp, converted UTC offset, solar-term decision, and convention used at every boundary.

## Quality questions

- Could another researcher reproduce the same input normalization and computation?
- Which claim comes from a primary text, which from a commentator, and which is synthesis?
- What plausible alternative school would read this differently?
- Is the output being used as reflection, entertainment, or a high-stakes decision proxy?

Do not use “scientific,” “proven,” “accurate prediction,” or “success rate” for symbolic interpretations. If asked whether the method works, discuss construct validity, reproducibility, confirmation bias, cultural meaning, and the difference between useful reflection and predictive validity. Never invent a percentage.
