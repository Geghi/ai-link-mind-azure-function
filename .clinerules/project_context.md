# Project Context: AI Link Mind Azure Function

This document outlines the project's functional workflow, components, and data models to guide development.

## Functional Overview

The application recursively scrapes a website, extracts text, generates OpenAI embeddings, and stores the data in Supabase.

**Workflow:**
1.  **Initiation:** An HTTP trigger (`ScrapeUrl`) receives a `task_id`, `url`, and `max_depth`. It creates an initial record in `scraped_pages` and queues the first job in an Azure Storage Queue.
2.  **Recursive Scraping:** A queue trigger (`ScrapeUrlRecursive`) processes each job:
    *   Fetches HTML and extracts text content.
    *   Updates the page status to "Processing" in Supabase.
3.  **Chunking & Embedding:**
    *   Splits extracted text into smaller, overlapping chunks.
    *   Generates an OpenAI embedding for each chunk.
    *   Stores the chunk and its embedding in the `page_chunks` table.
4.  **Link Discovery & Queuing:**
    *   Finds all new internal links on the page.
    *   For each new link, creates a "Queued" record in `scraped_pages`.
    *   If `depth < max_depth - 1`, queues a new job to the Azure Storage Queue.
    *   If `depth == max_depth - 1`, queues the job to Azure Service Bus to end the recursion.
5.  **Completion:** Updates the page status to "Completed" in Supabase.

## Core Components & Roles

*   **`function_app.py`:** Contains the `ScrapeUrl` (HTTP trigger) and `ScrapeUrlRecursive` (Queue trigger) functions.
*   **`src/services/scraper.py`:** Fetches HTML, extracts text, and finds internal links.
*   **`src/services/supabase_service.py`:** Manages the Supabase client connection.
*   **`src/services/scraped_pages_service.py`:** Handles all database interactions with `scraped_pages` and `page_chunks` tables.
*   **`src/services/openai_service.py`:** Generates embeddings using the OpenAI API.
*   **`src/services/azure_service_bus_service.py`:** Sends messages to the final Azure Service Bus queue.

## Data Models (Supabase Tables)

*   **`scraped_pages`**:
    *   `id`, `task_id`, `url`, `status` ("Queued", "Processing", "Completed", "Failed"), `page_text_content`, `created_at`.
*   **`page_chunks`**:
    *   `id`, `scraped_page_id` (FK), `chunk_text`, `embedding`, `created_at`.
