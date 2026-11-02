"""Offline tests: python -m unittest src.data_tool.test_data_tool."""

import csv
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID

from .import_customers import CSV_COLUMNS, import_customers, read_customers
from .query import SafeQueryError, run_safe_query, validate_query

ROW = ["a8b2ac22-dd31-483e-8672-592b7089138f", "Brenda Grant", "example@example.com",
       "790", "Weekly", "28", "Checking my payment.", "0"]


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "train.csv"

    def write_rows(self, rows):
        with self.path.open("w", encoding="utf-8", newline="") as source:
            writer = csv.writer(source)
            writer.writerow(CSV_COLUMNS)
            writer.writerows(rows)

    def test_reads_and_normalizes(self):
        row = ROW.copy()
        row[4] = " weekly "
        self.write_rows([row])
        result = read_customers(self.path)
        self.assertEqual(result[0][0], UUID(ROW[0]))
        self.assertEqual(result[0][4], "Weekly")
        self.assertEqual(result[0][3], 790)

    def test_invalid_or_duplicate_rows_rejected_before_connecting(self):
        invalid_sets = [[], [ROW, ROW]]
        for index, value in [(0, "invalid"), (3, "-1"), (4, "Monthly"), (5, "1.5"), (7, "2")]:
            row = ROW.copy()
            row[index] = value
            invalid_sets.append([row])
        for rows in invalid_sets:
            with self.subTest(rows=rows), patch("src.data_tool.import_customers.psycopg.connect") as connect:
                self.write_rows(rows)
                with self.assertRaises(ValueError):
                    import_customers(self.path)
                connect.assert_not_called()

    def test_import_upserts_in_one_transaction(self):
        self.write_rows([ROW])
        with patch("src.data_tool.import_customers.database_url", return_value="test"), \
             patch("src.data_tool.import_customers.psycopg.connect") as connect:
            connection = connect.return_value.__enter__.return_value
            cursor = connection.cursor.return_value.__enter__.return_value
            self.assertEqual(import_customers(self.path), 1)
            self.assertIn("ON CONFLICT (customer_id) DO UPDATE", cursor.executemany.call_args.args[0])
            cursor.executemany.side_effect = RuntimeError("failed insert")
            with self.assertRaises(RuntimeError):
                import_customers(self.path)
            self.assertIs(connect.return_value.__exit__.call_args.args[0], RuntimeError)


class QueryTests(unittest.TestCase):
    def test_allowed_analytics(self):
        for query in [
            "SELECT COUNT(*) AS total FROM customers",
            "SELECT login_frequency, AVG(daily_usage_mins) AS usage FROM customers "
            "WHERE churn=1 GROUP BY login_frequency ORDER BY usage DESC LIMIT 5",
            "SELECT ROUND(100.0 * SUM(churn) / NULLIF(COUNT(*),0),2) AS churn_rate FROM public.customers",
            "SELECT c.name FROM customers c WHERE c.account_age_days BETWEEN 1 AND 30",
            "SELECT COUNT(*) FROM customers WHERE name ILIKE 'a%' AND churn IN (0,1)",
            "SELECT SUM(CASE WHEN churn=1 THEN 1 ELSE 0 END) FROM customers",
        ]:
            with self.subTest(query=query):
                self.assertIn("public.customers", validate_query(query))

    def test_unsafe_queries_rejected_before_connecting(self):
        queries = [
            "DELETE FROM customers", "SELECT * FROM customers; DROP TABLE customers",
            "SELECT * INTO copied FROM customers", "SELECT * FROM customers FOR UPDATE",
            "SELECT * FROM documents", "SELECT * FROM pg_catalog.pg_authid",
            "SELECT * FROM pg_temp.customers", "SELECT * FROM customers c JOIN customers d ON true",
            "SELECT pg_sleep(30) FROM customers", "SELECT set_config('role','owner',true) FROM customers",
            "SELECT public.lower(name) FROM customers", "SELECT name::regclass FROM customers",
            "WITH gone AS (DELETE FROM customers RETURNING *) SELECT * FROM gone",
            "SELECT * FROM customers UNION SELECT * FROM customers",
            "SELECT (SELECT secret FROM other_table) FROM customers",
            "SELECT churn_date FROM customers", "SELECT * FROM customers LIMIT -1",
            "SELECT * FROM customers LIMIT '10'", "SELECT * FROM customers OFFSET pg_sleep(1)",
            "SELECT current_user FROM customers", "SELECT * FROM customers TABLESAMPLE SYSTEM (10)",
        ]
        with patch("src.data_tool.query.psycopg.connect") as connect:
            for query in queries:
                with self.subTest(query=query), self.assertRaises(SafeQueryError):
                    run_safe_query(query)
            connect.assert_not_called()

    def test_execution_is_read_only_and_limited(self):
        with patch("src.data_tool.query.database_url", return_value="test"), \
             patch("src.data_tool.query.psycopg.connect") as connect:
            connection = connect.return_value.__enter__.return_value
            cursor = connection.cursor.return_value.__enter__.return_value
            cursor.description = [SimpleNamespace(name="average")]
            cursor.fetchmany.return_value = [(Decimal("1.5"),)] * 101
            result = run_safe_query("SELECT AVG(daily_usage_mins) FROM customers")
            self.assertEqual(connection.execute.call_args_list[0].args[0], "SET TRANSACTION READ ONLY")
            self.assertIn("LIMIT 101", cursor.execute.call_args.args[0])
            self.assertEqual(result["row_count"], 100)
            self.assertTrue(result["truncated"])
            json.dumps(result)


if __name__ == "__main__":
    unittest.main()
