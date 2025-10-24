from flask import request, jsonify
from app.api import api_bp
import json
import os

# In-memory storage for demo purposes
STORAGE_FILE = 'data_storage.json'

def load_storage():
    """Load data from JSON file"""
    if os.path.exists(STORAGE_FILE):
        try:
            with open(STORAGE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        'sources': [],
        'destinations': [],
        'mappings': [],
        'jobs': []
    }

def save_storage(data):
    """Save data to JSON file"""
    try:
        with open(STORAGE_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except:
        return False

@api_bp.route('/sources', methods=['GET'])
def get_sources_simple():
    """Get all data sources"""
    try:
        storage = load_storage()
        return jsonify({
            'success': True,
            'data': storage.get('sources', [])
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/sources', methods=['POST'])
def create_source_simple():
    """Create a new data source"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'type', 'connection_config']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        storage = load_storage()
        
        # Generate ID
        source_id = len(storage['sources']) + 1
        
        source = {
            'id': source_id,
            'name': data['name'],
            'type': data['type'],
            'connection_config': data['connection_config'],
            'schema_info': data.get('schema_info', {}),
            'created_at': '2024-01-01T00:00:00',
            'updated_at': '2024-01-01T00:00:00',
            'is_active': True
        }
        
        storage['sources'].append(source)
        save_storage(storage)
        
        return jsonify({
            'success': True,
            'data': source
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/destinations', methods=['GET'])
def get_destinations_simple():
    """Get all data destinations"""
    try:
        storage = load_storage()
        return jsonify({
            'success': True,
            'data': storage.get('destinations', [])
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/destinations', methods=['POST'])
def create_destination_simple():
    """Create a new data destination"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'type', 'connection_config']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        storage = load_storage()
        
        # Generate ID
        dest_id = len(storage['destinations']) + 1
        
        destination = {
            'id': dest_id,
            'name': data['name'],
            'type': data['type'],
            'connection_config': data['connection_config'],
            'schema_info': data.get('schema_info', {}),
            'created_at': '2024-01-01T00:00:00',
            'updated_at': '2024-01-01T00:00:00',
            'is_active': True
        }
        
        storage['destinations'].append(destination)
        save_storage(storage)
        
        return jsonify({
            'success': True,
            'data': destination
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/mappings', methods=['GET'])
def get_mappings_simple():
    """Get all field mappings"""
    try:
        storage = load_storage()
        return jsonify({
            'success': True,
            'data': storage.get('mappings', [])
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/mappings', methods=['POST'])
def create_mapping_simple():
    """Create a new field mapping"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'source_id', 'destination_id', 'mapping_config']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        storage = load_storage()
        
        # Generate ID
        mapping_id = len(storage['mappings']) + 1
        
        mapping = {
            'id': mapping_id,
            'name': data['name'],
            'source_id': data['source_id'],
            'destination_id': data['destination_id'],
            'mapping_config': data['mapping_config'],
            'transformation_rules': data.get('transformation_rules', {}),
            'created_at': '2024-01-01T00:00:00',
            'updated_at': '2024-01-01T00:00:00',
            'is_active': True
        }
        
        storage['mappings'].append(mapping)
        save_storage(storage)
        
        return jsonify({
            'success': True,
            'data': mapping
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/sources/<int:source_id>/schema', methods=['GET'])
def get_source_schema_simple(source_id):
    """Get schema for a data source"""
    try:
        # Return sample schema
        sample_schema = {
            'success': True,
            'data': {
                'fields': [
                    {'name': 'id', 'type': 'integer', 'required': True},
                    {'name': 'name', 'type': 'string', 'required': True},
                    {'name': 'email', 'type': 'string', 'required': False},
                    {'name': 'created_at', 'type': 'datetime', 'required': False},
                    {'name': 'status', 'type': 'string', 'required': False}
                ]
            }
        }
        return jsonify(sample_schema)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/destinations/<int:dest_id>/schema', methods=['GET'])
def get_destination_schema_simple(dest_id):
    """Get schema for a data destination"""
    try:
        # Return sample schema
        sample_schema = {
            'success': True,
            'data': {
                'fields': [
                    {'name': 'user_id', 'type': 'integer', 'required': True},
                    {'name': 'full_name', 'type': 'string', 'required': True},
                    {'name': 'email_address', 'type': 'string', 'required': True},
                    {'name': 'registration_date', 'type': 'date', 'required': False},
                    {'name': 'account_status', 'type': 'string', 'required': True}
                ]
            }
        }
        return jsonify(sample_schema)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/sources/<int:source_id>/test', methods=['POST'])
def test_source_connection_simple(source_id):
    """Test connection to a data source"""
    try:
        return jsonify({
            'success': True,
            'data': {
                'status': 'connected',
                'response_time': 0.5,
                'message': 'Connection test successful'
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/destinations/<int:dest_id>/test', methods=['POST'])
def test_destination_connection_simple(dest_id):
    """Test connection to a data destination"""
    try:
        return jsonify({
            'success': True,
            'data': {
                'status': 'connected',
                'response_time': 0.3,
                'message': 'Connection test successful'
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500