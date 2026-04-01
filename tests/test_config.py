import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


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


class AppConfigTests(unittest.TestCase):
    def create_app(self):
        contacts_package = load_contacts_package()
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)

        app = contacts_package.create_app(
            {'TESTING': True, 'DATABASE': str(Path(temp_dir.name) / 'test.sqlite')}
        )
        return app

    def test_dev_defaults_to_safe_local_secret_key(self):
        with patch.dict(
            os.environ, {'SECRET_KEY': '', 'HAMPY_ENV': 'development'}, clear=False
        ):
            os.environ.pop('SECRET_KEY', None)
            app = self.create_app()
            self.assertEqual(app.config['SECRET_KEY'], 'dev-insecure-change-me')
            self.assertEqual(app.config['HAMPY_ENV'], 'development')

    def test_secret_key_reads_from_environment(self):
        with patch.dict(
            os.environ,
            {'SECRET_KEY': 'env-driven-secret', 'HAMPY_ENV': 'development'},
            clear=False,
        ):
            app = self.create_app()
            self.assertEqual(app.config['SECRET_KEY'], 'env-driven-secret')

    def test_production_requires_secret_key(self):
        with patch.dict(
            os.environ, {'SECRET_KEY': '', 'HAMPY_ENV': 'production'}, clear=False
        ):
            os.environ.pop('SECRET_KEY', None)
            contacts_package = load_contacts_package()
            with self.assertRaises(RuntimeError):
                contacts_package.create_app({'TESTING': True})

    def test_production_allows_env_secret_key(self):
        with patch.dict(
            os.environ,
            {'SECRET_KEY': 'prod-secret', 'HAMPY_ENV': 'production'},
            clear=False,
        ):
            app = self.create_app()
            self.assertEqual(app.config['SECRET_KEY'], 'prod-secret')
            self.assertEqual(app.config['HAMPY_ENV'], 'production')


if __name__ == '__main__':
    unittest.main()
