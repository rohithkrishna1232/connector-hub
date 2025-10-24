from flask import Blueprint

# Create the API blueprint
api_bp = Blueprint('api', __name__)

# Import all API routes
from app.api import sources, destinations, mappings, jobs, transformations, ai_endpoints