# Map Theme Chain

Use this after announcement collection or when a human/agent has prepared explicit theme evidence. The script uses a layer-first workflow: rank scarce industry-chain layers before ranking companies or funds.

```bash
python skills/a-share-investment-research/scripts/theme_chain.py data/raw/300750.SZ/announcements.json
```

With explicit theme evidence:

```bash
python skills/a-share-investment-research/scripts/theme_chain.py data/raw/300750.SZ/announcements.json --theme-input data/raw/300750.SZ/theme_input.json
```

Template:

```bash
skills/a-share-investment-research/templates/theme_input.example.json
```

Output:

```text
data/raw/300750.SZ/theme_chain.json
```

Theme evidence must map `theme -> system change -> scarce layer -> candidate universe -> company exposure -> profit transmission -> risks`. Keyword-only matches are low-confidence evidence and cannot alone justify `pilot_build` or `add`.
