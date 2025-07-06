import os
import logging
from azure.servicebus import ServiceBusClient, ServiceBusMessage, ServiceBusSender, ServiceBusReceiver, ServiceBusReceivedMessage

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

def receive_single_message_from_service_bus(receiver: ServiceBusReceiver) -> ServiceBusReceivedMessage | None:
    """
    Receives a single message from the Azure Service Bus queue.

    Args:
        receiver (ServiceBusReceiver): The ServiceBusReceiver instance.

    Returns:
        ServiceBusReceivedMessage | None: The received message or None if no message is available.
    """
    try:
        # Try to receive a single message without blocking indefinitely
        messages = receiver.receive_messages(max_message_count=1, max_wait_time=5)
        if messages:
            logging.info("Received a message from Azure Service Bus.")
            return messages[0]
        else:
            logging.info("No messages available in Service Bus queue.")
            return None
    except Exception as e:
        logging.error(f"Error receiving message from Azure Service Bus: {e}", exc_info=True)
        return None

def get_service_bus_receiver(queue_name: str) -> ServiceBusReceiver:
    """
    Initializes and returns an Azure Service Bus receiver.

    Retrieves Service Bus connection string from environment variables.

    Args:
        queue_name (str): The name of the queue to receive messages from.

    Returns:
        ServiceBusReceiver: An instance of ServiceBusReceiver.

    Raises:
        ValueError: If SERVICE_BUS_CONNECTION_STR environment variable is not set.
        Exception: If there is an error creating the Service Bus client or receiver.
    """
    SERVICE_BUS_CONNECTION_STR = os.environ.get("SERVICE_BUS_CONNECTION_STR")
    if not SERVICE_BUS_CONNECTION_STR:
        raise ValueError("SERVICE_BUS_CONNECTION_STR environment variable not set.")

    try:
        servicebus_client = ServiceBusClient.from_connection_string(SERVICE_BUS_CONNECTION_STR)
        receiver = servicebus_client.get_queue_receiver(queue_name=queue_name)
        return receiver
    except Exception as e:
        logging.error(f"Error creating Service Bus client or receiver: {e}", exc_info=True)
        raise

def complete_message(receiver: ServiceBusReceiver, message: ServiceBusReceivedMessage) -> None:
    """
    Completes a received message in the Azure Service Bus queue.

    Args:
        receiver (ServiceBusReceiver): The ServiceBusReceiver instance.
        message (ServiceBusReceivedMessage): The message to complete.
    """
    try:
        receiver.complete_message(message)
        logging.info(f"Completed Service Bus message: {message.sequence_number}")
    except Exception as e:
        logging.error(f"Error completing Service Bus message: {e}", exc_info=True)
        raise

def dead_letter_message(receiver: ServiceBusReceiver, message: ServiceBusReceivedMessage, reason: str | None = None, description: str | None = None) -> None:
    """
    Dead-letters a received message in the Azure Service Bus queue.

    Args:
        receiver (ServiceBusReceiver): The ServiceBusReceiver instance.
        message (ServiceBusReceivedMessage): The message to dead-letter.
        reason (str | None): The reason for dead-lettering the message.
        description (str | None): The description of the dead-lettering error.
    """
    try:
        receiver.dead_letter_message(message, reason=reason, error_description=description)
        logging.warning(f"Dead-lettered Service Bus message: {message.sequence_number}. Reason: {reason}, Description: {description}")
    except Exception as e:
        logging.error(f"Error dead-lettering Service Bus message: {e}", exc_info=True)
        raise
