from flask import request, jsonify
from app.api import api_bp
from app.models import DataSource, db
import json

@api_bp.route('/sources', methods=['GET'])
def get_sources():
    """Get all data sources"""
    try:
        sources = DataSource.query.filter_by(is_active=True).all()
        return jsonify({
            'success': True,
            'data': [source.to_dict() for source in sources]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/sources', methods=['POST'])
def create_source():
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
        
        source = DataSource(
            name=data['name'],
            type=data['type'],
            connection_config=json.dumps(data['connection_config']),
            schema_info=json.dumps(data.get('schema_info', {}))
        )
        
        db.session.add(source)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': source.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/sources/<int:source_id>', methods=['GET'])
def get_source(source_id):
    """Get a specific data source"""
    try:
        source = DataSource.query.get(source_id)
        if not source:
            return jsonify({
                'success': False,
                'error': 'Source not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': source.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/sources/<int:source_id>', methods=['PUT'])
def update_source(source_id):
    """Update a data source"""
    try:
        source = DataSource.query.get(source_id)
        if not source:
            return jsonify({
                'success': False,
                'error': 'Source not found'
            }), 404
        
        data = request.get_json()
        
        # Update fields if provided
        if 'name' in data:
            source.name = data['name']
        if 'type' in data:
            source.type = data['type']
        if 'connection_config' in data:
            source.connection_config = json.dumps(data['connection_config'])
        if 'schema_info' in data:
            source.schema_info = json.dumps(data['schema_info'])
        if 'is_active' in data:
            source.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': source.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/sources/<int:source_id>', methods=['DELETE'])
def delete_source(source_id):
    """Delete a data source (soft delete)"""
    try:
        source = DataSource.query.get(source_id)
        if not source:
            return jsonify({
                'success': False,
                'error': 'Source not found'
            }), 404
        
        source.is_active = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Source deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/sources/<int:source_id>/test', methods=['POST'])
def test_source_connection(source_id):
    """Test connection to a data source"""
    try:
        source = DataSource.query.get(source_id)
        if not source:
            return jsonify({
                'success': False,
                'error': 'Source not found'
            }), 404
        
        # Import and use the source service to test connection
        from app.services.source_service import SourceService
        service = SourceService()
        result = service.test_connection(source)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/sources/<int:source_id>/schema', methods=['GET'])
def get_source_schema(source_id):
    """Get schema information for a data source"""
    try:
        source = DataSource.query.get(source_id)
        if not source:
            return jsonify({
                'success': False,
                'error': 'Source not found'
            }), 404
        
        # Import and use the source service to get schema
        from app.services.source_service import SourceService
        service = SourceService()
        schema = service.get_schema(source)
        
        return jsonify({
            'success': True,
            'data': schema
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500