import os
from azure.storage.queue import QueueClient

def clear_azurite_queue():
    """
    Connects to the local Azurite queue and clears all messages.
    """
    connection_string = "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;"
    queue_name = "embedding-queue"

    try:
        queue_client = QueueClient.from_connection_string(connection_string, queue_name)
        
        # Check if the queue exists
        try:
            properties = queue_client.get_queue_properties()
            print(f"Queue '{queue_name}' found. Approximate messages: {properties.approximate_message_count}")
        except Exception:
            print(f"Queue '{queue_name}' does not exist. Nothing to clear.")
            return

        print(f"Clearing all messages from queue: {queue_name}...")
        queue_client.clear_messages()
        print("Queue cleared successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    clear_azurite_queue()
