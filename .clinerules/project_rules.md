# Cline Directives: AI Link Mind Azure Function

**Objective:** Follow these rules to write clean, well-structured, and secure code for this project, adhering to Azure Function best practices.

**Project Context:** A Python Azure Function for recursive web scraping, embedding text with OpenAI, and storing results in Supabase.

**Core Tech:** Python, Azure Functions, Azure Service Bus, Supabase, OpenAI.

---

### **Azure Function & Python Best Practices**

*   **Function Design:** Functions must be small, stateless, idempotent, and have a single responsibility.
*   **Code Structure:**
    *   Isolate external service interactions in `src/services`.
    *   Strictly follow PEP 8 naming conventions.
*   **Code Quality:**
    *   Use type hints for all function signatures.
    *   Implement robust `try-except` blocks for all I/O and API calls, with clear and informative logging with exc_info=True for stack trace.
    *   Adhere to the "Don't Repeat Yourself" (DRY) principle by abstracting common logic into reusable functions or classes.
    *   Prioritize readability and simplicity over overly complex or clever solutions.
    *   Write very simple docstring ONLY for complex methods but keep them minimal.

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
