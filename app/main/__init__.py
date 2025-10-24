from flask import Blueprint, render_template, request, jsonify, redirect, url_for

# Create the main blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@main_bp.route('/sources')
def sources():
    """Sources management page"""
    return render_template('sources.html')

@main_bp.route('/destinations')
def destinations():
    """Destinations management page"""
    return render_template('destinations.html')

@main_bp.route('/mappings')
def mappings():
    """Field mappings management page"""
    return render_template('mappings.html')

@main_bp.route('/mappings/create')
def create_mapping():
    """Create new mapping page"""
    return render_template('create_mapping.html')

@main_bp.route('/mappings/<int:mapping_id>')
def view_mapping(mapping_id):
    """View/edit specific mapping"""
    return render_template('view_mapping.html', mapping_id=mapping_id)

@main_bp.route('/jobs')
def jobs():
    """Processing jobs page"""
    return render_template('jobs.html')

@main_bp.route('/transformations')
def transformations():
    """Data transformations page"""
    return render_template('transformations.html')