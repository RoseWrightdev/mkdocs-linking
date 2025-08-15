# **MkDocs Migration Helper**

A command-line utility and plugin hook to support large-scale documentation refactoring for [MkDocs](https://www.mkdocs.org/) projects. 🚀

This tool automates the tedious and error-prone tasks of managing redirects and fixing internal links when you reorganize your documentation, ensuring that your site remains robust and maintainable.

## **Core Features**

* **Permanent Page IDs**: Injects a unique, permanent ID into the frontmatter of every Markdown file, creating a stable reference for each page.  
* **Resilient Internal Linking**: Provides a command to convert fragile relative links (e.g., ../../api/v1.md) into a robust macro format ({{ internal\_link('api-v1-id') }}) that won't break when files are moved.  
* **Automatic Redirect Generation**: When you build your site, the script automatically detects moved files and injects the necessary 301 redirect rules into your mkdocs.yml configuration.

## **Installation**

This script relies on two MkDocs plugins. Install them using pip:

pip install mkdocs-redirects mkdocs-macros-plugin

## **Usage Workflow**

Follow these steps to safely refactor your documentation site.

### **Step 1: Prepare Your Documentation**

This is a **one-time** setup step that prepares your files for refactoring by assigning a unique ID to every page.

1. **Run the script in \--prepare mode:**  
   python linking.py \--prepare

2. **What it does:**  
   * Scans every .md file in your docs/ directory.  
   * Injects a unique id: into the YAML frontmatter of any file that doesn't have one.  
   * Creates a redirect\_map.json file, which is a snapshot of your site's structure *before* any files are moved.

### **Step 2: Convert Internal Links (Optional but Recommended)**

To make your documentation immune to future link breakage, convert all relative Markdown links to use the resilient macro format.

1. **Run the script in \--convert-links mode:**  
   python linking.py \--convert-links

2. **What it does:**  
   * Scans all .md files for relative links pointing to other .md files.  
   * Replaces each link with the internal\_link macro, using the target page's unique ID.

**Before:**See the \[Authentication Guide\](../../api/v1/auth.md) for more details.
**After:**See the \[Authentication Guide\]({{ internal\_link('api-v1-auth') }}) for more details.

### **Step 3: Reorganize Your Files**

With the preparation complete, you can now **manually move your files and folders** into the new desired structure. The permanent IDs ensure that the script can track where each file ends up.

### **Step 4: Configure mkdocs.yml**

To enable the automated features, you must configure the macros plugin and add the linking.py script as a hook in your mkdocs.yml.

\# mkdocs.yml

\# ... other configurations ...

plugins:  
  \- search  
  \- redirects  \# The hook will automatically update mkdocs.yml with a redirect\_maps section  
  \- macros:  
      module\_name: main \# Assumes your macro function is in main.py

\# Add the hook to run the script during the build.  
hooks:  
  \- linking.py

### **Step 5: Build Your Site**

Now, simply run the standard MkDocs build command. The hook will manage the redirects automatically.

mkdocs build

During the build, the linking.py hook compares the new file structure to the original redirect\_map.json and injects redirect rules into mkdocs.yml. Simultaneously, the mkdocs-macros plugin calls the internal\_link function (from main.py) to resolve all macros into the correct, updated relative paths.

## **Command-Line Reference**

| Command                                | Description                                                                         |
| :------------------------------------- | :---------------------------------------------------------------------------------- |
| python linking.py \--prepare           | Scans docs/, injects unique IDs into frontmatter, and creates redirect\_map.json.   |
| python linking.py \--convert-links     | Converts relative Markdown links into the {{ internal\_link(...) }} macro format.   |
| python linking.py \--docs-dir \<path\> | Specifies a custom documentation directory (default is docs).                       |
| python linking.py \--dry-run           | Use with \--prepare to preview which files would be changed without modifying them. |
