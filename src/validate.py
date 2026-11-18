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


def check_with_customers(df, customers):
    dates = pd.to_datetime(df["date"], format="%Y-%m-%d")
    paused = df["status"] == "paused"

    # 1. every customer in the file must exist in customers.csv
    bad = df[~df["customer_id"].isin(customers["customer_id"])]
    if len(bad):
        _fail("customer_id must exist in customers.csv", bad)

    # 2. a customer has at most one paused run, with no gaps
    first = dates[paused].groupby(df["customer_id"][paused]).min()
    last = dates[paused].groupby(df["customer_id"][paused]).max()
    count = df[paused].groupby("customer_id").size()
    length = (last - first).dt.days + 1
    broken = count[count != length]
    if len(broken):
        raise DataValidationError(
            "Rule failed: each customer may have only one paused run. "
            f"Customers with a gap or a second run: {list(broken.index)}")

    # 3. nothing but paused rows may fall inside a paused run
    run_start = df["customer_id"].map(first)
    run_end = df["customer_id"].map(last)
    inside = (dates >= run_start) & (dates <= run_end)
    bad = df[inside & ~paused]
    if len(bad):
        _fail("no delivery or skip may fall inside a paused run", bad)

    # 4. staple rows must follow the plan's rhythm
    m = df.merge(customers[["customer_id", "plan", "staple_product_id"]],
                 on="customer_id", how="left")
    d = pd.to_datetime(m["date"], format="%Y-%m-%d")
    day_number = (d - d.min()).dt.days
    staple = (m["product_id"] == m["staple_product_id"]) & m["status"].isin(["delivered", "skipped"])
    bad = m[(m["plan"] == "alternate_days") & staple & (day_number % 2 != 0)]
    if len(bad):
        _fail("alternate_days staple rows must fall on every second day", bad)
        bad = m[(m["plan"] == "weekly") & staple & (d.dt.day_of_week != 4)]
    if len(bad):
        _fail("weekly staple rows must fall on a Friday", bad)

if __name__ == "__main__":
    try:
        data = load_interactions("data/interactions.csv")
        customers = load_interactions("data/customers.csv")
        check_interactions(data)
        check_with_customers(data, customers)
    except DataValidationError as error:
        print(error)
        sys.exit(1)
    print(f"OK: {len(data)} rows checked, all rules passed")