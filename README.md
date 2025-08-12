# **MkDocs Migration Helper**

This repository contains a Python script (linking.py) designed to assist with large-scale documentation refactoring in an [MkDocs](https://www.mkdocs.org/) project. It automates the creation of 301 redirects for moved pages and provides a resilient internal linking mechanism to prevent broken links after a reorganization.

## **Purpose**

When restructuring a documentation site, manually updating all internal links and creating server-side redirects is tedious and error-prone. This script solves that problem by:

1. **Assigning a permanent, unique ID** to every Markdown file.  
2. **Automatically generating a redirect map** for moved files that can be used by the mkdocs-redirects plugin.  
3. **Providing a linking macro** (internal\_link) that uses the permanent ID, making links immune to future file moves.

## **Workflow**

The migration process is managed in three phases.

### **Phase 1: Preparation**

This is a **one-time** setup step to prepare your documentation for the migration.

1. **Run the script in \--prepare mode:**  
   python redirects.py \--prepare

2. **What it does:**  
   * Scans every .md file in the docs/ directory.  
   * Injects a unique id: into the YAML frontmatter of any file that doesn't have one.  
   * Creates a redirect\_map.json file, which is a snapshot of the site's structure *before* any files are moved.

### **Phase 2: Reorganization**

With the preparation complete, you can now manually move your files and folders into the new desired structure. The permanent IDs ensure that the script can track where each file ends up.

### **Phase 3: Build**

Once you have reorganized the files, the script works automatically with the mkdocs build command.

1. **Update mkdocs.yml** to enable the script as a hook (see below).  
2. **Run the build:**  
   mkdocs build

3. **What it does:**  
   * The on\_config function in the script runs automatically.  
   * It compares the current file structure to the redirect\_map.json created in Phase 1\.  
   * It dynamically generates all necessary redirect rules and configures the mkdocs-redirects plugin.  
   * It makes the {{ internal\_link('page-id') }} macro available to the mkdocs-macros plugin.

## **Configuration**

To enable the script, add it to your mkdocs.yml file as a hook.

```yaml
\# mkdocs.yml

\# ... other configurations ...

plugins:  
  \- search  
  \- redirects:  
      \# This map will be populated automatically by the hook.  
      redirect\_maps: {}  
  \- macros:  
      \# The hook will inject the macro function here.  
      python\_macros: {}

\# Add the hook to run the script during the build.  
hooks:  
  \- linking.py
```

## **Prerequisites**

This script relies on two MkDocs plugins. Install them using pip:

pip install mkdocs-redirects mkdocs-macros-plugin
