---
name: bazi-calendar-research
license: MIT
description: Research BaZi and Chinese calendrical notation as convention-dependent time labeling, with transparent sexagenary-cycle calculations, solar-term boundaries, source provenance, and uncertainty. Use when Codex is asked about 八字、四柱、天干地支、节气、真太阳时 or Chinese calendar algorithms.
---

# BaZi and Calendar Research

Treat BaZi as a historical interpretive system built on calendrical labels. The calendar arithmetic can be reproduced; claims that a chart causes personality, health, wealth, compatibility, or destiny are not established scientific conclusions.

## Runtime: Python 3.10+

The bundled helper requires Python 3.10+ and only the Python standard library. It is deterministic and does not make network requests.

## Workflow

1. Preserve raw civil time, UTC offset, location, and precision. Never replace an unknown birth time with noon without labeling it.
2. Choose and record the convention: year boundary (立春 or lunar New Year), month boundary (solar terms or lunar months), day boundary (midnight or 子初), and true-solar-time adjustment.
3. Compute only the fields supported by verified inputs. Use `scripts/sexagenary.py` for transparent year/month labels; it deliberately does not pretend to calculate a complete chart without an ephemeris and boundary decision.
4. Separate the resulting labels from later school interpretations. Cite the school, commentator, date, and alternative reading.
5. Report sensitivity: which pillars change under another boundary convention, and which observations remain unchanged.
6. Convert reflection into observable questions and actions. Do not issue professional, medical, financial, legal, or irreversible life advice.

## Output contract

Return: `inputs`, `conventions`, `computed_labels`, `unknowns`, `textual_sources`, `school_readings`, `alternative_reading`, and `reflection_questions`. Never return a single “fate score.”

Read [knowledge-model.md](references/knowledge-model.md), [conventions.md](references/conventions.md), and [sources.md](references/sources.md) before calculating or interpreting.
