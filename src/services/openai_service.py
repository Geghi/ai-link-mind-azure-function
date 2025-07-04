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
