# Cline Directives: AI Link Mind Azure Function

**Objective:** Follow these rules to write clean, well-structured, and secure code for this project, adhering to Azure Function best practices.

**Project Context:** A Python Azure Function for recursive web scraping, embedding text with OpenAI, and storing results in Supabase.

**Core Tech:** Python, Azure Functions, Azure Service Bus, Supabase, OpenAI.

---

### **Azure Function & Python Best Practices**

*   **Function Design:** Functions must be small, stateless, idempotent, and have a single responsibility.
*   **Code Structure:**
    *   Prefer class-based design for components with clear responsibilities (e.g., Scraper, RAGExtractor).
    *   Each class should have a single, well-defined scope following the Single Responsibility Principle.
    *   Isolate external service interactions in `src/services` using service classes.
    *   Strictly follow PEP 8 naming conventions:
        - Class names: `PascalCase`
        - Method names: `snake_case`
        - Constants: `UPPER_SNAKE_CASE`
*   **Class Design Guidelines:**
    *   Keep classes focused on one primary responsibility.
    *   Use `__init__` for required dependencies, not for complex initialization logic.
    *   Document public methods with concise docstrings following Google style.
    *   Prefer composition over inheritance for code reuse.
    *   Make classes testable by injecting dependencies.
*   **Code Quality:**
    *   Use type hints for all function signatures and class attributes.
    *   Implement robust `try-except` blocks for all I/O and API calls, with clear and informative logging with exc_info=True for stack trace.
    *   Adhere to the "Don't Repeat Yourself" (DRY) principle by abstracting common logic into reusable classes or functions.
    *   Prioritize readability and simplicity over overly complex or clever solutions.
    *   Write simple docstrings for public methods and classes.
*   **Modularization:**
    *   Group related functionality into cohesive modules.
    *   Keep module interfaces small and focused.
    *   Use private methods (`_prefix`) for internal implementation details.
    *   Maintain clear separation between different abstraction levels.

---

### **Security Mandates**

*   **No Hardcoded Secrets:** Access all secrets (API keys, connection strings) from environment variables ONLY.
*   **Validate All Inputs:** Sanitize all data from external sources (HTTP requests, queues).
*   **CRITICAL: Forbidden File Access (for Agent):** The AI agent (Cline) is strictly forbidden from reading `local.settings.json`, `.env`, or any other configuration files that may contain sensitive information. This is to prevent accidental exposure of secrets to external LLM services.

---

### **Maintaining Project Context**

*   **Dynamic Updates:** These directive and context files are living documents. If a change in project requirements affects the workflow, data models, or core components, you must update the relevant `.clinerules` files to reflect these changes.
*   **Examples of Updates:**
    *   If a new table is added to Supabase, update the "Data Models" section in `project_context.md` and create a migrations file.
    *   If a new service or directory is added, update the "Core Components & Roles" in `project_context.md` and, if necessary, add new rules to this file.
    *   If the core workflow changes, update the "Functional Overview" in `project_context.md`.
*   **Proactive Maintenance:** Always consider whether a code change necessitates a documentation change. Keeping the context files synchronized with the codebase is crucial for effective development.
