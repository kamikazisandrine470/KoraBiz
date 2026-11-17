import sqlite3
import tempfile
import unittest
from pathlib import Path


SCHEMA = Path(__file__).resolve().parents[1] / "app" / "schema.sql"


class DatabaseSchemaTests(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        self.temp_file.close()
        self.db = sqlite3.connect(self.temp_file.name)
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript(SCHEMA.read_text(encoding="utf-8"))

    def tearDown(self):
        self.db.close()
        Path(self.temp_file.name).unlink(missing_ok=True)

    def test_expected_tables_exist(self):
        rows = self.db.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
        names = {row[0] for row in rows}
        expected = {
            "users", "categories", "products", "sales",
            "sale_items", "expenses", "stock_movements",
        }
        self.assertTrue(expected.issubset(names))

    def test_product_cannot_have_negative_quantity(self):
        self.db.execute(
            "INSERT INTO products (name, buying_price, selling_price, quantity) "
            "VALUES (?, ?, ?, ?)",
            ("Test sugar", 800, 1000, 4),
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "INSERT INTO products (name, buying_price, selling_price, quantity) "
                "VALUES (?, ?, ?, ?)",
                ("Invalid item", 500, 700, -1),
            )

    def test_user_role_is_restricted(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "INSERT INTO users (username, full_name, password_hash, role) "
                "VALUES (?, ?, ?, ?)",
                ("badrole", "Test User", "not-a-real-hash", "manager"),
            )


if __name__ == "__main__":
    unittest.main()
