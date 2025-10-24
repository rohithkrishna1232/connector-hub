from flask import request, jsonify
from app.api import api_bp

@api_bp.route('/transform', methods=['POST'])
def transform_data():
    """Transform data using transformation rules"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'data' not in data or 'transformations' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: data, transformations'
            }), 400
        
        # Import and use the transformation service
        from app.services.transformation_service import TransformationService
        service = TransformationService()
        result = service.transform_data(data['data'], data['transformations'])
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/transform/validate', methods=['POST'])
def validate_transformations():
    """Validate transformation rules"""
    try:
        data = request.get_json()
        
        if 'transformations' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: transformations'
            }), 400
        
        # Import and use the transformation service
        from app.services.transformation_service import TransformationService
        service = TransformationService()
        result = service.validate_transformations(data['transformations'])
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/transform/functions', methods=['GET'])
def get_transformation_functions():
    """Get available transformation functions"""
    try:
        # Import and use the transformation service
        from app.services.transformation_service import TransformationService
        service = TransformationService()
        functions = service.get_available_functions()
        
        return jsonify({
            'success': True,
            'data': functions
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500