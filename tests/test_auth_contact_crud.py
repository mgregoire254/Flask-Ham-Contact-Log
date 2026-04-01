import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


def load_contacts_package():
    repo_root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        'Contacts',
        repo_root / '__init__.py',
        submodule_search_locations=[str(repo_root)],
    )
    package = importlib.util.module_from_spec(spec)
    sys.modules['Contacts'] = package
    spec.loader.exec_module(package)
    return package


class AuthContactCrudTests(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[1]
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        contacts_package = load_contacts_package()
        self.app = contacts_package.create_app(
            {
                'TESTING': True,
                'DATABASE': str(Path(self.temp_dir.name) / 'test.sqlite'),
                'SECRET_KEY': 'test-secret-key',
            }
        )

        with self.app.app_context():
            schema_sql = (self.repo_root / 'schema.sql').read_text(encoding='utf-8')
            seed_sql = (self.repo_root / 'tests' / 'data.sql').read_text(encoding='utf-8')
            from Contacts.db import get_db

            db = get_db()
            db.executescript(schema_sql)
            db.executescript(seed_sql)
            db.commit()

        self.client = self.app.test_client()

    def login(self, username='test', password='test'):
        return self.client.post(
            '/auth/login', data={'username': username, 'password': password}
        )

    def test_register_login_logout_flow(self):
        register_response = self.client.post(
            '/auth/register',
            data={'username': 'new-user', 'password': 'new-password'},
            follow_redirects=False,
        )
        self.assertEqual(register_response.status_code, 302)
        self.assertIn('/auth/login', register_response.headers['Location'])

        login_response = self.client.post(
            '/auth/login',
            data={'username': 'new-user', 'password': 'new-password'},
            follow_redirects=False,
        )
        self.assertEqual(login_response.status_code, 302)
        self.assertEqual(login_response.headers['Location'], '/')

        with self.client.session_transaction() as session:
            self.assertIsNotNone(session.get('user_id'))

        logout_response = self.client.get('/auth/logout', follow_redirects=False)
        self.assertEqual(logout_response.status_code, 302)
        self.assertEqual(logout_response.headers['Location'], '/')

        with self.client.session_transaction() as session:
            self.assertIsNone(session.get('user_id'))

    def test_create_contact(self):
        self.login()

        create_response = self.client.post(
            '/create',
            data={
                'callsign': 'N0CALL',
                'comments': 'Created in test',
                'frequency': '7050',
                'mode': 'CW',
                'power': '20',
                'self_location': 'Denver, CO',
                'contact_location': 'Austin, TX',
                'self_rst': '59',
                'contact_rst': '58',
            },
            follow_redirects=False,
        )
        self.assertEqual(create_response.status_code, 302)
        self.assertEqual(create_response.headers['Location'], '/')

        with self.app.app_context():
            from Contacts.db import get_db

            row = get_db().execute(
                "SELECT callsign, comments, author_id FROM contacts WHERE callsign = 'N0CALL'"
            ).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row['comments'], 'Created in test')
            self.assertEqual(row['author_id'], 1)

    def test_update_and_delete_own_contact(self):
        self.login()

        update_response = self.client.post(
            '/1/update',
            data={
                'callsign': 'K1ABC-UPDATED',
                'comments': 'Updated from test',
                'frequency': '146520',
                'mode': 'FM',
                'power': '30',
                'self_location': 'Boston, MA',
                'contact_location': 'Providence, RI',
                'self_rst': '59',
                'contact_rst': '57',
            },
            follow_redirects=False,
        )
        self.assertEqual(update_response.status_code, 302)
        self.assertEqual(update_response.headers['Location'], '/')

        with self.app.app_context():
            from Contacts.db import get_db

            updated = get_db().execute(
                'SELECT callsign, comments, power FROM contacts WHERE id = 1'
            ).fetchone()
            self.assertEqual(updated['callsign'], 'K1ABC-UPDATED')
            self.assertEqual(updated['comments'], 'Updated from test')
            self.assertEqual(updated['power'], 30)

        delete_response = self.client.post('/1/delete', follow_redirects=False)
        self.assertEqual(delete_response.status_code, 302)
        self.assertEqual(delete_response.headers['Location'], '/')

        with self.app.app_context():
            from Contacts.db import get_db

            deleted = get_db().execute('SELECT id FROM contacts WHERE id = 1').fetchone()
            self.assertIsNone(deleted)

    def test_forbidden_access_on_other_users_records(self):
        self.login(username='test', password='test')

        update_response = self.client.post(
            '/2/update',
            data={
                'callsign': 'NOPE',
                'comments': 'Should not update',
                'frequency': '146520',
                'mode': 'FM',
                'power': '30',
                'self_location': 'Boston, MA',
                'contact_location': 'Providence, RI',
                'self_rst': '59',
                'contact_rst': '57',
            },
        )
        self.assertEqual(update_response.status_code, 403)

        delete_response = self.client.post('/2/delete')
        self.assertEqual(delete_response.status_code, 403)


if __name__ == '__main__':
    unittest.main()
