import azure.functions as func
import logging
import os
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logging.getLogger().setLevel(logging.INFO)

# Create a blueprint for utility functions
utility_bp = func.Blueprint()

@utility_bp.route(route="check_env_var", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def check_env_var(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('check_env_var HTTP trigger function processed a request.')

    env_var_name = req.params.get('name')

    if not env_var_name:
        return func.HttpResponse(
             "Please pass a name in the request body",
             status_code=400
        )

    env_var_value = os.environ.get(env_var_name)

    if env_var_value:
        return func.HttpResponse(
             json.dumps({
                 "status": "OK",
                 "length": len(env_var_value)
             }),
             mimetype="application/json",
             status_code=200
        )
    else:
        return func.HttpResponse(
             json.dumps({
                 "status": "KO",
                 "length": 0
             }),
             mimetype="application/json",
             status_code=200
        )


@utility_bp.route(route="health", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def HealthCheck(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure HTTP Trigger function for health checks.
    """
    logging.info('HealthCheck HTTP trigger function processed a request.')
    return func.HttpResponse("Azure Function Status: OK", status_code=200)
