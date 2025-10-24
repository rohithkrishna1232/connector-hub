from flask import request, jsonify
from app.api import api_bp
from app.models import DataDestination, db
import json

@api_bp.route('/destinations', methods=['GET'])
def get_destinations():
    """Get all data destinations"""
    try:
        destinations = DataDestination.query.filter_by(is_active=True).all()
        return jsonify({
            'success': True,
            'data': [dest.to_dict() for dest in destinations]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/destinations', methods=['POST'])
def create_destination():
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
        
        destination = DataDestination(
            name=data['name'],
            type=data['type'],
            connection_config=json.dumps(data['connection_config']),
            schema_info=json.dumps(data.get('schema_info', {}))
        )
        
        db.session.add(destination)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': destination.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/destinations/<int:dest_id>', methods=['GET'])
def get_destination(dest_id):
    """Get a specific data destination"""
    try:
        destination = DataDestination.query.get(dest_id)
        if not destination:
            return jsonify({
                'success': False,
                'error': 'Destination not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': destination.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/destinations/<int:dest_id>', methods=['PUT'])
def update_destination(dest_id):
    """Update a data destination"""
    try:
        destination = DataDestination.query.get(dest_id)
        if not destination:
            return jsonify({
                'success': False,
                'error': 'Destination not found'
            }), 404
        
        data = request.get_json()
        
        # Update fields if provided
        if 'name' in data:
            destination.name = data['name']
        if 'type' in data:
            destination.type = data['type']
        if 'connection_config' in data:
            destination.connection_config = json.dumps(data['connection_config'])
        if 'schema_info' in data:
            destination.schema_info = json.dumps(data['schema_info'])
        if 'is_active' in data:
            destination.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': destination.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/destinations/<int:dest_id>', methods=['DELETE'])
def delete_destination(dest_id):
    """Delete a data destination (soft delete)"""
    try:
        destination = DataDestination.query.get(dest_id)
        if not destination:
            return jsonify({
                'success': False,
                'error': 'Destination not found'
            }), 404
        
        destination.is_active = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Destination deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/destinations/<int:dest_id>/test', methods=['POST'])
def test_destination_connection(dest_id):
    """Test connection to a data destination"""
    try:
        destination = DataDestination.query.get(dest_id)
        if not destination:
            return jsonify({
                'success': False,
                'error': 'Destination not found'
            }), 404
        
        # Import and use the destination service to test connection
        from app.services.destination_service import DestinationService
        service = DestinationService()
        result = service.test_connection(destination)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500