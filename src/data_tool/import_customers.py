"""Import train.csv into Neon: python -m src.data_tool.import_customers."""

import argparse
import csv
from pathlib import Path
from uuid import UUID

import psycopg

from src.db.connection import database_url

DEFAULT_DATA = Path(__file__).resolve().parents[2] / "datasets/customer_churn/train.csv"
CSV_COLUMNS = ["Customer_ID", "Name", "Email", "Account_Age_Days", "Login_Frequency",
               "Daily_Usage_Mins", "Last_Support_Ticket", "Churn"]


def read_customers(path):
    """Validate the entire file before opening a write transaction."""
    rows, seen = [], set()
    with Path(path).open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None or set(reader.fieldnames) != set(CSV_COLUMNS) or len(reader.fieldnames) != 8:
            raise ValueError(f"CSV must contain exactly these columns: {', '.join(CSV_COLUMNS)}")
        for line, row in enumerate(reader, start=2):
            try:
                if None in row or any(value is None for value in row.values()):
                    raise ValueError("Incorrect number of CSV fields.")
                identifier = UUID(row["Customer_ID"].strip())
                if identifier in seen:
                    raise ValueError("Duplicate Customer_ID in CSV.")
                age, usage, churn = (int(row[column]) for column in
                                     ("Account_Age_Days", "Daily_Usage_Mins", "Churn"))
                if age < 0 or usage < 0 or max(age, usage) > 2147483647 or churn not in (0, 1):
                    raise ValueError("Invalid account age, usage, or churn label.")
                frequency = row["Login_Frequency"].strip().capitalize()
                if frequency not in {"Daily", "Weekly", "Rarely"}:
                    raise ValueError("Login_Frequency must be Daily, Weekly, or Rarely.")
                rows.append((identifier, row["Name"].strip() or None, row["Email"].strip() or None,
                             age, frequency, usage, row["Last_Support_Ticket"].strip() or None, churn))
                seen.add(identifier)
            except (ValueError, TypeError, AttributeError) as exc:
                raise ValueError(f"Invalid CSV row {line}: {exc}") from None
    if not rows:
        raise ValueError("CSV contains no customer rows.")
    return rows


def import_customers(path=DEFAULT_DATA):
    rows = read_customers(path)
    with psycopg.connect(database_url(), connect_timeout=10) as connection:
        with connection.cursor() as cursor:
            cursor.executemany(
                "INSERT INTO public.customers "
                "(customer_id, name, email, account_age_days, login_frequency, daily_usage_mins, "
                "last_support_ticket, churn) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) "
                "ON CONFLICT (customer_id) DO UPDATE SET "
                "name=EXCLUDED.name, email=EXCLUDED.email, account_age_days=EXCLUDED.account_age_days, "
                "login_frequency=EXCLUDED.login_frequency, daily_usage_mins=EXCLUDED.daily_usage_mins, "
                "last_support_ticket=EXCLUDED.last_support_ticket, churn=EXCLUDED.churn",
                rows,
            )
    return len(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, default=DEFAULT_DATA)
    args = parser.parse_args()
    try:
        count = import_customers(args.file)
    except psycopg.Error:
        parser.exit(1, "Import failed: check DATABASE_URL, write permissions, and run python -m src.db.setup.\n")
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Import failed: {exc}\n")
    print(f"Imported {count:,} customers from {args.file.name} (inserted or updated by Customer_ID).")


if __name__ == "__main__":
    main()
