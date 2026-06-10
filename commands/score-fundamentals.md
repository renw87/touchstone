# Score Fundamentals

Use this after financial data collection.

```bash
python skills/a-share-investment-research/scripts/fundamental_score.py data/raw/300750.SZ/financials.json
```

Output:

```text
data/raw/300750.SZ/fundamental_score.json
```

The score is a compact input for downstream agents. Missing revenue, profit, cash flow, ROE, margin, debt, receivable, inventory, or goodwill fields must remain in `insufficient_data` and must limit signal upgrades.
