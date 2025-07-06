# Project Context: AI Link Mind Azure Function

This document outlines the project's functional workflow, components, and data models to guide development.

## Functional Overview

The application recursively scrapes a website, extracts text, generates OpenAI embeddings, and stores the data in Supabase and Pinecone.

**Workflow:**
1.  **Initiation:** An HTTP trigger (`ScrapeUrl`) receives a `task_id`, `url`, and `max_depth`. It creates an initial record in `scraped_pages` and queues the first job in an Azure Storage Queue.
2.  **Recursive Scraping (Queue Trigger):** A queue trigger (`ScrapeUrlRecursive`) processes each job:
    *   Fetches HTML and extracts text content.
    *   Updates the page status to "Processing" in Supabase.
    *   Utilizes the `EmbeddingService` to chunk text and generate OpenAI embeddings.
    *   Finds all new internal links on the page.
    *   For each new link, creates a "Queued" record in `scraped_pages`.
    *   If `depth < max_depth - 1`, queues a new job to the Azure Storage Queue.
    *   If `depth == max_depth - 1`, queues the job to Azure Service Bus to end the recursion.
    *   Updates the page status to "Completed" in Supabase.
3.  **Service Bus Leaf Node Processing (Timer Trigger):** A timer trigger (`ProcessServiceBusLeafNodes`) periodically dequeues messages from Azure Service Bus:
    *   Receives messages indicating the end of a scraping branch (leaf nodes).
    *   Fetches HTML and extracts text content for these leaf nodes.
    *   Utilizes the `EmbeddingService` to chunk text and generate OpenAI embeddings.
    *   Updates the page status to "Completed" in Supabase.

## Core Components & Roles

*   **`function_app.py`:** Contains the `ScrapeUrl` (HTTP trigger), `ScrapeUrlRecursive` (Queue trigger), and `ProcessServiceBusLeafNodes` (Timer trigger) functions, along with helper functions for parsing and link processing.
*   **`src/services/scraper.py`:** Fetches HTML, extracts text, and finds internal links.
*   **`src/services/supabase_service.py`:** Manages the Supabase client connection.
*   **`src/services/scraped_pages_service.py`:** Handles all database interactions with `scraped_pages` and `page_chunks` tables.
*   **`src/services/openai_service.py`:** Generates embeddings using the OpenAI API.
*   **`src/services/azure_service_bus_service.py`:** Manages sending and receiving messages from Azure Service Bus.
*   **`src/services/pinecone_service.py`:** Manages the Pinecone client connection and vector uploads.
*   **`src/services/embedding_service.py`:** Encapsulates the logic for text chunking and OpenAI embedding generation.

## Data Models (Supabase Tables)

*   **`scraped_pages`**:
    *   `id`, `task_id`, `url`, `status` ("Queued", "Processing", "Completed", "Failed"), `page_text_content`, `created_at`.
    *   **Note:** A unique constraint on `(task_id, url)` is required for `upsert` operations.
*   **`page_chunks`**:
    *   `id`, `scraped_page_id` (FK), `chunk_text`, `embedding`, `created_at`.
*   **`chat_summaries`**:
    *   `id`, `task_id`, `summary_text`, `created_at`, `updated_at`.
    *   **Note:** Stores a history of conversation summaries for a given `task_id`. The latest summary is retrieved for context.
