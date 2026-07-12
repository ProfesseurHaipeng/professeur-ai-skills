---
name: western-astrology-research
license: MIT
description: Research Western astrology as a historical symbolic system while keeping astronomy, coordinate systems, ephemerides, and uncertainty technically explicit. Use when Codex is asked about zodiac signs, natal charts, planets, houses, transits, precession, constellations, or astrology versus astronomy.
---

# Western Astrology Research

Separate the sky layer from the meaning layer. Astronomy can calculate positions from an ephemeris and coordinate convention; astrology assigns symbolic meaning that is not established causal science. Never turn a chart into medical, legal, financial, employment, fertility, or relationship certainty.

## Workflow

1. Normalize civil timestamp, UTC offset, observer location, and time precision.
2. State zodiac convention (tropical or sidereal), epoch, ayanamsa if relevant, house system, coordinate frame, and ephemeris.
3. Compute or cite only observable/calculable sky facts. If the ephemeris is unavailable, return an explicit unknown instead of inventing positions.
4. Explain the historical tradition behind a symbolic claim and distinguish sign, constellation, planet, house, aspect, and mythology.
5. Give multiple interpretive readings and identify what would challenge each one. Unknown birth time requires sensitivity analysis rather than a guessed ascendant.
6. For “does astrology work?” separate subjective reflection from predictive validity and propose a blinded, base-rate comparison.

## Output contract

Return `inputs`, `coordinate_convention`, `sky_facts`, `symbolic_tradition`, `uncertainties`, `alternative_readings`, and `reality_checks`. Never collapse them into a personality score or deterministic forecast.

Read [knowledge-model.md](references/knowledge-model.md), [astronomy-boundary.md](references/astronomy-boundary.md), and [sources.md](references/sources.md) before answering.
