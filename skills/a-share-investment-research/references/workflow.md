# Dynamic Research Workflow

## 0. User Profile

Capture:

- horizon: short, swing, medium, long.
- risk style: conservative, balanced, aggressive.
- max single-stock weight, max industry weight, max loss per trade.
- current position and cash.
- blocked areas: ST, low liquidity, loss-making companies, high pledge risk, etc.

## 1. Stock Intake

Build profile:

- code, exchange, board, industry, main business, list date.
- market cap, float cap, daily amount, turnover.
- ST/suspension/delisting/regulatory/unlock/pledge flags.

If a no-trade gate is active, stop and write a risk report.

## 2. Evidence Collection

Collect in priority:

1. Prices and adjusted prices.
2. Financial statements and key indicators.
3. Announcements and regulatory filings.
4. Industry and peers.
5. Policy, news, and themes.
6. Flow data: amount, turnover, Dragon-Tiger, financing.
7. Market environment and industry index.

Keep source URL, source name, timestamp, and raw values.

## 3. Core Analysis

Run:

- Fundamental quality.
- Valuation.
- Theme and industry-chain transmission.
- Technical setup.
- Support/resistance.
- Capital flow.
- Bear case.

Each block must produce score, evidence, doubt, and invalidation trigger.

## 4. Convert Thesis To Rules

Examples:

- close breaks 60-day high and amount > 1.5x 20-day average.
- pullback holds 20-day MA for 2 closes and industry index outperforms CSI 300.
- earnings forecast revision plus valuation below 5-year median.

The rule must be testable and free of future data.

## 5. Backtest

Report:

- sample range.
- adjustment mode.
- entry/exit rules.
- cost, tax, slippage, T+1, price-limit assumption.
- trade count, win rate, profit factor, max drawdown.
- failed samples.

If backtest quality is weak, cap the signal at `watch`.

## 6. Signal Generation

The orchestrator combines:

- research layer: fundamentals, valuation, theme, risk.
- execution layer: technical setup, support/resistance, flow.
- risk layer: position size, stop, take-profit, backtest, market regime.

Output a conditional signal only.

## 7. Review Cadence

- Pre-market: announcements, policy, overnight events, trigger levels.
- Intraday: price/amount/support/stop/take-profit triggers only.
- Post-market: K-line, flow, industry relative strength, signal result.
- Weekly: industry, valuation, backtest parameters.
- After earnings: full fundamental, valuation, bear-case refresh.

Each review answers:

- What evidence changed?
- Did the thesis change?
- Did any trigger fire or fail?
- Is risk still inside budget?
