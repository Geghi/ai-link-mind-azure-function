import os
import logging
from azure.servicebus import ServiceBusClient, ServiceBusMessage, ServiceBusSender

def get_service_bus_sender_and_queue_name() -> tuple[ServiceBusSender, str]:
    """
    Initializes and returns an Azure Service Bus sender and the queue name.

    Retrieves Service Bus connection string and queue name from environment variables.

    Returns:
        tuple[ServiceBusSender, str]: A tuple containing the ServiceBusSender instance
                                     and the name of the queue.

    Raises:
        ValueError: If SERVICE_BUS_CONNECTION_STR or SERVICE_BUS_QUEUE_NAME environment
                    variables are not set.
        Exception: If there is an error creating the Service Bus client or sender.
    """
    SERVICE_BUS_CONNECTION_STR = os.environ.get("SERVICE_BUS_CONNECTION_STR")
    SERVICE_BUS_QUEUE_NAME = os.environ.get("SERVICE_BUS_QUEUE_NAME")

    if not SERVICE_BUS_CONNECTION_STR:
        raise ValueError("SERVICE_BUS_CONNECTION_STR environment variable not set.")
    if not SERVICE_BUS_QUEUE_NAME:
        raise ValueError("SERVICE_BUS_QUEUE_NAME environment variable not set.")

    try:
        servicebus_client = ServiceBusClient.from_connection_string(SERVICE_BUS_CONNECTION_STR)
        sender = servicebus_client.get_queue_sender(queue_name=SERVICE_BUS_QUEUE_NAME)
        return sender, SERVICE_BUS_QUEUE_NAME
    except Exception as e:
        logging.error(f"Error creating Service Bus client or sender: {e}", exc_info=True)
        raise # Re-raise the exception after logging

def send_message_to_service_bus(sender: ServiceBusSender, message_body: str) -> None:
    """
    Sends a message to the Azure Service Bus queue.

    Args:
        sender (ServiceBusSender): The ServiceBusSender instance.
        message_body (str): The content of the message to send.

    Raises:
        Exception: If there is an error sending the message.
    """
    try:
        message = ServiceBusMessage(message_body)
        sender.send_messages(message)
        logging.info(f"Message sent to Azure Service Bus: {message_body}")
    except Exception as e:
        logging.error(f"Error sending message to Azure Service Bus: {e}", exc_info=True)
        raise
