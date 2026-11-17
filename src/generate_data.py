import numpy as np
import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

N_CUSTOMERS = 20
N_DAYS = 28
START_DATE = "2026-10-01"
rng = np.random.default_rng(42)  # fixed seed: same data every run

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
print(products)
print(customers.head())