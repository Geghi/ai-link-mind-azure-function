import azure.functions as func
import logging
import sys
import os
import json 

# Import blueprints
from blueprints.scrape_url_blueprint import scrape_url_bp
from blueprints.scrape_url_recursive_blueprint import scrape_url_recursive_bp
from blueprints.rag_blueprint import rag_bp
from blueprints.utility_blueprint import utility_bp
from blueprints.perform_scraping_blueprint import perform_scraping_bp
from blueprints.embedding_blueprint import embedding_bp

# Configure logging
logging.basicConfig(level=logging.INFO)
logging.getLogger().setLevel(logging.INFO)

logging.info("Azure Function App is starting...")

app = func.FunctionApp()

# Register blueprints
app.register_blueprint(scrape_url_bp)
app.register_blueprint(scrape_url_recursive_bp)
app.register_blueprint(rag_bp)
app.register_blueprint(utility_bp)
app.register_blueprint(perform_scraping_bp)
app.register_blueprint(embedding_bp)
