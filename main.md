## **Introduction**

I've incorporated the community's feedback from my last proposal to rework the documentation in Next.js, simplifying the process to better align with the needs of our audience and maintainers as networking engineers. While we are still using MkDocs, it's best to think of this as a *migration* due to the substantial changes and scope. This plan is long-term and high-level, and by no means must we follow it exactly. It's important to focus on the goal of improving the user experience through tried and true best practices laid out by [The Grand Unified Theory of Documentation](https://diataxis.fr/) and subsequently SIG Docs.

## **Documentation Outline**
```
outline:
    # "Welcome" serves as the high-level landing page and "front door" to the documentation.
    # Its goal is to orient the user and direct them to the section that best fits their needs.
    # This is NOT the website's landing page.
    # Example: https://kubernetes.io/docs/home/
    - "Welcome"

    # Concepts provides understanding and context. This section builds a user's mental model of the API.
    # It answers "why" questions and explains the concepts behind the API's design.
    # https://diataxis.fr/explanation/
    - "Concepts":
        - "Introduction"                         # What is Gateway API and what core problems does it solve?
        - "Why Gateway API? (A Comparison to Ingress)" # A persuasive but balanced argument for adoption, targeting experienced k8s users.
        - "Core Concepts":                        # The "big ideas" that make Gateway API unique.
            - "The Role-Oriented Model (Ian, Ana, & Chihiro)" # Explains the *who* (personas), the most foundational concept.
            - "Design Principles (Portable, Expressive, Extensible)" # Explains the *how* and *why* of the API's structure.
            - "The Security Model"               # Explains the *safety* and delegation model that results from the role-oriented design.
            - "Policy Attachment"
            - "Service Mesh (GAMMA)"
            - "API Development Methodology"        # Explains how we think about updates to gateway api
            - "Versioning Strategy"                # Core documentation of how API versions evolve and are managed
        - "Use Cases":                            # Connects concepts to real-world scenarios.
            - "Ingress (Managing North-South Traffic)"
            - "Service Mesh (Managing East-West Traffic)"
            - "Cross-Namespace Routing"           # Multi-tenant scenarios requiring routing across namespace boundaries
            - "Backend Protocol Selection"        # Scenarios for choosing appropriate backend communication protocols
            - "Infrastructure Attributes"         # Platform-specific configuration and infrastructure integration patterns
        - "Best Practices": # For users moving from "it works" to "it works well in production."
            - "BackendTLS" # Explicity tell users to not misuse these features -> do's and dont's
            - "Policy Attachment" # ^
            - "CRD Management"
        - "Implementations and Conformance":      # Resources for both implementors and end users seeking compatible solutions
            - "Implementations"                  # list of which proxies/controllers implement the API.
            - "Conformance"                      # Explains what it means to be a conformant implementation.
            - "Comparisons":
                - "1.3"
                - "1.2"
                - "1.1"
                - "1.0"
        - "FAQ"                                   # Frequently asked questions and common troubleshooting guidance
        - "Talks & Presentations":                # For deeper dives and community context.
            - "Future Events"
            - "KubeCon 2024"
            - "KubeCon 2023"
            - "KubeCon 2022"
        - "Glossary"                              # Here we want to have links to all of the jargon we use spefic to Gateway API

    # Tutorials are learning-focused, designed to take a user through a complete, hands-on learning exercise.
    # The tone should be encouraging and guide the user step-by-step.
    # https://diataxis.fr/tutorials/
    - "Tutorials"
        # The Quick Start is for users who want to see value immediately.
        # It should provide the fastest possible path to a working example, ideally with a docker image and a frontend visualizing whats happening.
        # https://react.dev/learn
        - "Quick Start"
        # Hello World is for users who want to understand the fundamental resources and how they connect.
        # It's a more deliberate, foundational walkthrough than the Quick Start.
        - "Hello World: Your First Gateway"
        # Real-world examples and patterns from various implementers like Envoy Gateway
        - "Examples from Implementers"           # Concrete implementations and patterns from the ecosystem

    # How-to Guides are goal-oriented recipes for users who already know what they want to accomplish.
    # They should be concise, focused on a single task, and easy to follow.
    # https://diataxis.fr/how-to-guides/
    - "How-to Guides":
        - "Configure a Simple Gateway"       # The most basic, foundational guide.
        - "HTTP Routing"                     # Covers common path/header/query param routing.
        - "gRPC Routing"                     # Specific guidance for a key L7 protocol.
        - "TCP Routing"                      # For L4 use cases.
        - "TLS Configuration"                # Covers certificates, termination, and other security aspects.
        - "Traffic Splitting"                # For canary releases and blue/green deployments.
        - "HTTP Header Modification"         # A common, practical need for manipulating requests/responses.
        - "HTTP Redirect & Rewrite"          # Covers URL rewrites and permanent/temporary redirects.
        - "HTTP Request Mirroring"           # For traffic shadowing and non-disruptive testing.
        - "Backend Protocol"                 # How to specify protocols like HTTP/2 or gRPC to the backend.
        - "Cross-Namespace Routing"          # Enables routing across different namespaces for multi-tenant scenarios.
        - "Backend Protocol Selection"       # Guide for configuring backend communication protocols.
        - "Infrastructure Attributes"        # How to configure infrastructure-specific settings and annotations.
        - "Migrating from Ingress"           # A critical guide for a huge portion of the user base. Should address common patterns. Frictions. Etc.
        - "Implementers Guide"               # A key guide for the vendor/provider ecosystem building controllers.

    # Reference is for technical, factual information. It should be accurate, comprehensive, and example-driven.
    # The audience is users and implementers who need to look up specific details.
    # https://diataxis.fr/reference/
    - "API Reference":
        - "Full Specification":                   # The canonical, formal API spec. The ultimate source of truth, aimed at implementers.
        - "Standard"
        - "Experimental"
        - "API Types":                            # Practical, example-rich reference pages for day-to-day use.
            - "Gateway"
            - "GatewayClass"
            - "Routes":
                - "(HTTP, gRPC, TCP, etc.)"
            - "Policies":
                - "(BackendTLS, BackendTraffic, etc.)"
            - "ReferenceGrant"

    # Enhancement Proposals (GEPs) - Design documents and feature requests
    # Contains material about the state of feature requests and API evolution proposals
    - "Enhancement Proposals (GEPs)":
        - "Process Overview"                      # Explains the GEP process
        - "Standard":                             # Includes all standard category GEPs
            - "GEP-XXXX: Name"
        - "Experimental":                         # Includes all experimental category GEPs
            - "GEP-XXXX: Name"
        - "Provisional":                          # Includes all provisional category GEPs
            - "GEP-XXXX: Name"
        - "Other Categories":                     # Additional GEP categories beyond the core three
            - "GEP-XXXX: Name"

    # Contributing is for people who want to work on the project itself.
    - "Contributing":
        - "Getting Started":                        # The main on-ramp for new contributors. Should be very welcoming.
            - "Project Organization & Working Groups" # Explains who's who and the project structure.
            - "Finding an Issue to Work On"        # Actionable steps to making a first contribution.
        - "Contributor Guides":                     # The "handbook" for active and aspiring contributors.
            - "Contributor Ladder"                # The "career path" - explains roles and expectations at each level.
            - "Developer Guide (Setup & Testing)" # The primary "how-to" guide for setting up the development environment.
            - "Navigating the Codebase"           # A map of the repository.
            - "Release Cycle"                     # Explains the process and cadence of new releases.
            - "Style Guide"                       # Code and documentation style requirements.

```

## **mkdocs.yml**

We explicitly declare the navigation so we can control the order of the navigation elements.

```
  site_name: GatewayAPI
  theme:
    name: readthedocs
  repo_url: https://github.com/kubernetes-sigs/gateway-api
  plugins:
    - search
    - macros
    - redirects
  nav:
    - "Welcome": "welcome.md"
    - "Concepts":
        - "Introduction": "concepts/introduction.md"
        - "Why Gateway API? (A Comparison to Ingress)": "concepts/why-gateway-api.md"
        - "Core Concepts":
            - "The Role-Oriented Model (Ian, Ana, & Chihiro)": "concepts/core-concepts/role-oriented-model.md"
            - "Design Principles (Portable, Expressive, Extensible)": "concepts/core-concepts/design-principles.md"
            - "The Security Model": "concepts/core-concepts/security-model.md"
            - "Policy Attachment": "concepts/core-concepts/policy-attachment.md"
            - "Service Mesh (GAMMA)": "concepts/core-concepts/service-mesh-gamma.md"
            - "API Development Methodology": "concepts/core-concepts/api-development-methodology.md"
            - "Versioning Strategy": "concepts/core-concepts/versioning-strategy.md"
        - "Use Cases":
            - "Ingress (Managing North-South Traffic)": "concepts/use-cases/ingress.md"
            - "Service Mesh (Managing East-West Traffic)": "concepts/use-cases/service-mesh.md"
            - "Cross-Namespace Routing": "concepts/use-cases/cross-namespace-routing.md"
            - "Backend Protocol Selection": "concepts/use-cases/backend-protocol-selection.md"
            - "Infrastructure Attributes": "concepts/use-cases/infrastructure-attributes.md"
        - "Best Practices":
            - "BackendTLS": "concepts/best-practices/backendtls.md"
            - "Policy Attachment": "concepts/best-practices/policy-attachment.md"
            - "CRD Management": "concepts/best-practices/crd-management.md"
        - "Implementations and Conformance":
            - "Implementations": "concepts/implementations-conformance/implementations.md"
            - "Conformance":
              - "Comparisons":
                - "1.3": "concepts/implementations-conformance/conformance/1-3.md"
                - "1.2": "concepts/implementations-conformance/conformance/1-2.md"
                - "1.1": "concepts/implementations-conformance/conformance/1-1.md"
                - "1.0": "concepts/implementations-conformance/conformance/1-0.md"
        - "FAQ": "concepts/faq.md"
        - "Talks & Presentations":
            - "Future Events": "talks/future-events.md"
            - "KubeCon 2024": "talks/kubecon-2024.md"
            - "KubeCon 2023": "talks/kubecon-2023.md"
            - "KubeCon 2022": "talks/kubecon-2022.md"
        - "Glossary": "concepts/glossary.md"
    - "Tutorials":
        - "Quick Start": "tutorials/quick-start.md"
        - "Hello World: Your First Gateway": "tutorials/hello-world.md"
        - "Examples from Implementers": "tutorials/examples-implementers.md"
    - "How-to Guides":
        - "Configure a Simple Gateway": "how-to-guides/simple-gateway.md"
        - "HTTP Routing": "how-to-guides/http-routing.md"
        - "gRPC Routing": "how-to-guides/grpc-routing.md"
        - "TCP Routing": "how-to-guides/tcp-routing.md"
        - "TLS Configuration": "how-to-guides/tls-configuration.md"
        - "Traffic Splitting": "how-to-guides/traffic-splitting.md"
        - "HTTP Header Modification": "how-to-guides/http-header-modification.md"
        - "HTTP Redirect & Rewrite": "how-to-guides/http-redirect-rewrite.md"
        - "HTTP Request Mirroring": "how-to-guides/http-request-mirroring.md"
        - "Backend Protocol": "how-to-guides/backend-protocol.md"
        - "Cross-Namespace Routing": "how-to-guides/cross-namespace-routing.md"
        - "Backend Protocol Selection": "how-to-guides/backend-protocol-selection.md"
        - "Infrastructure Attributes": "how-to-guides/infrastructure-attributes.md"
        - "Migrating from Ingress": "how-to-guides/migrating-from-ingress.md"
        - "Implementers Guide": "how-to-guides/implementers-guide.md"
    - "API Reference":
        - "Full Specification":
          - "Standard": "api-reference/spec/standard.md"
          - "Experimental": "api-reference/spec/experimental.md"
        - "API Types":
            - "Gateway": "api-reference/types/gateway.md"
            - "GatewayClass": "api-reference/types/gateway-class.md"
            - "Routes (HTTP, gRPC, TCP, etc.)": "api-reference/types/routes.md"
            - "Policies (BackendTLS, BackendTraffic, etc.)": "api-reference/types/policies.md"
            - "ReferenceGrant": "api-reference/types/reference-grant.md"
    - "Enhancement Proposals (GEPs)":
        - "Process Overview": "geps/process.md"
        - "Standard":
            - "GEP-XXXX: Name": "geps/standard/gep-xxxx.md"
        - "Experimental":
            - "GEP-XXXX: Name": "geps/experimental/gep-xxxx.md"
        - "Provisional":
            - "GEP-XXXX: Name": "geps/provisional/gep-xxxx.md"
        - "Other Categories":
            - "GEP-XXXX: Name": "geps/other/gep-xxxx.md"
    - "Contributing":
        - "Getting Started":
            - "Project Organization & Working Groups": "contributing/getting-started/project-organization.md"
            - "Finding an Issue to Work On": "contributing/getting-started/finding-an-issue.md"
        - "Contributor Guides":
            - "Contributor Ladder": "contributing/guides/contributor-ladder.md"
            - "Developer Guide (Setup & Testing)": "contributing/guides/developer-guide.md"
            - "Navigating the Codebase": "contributing/guides/navigating-codebase.md"
            - "Release Cycle": "contributing/guides/release-cycle.md"
            - "Style Guide": "contributing/guides/style-guide.md"
  hooks:
    - "redirect.py"

```

## **Streamlining the Refactor with a Mkdocs Python Hook**

The minimum we need is a way to handle changing the file tree without breaking both internal and external links. Doing this by hand is functionally impossible due to time constraints. Therefore, we will leverage an [MKDocs Python hook](https://www.mkdocs.org/user-guide/configuration/#hooks).
### **The Workflow**

The core of this migration hinges on a MkDocs Python hook to automate the tedious parts of the reorganization. The goal is twofold:

1. **Generate 301 Redirects:** To ensure external links and user bookmarks don't break.
2. **Fix Internal Links:** To ensure the documentation site itself remains consistent and navigable after the file structure changes.

The script will manage this process by assigning a unique, persistent ID to every page.

**The process is as follows:**

1. **Phase 1: Preparation (Before the move)**
    - **Assign Unique IDs:** A script will traverse the current `docs` directory. For each `.md` file, it will generate a unique, human-readable ID (e.g., based on its path, like `how-to-http-routing`). This ID will be injected into the YAML frontmatter of each file.
    - **Create "Before" State Map:** The script will then create a map of the current structure: `unique_id -> old_path`. This map is saved to a file (e.g., `redirect_map.json`).
2. **Phase 2: Manual Reorganization**
    - With the IDs in place, we can now **manually move files and directories** to match the new information architecture outlined in this proposal. The content of the files is not changed, only their location.
3. **Phase 3: Generating Redirects & Fixing Links (Using an `on_config` hook)**
    - **Create "After" State Map:** On `mkdocs build`, the hook script runs. It walks the *new* file structure and creates an "after" map: `unique_id -> new_path`.
    - **Compare and Generate Redirects:** The script loads the "before" map and compares it with the "after" map. For any `unique_id` where the path has changed, it programmatically injects a redirect rule into the MkDocs configuration. For example:
        
        ```
        # This is generated by the script
        - 'old/guides/http.md': 'how-to-guides/http-routing.md'
        ```
        
    - **Fix Internal Links:** To make future refactors easier, the script can also find all relative markdown links (e.g., `[link](../topics/concepts.md)`) and replace them with a robust macro that uses the unique ID: `[link]({{ internal_link('concepts-id') }})`. This makes the links independent of the file structure. At build time, the script will replace `[link]({{ internal_link('concepts-id') }})`  with `[link](./some-relative-path)` to comply with [mkdocs recommendations](https://www.mkdocs.org/user-guide/writing-your-docs/#internal-links).
4. **Phase 4: Build**
    - MkDocs proceeds with the build. The `mkdocs-redirects` plugin uses the generated rules to create proper 301 redirects, and the `mkdocs-macros` plugin ensures all internal links point to the correct new locations.

This approach ensures that all links, both internal and external, remain functional throughout this significant refactor with minimal manual intervention.

### **Additional Consideration: Resilient Internal Linking**

To improve maintainability moving forward, we should also implement a simple macro with `mkdocs-macros` to handle internal linking. This prevents future reorganizations from breaking links.

Instead of writing a fragile relative link:

[My Link](../../section/another-page.md)

We would use the page's unique ID:

{{ internal_link('another-page-id') }}

The macro would look up the page's current URL from a manifest and render the correct link at build time. This makes content robust against file moves.

### **Dependencies**

- `mkdocs-redirects`: To handle the 301 redirects from old URLs to new ones.
- `mkdocs-macros`: To enable the custom `internal_link` macro for resilient linking.

## **Easy, but Impactful Improvements** 

### **readthedocs Theme**

We should consider changing from our current theme to “[readthedocs](https://www.mkdocs.org/user-guide/choosing-your-theme/#readthedocs)” due to it’s linear structure, more similar to the [main Kubernetes documentation](https://kubernetes.io/docs/home/). This would require no additional dependencies. It is a **one-line change**. 

### **Building a Landing Page**

We should follow the standard and build a simple page similar to [kubernetes.io](https://kubernetes.io/) so that the main domain doesn’t immediately direct to the documentation because it is jarring to users. This would be basic HTML & CSS. 

## **Phased Rollout Plan**

This is a large undertaking. We can break it down into manageable phases.

**Phase 1: Foundational Reorganization**

- **Task 1:** Implement the `linking.py` hook script.
- **Task 2:** Physically move all existing `.md` files into the new directory structure outlined above.
- **Task 3:** Run the build. The script should generate all necessary redirects. Verify that old URLs correctly redirect to the new locations. (mkdocs dose this by default)
- **Task 4:** Update the `nav` section in `mkdocs.yml` to reflect the new structure.

**Phase 2: Content Alignment & Rewriting**

- **Task 5:** Audit every page. Does its content match its new home? A "How-to Guide" should be a recipe, an "Explanation" page should explain a concept, etc.
- **Task 6:** Create new placeholder pages for documentation that is missing from the outline.
- **Task 7:** Rewrite/refactor content to fit the [Diátaxis](https://diataxis.fr/) model AND the [Kubernetes Documentation Style Guide](https://kubernetes.io/docs/contribute/style/style-guide/). This is the most significant content-focused part of the project.
- **Task 8:** For pages that need significant changes during the audit, add an "under construction" banner or similar indicator while changes are being prioritized and implemented.
- **Task 9:** Build a simple landing page.
- **Task 10:** Update the theme to [readthedocs](https://www.mkdocs.org/user-guide/choosing-your-theme/#readthedocs).

*Note: Upgrade Guides have been removed from this proposal as they are implementation-specific and better suited for individual vendor documentation rather than the core API specification.*

## **Call for Participation**

This is a significant effort that will greatly improve the experience for all our users and contributors. I'm looking for feedback on this plan and volunteers to help tackle the phases outlined above, but I understand the project is already stretched thin.

As some of you may know, I'm a college student at the University of Minnesota. I've spoken with several of my classmates who are eager to contribute to this project. To make this migration a success, however, we need the support and expertise of the existing community.

Specifically, help would be appreciated in:

- Reviewing the proposed architecture.
- Auditing and rewriting content once the new structure is in place.

Please leave your comments, suggestions, and feedback below!
