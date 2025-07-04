import requests
import json
import uuid

# Azure Function local endpoint
FUNCTION_URL = "http://localhost:7071/api/ScrapeUrl"

# Example payload
payload = {
    "url": "https://mantovani-giacomo.com/",
    # "task_id": str(uuid.uuid4())
    "task_id": "afd397a3-9f4a-4155-bccf-d13fe0a7460f",  # Example task ID
}

headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(FUNCTION_URL, data=json.dumps(payload), headers=headers)
    response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)

    print(f"Status Code: {response.status_code}")
    print("Response Body:")
    print(response.json())

    if response.status_code == 202:
        print("Scraping initiated successfully. Check Azure Function logs for background processing.")

except requests.exceptions.RequestException as e:
    print(f"Error making request: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"Response Status Code: {e.response.status_code}")
        print(f"Response Body: {e.response.text}")
except json.JSONDecodeError:
    print("Error decoding JSON response.")
    print(f"Raw response: {response.text}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
