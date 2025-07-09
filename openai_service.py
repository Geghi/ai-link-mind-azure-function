import os
from openai import OpenAI
import logging

def get_openai_client() -> OpenAI:
    """
    Initializes and returns an OpenAI client.

    Retrieves the OpenAI API key from environment variables.

    Returns:
        OpenAI: An initialized OpenAI client instance.

    Raises:
        ValueError: If the OPENAI_API_KEY environment variable is not set.
    """
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable not set.")
    return OpenAI(api_key=OPENAI_API_KEY)

def get_embedding(text: str, model: str = "text-embedding-ada-002") -> list[float]:
    """
    Generates an embedding for the given text using the specified OpenAI model.

    Args:
        text (str): The input text to generate an embedding for.
        model (str): The OpenAI embedding model to use. Defaults to "text-embedding-ada-002".

    Returns:
        list[float]: A list of floats representing the embedding.

    Raises:
        Exception: If there is an error generating the embedding.
    """
    client = get_openai_client()
    text = text.replace("\n", " ")
    try:
        return client.embeddings.create(input=[text], model=model).data[0].embedding
    except Exception as e:
        logging.error(f"Error generating embedding for text: {e}", exc_info=True)
        raise # Re-raise the exception after logging

def summarize_conversation(messages: list[dict], model: str = "gpt-3.5-turbo") -> str:
    """
    Summarizes a list of conversation messages using the OpenAI chat completion model.

    Args:
        messages (list[dict]): A list of message dictionaries representing the conversation history.
        model (str): The OpenAI chat completion model to use for summarization.

    Returns:
        str: A concise summary of the conversation.

    Raises:
        Exception: If there is an error generating the summary.
    """
    summary_prompt = [
        {"role": "system", "content": "You are a helpful assistant. Summarize the following conversation concisely, retaining all key information and context relevant to continuing the dialogue. The summary should be brief and to the point."},
        *messages # Unpack the conversation messages
    ]
    try:
        summary = get_chat_completion(summary_prompt, model=model)
        logging.info(f"Generated conversation summary: {summary}")
        return summary
    except Exception as e:
        logging.error(f"Error summarizing conversation: {e}", exc_info=True)
        raise # Re-raise the exception after logging

def get_chat_completion(messages: list[dict], model: str = "gpt-3.5-turbo") -> str:
    """
    Generates a chat completion using the specified OpenAI model.

    Args:
        messages (list[dict]): A list of message dictionaries for the chat completion.
                               Each dictionary should have 'role' and 'content' keys.
        model (str): The OpenAI chat completion model to use. Defaults to "gpt-3.5-turbo".

    Returns:
        str: The content of the generated chat completion.

    Raises:
        Exception: If there is an error generating the chat completion.
    """
    client = get_openai_client()
    logging.info(f"Generating chat completion with model: {model} and messages: {messages}")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        content = response.choices[0].message.content
        if content is None:
            logging.warning("OpenAI chat completion returned None content. Returning empty string.")
            return ""
        return content
    except Exception as e:
        logging.error(f"Error generating chat completion: {e}", exc_info=True)
        raise # Re-raise the exception after logging
