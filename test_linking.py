"""Tests for the linking.py documentation migration script."""

import json
import shutil
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Tuple

# Ensure the current directory is in sys.path so 'linking' can be imported
sys.path.insert(0, str(Path(__file__).parent))

from linking import on_config
from linking import prepare_docs


class TestMigrationScript(unittest.TestCase):
    """Tests the migration script's prepare and on_config functions."""

    def setUp(self) -> None:
        """Set up a temporary directory structure for each test."""
        self.test_dir = Path('./temp_test_project')
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

        self.docs_path = self.test_dir / 'docs'
        self.redirect_map_file = self.test_dir / 'redirect_map.json'
        self.docs_path.mkdir(parents=True)

        # The script under test uses module-level globals for configuration.
        # To ensure tests are isolated, we temporarily redirect these globals
        # to point to our test directory during test execution.
        self.linking_module = sys.modules['linking']
        self.original_globals = {
            'DOCS_DIR': self.linking_module.DOCS_DIR,
            'REDIRECT_MAP_FILE': self.linking_module.REDIRECT_MAP_FILE,
        }
        self.linking_module.DOCS_DIR = self.docs_path
        self.linking_module.REDIRECT_MAP_FILE = self.redirect_map_file

    def tearDown(self) -> None:
        """Clean up the temporary directory after each test."""
        shutil.rmtree(self.test_dir)
        # Restore the original global variables to avoid side-effects between
        # test runs.
        for key, value in self.original_globals.items():
            setattr(self.linking_module, key, value)

    def test_prepare_fresh_run_no_frontmatter(self) -> None:
        """Test that IDs are correctly injected into files."""
        # Arrange: Create a file structure with no existing frontmatter.
        (self.docs_path / 'index.md').write_text('Welcome page')
        (self.docs_path / 'guides').mkdir()
        (self.docs_path / 'guides' / 'http.md').write_text('HTTP Guide')

        # Act: Run the preparation function.
        prepare_docs()

        # Assert: Verify the redirect map file was created and is correct.
        self.assertTrue(self.redirect_map_file.exists())
        redirect_map: Dict[str, str] = json.loads(
            self.redirect_map_file.read_text()
        )
        self.assertEqual(redirect_map.get('index'), 'index.md')
        self.assertEqual(redirect_map.get('guides-http'), 'guides/http.md')

    def _create_mock_config(
        self, pages_data: List[Tuple[str, str, str]]
    ) -> Dict[str, Any]:
        """Create a mock MkDocs config object for testing the hook function."""
        mock_pages: List[SimpleNamespace] = []
        for page_id, src_path, url in pages_data:
            page = SimpleNamespace(
                file=SimpleNamespace(src_path=src_path), url=url
            )
            # The hook function reads files to get IDs, so we must create them.
            file_path = self.docs_path / src_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(f'---\nid: {page_id}\n---\nContent')
            mock_pages.append(page)

        return {
            'docs_dir': str(self.docs_path),
            'pages': mock_pages,
            'plugins': {
                'redirects': {'config': {'redirect_maps': {}}},
                'macros': {'config': {'python_macros': {}}},
            },
        }

    def test_on_config_one_file_moved(self) -> None:
        """Test that a redirect is correctly generated for a moved file."""
        # Arrange: Create an initial state and run prepare_docs.
        (self.docs_path / 'old-path.md').write_text('Content')
        prepare_docs()
        # Arrange: Simulate a file move by creating a config where the path for
        # the same ID has changed.
        mock_config = self._create_mock_config(
            [('old-path', 'new/path/for/doc.md', '/new/path/for/doc/')]
        )

        # Act: Run the on_config hook with the new state.
        updated_config = on_config(mock_config)

        # Assert: Check that a redirect rule was correctly generated.
        redirects = updated_config['plugins']['redirects']['config'][
            'redirect_maps'
        ]
        self.assertEqual(len(redirects), 1)
        self.assertEqual(redirects['old-path.md'], 'new/path/for/doc.md')


if __name__ == '__main__':
    unittest.main(verbosity=2)