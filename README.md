# AI Link Mind - Azure Function

This Azure Function app is designed for recursively scraping URLs and processing the extracted data. It utilizes Azure Service Bus for message queuing and Supabase for data storage.

## Overview

The function app consists of two main functions:

-   `ScrapeUrlRecursive`: This function is triggered by messages in an Azure Queue Storage queue named `scrape-queue`. It recursively scrapes internal links from a given URL up to a specified maximum depth.
-   `ScrapeUrl`: This function is triggered by HTTP requests. It accepts a URL and a task ID in the request body and initiates the scraping process.

## Architecture

1.  **HTTP Trigger (ScrapeUrl)**:
    -   Receives an HTTP request with a URL and task ID.
    -   Inserts the base URL into the `scraped_pages` table in Supabase with a status of "Completed".
    -   Sends an initial message to the `scrape-queue` to start the recursive scraping process.

2.  **Queue Trigger (ScrapeUrlRecursive)**:
    -   Receives a message from the `scrape-queue` containing a URL, task ID, current depth, and maximum depth.
    -   Checks if the maximum depth has been reached. If so, the function exits.
    -   Extracts internal links from the URL using the `get_internal_links` function from `src/services/scraper.py`.
    -   For each internal link:
        -   Inserts the link into the `scraped_pages` table in Supabase with a status of "Queued".
        -   Sends a message to Azure Service Bus with the URL, task ID, and depth.
        -   Enqueues a new message to the `scrape-queue` for the next level of scraping, if the maximum depth has not been reached.

3.  **Data Storage**:
    -   Supabase is used to store the scraped pages and their status. The `scraped_pages` table contains columns for `task_id`, `url`, and `status`.

4.  **Message Queuing**:
    -   Azure Service Bus is used for asynchronous message processing. When a new URL needs to be scraped, a message is sent to the Service Bus queue.

## Dependencies

-   `azure-functions`: Azure Functions runtime library.
-   `requests`: HTTP library for making requests.
-   `beautifulsoup4`: Library for parsing HTML and XML.
-   `supabase`: Supabase client library.
-   `azure-servicebus`: Azure Service Bus client library.

## Configuration

The following environment variables must be set:

-   `AzureWebJobsStorage`: The connection string for the Azure Storage account.
-   `SUPABASE_URL`: The URL for the Supabase project.
-   `SUPABASE_KEY`: The API key for the Supabase project.
-   `SERVICE_BUS_CONNECTION_STR`: The connection string for the Azure Service Bus namespace.
-   `SERVICE_BUS_QUEUE_NAME`: The name of the Azure Service Bus queue.

These environment variables can be configured in the `local.settings.json` file for local development and in the Azure Function app settings in the Azure portal for production deployments.

## Getting Started

1.  **Install Dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure Environment Variables**:

    -   Create a `local.settings.json` file with the required environment variables.
    -   Update the `SERVICE_BUS_CONNECTION_STR` with your Azure Service Bus connection string.
    -   Update the `SUPABASE_URL` and `SUPABASE_KEY` with your Supabase project credentials.

    ```json
    {
      "IsEncrypted": false,
      "Values": {
        "FUNCTIONS_WORKER_RUNTIME": "python",
        "AzureWebJobsStorage": "UseDevelopmentStorage=true",
        "SUPABASE_URL": "YOUR_SUPABASE_URL",
        "SUPABASE_KEY": "YOUR_SUPABASE_KEY",
        "SERVICE_BUS_CONNECTION_STR": "YOUR_SERVICE_BUS_CONNECTION_STRING",
        "SERVICE_BUS_QUEUE_NAME": "scrape_urls"
      }
    }
    ```

4.  **Run the Function App Locally**:
Ensure Azurite is running locally. You can start it via Docker, VS Code extension, or by running the `azurite` command if installed globally. This is essential for local queue storage operations.

    ```bash
    func host start
    ```

## Deployment

1.  **Create an Azure Function App**:
    -   In the Azure portal, create a new Azure Function app.
    -   Choose the Python runtime stack.

2.  **Configure Application Settings**:
    -   In the Azure Function app, go to "Configuration" under "Settings".
    -   Add the required environment variables (`AzureWebJobsStorage`, `SUPABASE_URL`, `SUPABASE_KEY`, `SERVICE_BUS_CONNECTION_STR`, `SERVICE_BUS_QUEUE_NAME`) with their respective values.

3.  **Deploy the Code**:
    -   You can deploy the code using various methods, such as:
        -   VS Code Azure Functions extension
        -   Azure CLI
        -   GitHub Actions

## Usage

1.  **HTTP Trigger (ScrapeUrl)**:
    -   Send an HTTP POST request to the `ScrapeUrl` endpoint with a JSON payload containing the `url` and `task_id`.

    ```json
    {
      "url": "https://example.com",
      "task_id": uuid
    }
    ```

2.  **Queue Trigger (ScrapeUrlRecursive)**:
    -   The `ScrapeUrlRecursive` function will automatically be triggered by messages in the `scrape-queue`.
