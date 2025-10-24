from flask import request, jsonify
from app.api import api_bp
from app.services.gemini_service import GeminiAIService
import json

@api_bp.route('/ai/analyze-docs', methods=['POST'])
def analyze_documentation():
    """Analyze API documentation using Gemini AI"""
    try:
        data = request.get_json()
        
        if 'content' not in data:
            return jsonify({
                'success': False,
                'error': 'Documentation content is required'
            }), 400
        
        content = data['content']
        file_type = data.get('file_type', 'text')
        
        gemini_service = GeminiAIService()
        result = gemini_service.analyze_api_documentation(content, file_type)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/ai/analyze-postman', methods=['POST'])
def analyze_postman_collection():
    """Analyze Postman collection using Gemini AI"""
    try:
        data = request.get_json()
        
        if 'collection' not in data:
            return jsonify({
                'success': False,
                'error': 'Postman collection data is required'
            }), 400
        
        collection_data = data['collection']
        
        gemini_service = GeminiAIService()
        result = gemini_service.analyze_postman_collection(collection_data)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/ai/suggest-mappings', methods=['POST'])
def suggest_field_mappings():
    """Generate AI-powered field mapping suggestions"""
    try:
        data = request.get_json()
        
        required_fields = ['source_schema', 'destination_schema']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        source_schema = data['source_schema']
        destination_schema = data['destination_schema']
        
        gemini_service = GeminiAIService()
        result = gemini_service.suggest_field_mappings(source_schema, destination_schema)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/ai/validate-mapping', methods=['POST'])
def validate_mapping():
    """Validate mapping configuration using Gemini AI"""
    try:
        data = request.get_json()
        
        required_fields = ['mapping_config', 'source_schema', 'destination_schema']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        mapping_config = data['mapping_config']
        source_schema = data['source_schema']
        destination_schema = data['destination_schema']
        
        gemini_service = GeminiAIService()
        result = gemini_service.validate_mapping_configuration(
            mapping_config, source_schema, destination_schema
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/ai/suggest-transformations', methods=['POST'])
def suggest_transformations():
    """Suggest transformations for a field mapping"""
    try:
        data = request.get_json()
        
        required_fields = ['source_field', 'destination_field']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        source_field = data['source_field']
        destination_field = data['destination_field']
        
        gemini_service = GeminiAIService()
        result = gemini_service.suggest_transformations(source_field, destination_field)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/ai/auto-configure-source', methods=['POST'])
def auto_configure_source():
    """Auto-configure a data source using API documentation"""
    try:
        data = request.get_json()
        
        if 'documentation' not in data:
            return jsonify({
                'success': False,
                'error': 'API documentation is required'
            }), 400
        
        documentation = data['documentation']
        source_type = data.get('source_type', 'api')
        
        gemini_service = GeminiAIService()
        
        # Analyze the documentation
        analysis_result = gemini_service.analyze_api_documentation(documentation)
        
        if not analysis_result['success']:
            return jsonify(analysis_result)
        
        analysis = analysis_result.get('analysis')
        if not analysis:
            return jsonify({
                'success': False,
                'error': 'Could not extract structured information from documentation'
            })
        
        # Create source configuration based on analysis
        source_config = {
            'name': f"Auto-configured {source_type.upper()} Source",
            'type': source_type,
            'connection_config': {},
            'schema_info': {}
        }
        
        if source_type == 'api' and analysis:
            # Configure API source
            base_url = analysis.get('base_url', '')
            auth = analysis.get('authentication', {})
            
            source_config['connection_config'] = {
                'url': base_url,
                'method': 'GET',
                'headers': {'Content-Type': 'application/json'},
                'auth': {
                    'type': auth.get('type', 'none'),
                    'description': auth.get('description', '')
                }
            }
            
            # Extract schema from endpoints
            endpoints = analysis.get('endpoints', [])
            if endpoints:
                # Use the first GET endpoint as the source
                get_endpoints = [ep for ep in endpoints if ep.get('method') == 'GET']
                if get_endpoints:
                    endpoint = get_endpoints[0]
                    source_config['connection_config']['url'] = f"{base_url}{endpoint.get('path', '')}"
                    
                    # Extract schema from response
                    response_schema = endpoint.get('response_schema', {})
                    if response_schema:
                        fields = []
                        for field_name, field_type in response_schema.items():
                            fields.append({
                                'name': field_name,
                                'type': field_type,
                                'required': False
                            })
                        source_config['schema_info'] = {'fields': fields}
            
            # Add common fields if available
            common_fields = analysis.get('common_fields', [])
            if common_fields and not source_config['schema_info']:
                source_config['schema_info'] = {'fields': common_fields}
        
        return jsonify({
            'success': True,
            'source_config': source_config,
            'analysis': analysis,
            'suggested_endpoints': analysis.get('endpoints', []) if analysis else []
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/ai/auto-configure-destination', methods=['POST'])
def auto_configure_destination():
    """Auto-configure a data destination using API documentation"""
    try:
        data = request.get_json()
        
        if 'documentation' not in data:
            return jsonify({
                'success': False,
                'error': 'API documentation is required'
            }), 400
        
        documentation = data['documentation']
        dest_type = data.get('destination_type', 'api')
        
        gemini_service = GeminiAIService()
        
        # Analyze the documentation
        analysis_result = gemini_service.analyze_api_documentation(documentation)
        
        if not analysis_result['success']:
            return jsonify(analysis_result)
        
        analysis = analysis_result.get('analysis')
        if not analysis:
            return jsonify({
                'success': False,
                'error': 'Could not extract structured information from documentation'
            })
        
        # Create destination configuration based on analysis
        dest_config = {
            'name': f"Auto-configured {dest_type.upper()} Destination",
            'type': dest_type,
            'connection_config': {},
            'schema_info': {}
        }
        
        if dest_type == 'api' and analysis:
            # Configure API destination
            base_url = analysis.get('base_url', '')
            auth = analysis.get('authentication', {})
            
            dest_config['connection_config'] = {
                'url': base_url,
                'method': 'POST',
                'headers': {'Content-Type': 'application/json'},
                'auth': {
                    'type': auth.get('type', 'none'),
                    'description': auth.get('description', '')
                }
            }
            
            # Extract schema from endpoints
            endpoints = analysis.get('endpoints', [])
            if endpoints:
                # Use the first POST endpoint as the destination
                post_endpoints = [ep for ep in endpoints if ep.get('method') in ['POST', 'PUT']]
                if post_endpoints:
                    endpoint = post_endpoints[0]
                    dest_config['connection_config']['url'] = f"{base_url}{endpoint.get('path', '')}"
                    dest_config['connection_config']['method'] = endpoint.get('method', 'POST')
                    
                    # Extract schema from request
                    request_schema = endpoint.get('request_schema', {})
                    if request_schema:
                        fields = []
                        for field_name, field_type in request_schema.items():
                            fields.append({
                                'name': field_name,
                                'type': field_type,
                                'required': True  # Assume required for destinations
                            })
                        dest_config['schema_info'] = {'fields': fields}
            
            # Add common fields if available
            common_fields = analysis.get('common_fields', [])
            if common_fields and not dest_config['schema_info']:
                dest_config['schema_info'] = {'fields': common_fields}
        
        return jsonify({
            'success': True,
            'destination_config': dest_config,
            'analysis': analysis,
            'suggested_endpoints': analysis.get('endpoints', []) if analysis else []
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/ai/generate-sample-data', methods=['POST'])
def generate_sample_data():
    """Generate sample data based on schema"""
    try:
        data = request.get_json()
        
        if 'schema' not in data:
            return jsonify({
                'success': False,
                'error': 'Schema is required'
            }), 400
        
        schema = data['schema']
        num_records = data.get('num_records', 5)
        
        prompt = f"""
        Generate {num_records} realistic sample data records based on this schema:
        
        {json.dumps(schema, indent=2)}
        
        Return the data in JSON format as an array of objects:
        [
            {{"field1": "value1", "field2": "value2"}},
            {{"field1": "value3", "field2": "value4"}}
        ]
        
        Make the data realistic and varied. For example:
        - Use real-looking names, emails, addresses
        - Use appropriate data types (integers, dates, booleans)
        - Vary the values to show different scenarios
        - Include some edge cases if relevant
        """
        
        gemini_service = GeminiAIService()
        result = gemini_service.generate_content(prompt)
        
        if result['success']:
            try:
                content = result['content']
                # Extract JSON from the response
                if '```json' in content:
                    json_start = content.find('```json') + 7
                    json_end = content.find('```', json_start)
                    content = content[json_start:json_end].strip()
                elif '[' in content and ']' in content:
                    # Find the JSON array
                    json_start = content.find('[')
                    json_end = content.rfind(']') + 1
                    content = content[json_start:json_end]
                
                sample_data = json.loads(content)
                
                return jsonify({
                    'success': True,
                    'sample_data': sample_data,
                    'count': len(sample_data)
                })
                
            except json.JSONDecodeError:
                return jsonify({
                    'success': False,
                    'error': 'Could not parse generated sample data',
                    'raw_content': result['content']
                })
        else:
            return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500