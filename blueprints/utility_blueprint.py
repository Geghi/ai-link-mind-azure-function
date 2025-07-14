import azure.functions as func
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logging.getLogger().setLevel(logging.INFO)

# Create a blueprint for utility functions
utility_bp = func.Blueprint()

@utility_bp.route(route="health", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def HealthCheck(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure HTTP Trigger function for health checks.
    """
    logging.info('HealthCheck HTTP trigger function processed a request.')
    return func.HttpResponse("Azure Function Status: OK", status_code=200)
