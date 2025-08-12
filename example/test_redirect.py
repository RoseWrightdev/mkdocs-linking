#!/usr/bin/env python3
"""
Test script to manually verify mkdocs-redirects plugin behavior
"""

import os
import sys
sys.path.insert(0, '/home/rose/Projects/mkdocs-linking/example')

# Test 1: Check if redirects plugin can be imported
try:
    from mkdocs.plugins import get_plugin_logger
    from mkdocs_redirects.plugin import RedirectPlugin
    print("✅ mkdocs-redirects plugin imported successfully")
except ImportError as e:
    print(f"❌ Failed to import mkdocs-redirects: {e}")
    sys.exit(1)

# Test 2: Check if the plugin can create a simple redirect file
try:
    plugin = RedirectPlugin()
    plugin.config = {
        'redirect_maps': {
            'test.md': 'wooo/page.md'
        }
    }
    print("✅ Plugin configuration created")
except Exception as e:
    print(f"❌ Failed to configure plugin: {e}")

print("Manual test completed")
