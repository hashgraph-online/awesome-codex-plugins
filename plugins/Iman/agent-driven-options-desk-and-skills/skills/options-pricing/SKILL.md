---
name: options-pricing
description: Price a vanilla American or European option with the optional QuantLib backend. Use when comparing exercise-style prices, not the full chain Greek ladder.
---

# Options Pricing

Use the `option_price` MCP tool. Supply spot, strike, valuation_date, expiry, volatility, rate, dividend_yield, kind (call or put), and exercise_style (american or european). All rates and volatility are decimal fractions. No value is defaulted.

CLI example with synthetic inputs:

```sh
optiondesk price --spot 80 --strike 100 --valuation-date 2026-09-12 --expiry 2027-09-12 --volatility .2 --rate .05 --dividend-yield 0 --kind put --exercise-style american
```

The backend requires `optiondesk-engine[quantlib]`. It runs each request in a fresh process to isolate QuantLib settings. Report price per underlying unit, exercise style, the European reference and the grid-difference warning. Multiply by a contract size only when that size is established.

The model uses constant volatility, Actual/365 Fixed, flat continuously compounded rates and a continuous dividend yield. Discrete dividends and chain-wide American Greeks are not implemented. Do not combine this price with the existing European Greek ladder without identifying the model difference.

Research software, not investment advice. See DISCLAIMER.md.
