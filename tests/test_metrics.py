import pandas as pd
import pytest

from src.metrics import compute_metrics
from src.validate import DataValidationError


def make_interactions():
    return pd.DataFrame({
        "customer_id": [1, 1, 2, 2],
        "product_id": [1, 2, 1, 1],
        "date": ["2026-10-01", "2026-10-01", "2026-10-01", "2026-10-02"],
        "slot": ["morning", "morning", "evening", "evening"],
        "quantity": [1, 1, 1, 0],
        "status": ["delivered", "delivered", "delivered", "skipped"],
        "amount_pkr": [260.0, 250.0, 260.0, None],
    })


def make_products():
    return pd.DataFrame({
        "product_id": [1, 2],
        "product_name": ["Full-Cream Milk 1L", "Low-Fat Milk 1L"],
        "category": ["milk", "milk"],
        "price_pkr": [260, 250],
    })


def test_compute_metrics_returns_expected_keys():
    result = compute_metrics(make_interactions(), make_products())
    expected = [
        "counts", "purchases_per_customer", "top_products",
        "repeat_purchase_rate_all", "repeat_purchase_rate_extras",
        "sparsity", "skip_rate", "pause_rate",
        "deliveries_by_weekday", "deliveries_by_slot",
    ]
    for key in expected:
        assert key in result

def test_unknown_product_id_raises_error():
    df = make_interactions()
    df.loc[0, "product_id"] = 999   # 999 is not in make_products()
    with pytest.raises(DataValidationError, match="not in products"):
        compute_metrics(df, make_products())