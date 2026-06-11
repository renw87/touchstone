# Theme Chain Scan

Use this when the user starts from a hot theme and wants to find which industry-chain layers, stocks, or fund directions deserve research priority.

Core rule:

- rank layers before companies;
- identify scarce layers before listing tickers;
- use strong A-share evidence before upgrading confidence;
- output research priority, not buy/sell instructions.

Minimal run:

```bash
python skills/a-share-investment-research/scripts/theme_chain.py data/raw/300750.SZ/announcements.json
```

With explicit layer-first inputs:

```bash
python skills/a-share-investment-research/scripts/theme_chain.py data/raw/300750.SZ/announcements.json --theme-input skills/a-share-investment-research/templates/theme_input.example.json
```

Output:

```text
data/raw/300750.SZ/theme_chain.json
```

Use `skills/a-share-investment-research/references/chain-bottleneck-research.md` for the workflow and evidence ladder.
