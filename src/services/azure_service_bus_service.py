import os
import logging
from azure.servicebus import ServiceBusClient, ServiceBusMessage

def get_service_bus_sender_and_queue_name():
    SERVICE_BUS_CONNECTION_STR = os.environ.get("SERVICE_BUS_CONNECTION_STR")
    SERVICE_BUS_QUEUE_NAME = os.environ.get("SERVICE_BUS_QUEUE_NAME", "scrape_urls")

    if not SERVICE_BUS_CONNECTION_STR:
        raise ValueError("SERVICE_BUS_CONNECTION_STR environment variable not set.")

    servicebus_client = ServiceBusClient.from_connection_string(SERVICE_BUS_CONNECTION_STR)
    sender = servicebus_client.get_queue_sender(queue_name=SERVICE_BUS_QUEUE_NAME)
    return sender, SERVICE_BUS_QUEUE_NAME

def send_message_to_service_bus(sender, message_body):
    try:
        message = ServiceBusMessage(message_body)
        sender.send_messages(message)
        logging.info(f"Message sent to Azure Service Bus: {message_body}")
    except Exception as e:
        logging.error(f"Error sending message to Azure Service Bus: {e}")
        raise
