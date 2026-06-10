# Map Theme Chain

Use this after announcement collection or when a human/agent has prepared explicit theme evidence.

```bash
python skills/a-share-investment-research/scripts/theme_chain.py data/raw/300750.SZ/announcements.json
```

With explicit theme evidence:

```bash
python skills/a-share-investment-research/scripts/theme_chain.py data/raw/300750.SZ/announcements.json --theme-input data/raw/300750.SZ/theme_input.json
```

Output:

```text
data/raw/300750.SZ/theme_chain.json
```

Theme evidence must map `theme -> chain segment -> company exposure -> profit transmission -> risks`. Keyword-only matches are low-confidence evidence and cannot alone justify `pilot_build` or `add`.
