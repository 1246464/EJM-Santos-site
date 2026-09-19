"""Regressões do script executado no build do Render."""

import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest


class RenderStartupTests(unittest.TestCase):
    def test_script_migrates_legacy_database_and_is_idempotent(self):
        root = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "legacy.db"
            connection = sqlite3.connect(database_path)
            try:
                connection.execute(
                    'CREATE TABLE "user" ('
                    'id INTEGER PRIMARY KEY, nome VARCHAR(120) NOT NULL, '
                    'email VARCHAR(150) NOT NULL UNIQUE, senha_hash VARCHAR(256) NOT NULL, '
                    'is_admin BOOLEAN, created_at TIMESTAMP)'
                )
                connection.execute(
                    'CREATE TABLE "order" ('
                    'id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, '
                    'total FLOAT NOT NULL, status VARCHAR(50), created_at TIMESTAMP)'
                )
                connection.commit()
            finally:
                connection.close()

            environment = os.environ.copy()
            environment.update({
                "DATABASE_URL": "sqlite:///" + database_path.as_posix(),
                "EJM_ADMIN_EMAIL": "",
                "EJM_ADMIN_PASSWORD": "",
            })
            command = [sys.executable, str(root / "init_render.py")]
            first = subprocess.run(
                command, cwd=root, env=environment, capture_output=True,
                text=True, timeout=30, check=False,
            )
            second = subprocess.run(
                command, cwd=root, env=environment, capture_output=True,
                text=True, timeout=30, check=False,
            )
            self.assertEqual(first.returncode, 0, first.stderr + first.stdout)
            self.assertEqual(second.returncode, 0, second.stderr + second.stdout)

            connection = sqlite3.connect(database_path)
            try:
                user_columns = {
                    row[1] for row in connection.execute('PRAGMA table_info("user")')
                }
                order_columns = {
                    row[1] for row in connection.execute('PRAGMA table_info("order")')
                }
                product_columns = {
                    row[1] for row in connection.execute('PRAGMA table_info("product")')
                }
            finally:
                connection.close()

            self.assertTrue({
                "mobile_token_version", "is_active", "password_reset_hash",
                "password_reset_expires_at", "password_reset_attempts",
            }.issubset(user_columns))
            self.assertTrue({
                "subtotal", "delivery_fee", "client_reference", "payment_status",
                "external_payment_id", "inventory_released",
            }.issubset(order_columns))
            self.assertTrue({
                "categoria", "origem", "beneficios", "sem_adicao_acucar", "destaque",
            }.issubset(product_columns))


if __name__ == "__main__":
    unittest.main()
