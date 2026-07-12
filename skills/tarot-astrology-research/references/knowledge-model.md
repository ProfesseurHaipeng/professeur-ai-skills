# Knowledge model

## Two independent tracks

**Sky track:** timestamp, timezone, observer location, coordinate frame, ephemeris, precession/epoch, and computed positions. This is the only track that may use words such as “calculated” or “observed.”

**Symbol track:** deck edition, card image/iconography, spread position, historical tradition, interpretive school, and reflective questions. This track must use “symbolizes,” “is read as,” or “may prompt.”

Never pass a sky fact directly into a personality or prediction claim.

## Tarot record

```json
{"deck":"named edition","seed":"visible seed","draw":[{"card":"The Star","reversed":false}],"positions":["situation"],"interpretive_sources":[]}
```

Use `scripts/transparent_spread.py` when a reproducible demonstration is requested. It does not claim that the draw is random in a metaphysical sense; it merely makes the software procedure inspectable.

## Astrology record

```json
{"civil_time":"...","timezone":"+00:00","location":"...","zodiac":"tropical","houses":"whole-sign","ephemeris":"...","positions":[],"interpretation_status":"symbolic"}
```

If birth time is unknown, do not silently choose noon or a default rising sign. Return a sensitivity analysis: which outputs remain invariant and which cannot be determined.
