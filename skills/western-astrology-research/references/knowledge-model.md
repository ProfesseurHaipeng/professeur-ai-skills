# Chart data model

```json
{
  "civil_time":"YYYY-MM-DDThh:mm:ss",
  "timezone":"+00:00",
  "location":{"latitude":null,"longitude":null},
  "zodiac":"tropical",
  "epoch":"J2000.0",
  "houses":"whole-sign",
  "ephemeris":"named source and version",
  "sky_facts":[],
  "symbolic_reading":{"tradition":"","claims":[],"uncertainties":[]}
}
```

If time is unknown, mark houses and rising sign as unavailable. Do not fill missing data with noon, a default city, or a guessed offset.
