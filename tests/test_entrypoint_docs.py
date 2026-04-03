import ast
import unittest
from pathlib import Path


class EntrypointDocsTests(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_readme_documents_canonical_flask_command(self):
        readme = (self.repo_root / 'README.md').read_text(encoding='utf-8')
        self.assertIn('Contacts:create_app', readme)
        self.assertIn('flask --app Contacts:create_app run --debug', readme)
        self.assertIn('flask --app Contacts:create_app init-db', readme)

    def test_setup_discovers_packages(self):
        setup_source = (self.repo_root / 'setup.py').read_text(encoding='utf-8')
        setup_tree = ast.parse(setup_source)

        setup_call = None
        for node in ast.walk(setup_tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'setup':
                setup_call = node
                break

        self.assertIsNotNone(setup_call, 'setup.py must call setup(...)')
        keyword_values = {kw.arg: kw.value for kw in setup_call.keywords if kw.arg}

        packages_node = keyword_values.get('packages')
        self.assertIsInstance(packages_node, ast.Call)
        self.assertIsInstance(packages_node.func, ast.Name)
        self.assertEqual(packages_node.func.id, 'find_packages')


if __name__ == '__main__':
    unittest.main()
