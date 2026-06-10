---
name: trap-detector
description: Use when checking A-share promotion, pump-and-dump, scam, paid group, "teacher", "inside information", "guaranteed profit", 小红书/抖音/微信群 recommendation, or suspicious stock hype risk. 输出杀猪盘/诱导接盘风险扫描，不做买卖建议。
metadata:
  short-description: A 股推广诱导和杀猪盘风险扫描
---

# Trap Detector

Use this before any trade-level signal when the user's source is social media, a private group, a "teacher", a friend recommendation, or an insider rumor.

## Signals

Check each signal as `hit`, `not_hit`, or `insufficient_data`:

1. Many low-quality accounts recommending the same stock.
2. Template-like promotion language.
3. Paid group, VIP room, livestream, or teacher funnel.
4. Fundamentals disconnected from sudden popularity.
5. Price already pumped before recommendation wave.
6. "Stock god" or teacher persona marketing.
7. Cross-platform synchronized recommendation.
8. Rumor, fake report, or unverifiable catalyst.

## Output

Return:

- risk level: green, yellow, orange, red.
- signals table.
- evidence and source links when available.
- user-keyword boost.
- recommendation as a risk warning only.

## Boundary

This skill can downgrade or block `pilot_build` and `add`. It cannot create a buy signal.
