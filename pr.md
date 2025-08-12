# **MkDocs Migration Helper Implementation**

## **Introduction**

This pull request implements the automated documentation restructuring system outlined in the [migration proposal](main.md). It's best to think of this as the *technical foundation* for the migration described in that proposal. This tool provides a way to handle changing the file tree without breaking both internal and external links—something that's functionally impossible to do by hand due to time constraints.

## **The Problem**

The migration proposal identified the core challenge: how do we reorganize documentation without breaking links? Manual link maintenance simply doesn't scale when you're dealing with dozens of interconnected files. SEO breaks, internal navigation fragments, and future reorganizations become increasingly complex.

## **The Solution**

This implementation delivers a 3-phase automated workflow that transforms a manual, error-prone process into something reliable and painless.

### **Phase 1: Preparation (Before the move)**

```bash
python3 linking.py --prepare
```

The script traverses the current `docs` directory. For each `.md` file, it generates a unique, human-readable ID (based on the path, like `how-to-http-routing`). This ID gets injected into the YAML frontmatter of each file. The script then creates a map of the current structure: `unique_id -> old_path`. This map is saved to `redirect_map.json`.

### **Phase 2: Manual Reorganization**

With the IDs in place, we can now **manually move files and directories** to match the new information architecture. The content of the files is not changed, only their location.

### **Phase 3: Generating Redirects & Fixing Links (Using an `on_config` hook)**

On `mkdocs build`, the hook script runs. It walks the new file structure and creates an "after" map: `unique_id -> new_path`. The script loads the "before" map and compares it with the "after" map. For any `unique_id` where the path has changed, it programmatically injects a redirect rule into the MkDocs configuration.

It also provides the `internal_link` macro for resilient internal linking going forward. Instead of writing a fragile relative link like `[My Link](../../section/another-page.md)`, we will the page's unique ID: `{{ internal_link('another-page-id') }}`. The macro looks up the page's current URL and renders the correct link at build time.

## **What's Implemented**

### **Core Features**

- ID generation: `how-to-guides/http-routing.md` → `how-to-guides-http-routing`
- YAML frontmatter injection without breaking existing metadata
- "Before" and "after" state comparison
- Automatic redirect rule generation
- `internal_link` macro for future-proof linking

### **Additional Features**

- `--dry-run` flag to preview changes
- `--docs-dir` to work with custom directory structures  
- Unicode and special character support
- Graceful handling of malformed YAML

## **Usage**

```bash
# 1. Prepare files with IDs
python3 linking.py --prepare

# 2. Move files manually (Git, file manager, whatever)
git mv docs/old-structure/* docs/new-structure/

# 3. Build - redirects are generated automatically
mkdocs build
```

### **Configuration**

Add to your `mkdocs.yml`:

```yaml
plugins:
  - redirects
  - macros

hooks:
  - linking.py
```

### **Future-Proof Links**

```markdown
<!-- Old fragile way -->
[HTTP Routing Guide](../../how-to/http-routing.md)

<!-- New resilient way -->
{{ internal_link('how-to-guides-http-routing') }}
```

## **Dependencies**

- `mkdocs-redirects`: To handle the 301 redirects from old URLs to new ones
- `mkdocs-macros`: To enable the custom `internal_link` macro

## **Testing**

The implementation includes 41 test cases covering:

- Basic migration functionality
- Link breakage scenarios
- YAML edge cases (malformed frontmatter, Unicode, etc.)
- Performance with large file sets
- CLI functionality

## **Files Modified**

- `linking.py` - The main implementation
- `test_linking.py` - Comprehensive test suite
- `README.md` - Installation and usage documentation

## **What This Enables**

This tool makes the migration outlined in the proposal actually feasible. Instead of spending days manually updating links and risking broken navigation, the entire process becomes:

```bash
python3 linking.py --prepare
# move files to match new structure
mkdocs build
```

All redirects are generated automatically. All internal links can be made future-proof. The foundation is in place for the larger documentation reorganization.
