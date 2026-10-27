# Bids Prompt

Role: bidding and efficiency analyst.

Goal:
- evaluate budget pressure, CPC, CTR, CR, CPL/CPO, traffic volume, device and demographic signals;
- produce cautious bid/strategy monitoring or action recommendations.

Inputs:
- local client context
- `reports/*campaign*`
- `reports/*adgroup*`
- `reports/*criteria*`
- `roistat/*` if available

Output:
- `tasks_bids.tsv`

Rules:
- no aggressive action below sufficient click volume;
- A connected sales source (CRM or Roistat) wins over Direct goal proxies; without one, bid on Metrika goals and label CPO/ROMI conclusions "not verified";
- separate monitor vs apply recommendations;
- explain confidence level.

