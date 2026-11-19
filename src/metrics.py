import json
import sys
from pathlib import Path
import pandas as pd
from src.validate import load_interactions, check_interactions, DataValidationError

STAPLE_IDS = {1, 2}   # the two milk products; every other product is an "extra"
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday"]


def get_delivered(df):
    """Only delivered rows count as purchases."""
    return df[df["status"] == "delivered"]


def count_basics(df):
    return {
        "n_customers": int(df["customer_id"].nunique()),
        "n_products": int(df["product_id"].nunique()),
        "n_interactions": int(len(df)),
        "n_purchases": int(len(get_delivered(df))),
    }


def purchases_per_customer(df):
    counts = get_delivered(df).groupby("customer_id").size()
    # customers with zero purchases must still count, so add them back as 0
    counts = counts.reindex(df["customer_id"].unique(), fill_value=0)
    return {
        "mean": round(float(counts.mean()), 2),
        "median": float(counts.median()),
        "std": round(float(counts.std(ddof=0)), 2),
    }


def top_products(df, products, n=5):
    counts = (get_delivered(df).groupby("product_id").size()
              .sort_values(ascending=False).head(n))
    names = dict(zip(products["product_id"], products["product_name"]))
    return {names.get(pid, str(pid)): int(c) for pid, c in counts.items()}


def repeat_purchase_rate(df, exclude_ids=()):
    delivered = get_delivered(df)
    delivered = delivered[~delivered["product_id"].isin(exclude_ids)]
    # for each customer-product pair, on how many different days was it delivered?
    days = delivered.groupby(["customer_id", "product_id"])["date"].nunique()
    if len(days) == 0:
        return 0.0
    return round(float((days >= 2).mean()), 4)


def sparsity(df, n_products):
    filled = len(get_delivered(df)[["customer_id", "product_id"]].drop_duplicates())
    total = df["customer_id"].nunique() * n_products
    return round(1 - filled / total, 4)


def skip_rate(df):
    staple = df[df["product_id"].isin(STAPLE_IDS)]
    skipped = int((staple["status"] == "skipped").sum())
    delivered = int((staple["status"] == "delivered").sum())
    if skipped + delivered == 0:
        return 0.0
    return round(skipped / (skipped + delivered), 4)


def pause_rate(df):
    paused_customers = df[df["status"] == "paused"]["customer_id"].nunique()
    return round(float(paused_customers / df["customer_id"].nunique()), 4)


def deliveries_by_weekday(df):
    names = pd.to_datetime(get_delivered(df)["date"]).dt.day_name()
    counts = names.value_counts().reindex(WEEKDAYS, fill_value=0)
    return {day: int(c) for day, c in counts.items()}


def deliveries_by_slot(df):
    counts = get_delivered(df)["slot"].value_counts()
    return {slot: int(c) for slot, c in counts.items()}


def compute_metrics(df, products):
    if len(get_delivered(df)) == 0:
        raise DataValidationError("No delivered rows, so there is nothing to measure.")
    n_products = len(products)
    return {
        "counts": count_basics(df),
        "purchases_per_customer": purchases_per_customer(df),
        "top_products": top_products(df, products),
        "repeat_purchase_rate_all": repeat_purchase_rate(df),
        "repeat_purchase_rate_extras": repeat_purchase_rate(df, exclude_ids=STAPLE_IDS),
        "sparsity": sparsity(df, n_products),
        "skip_rate": skip_rate(df),
        "pause_rate": pause_rate(df),
        "deliveries_by_weekday": deliveries_by_weekday(df),
        "deliveries_by_slot": deliveries_by_slot(df),
    }


if __name__ == "__main__":
    try:
        data = load_interactions("data/interactions.csv")
        check_interactions(data)
        products = load_interactions("data/products.csv")
        metrics = compute_metrics(data, products)
    except DataValidationError as error:
        print(error)
        sys.exit(1)
    Path("data/metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))
    print("Saved data/metrics.json")