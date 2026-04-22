import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE_NAME = 'Contacts'


def load_contacts_package():
    repo_root = Path(__file__).resolve().parents[1]
    sys.modules.pop(PACKAGE_NAME, None)

    spec = importlib.util.spec_from_file_location(
        PACKAGE_NAME,
        repo_root / '__init__.py',
        submodule_search_locations=[str(repo_root)],
    )
    if spec is None or spec.loader is None:
        raise RuntimeError('Unable to load Contacts package spec for tests.')

    package = importlib.util.module_from_spec(spec)
    sys.modules[PACKAGE_NAME] = package
    spec.loader.exec_module(package)
    return package


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[1]
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.addCleanup(lambda: sys.modules.pop(PACKAGE_NAME, None))

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

    def login(self):
        response = self.client.post(
            '/api/auth/login',
            json={'username': 'test', 'password': 'test'},
        )
        self.assertEqual(response.status_code, 200)
        return response

    def test_root_serves_react_shell(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<div id="root"></div>', response.data)
        self.assertIn(b'/static/dist/app.js', response.data)

    def test_api_auth_and_contact_crud(self):
        unauthenticated = self.client.get('/api/contacts')
        self.assertEqual(unauthenticated.status_code, 401)

        self.login()

        list_response = self.client.get('/api/contacts')
        self.assertEqual(list_response.status_code, 200)
        list_payload = list_response.get_json()
        contacts = list_payload['contacts']
        self.assertEqual([contact['callsign'] for contact in contacts], ['K1ABC'])
        self.assertEqual(list_payload['total_contacts'], 1)

        create_response = self.client.post(
            '/api/contacts',
            json={
                'callsign': 'n0call',
                'comments': 'Created through API',
                'frequency': '7050',
                'mode': 'cw',
                'power': '20',
                'self_location': 'Denver, CO',
                'contact_location': 'Austin, TX',
                'self_rst': '59',
                'contact_rst': '58',
            },
        )
        self.assertEqual(create_response.status_code, 201)
        created = create_response.get_json()['contact']
        self.assertEqual(created['callsign'], 'N0CALL')
        self.assertEqual(created['mode'], 'CW')

        update_response = self.client.put(
            f"/api/contacts/{created['id']}",
            json={**created, 'comments': 'Updated through API', 'power': '25'},
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.get_json()['contact']['power'], 25)

        delete_response = self.client.delete(f"/api/contacts/{created['id']}")
        self.assertEqual(delete_response.status_code, 200)
        self.assertTrue(delete_response.get_json()['deleted'])

    def test_contact_search_matches_owned_contacts_only(self):
        self.login()

        callsign_response = self.client.get('/api/contacts?q=k1a')
        self.assertEqual(callsign_response.status_code, 200)
        callsign_payload = callsign_response.get_json()
        callsign_matches = callsign_payload['contacts']
        self.assertEqual([contact['callsign'] for contact in callsign_matches], ['K1ABC'])
        self.assertIn(callsign_payload['search_backend'], {'meilisearch', 'sqlite'})
        self.assertEqual(callsign_payload['query'], 'k1a')
        self.assertEqual(callsign_payload['total_contacts'], 1)

        location_response = self.client.get('/api/contacts?q=providence')
        self.assertEqual(location_response.status_code, 200)
        location_matches = location_response.get_json()['contacts']
        self.assertEqual([contact['callsign'] for contact in location_matches], ['K1ABC'])

        leaked_response = self.client.get('/api/contacts?q=portland')
        self.assertEqual(leaked_response.status_code, 200)
        self.assertEqual(leaked_response.get_json()['contacts'], [])


if __name__ == '__main__':
    unittest.main()
