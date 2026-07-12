# Convention matrix

| Decision | Common alternatives | Required record |
| --- | --- | --- |
| Year boundary | 立春 / lunar New Year / Gregorian year | source and exact transition time |
| Month boundary | solar terms / lunar month | term name, ephemeris, timezone |
| Day boundary | midnight / 子初 | clock rule and local date |
| Location | civil timezone / true solar time | coordinates, offset, adjustment |
| Missing time | unknown / interval sensitivity | fields that cannot be computed |

Never silently mix columns. A chart that changes under the chosen boundary must show both outcomes and the reason.
