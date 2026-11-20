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
`OK: 614 rows checked, all rules passed.` and pytest prints `2 passed`.

## What the data is

| File | What it holds |
|---|---|
| `data/products.csv` | 8 dairy products: id, name, category, price in PKR |
| `data/customers.csv` | 20 customers: delivery plan (daily, alternate_days, weekly), preferred slot, staple milk product, staple quantity |
| `data/interactions.csv` | 614 rows. One row = one delivery event: customer_id, product_id, date, slot, quantity, status, amount_pkr |

Status is `delivered`, `skipped` (one missed day) or `paused` (a block of
consecutive days). Skipped and paused rows have quantity 0 and an empty amount.

## Metrics (data/metrics.json)

`metrics.json` is a text file holding the results below as a dictionary. The
program creates it.

| Metric | Value | Meaning |
|---|---|---|
| Interactions / purchases | 614 / 587 | all rows / delivered rows only |
| Purchases per customer | mean 29.35, median 29.5 | delivered rows per customer |
| Repeat purchase rate (all) | 0.75 | of the customer-product pairs bought at least once, the share delivered on 2 or more different days |
| Repeat purchase rate (extras only) | 0.6932 | same, but the two milk products (ids 1 and 2) left out |
| Sparsity | 0.325 | share of customer-product pairs with no purchase |
| Skip rate | 0.0349 | skipped milk days as a share of skipped + delivered milk days (paused days not counted) |
| Pause rate | 0.15 | share of customers who paused at least once |
| Top products (names shortened) | Full-Cream Milk 233, Low-Fat Milk 126, Dahi 82, Farm Eggs 48, Sweet Lassi 42 | most delivered products |

Sparsity 0.325 is **low**: with only 8 products and random buying, most
customers touched most products. Real data would be much sparser.

## Wrong or empty input

Missing, empty or broken files do not crash the program. It prints one clear
message and stops. Example with `interactions.csv` missing:

```
File not found: data\interactions.csv. Run python src/generate_data.py first.
```

The rules are in `src/validate.py` (missing columns, bad status, negative
quantity, unknown customer, and others).

## Tests

`python -m pytest -v` runs `tests/test_metrics.py` (2 tests, using a small
table built inside the test, not the real CSV):

1. Main path: `compute_metrics` returns all the expected keys.
2. Failure path: a `product_id` that is not in products raises
   `DataValidationError`.

The validation rules were also checked by hand by breaking data in memory.

## Performance and security notes

- Performance: pandas handles these 614 rows quickly. Much larger data would
  need to be tested again.
- Security: no passwords, keys or real customer data in the repo. All data is
  generated, and input files are validated before use.