import numpy as np
import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

N_CUSTOMERS = 20
N_DAYS = 28
START_DATE = "2026-10-01"
rng = np.random.default_rng(42)
pause_rng = np.random.default_rng(7)  # separate generator used only for pauses  # fixed seed: same data every run

# ---------- 1. Products (8) ----------
products = pd.DataFrame({
    "product_id":   [1, 2, 3, 4, 5, 6, 7, 8],
    "product_name": ["Full-Cream Milk 1L", "Low-Fat Milk 1L", "Dahi (Yogurt) 500g",
                     "Desi Ghee 1kg", "Butter 200g", "Paneer 250g",
                     "Sweet Lassi 500ml", "Farm Eggs (Dozen)"],
    "category":     ["milk", "milk", "yogurt", "ghee", "butter",
                     "cheese", "drink", "eggs"],
    "price_pkr":    [260, 250, 190, 2800, 650, 420, 150, 420],
})
price = dict(zip(products["product_id"], products["price_pkr"]))

# ---------- 2. Customers (20) ----------
customers = pd.DataFrame({
    "customer_id":       np.arange(1, N_CUSTOMERS + 1),
    "plan":              rng.choice(["daily", "alternate_days", "weekly"], size=N_CUSTOMERS, p=[0.6, 0.25, 0.15]),
    "preferred_slot":    rng.choice(["morning", "evening"], size=N_CUSTOMERS, p=[0.75, 0.25]),
    "staple_product_id": rng.choice([1, 2], size=N_CUSTOMERS, p=[0.7, 0.3]),
    "staple_qty":        rng.choice([1, 2, 3], size=N_CUSTOMERS, p=[0.5, 0.35, 0.15]),
})

products.to_csv(DATA_DIR / "products.csv", index=False)
customers.to_csv(DATA_DIR / "customers.csv", index=False)
print(customers)
print(customers["plan"].value_counts())

dates = pd.date_range(START_DATE, periods=N_DAYS, freq="D")
rows = []

# Draw every customer's pause up front, from its own generator.
pauses = {}
for c in customers.itertuples():
    if pause_rng.random() < 0.25:
        start = int(pause_rng.integers(3, 20))
        length = int(pause_rng.integers(3, 8))
        pauses[c.customer_id] = (start, start + length - 1)

for c in customers.itertuples():
    pause_start, pause_end = pauses.get(c.customer_id, (None, None))

    for day_number, d in enumerate(dates):
        # paused day: quantity 0, empty amount
        if pause_start is not None and pause_start <= day_number <= pause_end:
            rows.append((c.customer_id, c.staple_product_id, d.date(),
                         c.preferred_slot, 0, "paused", None))
            continue

        scheduled = (
            c.plan == "daily"
            or (c.plan == "alternate_days" and day_number % 2 == 0)
            or (c.plan == "weekly" and d.weekday() == 4)
        )
        if scheduled:
            qty = int(c.staple_qty) * (3 if c.plan == "weekly" else 1)
            if rng.random() < 0.05:
                rows.append((c.customer_id, c.staple_product_id, d.date(),
                             c.preferred_slot, 0, "skipped", None))
            else:
                rows.append((c.customer_id, c.staple_product_id, d.date(),
                             c.preferred_slot, qty, "delivered",
                             qty * price[c.staple_product_id]))

        # extras (dahi, ghee, ...): more likely at weekends
        boost = 1.6 if d.weekday() in (4, 5, 6) else 1.0
        for pid, p in {3: 0.12, 4: 0.01, 5: 0.03, 6: 0.04, 7: 0.06, 8: 0.08}.items():
            if rng.random() < p * boost:
                rows.append((c.customer_id, pid, d.date(), c.preferred_slot,
                             1, "delivered", price[pid]))

interactions = pd.DataFrame(rows, columns=[
    "customer_id", "product_id", "date", "slot", "quantity", "status", "amount_pkr"])
interactions = interactions.sort_values(["date", "customer_id"]).reset_index(drop=True)
interactions["amount_pkr"] = interactions["amount_pkr"].astype("Int64")
interactions.to_csv(DATA_DIR / "interactions.csv", index=False)

print(interactions.head())
print(len(interactions))
print(interactions["status"].value_counts())
print("Customers with a pause:", sorted(interactions[interactions["status"] == "paused"]["customer_id"].unique()))