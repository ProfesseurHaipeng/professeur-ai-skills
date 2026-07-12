# Entity and map schema

Use a graph rather than a flat “monster list.” Each record must include:

```json
{
  "id": "stable-slug",
  "name_original": "",
  "name_variants": [],
  "entity_type": "mountain|water|creature|deity|people|plant|object",
  "textual_location": {"chapter":"", "direction":"", "relation":""},
  "source": {"work":"Shanhaijing", "edition":"", "uri":"", "accessed":""},
  "translation_notes": "",
  "confidence": "direct-text|editorial-inference|creative-layer"
}
```

Relations should use controlled verbs: `located-near`, `flows-to`, `guards`, `eats`, `resembles`, `appears-in`, `later-associated-with`. A visual line must carry the relation and confidence in accessible text.

## Map projections

- **Textual topology:** preserve chapter order, directional words, adjacency, and repeated motifs.
- **Comparative hypothesis:** overlay a modern map only when a source proposes an alignment; show it as a separate layer.
- **Creative atlas:** permit vertical world maps, floating Kunlun, or creature migrations, but label the layer “creative adaptation.”

No projection can turn a mythic direction into verified longitude/latitude. Avoid geocoding legendary places as if they were surveyed locations.
