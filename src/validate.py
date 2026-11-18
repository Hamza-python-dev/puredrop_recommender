import sys
from pathlib import Path
import pandas as pd


class DataValidationError(Exception):
    """Raised when the interactions data is missing, empty or wrong."""


REQUIRED_COLUMNS = ["customer_id", "product_id", "date", "slot",
                    "quantity", "status", "amount_pkr"]
VALID_STATUS = {"delivered", "skipped", "paused"}
VALID_SLOTS = {"morning", "evening"}


def load_interactions(path):
    path = Path(path)
    if not path.exists():
        raise DataValidationError(
            f"File not found: {path}. Run python src/generate_data.py first.")
    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        raise DataValidationError(f"File is empty: {path}")
    if df.empty:
        raise DataValidationError(f"File has a header but no rows: {path}")
    return df


def _fail(rule, bad_rows):
    examples = [f"customer {r.customer_id} on {r.date}"
                for r in bad_rows.head(3).itertuples()]
    raise DataValidationError(
        f"Rule failed: {rule}. {len(bad_rows)} rows broken, e.g. "
        + "; ".join(examples))


def check_interactions(df):
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise DataValidationError(f"Missing columns: {missing}")

    bad = df[~df["status"].isin(VALID_STATUS)]
    if len(bad):
        _fail("status must be delivered, skipped or paused", bad)

    bad = df[~df["slot"].isin(VALID_SLOTS)]
    if len(bad):
        _fail("slot must be morning or evening", bad)

    dates = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")
    bad = df[dates.isna()]
    if len(bad):
        _fail("date must look like 2026-10-01", bad)

    qty = pd.to_numeric(df["quantity"], errors="coerce")
    bad = df[qty.isna() | (qty < 0)]
    if len(bad):
        _fail("quantity must be a number that is 0 or more", bad)

    delivered = df["status"] == "delivered"
    no_amount = df["amount_pkr"].isna()

    bad = df[delivered & (qty < 1)]
    if len(bad):
        _fail("a delivered row needs quantity 1 or more", bad)

    bad = df[delivered & no_amount]
    if len(bad):
        _fail("a delivered row needs an amount", bad)

    bad = df[~delivered & ((qty != 0) | ~no_amount)]
    if len(bad):
        _fail("skipped and paused rows need quantity 0 and an empty amount", bad)

    bad = df[df.duplicated(["customer_id", "product_id", "date"], keep=False)]
    if len(bad):
        _fail("each customer, product and date may appear only once", bad)


if __name__ == "__main__":
    try:
        data = load_interactions("data/interactions.csv")
        check_interactions(data)
    except DataValidationError as error:
        print(error)
        sys.exit(1)
    print(f"OK: {len(data)} rows checked, all rules passed")