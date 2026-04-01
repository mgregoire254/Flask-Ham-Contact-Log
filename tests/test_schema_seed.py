import sqlite3
import unittest
from pathlib import Path


class SchemaSeedTests(unittest.TestCase):
    def test_schema_and_seed_data_load(self):
        repo_root = Path(__file__).resolve().parents[1]
        schema_sql = (repo_root / 'schema.sql').read_text(encoding='utf-8')
        seed_sql = (repo_root / 'tests' / 'data.sql').read_text(encoding='utf-8')

        conn = sqlite3.connect(':memory:')
        try:
            conn.executescript(schema_sql)
            conn.executescript(seed_sql)

            user_count = conn.execute('SELECT COUNT(*) FROM user').fetchone()[0]
            contact_count = conn.execute('SELECT COUNT(*) FROM contacts').fetchone()[0]

            self.assertEqual(user_count, 2)
            self.assertEqual(contact_count, 2)
        finally:
            conn.close()


if __name__ == '__main__':
    unittest.main()
