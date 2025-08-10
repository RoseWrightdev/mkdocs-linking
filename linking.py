"""A tool to manage documentation migration for MkDocs.

This script provides two main functions for a documentation refactor:
1.  A preparation step that scans a docs folder, injects a unique,
    permanent ID into the frontmatter of each Markdown file, and creates a
    map of the site's structure before any changes are made.
2.  An MkDocs hook (`on_config`) that runs during the build process to
    dynamically generate 301 redirects for moved files and create a resilient
    internal linking macro.
"""

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple


# --- Configuration ---
# Global constants defining key file paths and metadata keys.
DOCS_DIR: Path = Path('docs')
REDIRECT_MAP_FILE: Path = Path('redirect_map.json')
FRONTMATTER_ID_KEY: str = 'id'


def _get_frontmatter(content: str) -> Tuple[Dict[str, str], int]:
    """Extracts simple key-value frontmatter using only the standard library.

    Args:
        content: The full text content of a file.

    Returns:
        A tuple containing the frontmatter data as a dictionary and the
        character position where the frontmatter section ends.
    """
    # Step 1: Look for a YAML frontmatter block (e.g., ---...---) at the
    # beginning of a file.
    match = re.match(r'^---\s*\n(.*?\n)---\s*\n', content, re.DOTALL)
    if not match:
        return {}, 0

    frontmatter_str: str = match.group(1)
    end_pos: int = len(match.group(0))

    # Step 2: Parse the frontmatter block line-by-line for simple key-value pairs.
    data: Dict[str, str] = {}
    for line in frontmatter_str.strip().split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            data[key.strip()] = value.strip()
    return data, end_pos


def _format_frontmatter_str(data: Dict[str, str]) -> str:
    """Formats a simple dictionary into a YAML-like string."""
    # Step 1: Convert dictionary to YAML-formatted lines.
    lines: List[str] = [f'{key}: {value}' for key, value in data.items()]
    return '\n'.join(lines) + '\n'


def prepare_docs(docs_dir_path: str = None) -> None:
    """Scans docs, injects unique IDs, and creates the redirect map."""
    print('Starting documentation preparation...')
    redirect_map: Dict[str, str] = {}
    
    # Use global variables for when no path specified
    if docs_dir_path is None:
        docs_dir = DOCS_DIR
        redirect_map_file = REDIRECT_MAP_FILE
    else:
        docs_dir = Path(docs_dir_path)
        redirect_map_file = Path(docs_dir_path).parent / 'redirect_map.json'

    # Step 1: Iterate through all markdown files in the documentation directory.
    for md_file in docs_dir.rglob('*.md'):
        # Step 2: Read file content and extract existing frontmatter.
        content: str = md_file.read_text('utf-8')
        frontmatter, end_pos = _get_frontmatter(content)
        page_id: str | None = frontmatter.get(FRONTMATTER_ID_KEY)

        # Step 3: If no permanent ID exists, generate one from the file path,
        # inject it into the frontmatter, and rewrite the file.
        if not page_id:
            relative_path: Path = md_file.relative_to(docs_dir)
            page_id = str(relative_path.with_suffix('')).replace(os.path.sep, '-')
            print(f"  - Assigning ID '{page_id}' to {md_file}")

            frontmatter[FRONTMATTER_ID_KEY] = page_id
            new_frontmatter_str = _format_frontmatter_str(frontmatter)

            body: str = content[end_pos:]
            new_content: str = f'---\n{new_frontmatter_str}---\n{body}'
            md_file.write_text(new_content, 'utf-8')
        else:
            print(f"  - Found existing ID '{page_id}' in {md_file}")

        # Step 4: Add the page's ID and current path to our map. This captures
        # the "before" state of the documentation.
        redirect_map[page_id] = str(md_file.relative_to(docs_dir))

    # Step 5: Write the completed map to a JSON file for persistence. This file
    # will be used by the MkDocs hook to generate redirects.
    redirect_map_file.write_text(json.dumps(redirect_map, indent=2))
    print(f'Preparation complete. Map saved to {redirect_map_file}')


def on_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Generates redirects and sets up the internal link macro for MkDocs."""
    print('Running MkDocs migration hook...')

    # Step 1: Load the "before" state map created by the prepare_docs step.
    # If this file doesn't exist, we cannot generate redirects.
    if not REDIRECT_MAP_FILE.exists():
        print(f'  Warning: {REDIRECT_MAP_FILE} not found. Skipping.')
        return config
    old_paths_map: Dict[str, str] = json.loads(REDIRECT_MAP_FILE.read_text())

    # Step 2: Build the "after" state map by inspecting the pages that
    # MkDocs has discovered for the current build.
    after_paths_map: Dict[str, str] = {}
    id_to_page_map: Dict[str, Any] = {}
    for page in config.get('pages', []):
        abs_path = Path(config['docs_dir']) / page.file.src_path
        content = abs_path.read_text('utf-8')
        frontmatter, _ = _get_frontmatter(content)
        page_id = frontmatter.get(FRONTMATTER_ID_KEY)

        if page_id:
            after_paths_map[page_id] = page.file.src_path
            id_to_page_map[page_id] = page

    # Step 3: Compare the before and after maps to find moved files and
    # dynamically populate the configuration for the mkdocs-redirects plugin.
    redirects = config['plugins'].get('redirects')
    if redirects:
        redirect_rules = redirects['config'].get('redirect_maps', {})
        count = 0
        for page_id, old_path in old_paths_map.items():
            new_path = after_paths_map.get(page_id)
            if new_path and new_path != old_path:
                redirect_rules[old_path] = new_path
                count += 1
        if count > 0:
            print(f'  Generated {count} redirect rules.')
        redirects['config']['redirect_maps'] = redirect_rules

    # Step 4: Define and inject the `internal_link` macro into the
    # mkdocs-macros plugin for resilient, ID-based linking.
    macros = config['plugins'].get('macros')
    if macros:
        def internal_link(page_id: str) -> str:
            """Looks up a page by ID and return its relative URL."""
            target_page = id_to_page_map.get(page_id)
            if not target_page:
                raise ValueError(
                    f"internal_link could not find page with ID: '{page_id}'"
                )
            return str(target_page.url)

        macros['config'].setdefault('python_macros', {})['internal_link'] = (
            internal_link
        )
        print('  `internal_link` macro is ready.')

    return config


def preview_docs(docs_dir_path: str = 'docs') -> None:
    """Shows what the prepare_docs function would do without making changes."""
    docs_dir = Path(docs_dir_path)
    
    print(f"Scanning documentation directory: {docs_dir}")
    
    # Step 1: Validate that the documentation directory exists.
    if not docs_dir.exists():
        print(f"  ERROR: Directory {docs_dir} does not exist")
        return
    
    # Step 2: Find all markdown files in the documentation directory.
    md_files = list(docs_dir.rglob('*.md'))
    if not md_files:
        print("  No markdown files found")
        return
    
    print(f"  Found {len(md_files)} markdown files")
    
    files_needing_ids = []
    files_with_ids = []
    
    # Step 3: Analyze each markdown file to determine its current state.
    for md_file in md_files:
        try:
            content = md_file.read_text('utf-8')
            frontmatter, _ = _get_frontmatter(content)
            page_id = frontmatter.get(FRONTMATTER_ID_KEY)
            
            if page_id:
                files_with_ids.append((md_file, page_id))
            else:
                relative_path = md_file.relative_to(docs_dir)
                generated_id = str(relative_path.with_suffix('')).replace(os.path.sep, '-')
                files_needing_ids.append((md_file, generated_id))
        except Exception as e:
            print(f"  Warning: Could not process {md_file}: {e}")
    
    # Step 4: Display files that would be modified with new IDs.
    if files_needing_ids:
        print(f"\nFiles that would be modified ({len(files_needing_ids)}):")
        for md_file, generated_id in files_needing_ids:
            relative_path = md_file.relative_to(docs_dir)
            print(f"  + {relative_path} -> ID: '{generated_id}'")
    
    # Step 5: Display files that already have IDs and would be preserved.
    if files_with_ids:
        print(f"\nFiles already with IDs ({len(files_with_ids)}):")
        for md_file, existing_id in files_with_ids:
            relative_path = md_file.relative_to(docs_dir)
            print(f"  * {relative_path} -> ID: '{existing_id}'")
    
    # Step 6: Show where the redirect map would be created or updated.
    print(f"\nWould create/update redirect map: {Path(docs_dir_path).parent / 'redirect_map.json'}")


def main() -> None:
    """Parses command line arguments and runs the preparation script."""
    parser = argparse.ArgumentParser(
        description='MkDocs migration helper - prepares docs for safe refactoring.',
        prog='linking'
    )
    parser.add_argument(
        '--prepare',
        action='store_true',
        help='Scan docs folder, inject IDs, and create redirect map'
    )
    parser.add_argument(
        '--docs-dir',
        default='docs',
        help='Documentation directory (default: docs)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )   
    args = parser.parse_args()

    if args.prepare:
        if args.dry_run:
            print("DRY RUN: Preview of changes that would be made")
            print("=" * 50)
            preview_docs(args.docs_dir)
        else:
            if args.docs_dir != 'docs':
                prepare_docs(args.docs_dir)
            else:
                prepare_docs()  # Use default behavior for backward compatibility
    else:
        parser.print_help()


if __name__ == '__main__':
    main()