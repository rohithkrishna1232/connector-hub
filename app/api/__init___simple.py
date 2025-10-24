from flask import Blueprint

# Create the API blueprint
api_bp = Blueprint('api', __name__)

# Import simple API routes (no database required)
from app.api import simple_endpoints, ai_endpoints