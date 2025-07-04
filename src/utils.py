import azure.functions as func
import json

def json_response(message: str, status_code: int) -> func.HttpResponse:
    """
    Creates an Azure Function HTTP response with a JSON payload.

    Args:
        message (str): The message to be included in the JSON response.
        status_code (int): The HTTP status code for the response.

    Returns:
        func.HttpResponse: An Azure Function HTTP response object with
                           the specified message and status code, and
                           'application/json' mimetype.
    """
    return func.HttpResponse(
        json.dumps({"message": message}),
        status_code=status_code,
        mimetype="application/json"
    )
