# Knowledge model

## Layers

| Layer | Store | Allowed claim |
| --- | --- | --- |
| Text | chapter, line, Chinese text, edition | “The passage says…” |
| Calendar | timestamp, timezone, solar-term source, convention | “Under this convention, the label is…” |
| School | commentator, period, interpretive rule | “This school reads it as…” |
| Reflection | user question, themes, alternatives | “This may prompt you to consider…” |
| Evaluation | prediction target, blinded protocol, outcome | “This test measured…” |

Never collapse these layers into a single “answer” field. Keep the raw input and convention next to every derived value.

## I Ching data shape

```json
{
  "hexagram": 1,
  "lines_bottom_to_top": [{"value": 7, "changing": false}],
  "source": {"work": "Zhouyi", "chapter": "乾", "edition": "..."},
  "reading": {"textual": "", "historical": "", "reflective": ""}
}
```

The six-line sequence must be explicit. Do not infer a relating hexagram unless changing lines are recorded. Do not generate a cast without a user-visible seed and method; use `../scripts/transparent_cast.py` for a reproducible demonstration.
