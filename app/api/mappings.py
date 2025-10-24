from flask import request, jsonify
from app.api import api_bp
from app.models import FieldMapping, DataSource, DataDestination, db
import json

@api_bp.route('/mappings', methods=['GET'])
def get_mappings():
    """Get all field mappings"""
    try:
        mappings = FieldMapping.query.filter_by(is_active=True).all()
        return jsonify({
            'success': True,
            'data': [mapping.to_dict() for mapping in mappings]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/mappings', methods=['POST'])
def create_mapping():
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
        
        # Validate source and destination exist
        source = DataSource.query.get(data['source_id'])
        destination = DataDestination.query.get(data['destination_id'])
        
        if not source:
            return jsonify({
                'success': False,
                'error': 'Source not found'
            }), 400
        
        if not destination:
            return jsonify({
                'success': False,
                'error': 'Destination not found'
            }), 400
        
        mapping = FieldMapping(
            name=data['name'],
            source_id=data['source_id'],
            destination_id=data['destination_id'],
            mapping_config=json.dumps(data['mapping_config']),
            transformation_rules=json.dumps(data.get('transformation_rules', {}))
        )
        
        db.session.add(mapping)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': mapping.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/mappings/<int:mapping_id>', methods=['GET'])
def get_mapping(mapping_id):
    """Get a specific field mapping"""
    try:
        mapping = FieldMapping.query.get(mapping_id)
        if not mapping:
            return jsonify({
                'success': False,
                'error': 'Mapping not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': mapping.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/mappings/<int:mapping_id>', methods=['PUT'])
def update_mapping(mapping_id):
    """Update a field mapping"""
    try:
        mapping = FieldMapping.query.get(mapping_id)
        if not mapping:
            return jsonify({
                'success': False,
                'error': 'Mapping not found'
            }), 404
        
        data = request.get_json()
        
        # Update fields if provided
        if 'name' in data:
            mapping.name = data['name']
        if 'mapping_config' in data:
            mapping.mapping_config = json.dumps(data['mapping_config'])
        if 'transformation_rules' in data:
            mapping.transformation_rules = json.dumps(data['transformation_rules'])
        if 'is_active' in data:
            mapping.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': mapping.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/mappings/<int:mapping_id>', methods=['DELETE'])
def delete_mapping(mapping_id):
    """Delete a field mapping (soft delete)"""
    try:
        mapping = FieldMapping.query.get(mapping_id)
        if not mapping:
            return jsonify({
                'success': False,
                'error': 'Mapping not found'
            }), 404
        
        mapping.is_active = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Mapping deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/mappings/<int:mapping_id>/preview', methods=['POST'])
def preview_mapping(mapping_id):
    """Preview the result of applying a mapping to sample data"""
    try:
        mapping = FieldMapping.query.get(mapping_id)
        if not mapping:
            return jsonify({
                'success': False,
                'error': 'Mapping not found'
            }), 404
        
        data = request.get_json()
        sample_data = data.get('sample_data', [])
        
        # Import and use the transformation service
        from app.services.transformation_service import TransformationService
        service = TransformationService()
        result = service.preview_transformation(mapping, sample_data)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500