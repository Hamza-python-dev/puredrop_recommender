# PureDrop Dairy: Product Recommender

Groundwork for a product recommender for PureDrop Dairy, a dairy with daily
milk delivery.

## Task 1: Interaction data and metrics

This task builds the interaction data, checks it against rules, and calculates
metrics. The question it answers: **which customers only buy milk, and which
extra products could we suggest to them?**

## Important notes

- The data is **made up**: 20 random customers over 28 days. The numbers show
  that the pipeline works, not real PureDrop behaviour.
- An AI assistant helped me build this project. I reviewed the code and can
  explain it.

## Setup and run (Windows PowerShell, from the project root)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/generate_data.py   # creates the 3 CSV files in data/
python -m src.validate        # checks interactions.csv against the rules
python -m src.metrics         # calculates metrics, saves data/metrics.json
python -m pytest -v           # runs the tests
```

Expected: `python -m src.validate` prints
`OK: 614 rows checked, all rules passed` and pytest prints `2 passed`.

## What the data is

| File | What it holds |
|---|---|
| `data/products.csv` | 8 dairy products: id, name, category, price in PKR |
| `data/customers.csv` | 20 customers: delivery plan (daily, alternate_days, weekly), preferred slot, staple milk product, staple quantity |
| `data/interactions.csv` | 614 rows. One row = one delivery event: customer_id, product_id, date, slot, quantity, status, amount_pkr |

Status is `delivered`, `skipped` (one missed day) or `paused` (a block of
consecutive days). Skipped and paused rows have quantity 0 and an empty amount.

## What `python -m src.validate` checks

"All rules passed" means every one of these held for `data/interactions.csv`.
If a rule fails, the program prints which rule and which rows, then stops.

**File and columns**
- The file exists, is not empty, and has data rows (not just a header).
- All 7 columns are present: customer_id, product_id, date, slot, quantity,
  status, amount_pkr.

**Values in each row**
- `status` is one of `delivered`, `skipped`, `paused`.
- `slot` is one of `morning`, `evening`.
- `date` is a real date in the format `YYYY-MM-DD`.
- `quantity` is a number that is 0 or more.
- A `delivered` row has quantity 1 or more and an amount in PKR.
- A `skipped` or `paused` row has quantity 0 and an empty amount.
- No duplicate rows for the same customer, product and date.

**Checks against `data/customers.csv`**
- Every customer in interactions exists in customers.csv.
- Each customer has at most one pause, with no gaps inside it, and nothing but
  paused rows inside it.
- A customer on `alternate_days` gets their staple milk every second day,
  counted from their own first date.
- A customer on `weekly` gets their staple milk on Friday.

## Metrics (data/metrics.json)

`metrics.json` is a text file holding the results below as a dictionary. The
program creates it.

| Metric | Value | Meaning |
|---|---|---|
| Interactions / purchases | 614 / 587 | all rows / delivered rows only |
| Purchases per customer | mean 29.35, median 29.5 | delivered rows per customer |
| Repeat