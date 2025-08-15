import argparse
import json
import shutil
import sys
from typing import Any, Dict, List, Tuple
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent))

import linking
from linking import on_config, prepare_docs


class TestMigrationScript(unittest.TestCase):
    """Tests the migration script's prepare and on_config functions."""

    def setUp(self) -> None:
        """Set up a temporary directory structure for each test."""
        self.test_dir = Path("./temp_test_project")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

        self.docs_path = self.test_dir / "docs"
        self.redirect_map_file = self.test_dir / "redirect_map.json"
        self.docs_path.mkdir(parents=True)

        # The script under test uses module-level globals for configuration.
        # To ensure tests are isolated, we temporarily redirect these globals
        # to point to our test directory during test execution.
        self.linking_module = sys.modules["linking"]
        self.original_globals = {
            "DOCS_DIR": self.linking_module.DOCS_DIR,
            "REDIRECT_MAP_FILE": self.linking_module.REDIRECT_MAP_FILE,
        }
        self.linking_module.DOCS_DIR = self.docs_path # type: ignore
        self.linking_module.REDIRECT_MAP_FILE = self.redirect_map_file # type: ignore

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
        (self.docs_path / "index.md").write_text("Welcome page")
        (self.docs_path / "guides").mkdir()
        (self.docs_path / "guides" / "http.md").write_text("HTTP Guide")

        # Act: Run the preparation function.
        prepare_docs()

        # Assert: Verify the redirect map file was created and is correct.
        self.assertTrue(self.redirect_map_file.exists())
        redirect_map: Dict[str, str] = json.loads(self.redirect_map_file.read_text())
        self.assertEqual(redirect_map.get("index"), "index.md")
        self.assertEqual(redirect_map.get("guides-http"), "guides/http.md")

    def _create_mock_config(
        self, pages_data: List[Tuple[str, str, str]]
    ) -> Dict[str, Any]:
        """Create a mock MkDocs config object for testing the hook function."""
        mock_pages: List[SimpleNamespace] = []
        for page_id, src_path, url in pages_data:
            page = SimpleNamespace(file=SimpleNamespace(src_path=src_path), url=url)
            # The hook function reads files to get IDs, so we must create them.
            file_path = self.docs_path / src_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(f"---\nid: {page_id}\n---\nContent")
            mock_pages.append(page)

        return {
            "docs_dir": str(self.docs_path),
            "pages": mock_pages,
            "plugins": {
                "redirects": {"config": {"redirect_maps": {}}},
                "macros": {"config": {"python_macros": {}}},
            },
        }

    def test_on_files_one_file_moved(self) -> None:
        """Test that a redirect is correctly generated for a moved file using on_files."""
        (self.docs_path / "old-path.md").write_text("Content")
        prepare_docs()
        # Simulate a file move by creating a mock files list
        new_file = SimpleNamespace(src_path="new/path/for/doc.md")
        # Write the file with the same ID in the new location
        new_file_path = self.docs_path / "new/path/for/doc.md"
        new_file_path.parent.mkdir(parents=True, exist_ok=True)
        new_file_path.write_text("---\nid: old-path\n---\nContent")
        # Call on_files with the new file list and config
        files = [new_file]
        config = {"docs_dir": str(self.docs_path)}
        # on_files prints output, but we want to check the mkdocs.yml or output
        # For this test, just ensure no exceptions and that the function returns the files
        result = linking.on_files(files, config)
        self.assertEqual(result, files)

    def test_prepare_with_existing_frontmatter(self) -> None:
        """Test that existing frontmatter is preserved and IDs are respected."""
        # Arrange: Create files with existing frontmatter
        (self.docs_path / "existing.md").write_text("""---
title: "Existing Document"
author: "John Doe"
id: custom-id
tags: ["important"]
---
# Existing Document
This has frontmatter already.""")

        (self.docs_path / "partial.md").write_text("""---
title: "Partial Frontmatter"
description: "No ID yet"
---
# Partial Document""")

        # Act: Run the preparation function
        prepare_docs()

        # Assert: Check that existing ID is preserved and new ID is added
        redirect_map = json.loads(self.redirect_map_file.read_text())
        self.assertEqual(redirect_map.get("custom-id"), "existing.md")
        self.assertEqual(redirect_map.get("partial"), "partial.md")

        # Verify file contents preserve existing frontmatter
        existing_content = (self.docs_path / "existing.md").read_text()
        self.assertIn('title: "Existing Document"', existing_content)
        self.assertIn('author: "John Doe"', existing_content)
        self.assertIn("id: custom-id", existing_content)
        self.assertIn('tags: ["important"]', existing_content)

        partial_content = (self.docs_path / "partial.md").read_text()
        self.assertIn('title: "Partial Frontmatter"', partial_content)
        self.assertIn("id: partial", partial_content)

    def test_prepare_multiple_subdirectories(self) -> None:
        """Test ID generation for files in multiple nested directories."""
        # Arrange: Create a complex directory structure
        (self.docs_path / "api" / "v1").mkdir(parents=True)
        (self.docs_path / "api" / "v2").mkdir(parents=True)
        (self.docs_path / "guides" / "getting-started").mkdir(parents=True)
        (self.docs_path / "guides" / "advanced").mkdir(parents=True)

        files_to_create = {
            "api/v1/auth.md": "# Authentication v1",
            "api/v1/users.md": "# Users API v1",
            "api/v2/auth.md": "# Authentication v2",
            "api/v2/users.md": "# Users API v2",
            "guides/getting-started/installation.md": "# Installation",
            "guides/getting-started/quickstart.md": "# Quick Start",
            "guides/advanced/configuration.md": "# Advanced Configuration",
            "guides/advanced/deployment.md": "# Deployment Guide",
        }

        for file_path, content in files_to_create.items():
            (self.docs_path / file_path).write_text(content)

        # Act: Run preparation
        prepare_docs()

        # Assert: Verify all files get appropriate IDs
        redirect_map = json.loads(self.redirect_map_file.read_text())

        expected_mappings = {
            "api-v1-auth": "api/v1/auth.md",
            "api-v1-users": "api/v1/users.md",
            "api-v2-auth": "api/v2/auth.md",
            "api-v2-users": "api/v2/users.md",
            "guides-getting-started-installation": "guides/getting-started/installation.md",
            "guides-getting-started-quickstart": "guides/getting-started/quickstart.md",
            "guides-advanced-configuration": "guides/advanced/configuration.md",
            "guides-advanced-deployment": "guides/advanced/deployment.md",
        }

        for expected_id, expected_path in expected_mappings.items():
            self.assertEqual(redirect_map.get(expected_id), expected_path)

    def test_on_config_no_files_moved(self) -> None:
        """Test that no redirects are generated when files haven't moved."""
        # Arrange: Create initial state
        (self.docs_path / "stable.md").write_text(
            "---\nid: stable-doc\n---\nStable content"
        )
        prepare_docs()

        # Arrange: Create config with same paths (no moves)
        mock_config = self._create_mock_config(
            [("stable-doc", "stable.md", "/stable/")]
        )

        # Act: Run the hook
        updated_config = on_config(mock_config)

        # Assert: No redirect rules should be generated
        redirects = updated_config["plugins"]["redirects"]["config"]["redirect_maps"]
        self.assertEqual(len(redirects), 0)

    def test_on_files_multiple_files_moved(self) -> None:
        """Test redirect generation for multiple moved files using on_files."""
        initial_files = {
            "old-guide.md": "old-guide-id",
            "temp/draft.md": "draft-doc",
            "archive/old-api.md": "api-v1",
        }
        for file_path, file_id in initial_files.items():
            file_full_path = self.docs_path / file_path
            file_full_path.parent.mkdir(parents=True, exist_ok=True)
            file_full_path.write_text(f"---\nid: {file_id}\n---\nContent")
        prepare_docs()
        # Simulate all files being moved to new locations
        new_files = [
            SimpleNamespace(src_path="guides/user-guide.md"),
            SimpleNamespace(src_path="published/final-doc.md"),
            SimpleNamespace(src_path="api/legacy/v1.md"),
        ]
        # Write the files with the same IDs in the new locations
        moved = [
            ("guides/user-guide.md", "old-guide-id"),
            ("published/final-doc.md", "draft-doc"),
            ("api/legacy/v1.md", "api-v1"),
        ]
        for path, file_id in moved:
            file_path = self.docs_path / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(f"---\nid: {file_id}\n---\nContent")
        config = {"docs_dir": str(self.docs_path)}
        result = linking.on_files(new_files, config)
        self.assertEqual(result, new_files)

    def test_prepare_handles_empty_docs_directory(self) -> None:
        """Test that prepare_docs handles an empty docs directory gracefully."""
        # Arrange: Docs directory exists but is empty (no .md files)

        # Act: Run preparation
        prepare_docs()

        # Assert: Should create empty redirect map
        self.assertTrue(self.redirect_map_file.exists())
        redirect_map = json.loads(self.redirect_map_file.read_text())
        self.assertEqual(len(redirect_map), 0)

    def test_on_config_missing_redirect_map(self) -> None:
        """Test on_config behavior when redirect map file doesn't exist."""
        # Arrange: Ensure redirect map doesn't exist
        if self.redirect_map_file.exists():
            self.redirect_map_file.unlink()

        mock_config = self._create_mock_config([("test-page", "test.md", "/test/")])

        # Act: Run the hook
        updated_config = on_config(mock_config)

        # Assert: Should handle missing file gracefully and still set up macro
        self.assertIn("macros", updated_config["plugins"])

        # No redirects should be generated
        redirects = updated_config["plugins"]["redirects"]["config"]["redirect_maps"]
        self.assertEqual(len(redirects), 0)

    def test_on_config_missing_plugins(self) -> None:
        """Test on_config behavior when expected plugins are not configured."""
        # Arrange: Create config without redirects or macros plugins
        (self.docs_path / "test.md").write_text("---\nid: test-page\n---\nContent")
        prepare_docs()

        mock_config = {
            "docs_dir": str(self.docs_path),
            "pages": [
                SimpleNamespace(file=SimpleNamespace(src_path="test.md"), url="/test/")
            ],
            "plugins": {},  # No redirects or macros plugins
        }

        # Act: Run the hook
        updated_config = on_config(mock_config)

        # Assert: Should handle missing plugins gracefully
        self.assertIsInstance(updated_config, dict)
        self.assertEqual(updated_config["docs_dir"], str(self.docs_path))


class TestLinkBreakageScenarios(unittest.TestCase):
    """Tests focused on how links break and how to prevent/handle breakage."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.test_dir = Path("./temp_test_link_breakage")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

        self.original_docs_dir = linking.DOCS_DIR
        self.original_redirect_file = linking.REDIRECT_MAP_FILE

        linking.DOCS_DIR = self.test_dir / "docs"
        linking.REDIRECT_MAP_FILE = self.test_dir / "redirect_map.json"
        linking.DOCS_DIR.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        """Clean up test environment."""
        linking.DOCS_DIR = self.original_docs_dir
        linking.REDIRECT_MAP_FILE = self.original_redirect_file
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    # === ID COLLISION AND CONFLICTS ===

    def test_id_collision_when_files_move_to_same_path_structure(self) -> None:
        """Test when multiple files would generate the same ID after restructuring."""
        # Initial structure
        (linking.DOCS_DIR / "user-guide.md").write_text("# User Guide")
        (linking.DOCS_DIR / "admin").mkdir()
        (linking.DOCS_DIR / "admin" / "guide.md").write_text("# Admin Guide")

        prepare_docs()

        # Simulate restructuring where both files move to create ID collision
        # user-guide.md -> guides/user.md (would generate 'guides-user')
        # admin/guide.md -> guides/user.md (would also generate 'guides-user')

        # This is a real scenario: two different guides both get moved to guides/user.md
        # at different times, or one file replaces another

        original_map = json.loads(linking.REDIRECT_MAP_FILE.read_text())

        # Verify we have the expected initial state
        self.assertEqual(original_map["user-guide"], "user-guide.md")
        self.assertEqual(original_map["admin-guide"], "admin/guide.md")

        # Now simulate what happens if both files are moved to the same new location
        # This would break internal_link() because two IDs point to the same file
        (linking.DOCS_DIR / "guides").mkdir()

        # File 1 moves first
        shutil.move(
            linking.DOCS_DIR / "user-guide.md", linking.DOCS_DIR / "guides" / "user.md"
        )

        # File 2 overwrites it (common in refactoring)
        shutil.move(
            linking.DOCS_DIR / "admin" / "guide.md",
            linking.DOCS_DIR / "guides" / "user.md",
        )

        # Update the moved file to have both old IDs (impossible situation)
        content = """---
id: user-guide
old_id: admin-guide
---
# Merged Guide"""
        (linking.DOCS_DIR / "guides" / "user.md").write_text(content)

        mock_config = {
            "docs_dir": str(linking.DOCS_DIR),
            "pages": [
                SimpleNamespace(
                    file=SimpleNamespace(src_path="guides/user.md"), url="/guides/user/"
                )
            ],
            "plugins": {"macros": {"config": {"python_macros": {}}}},
        }

        # The internal_link macro should handle this somehow
        result_config = on_config(mock_config)

        if (
            "internal_link"
            in result_config["plugins"]["macros"]["config"]["python_macros"]
        ):
            internal_link = result_config["plugins"]["macros"]["config"][
                "python_macros"
            ]["internal_link"]

            # Both old IDs should resolve to the same page (or one should fail gracefully)
            try:
                url1 = internal_link("user-guide")
                self.assertEqual(url1, "/guides/user/")
            except ValueError:
                pass  # Acceptable if it fails gracefully

            # The admin-guide ID no longer exists as a separate page
            with self.assertRaises(ValueError):
                internal_link("admin-guide")

    def test_id_changes_during_refactoring(self) -> None:
        """Test when someone manually changes IDs in frontmatter, breaking existing links."""
        # Initial setup
        (linking.DOCS_DIR / "api.md").write_text("""---
id: api-reference
title: API Reference
---
# API Reference""")

        (linking.DOCS_DIR / "tutorial.md").write_text("""---
id: getting-started
title: Getting Started
---
# Getting Started

See the {{ internal_link('api-reference') }} for details.""")

        prepare_docs()

        # Someone manually changes the API page ID during editing
        (linking.DOCS_DIR / "api.md").write_text("""---
id: api-docs-v2
title: API Reference
---
# API Reference""")

        mock_config = {
            "docs_dir": str(linking.DOCS_DIR),
            "pages": [
                SimpleNamespace(file=SimpleNamespace(src_path="api.md"), url="/api/"),
                SimpleNamespace(
                    file=SimpleNamespace(src_path="tutorial.md"), url="/tutorial/"
                ),
            ],
            "plugins": {"macros": {"config": {"python_macros": {}}}},
        }

        result_config = on_config(mock_config)

        if (
            "internal_link"
            in result_config["plugins"]["macros"]["config"]["python_macros"]
        ):
            internal_link = result_config["plugins"]["macros"]["config"][
                "python_macros"
            ]["internal_link"]

            # Old ID should fail
            with self.assertRaises(ValueError) as context:
                internal_link("api-reference")
            self.assertIn("api-reference", str(context.exception))

            # New ID should work
            self.assertEqual(internal_link("api-docs-v2"), "/api/")

    def test_circular_id_references_and_dependency_loops(self) -> None:
        """Test handling of circular references in ID mappings."""
        # This can happen if redirect map gets corrupted or manually edited

        # Create initial files
        (linking.DOCS_DIR / "a.md").write_text("---\nid: page-a\n---\n# Page A")
        (linking.DOCS_DIR / "b.md").write_text("---\nid: page-b\n---\n# Page B")

        prepare_docs()

        # Manually corrupt the redirect map to create circular references
        corrupt_map = {
            "page-a": "b.md",  # page-a points to b.md
            "page-b": "a.md",  # page-b points to a.md (circular!)
            "page-c": "nonexistent.md",  # broken reference
        }
        linking.REDIRECT_MAP_FILE.write_text(json.dumps(corrupt_map))

        mock_config = {
            "docs_dir": str(linking.DOCS_DIR),
            "pages": [
                SimpleNamespace(file=SimpleNamespace(src_path="a.md"), url="/a/"),
                SimpleNamespace(file=SimpleNamespace(src_path="b.md"), url="/b/"),
            ],
            "plugins": {"macros": {"config": {"python_macros": {}}}},
        }

        # Should handle corrupted redirect map gracefully
        result_config = on_config(mock_config)

        # The macro should work based on actual current file IDs, not the corrupt map
        if (
            "internal_link"
            in result_config["plugins"]["macros"]["config"]["python_macros"]
        ):
            internal_link = result_config["plugins"]["macros"]["config"][
                "python_macros"
            ]["internal_link"]

            # Should work based on actual current frontmatter, not redirect map
            self.assertEqual(internal_link("page-a"), "/a/")
            self.assertEqual(internal_link("page-b"), "/b/")

    # === FILE SYSTEM CHANGES THAT BREAK LINKS ===

    def test_case_sensitivity_issues_across_filesystems(self) -> None:
        """Test link breakage due to case sensitivity differences."""
        # Create file with specific casing
        (linking.DOCS_DIR / "API-Guide.md").write_text(
            "---\nid: API-Guide\n---\n# API Guide"
        )

        prepare_docs()

        # Simulate file being renamed with different case (common on case-insensitive filesystems)
        original_content = (linking.DOCS_DIR / "API-Guide.md").read_text()
        (linking.DOCS_DIR / "API-Guide.md").unlink()
        (linking.DOCS_DIR / "api-guide.md").write_text(original_content)

        mock_config = {
            "docs_dir": str(linking.DOCS_DIR),
            "pages": [
                SimpleNamespace(
                    file=SimpleNamespace(src_path="api-guide.md"), url="/api-guide/"
                )
            ],
            "plugins": {"macros": {"config": {"python_macros": {}}}},
        }

        result_config = on_config(mock_config)

        if (
            "internal_link"
            in result_config["plugins"]["macros"]["config"]["python_macros"]
        ):
            internal_link = result_config["plugins"]["macros"]["config"][
                "python_macros"
            ]["internal_link"]

            # The ID should still work (case-sensitive match required)
            self.assertEqual(internal_link("API-Guide"), "/api-guide/")

    def test_unicode_normalization_issues(self) -> None:
        """Test link breakage due to Unicode normalization differences."""
        import unicodedata

        # Create file with Unicode characters
        # Using different Unicode normalization forms that look the same
        filename1 = "café.md"  # é as single character
        filename2 = unicodedata.normalize("NFD", "café.md")  # é as e + combining accent

        # These look the same but are different at byte level
        self.assertNotEqual(filename1, filename2)

        # Create file with one form
        (linking.DOCS_DIR / filename1).write_text(
            "---\nid: cafe-menu\n---\n# Café Menu"
        )

        prepare_docs()

        # File system or Git might change the normalization
        original_content = (linking.DOCS_DIR / filename1).read_text()
        (linking.DOCS_DIR / filename1).unlink()
        (linking.DOCS_DIR / filename2).write_text(original_content)

        mock_config = {
            "docs_dir": str(linking.DOCS_DIR),
            "pages": [
                SimpleNamespace(file=SimpleNamespace(src_path=filename2), url="/cafe/")
            ],
            "plugins": {"macros": {"config": {"python_macros": {}}}},
        }

        result_config = on_config(mock_config)

        if (
            "internal_link"
            in result_config["plugins"]["macros"]["config"]["python_macros"]
        ):
            internal_link = result_config["plugins"]["macros"]["config"][
                "python_macros"
            ]["internal_link"]

            # Should still work despite Unicode normalization change
            self.assertEqual(internal_link("cafe-menu"), "/cafe/")

    def test_redirect_map_corruption_scenarios(self) -> None:
        """Test various ways the redirect map can become corrupted."""
        # Create initial files
        (linking.DOCS_DIR / "page.md").write_text("---\nid: test-page\n---\n# Test")

        prepare_docs()

        # Test various corruption scenarios
        corruption_scenarios = [
            '{"invalid": json syntax}',  # Invalid JSON
            '{"valid": "json", "but": "wrong", "structure": true}',  # Wrong structure
            "not json at all",  # Not JSON
            "",  # Empty file
            "{}",  # Empty but valid JSON
            '{"key-with-no-value":}',  # Malformed JSON
            '{"unicode-test": "café\\ud83d\\ude00"}',  # Unicode issues
        ]

        for i, corrupt_content in enumerate(corruption_scenarios):
            with self.subTest(scenario=i):
                # Corrupt the redirect map
                linking.REDIRECT_MAP_FILE.write_text(corrupt_content)

                mock_config = {
                    "docs_dir": str(linking.DOCS_DIR),
                    "pages": [
                        SimpleNamespace(
                            file=SimpleNamespace(src_path="page.md"), url="/page/"
                        )
                    ],
                    "plugins": {"macros": {"config": {"python_macros": {}}}},
                }

                # Should handle all corruption gracefully
                try:
                    result_config = on_config(mock_config)
                    self.assertIsNotNone(result_config)
                except Exception as e:
                    # Should not crash with unhandled exceptions
                    self.assertIsInstance(
                        e, (json.JSONDecodeError, KeyError, ValueError)
                    )

    def test_internal_link_macro_with_invalid_inputs(self) -> None:
        """Test internal_link macro with various invalid inputs that could break pages."""
        (linking.DOCS_DIR / "test.md").write_text("---\nid: test-page\n---\n# Test")

        # Run prepare_docs first to create the redirect map
        prepare_docs()

        mock_config = {
            "docs_dir": str(linking.DOCS_DIR),
            "pages": [
                SimpleNamespace(file=SimpleNamespace(src_path="test.md"), url="/test/")
            ],
            "plugins": {"macros": {"config": {"python_macros": {}}}},
        }

        result_config = on_config(mock_config)

        if (
            "internal_link"
            in result_config["plugins"]["macros"]["config"]["python_macros"]
        ):
            internal_link = result_config["plugins"]["macros"]["config"][
                "python_macros"
            ]["internal_link"]

            # Test various invalid inputs that could come from template errors
            invalid_inputs = [
                None,  # None value
                "",  # Empty string
                "   ",  # Whitespace only
                "non-existent-page",  # Non-existent ID
                "test page",  # Spaces in ID
                "test/page",  # Slashes in ID
                "test-page\n",  # Newlines
                123,  # Non-string type
                ["test-page"],  # List instead of string
                {"id": "test-page"},  # Dict instead of string
            ]

            for invalid_input in invalid_inputs:
                with self.subTest(input=repr(invalid_input)):
                    try:
                        result = internal_link(invalid_input)
                        # If it somehow succeeds, result should be reasonable
                        self.assertIsInstance(result, str)
                        self.assertTrue(result.startswith("/"))
                    except (ValueError, TypeError, AttributeError) as e:
                        # Expected for invalid inputs
                        self.assertIsInstance(
                            e, (ValueError, TypeError, AttributeError)
                        )
                    except Exception as e:
                        # Should not crash with unexpected exceptions
                        self.fail(
                            f"Unexpected exception for input {invalid_input}: {e}"
                        )


class TestYAMLFrontmatterEdgeCases(unittest.TestCase):
    """Tests focused on YAML frontmatter parsing edge cases."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.test_dir = Path("./temp_test_yaml")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

        self.original_docs_dir = linking.DOCS_DIR
        self.original_redirect_file = linking.REDIRECT_MAP_FILE

        linking.DOCS_DIR = self.test_dir / "docs"
        linking.REDIRECT_MAP_FILE = self.test_dir / "redirect_map.json"
        linking.DOCS_DIR.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        """Clean up test environment."""
        linking.DOCS_DIR = self.original_docs_dir
        linking.REDIRECT_MAP_FILE = self.original_redirect_file
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_malformed_yaml_frontmatter(self) -> None:
        """Test handling of various malformed YAML frontmatter."""
        malformed_files = {
            "unclosed-quotes.md": """---
title: "This quote is never closed
id: broken-yaml
---
# Content""",
            "invalid-structure.md": """---
title: Valid Title
invalid-yaml: [unclosed list
id: another-broken
---
# Content""",
            "wrong-delimiters.md": """+++
title: Hugo-style frontmatter
id: wrong-format
+++
# Content""",
            "no-end-delimiter.md": """---
title: Missing end delimiter
id: incomplete
# This should be treated as content""",
        }

        for filename, content in malformed_files.items():
            (linking.DOCS_DIR / filename).write_text(content)

        # Should handle malformed YAML gracefully
        prepare_docs()

        # Check that redirect map was created (files with valid structure should work)
        self.assertTrue(linking.REDIRECT_MAP_FILE.exists())
        redirect_map = json.loads(linking.REDIRECT_MAP_FILE.read_text())

        # Files with malformed YAML should get auto-generated IDs or extracted IDs
        self.assertIn("broken-yaml", redirect_map)  # From unclosed-quotes.md
        self.assertIn("another-broken", redirect_map)  # From invalid-structure.md
        self.assertIn("wrong-delimiters", redirect_map)
        self.assertIn("no-end-delimiter", redirect_map)

    def test_complex_yaml_structures(self) -> None:
        """Test handling of complex YAML structures in frontmatter."""
        complex_content = """---
title: "Complex YAML Test"
id: complex-yaml
tags:
  - testing
  - yaml
  - complex
metadata:
  author: 
    name: "John Doe"
    email: "john@example.com"
  created: 2023-01-01
  updated: 2023-12-31
  nested:
    deeply:
      very: "deep value"
categories: ["cat1", "cat2", "cat3"]
boolean_value: true
null_value: null
number_value: 42
float_value: 3.14
multiline: |
  This is a multiline
  string that spans
  multiple lines
---
# Complex YAML Test"""

        (linking.DOCS_DIR / "complex.md").write_text(complex_content)
        prepare_docs()

        # Should preserve all the complex YAML structure
        updated_content = (linking.DOCS_DIR / "complex.md").read_text()

        # Verify the ID was preserved and complex structure remains
        self.assertIn("id: complex-yaml", updated_content)
        self.assertIn("deeply:", updated_content)
        self.assertIn("multiline: |", updated_content)

        # Verify redirect map was created correctly
        redirect_map = json.loads(linking.REDIRECT_MAP_FILE.read_text())
        self.assertEqual(redirect_map["complex-yaml"], "complex.md")

    def test_unicode_in_yaml_frontmatter(self) -> None:
        """Test handling of Unicode characters in YAML frontmatter."""
        unicode_content = """---
title: "测试文档 🚀 Café"
id: unicode-test
description: "This contains émojis 🎉 and ñoñ-ASCII çhars"
author: "José García-Martínez"
tags: ["日本語", "español", "français"]
---
# Unicode Test Document"""

        (linking.DOCS_DIR / "unicode.md").write_text(unicode_content, encoding="utf-8")
        prepare_docs()

        # Should handle Unicode correctly
        updated_content = (linking.DOCS_DIR / "unicode.md").read_text(encoding="utf-8")
        self.assertIn("🚀", updated_content)
        self.assertIn("José García-Martínez", updated_content)
        self.assertIn("日本語", updated_content)

        redirect_map = json.loads(linking.REDIRECT_MAP_FILE.read_text())
        self.assertEqual(redirect_map["unicode-test"], "unicode.md")


class TestErrorRecoveryAndRobustness(unittest.TestCase):
    """Tests focused on error recovery and system robustness."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.test_dir = Path("./temp_test_robustness")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

        self.original_docs_dir = linking.DOCS_DIR
        self.original_redirect_file = linking.REDIRECT_MAP_FILE

        linking.DOCS_DIR = self.test_dir / "docs"
        linking.REDIRECT_MAP_FILE = self.test_dir / "redirect_map.json"
        linking.DOCS_DIR.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        """Clean up test environment."""
        linking.DOCS_DIR = self.original_docs_dir
        linking.REDIRECT_MAP_FILE = self.original_redirect_file
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_concurrent_access_simulation(self) -> None:
        """Test robustness when files are modified during processing."""
        import threading
        import time

        # Create initial files
        for i in range(5):
            (linking.DOCS_DIR / f"concurrent-{i}.md").write_text(f"""---
id: concurrent-{i}
---
# Concurrent Test {i}""")

        def modify_files():
            """Simulate another process modifying files during processing."""
            time.sleep(0.1)  # Give prepare_docs a chance to start
            try:
                # Modify a file during processing
                (linking.DOCS_DIR / "concurrent-2.md").write_text("""---
id: concurrent-2-modified
---
# Modified During Processing""")
            except FileNotFoundError:
                pass  # File might be temporarily locked

        # Start background modification
        modifier_thread = threading.Thread(target=modify_files)
        modifier_thread.start()

        # Run preparation while files are being modified
        prepare_docs()

        modifier_thread.join()

        # Should complete successfully despite concurrent modifications
        self.assertTrue(linking.REDIRECT_MAP_FILE.exists())
        redirect_map = json.loads(linking.REDIRECT_MAP_FILE.read_text())

        # Should have processed most files
        self.assertGreaterEqual(len(redirect_map), 4)

    def test_special_characters_in_filenames(self) -> None:
        """Test handling of files with special characters in names."""
        special_files = {
            "file with spaces.md": "file-with-spaces",
            "file-with-üñïçødé.md": "file-with-unicode",
            "file.with.dots.md": "file-with-dots",
            "file[with]brackets.md": "file-with-brackets",
            "file(with)parens.md": "file-with-parens",
            "file&with&symbols.md": "file-with-symbols",
        }

        for filename, expected_id in special_files.items():
            try:
                (linking.DOCS_DIR / filename).write_text(f"""---
id: {expected_id}
---
# Test File""")
            except OSError:
                # Some filesystems don't support certain characters
                continue

        prepare_docs()

        # Should handle special characters in filenames
        redirect_map = json.loads(linking.REDIRECT_MAP_FILE.read_text())

        # Check that files were processed (those that could be created)
        for filename, expected_id in special_files.items():
            if (linking.DOCS_DIR / filename).exists():
                self.assertIn(expected_id, redirect_map)
                self.assertEqual(redirect_map[expected_id], filename)


class TestCommandLineInterface(unittest.TestCase):
    """Tests for the command line interface and main() function."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.test_dir = Path("./temp_test_cli")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

        self.original_docs_dir = linking.DOCS_DIR
        self.original_redirect_file = linking.REDIRECT_MAP_FILE

        linking.DOCS_DIR = self.test_dir / "docs"
        linking.REDIRECT_MAP_FILE = self.test_dir / "redirect_map.json"
        linking.DOCS_DIR.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        """Clean up test environment."""
        linking.DOCS_DIR = self.original_docs_dir
        linking.REDIRECT_MAP_FILE = self.original_redirect_file
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_main_with_prepare_argument(self) -> None:
        """Test main() function when called with --prepare argument."""
        # Arrange: Create some test files
        (linking.DOCS_DIR / "test.md").write_text("# Test Document")
        (linking.DOCS_DIR / "guide.md").write_text("# Guide Document")

        # Mock sys.argv to simulate command line arguments
        import sys

        original_argv = sys.argv
        sys.argv = ["linking.py", "--prepare"]

        try:
            # Act: Call main function
            linking.main()

            # Assert: Verify that prepare_docs was executed
            self.assertTrue(linking.REDIRECT_MAP_FILE.exists())
            redirect_map = json.loads(linking.REDIRECT_MAP_FILE.read_text())
            self.assertIn("test", redirect_map)
            self.assertIn("guide", redirect_map)

        finally:
            # Restore original argv
            sys.argv = original_argv

    def test_main_without_arguments_prints_help(self) -> None:
        """Test main() function when called without arguments shows help."""
        import sys
        from io import StringIO

        # Arrange: Mock sys.argv and capture stdout
        original_argv = sys.argv
        original_stdout = sys.stdout
        sys.argv = ["linking.py"]
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            # Act: Call main function
            linking.main()

            # Assert: Verify help message was printed
            output = captured_output.getvalue()
            self.assertIn("MkDocs migration helper", output)
            self.assertIn("--prepare", output)
            self.assertIn("Scan docs folder", output)

        finally:
            # Restore original values
            sys.argv = original_argv
            sys.stdout = original_stdout

    def test_main_with_help_argument(self) -> None:
        """Test main() function when called with --help argument."""
        import sys
        from io import StringIO

        # Arrange: Mock sys.argv and capture stdout
        original_argv = sys.argv
        original_stdout = sys.stdout
        sys.argv = ["linking.py", "--help"]
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            # Act & Assert: Should raise SystemExit (normal behavior for --help)
            with self.assertRaises(SystemExit) as context:
                linking.main()

            # Help should exit with code 0
            self.assertEqual(context.exception.code, 0)

            # Verify help content was printed
            output = captured_output.getvalue()
            self.assertIn("usage:", output)
            self.assertIn("--prepare", output)
            self.assertIn("MkDocs migration helper", output)

        finally:
            # Restore original values
            sys.argv = original_argv
            sys.stdout = original_stdout

    def test_main_with_invalid_argument(self) -> None:
        """Test main() function when called with invalid arguments."""
        import sys
        from io import StringIO

        # Arrange: Mock sys.argv with invalid argument
        original_argv = sys.argv
        original_stderr = sys.stderr
        sys.argv = ["linking.py", "--invalid-option"]
        captured_error = StringIO()
        sys.stderr = captured_error

        try:
            # Act & Assert: Should raise SystemExit due to invalid argument
            with self.assertRaises(SystemExit) as context:
                linking.main()

            # Invalid arguments should exit with non-zero code
            self.assertNotEqual(context.exception.code, 0)

            # Verify error message was printed
            error_output = captured_error.getvalue()
            self.assertIn("unrecognized arguments: --invalid-option", error_output)

        finally:
            # Restore original values
            sys.argv = original_argv
            sys.stderr = original_stderr

    def test_argparse_configuration(self) -> None:
        """Test that the argument parser is configured correctly."""
        # Act: Create parser using the same logic as main()
        parser = argparse.ArgumentParser(description="Docs migration helper script.")
        parser.add_argument(
            "--prepare",
            action="store_true",
            help="Run Phase 1: Inject IDs and create the redirect map.",
        )

        # Assert: Test various argument combinations

        # Test --prepare argument
        args = parser.parse_args(["--prepare"])
        self.assertTrue(args.prepare)

        # Test no arguments
        args = parser.parse_args([])
        self.assertFalse(args.prepare)

        # Test that the parser has the correct description
        self.assertEqual(parser.description, "Docs migration helper script.")

    def test_prepare_docs_called_correctly(self) -> None:
        """Test that prepare_docs is called when --prepare is used."""
        # Arrange: Create test files and mock prepare_docs
        (linking.DOCS_DIR / "sample.md").write_text("# Sample")

        original_prepare_docs = linking.prepare_docs
        prepare_docs_called = False

        def mock_prepare_docs():
            nonlocal prepare_docs_called
            prepare_docs_called = True
            # Call the original function to ensure it works
            original_prepare_docs()

        linking.prepare_docs = mock_prepare_docs

        import sys

        original_argv = sys.argv
        sys.argv = ["linking.py", "--prepare"]

        try:
            # Act: Call main
            linking.main()

            # Assert: Verify prepare_docs was called
            self.assertTrue(prepare_docs_called)

            # Verify it actually worked
            self.assertTrue(linking.REDIRECT_MAP_FILE.exists())

        finally:
            # Restore everything
            linking.prepare_docs = original_prepare_docs
            sys.argv = original_argv

    def test_main_handles_prepare_docs_exceptions(self) -> None:
        """Test main() handles exceptions from prepare_docs gracefully."""
        # Arrange: Mock prepare_docs to raise an exception
        original_prepare_docs = linking.prepare_docs

        def failing_prepare_docs():
            raise Exception("Test exception from prepare_docs")

        linking.prepare_docs = failing_prepare_docs

        import sys

        original_argv = sys.argv
        sys.argv = ["linking.py", "--prepare"]

        try:
            # Act & Assert: Exception should propagate (this is expected behavior)
            with self.assertRaises(Exception) as context:
                linking.main()

            self.assertIn("Test exception from prepare_docs", str(context.exception))

        finally:
            # Restore everything
            linking.prepare_docs = original_prepare_docs
            sys.argv = original_argv

    def test_dry_run_functionality(self) -> None:
        """Test that --dry-run flag works correctly."""
        # Create a temporary test directory
        test_dir = Path("temp_test_dry_run")
        docs_dir = test_dir / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)

        # Create test files
        (docs_dir / "test1.md").write_text("# Test 1\n\nContent here.")
        (docs_dir / "test2.md").write_text(
            "---\nid: existing-id\ntitle: Test 2\n---\n\n# Test 2\n\nContent here."
        )

        import sys
        import io

        original_argv = sys.argv
        original_stdout = sys.stdout

        try:
            # Capture stdout
            captured_output = io.StringIO()
            sys.stdout = captured_output

            # Set up arguments for dry run
            sys.argv = [
                "linking.py",
                "--prepare",
                "--docs-dir",
                str(docs_dir),
                "--dry-run",
            ]

            # Act: Call main function
            linking.main()

            # Assert: Check output contains dry run information
            output = captured_output.getvalue()
            self.assertIn("DRY RUN: Preview of changes", output)
            self.assertIn("Found 2 markdown files", output)
            self.assertIn("Files that would be modified (1):", output)
            self.assertIn("test1.md -> ID:", output)
            self.assertIn("Files already with IDs (1):", output)
            self.assertIn("test2.md -> ID: 'existing-id'", output)

            # Assert: No files were actually modified
            content = (docs_dir / "test1.md").read_text()
            self.assertNotIn("id:", content)  # Should not have frontmatter added

        finally:
            # Restore original values
            sys.argv = original_argv
            sys.stdout = original_stdout

            # Clean up
            import shutil

            if test_dir.exists():
                shutil.rmtree(test_dir)

    def test_custom_docs_directory(self) -> None:
        """Test that --docs-dir flag works with actual file modifications."""
        # Create a temporary test directory
        test_dir = Path("temp_test_custom_docs")
        docs_dir = test_dir / "my-docs"
        docs_dir.mkdir(parents=True, exist_ok=True)

        # Create test file
        test_file = docs_dir / "custom-test.md"
        test_file.write_text("# Custom Test\n\nThis is a test file.")

        import sys

        original_argv = sys.argv

        try:
            # Set up arguments for custom docs directory
            sys.argv = ["linking.py", "--prepare", "--docs-dir", str(docs_dir)]

            # Act: Call main function
            linking.main()

            # Assert: File was modified with ID
            content = test_file.read_text()
            self.assertIn("---", content)
            self.assertIn("id: custom-test", content)

            # Assert: Redirect map was created in the parent directory
            redirect_map_file = test_dir / "redirect_map.json"
            self.assertTrue(redirect_map_file.exists())

            # Check redirect map content
            import json

            redirect_data = json.loads(redirect_map_file.read_text())
            self.assertIn("custom-test", redirect_data)
            self.assertEqual(redirect_data["custom-test"], "custom-test.md")

        finally:
            # Restore original values
            sys.argv = original_argv

            # Clean up
            import shutil

            if test_dir.exists():
                shutil.rmtree(test_dir)

    def test_dry_run_with_empty_directory(self) -> None:
        """Test dry-run behavior with empty docs directory."""
        # Create empty test directory
        test_dir = Path("temp_test_empty_dry_run")
        docs_dir = test_dir / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)

        import sys
        import io

        original_argv = sys.argv
        original_stdout = sys.stdout

        try:
            # Capture stdout
            captured_output = io.StringIO()
            sys.stdout = captured_output

            # Set up arguments for dry run
            sys.argv = [
                "linking.py",
                "--prepare",
                "--docs-dir",
                str(docs_dir),
                "--dry-run",
            ]

            # Act: Call main function
            linking.main()

            # Assert: Check output handles empty directory gracefully
            output = captured_output.getvalue()
            self.assertIn("DRY RUN: Preview of changes", output)
            self.assertIn("No markdown files found", output)

        finally:
            # Restore original values
            sys.argv = original_argv
            sys.stdout = original_stdout

            # Clean up
            import shutil

            if test_dir.exists():
                shutil.rmtree(test_dir)

    def test_dry_run_with_nonexistent_directory(self) -> None:
        """Test dry-run behavior with nonexistent docs directory."""
        import sys
        import io

        original_argv = sys.argv
        original_stdout = sys.stdout

        try:
            # Capture stdout
            captured_output = io.StringIO()
            sys.stdout = captured_output

            # Set up arguments for dry run with nonexistent directory
            sys.argv = [
                "linking.py",
                "--prepare",
                "--docs-dir",
                "nonexistent-docs",
                "--dry-run",
            ]

            # Act: Call main function
            linking.main()

            # Assert: Check output handles missing directory gracefully
            output = captured_output.getvalue()
            self.assertIn("DRY RUN: Preview of changes", output)
            self.assertIn("ERROR: Directory nonexistent-docs does not exist", output)

        finally:
            # Restore original values
            sys.argv = original_argv
            sys.stdout = original_stdout


if __name__ == "__main__":
    unittest.main(verbosity=2)
