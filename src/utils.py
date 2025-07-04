import azure.functions as func
import json

def json_response(message: str, status_code: int) -> func.HttpResponse:
    """
    Creates an Azure Function HTTP response with a JSON payload.
    """
    return func.HttpResponse(
        json.dumps({"message": message}),
        status_code=status_code,
        mimetype="application/json"
    )
