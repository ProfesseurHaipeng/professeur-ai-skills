# BaZi data model

```json
{
  "civil_time": "YYYY-MM-DDThh:mm:ss",
  "timezone": "+08:00",
  "location": {"city":"", "country":"", "latitude":null, "longitude":null},
  "conventions": {"year_boundary":"立春", "month_boundary":"solar-terms", "day_boundary":"midnight", "true_solar_time":false},
  "source": {"calendar":"", "ephemeris":"", "accessed":""},
  "computed": {"year":null, "month":null, "day":null, "hour":null},
  "unknowns": []
}
```

Each computed pillar needs a provenance pointer and boundary decision. Do not serialize school-specific “用神,” “喜忌,” or personality claims as objective fields; keep them under a named interpretation with citations.
