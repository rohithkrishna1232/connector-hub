import requests
import json
import os
from typing import Dict, List, Any, Optional

class GeminiAIService:
    """Service for integrating with Google Gemini AI API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or "AIzaSyAm1BC94o7Cym57yhz1nTp45-3wVYIM21w"
        self.base_url = "https://generativelanguage.googleapis.com/v1/models"
        self.model = "gemini-2.5-flash"
    
    def generate_content(self, prompt: str, max_tokens: int = 1000) -> Dict[str, Any]:
        """Generate content using Gemini AI"""
        try:
            url = f"{self.base_url}/{self.model}:generateContent"
            headers = {
                "Content-Type": "application/json"
            }
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "maxOutputTokens": max_tokens,
                    "temperature": 0.7
                }
            }
            
            response = requests.post(
                f"{url}?key={self.api_key}",
                headers=headers,
                json=data,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            if 'candidates' in result and len(result['candidates']) > 0:
                content = result['candidates'][0]['content']['parts'][0]['text']
                return {
                    'success': True,
                    'content': content,
                    'raw_response': result
                }
            else:
                return {
                    'success': False,
                    'error': 'No content generated'
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'API request failed: {str(e)}'
            }
        except KeyError as e:
            return {
                'success': False,
                'error': f'Invalid response format: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    def analyze_api_documentation(self, documentation: str, file_type: str = 'text') -> Dict[str, Any]:
        """Analyze API documentation and extract endpoints, schemas, etc."""
        prompt = f"""
        Analyze this API documentation and extract structured information for data integration:

        File Type: {file_type}
        Documentation Content:
        {documentation}

        Please extract and return the following in JSON format:
        {{
            "endpoints": [
                {{
                    "path": "/api/endpoint",
                    "method": "GET|POST|PUT|DELETE",
                    "description": "endpoint description",
                    "parameters": [
                        {{"name": "param1", "type": "string", "required": true, "description": "..."}}
                    ],
                    "request_schema": {{"field1": "type1", "field2": "type2"}},
                    "response_schema": {{"field1": "type1", "field2": "type2"}}
                }}
            ],
            "authentication": {{
                "type": "bearer|basic|api_key|oauth",
                "description": "auth description"
            }},
            "base_url": "https://api.example.com",
            "data_formats": ["json", "xml", "form-data"],
            "rate_limits": "description of rate limits",
            "common_fields": [
                {{"name": "id", "type": "integer", "description": "unique identifier"}},
                {{"name": "created_at", "type": "datetime", "description": "creation timestamp"}}
            ]
        }}

        Focus on extracting actual API endpoints, request/response schemas, and data field information that would be useful for creating data integration mappings.
        """
        
        result = self.generate_content(prompt, max_tokens=2000)
        
        if result['success']:
            try:
                # Try to parse JSON from the response
                content = result['content']
                # Extract JSON from the response (it might be wrapped in markdown)
                if '```json' in content:
                    json_start = content.find('```json') + 7
                    json_end = content.find('```', json_start)
                    content = content[json_start:json_end].strip()
                elif '```' in content:
                    json_start = content.find('```') + 3
                    json_end = content.find('```', json_start)
                    content = content[json_start:json_end].strip()
                
                parsed_data = json.loads(content)
                return {
                    'success': True,
                    'analysis': parsed_data,
                    'raw_content': result['content']
                }
            except json.JSONDecodeError:
                return {
                    'success': True,
                    'analysis': None,
                    'raw_content': result['content'],
                    'note': 'Could not parse as JSON, returning raw analysis'
                }
        else:
            return result
    
    def analyze_postman_collection(self, collection_data: Dict) -> Dict[str, Any]:
        """Analyze Postman collection and extract API information"""
        prompt = f"""
        Analyze this Postman collection and extract useful information for data integration:

        Collection Data:
        {json.dumps(collection_data, indent=2)}

        Please extract and return in JSON format:
        {{
            "collection_info": {{
                "name": "collection name",
                "description": "collection description"
            }},
            "endpoints": [
                {{
                    "name": "request name",
                    "method": "GET|POST|PUT|DELETE",
                    "url": "{{base_url}}/endpoint",
                    "headers": {{"Content-Type": "application/json"}},
                    "body_schema": {{"field1": "type1"}},
                    "response_examples": [{{}}],
                    "description": "what this endpoint does"
                }}
            ],
            "variables": {{
                "base_url": "https://api.example.com",
                "api_key": "{{api_key}}"
            }},
            "authentication": {{
                "type": "bearer|basic|api_key",
                "details": "how to authenticate"
            }},
            "suggested_sources": [
                {{
                    "name": "Source Name",
                    "endpoint": "/api/data",
                    "method": "GET",
                    "description": "Gets data from this API",
                    "fields": [{{"name": "id", "type": "integer"}}]
                }}
            ],
            "suggested_destinations": [
                {{
                    "name": "Destination Name", 
                    "endpoint": "/api/data",
                    "method": "POST",
                    "description": "Sends data to this API",
                    "fields": [{{"name": "id", "type": "integer"}}]
                }}
            ]
        }}

        Focus on extracting endpoints that could serve as data sources (GET requests) or destinations (POST/PUT requests).
        """
        
        result = self.generate_content(prompt, max_tokens=2000)
        
        if result['success']:
            try:
                content = result['content']
                # Extract JSON from the response
                if '```json' in content:
                    json_start = content.find('```json') + 7
                    json_end = content.find('```', json_start)
                    content = content[json_start:json_end].strip()
                elif '```' in content:
                    json_start = content.find('```') + 3
                    json_end = content.find('```', json_start)
                    content = content[json_start:json_end].strip()
                
                parsed_data = json.loads(content)
                return {
                    'success': True,
                    'analysis': parsed_data,
                    'raw_content': result['content']
                }
            except json.JSONDecodeError:
                return {
                    'success': True,
                    'analysis': None,
                    'raw_content': result['content'],
                    'note': 'Could not parse as JSON, returning raw analysis'
                }
        else:
            return result
    
    def suggest_field_mappings(self, source_schema: List[Dict], destination_schema: List[Dict]) -> Dict[str, Any]:
        """Generate AI-powered field mapping suggestions"""
        prompt = f"""
        Analyze these data schemas and suggest optimal field mappings and transformations:

        Source Schema:
        {json.dumps(source_schema, indent=2)}

        Destination Schema:
        {json.dumps(destination_schema, indent=2)}

        Please provide mapping suggestions in JSON format:
        {{
            "mappings": [
                {{
                    "source_field": "source_field_name",
                    "destination_field": "dest_field_name",
                    "confidence": 0.95,
                    "reason": "exact name match",
                    "transformation_needed": false,
                    "suggested_transformation": null
                }}
            ],
            "transformations": [
                {{
                    "field": "field_name",
                    "source_type": "string",
                    "dest_type": "datetime",
                    "rule": "format_date",
                    "parameters": {{"format": "%Y-%m-%d"}},
                    "description": "Convert string to date format"
                }}
            ],
            "unmapped_source_fields": ["field1", "field2"],
            "unmapped_dest_fields": ["field3", "field4"],
            "recommendations": [
                "Consider using default values for required destination fields that have no source mapping",
                "Validate data types before transformation"
            ],
            "potential_issues": [
                "Source field 'user_id' is string but destination expects integer",
                "Required destination field 'email' has no corresponding source field"
            ],
            "data_quality_checks": [
                {{
                    "field": "email",
                    "check": "email_validation",
                    "description": "Validate email format before inserting"
                }}
            ]
        }}

        Focus on:
        1. Exact name matches (highest confidence)
        2. Similar name matches (partial confidence)
        3. Semantic matches (moderate confidence)
        4. Required transformations for data type compatibility
        5. Data validation requirements
        """
        
        result = self.generate_content(prompt, max_tokens=2000)
        
        if result['success']:
            try:
                content = result['content']
                if '```json' in content:
                    json_start = content.find('```json') + 7
                    json_end = content.find('```', json_start)
                    content = content[json_start:json_end].strip()
                elif '```' in content:
                    json_start = content.find('```') + 3
                    json_end = content.find('```', json_start)
                    content = content[json_start:json_end].strip()
                
                parsed_data = json.loads(content)
                return {
                    'success': True,
                    'suggestions': parsed_data,
                    'raw_content': result['content']
                }
            except json.JSONDecodeError:
                return {
                    'success': True,
                    'suggestions': None,
                    'raw_content': result['content'],
                    'note': 'Could not parse as JSON, returning raw analysis'
                }
        else:
            return result
    
    def validate_mapping_configuration(self, mapping_config: Dict, source_schema: List[Dict], dest_schema: List[Dict]) -> Dict[str, Any]:
        """Validate a mapping configuration using AI"""
        prompt = f"""
        Validate this data integration mapping configuration:

        Mapping Configuration:
        {json.dumps(mapping_config, indent=2)}

        Source Schema:
        {json.dumps(source_schema, indent=2)}

        Destination Schema:
        {json.dumps(dest_schema, indent=2)}

        Please provide validation results in JSON format:
        {{
            "is_valid": true,
            "validation_score": 0.85,
            "issues": [
                {{
                    "severity": "error|warning|info",
                    "field": "field_name",
                    "issue": "Data type mismatch",
                    "description": "Source field is string but destination expects integer",
                    "suggestion": "Add integer conversion transformation"
                }}
            ],
            "missing_mappings": [
                {{
                    "field": "required_dest_field",
                    "reason": "Required destination field has no source mapping",
                    "suggestion": "Map from source field or provide default value"
                }}
            ],
            "data_type_issues": [
                {{
                    "source_field": "date_string",
                    "dest_field": "created_date",
                    "source_type": "string",
                    "dest_type": "datetime",
                    "solution": "Add date parsing transformation"
                }}
            ],
            "performance_considerations": [
                "Large text fields may impact transfer speed",
                "Consider pagination for large datasets"
            ],
            "best_practices": [
                "Add data validation before transformation",
                "Implement error handling for failed transformations",
                "Consider backup strategy for failed records"
            ],
            "recommendations": [
                "Test mapping with sample data before full execution",
                "Monitor data quality metrics during transfer"
            ]
        }}

        Check for:
        1. Data type compatibility
        2. Required field coverage
        3. Potential data loss
        4. Performance implications
        5. Best practices compliance
        """
        
        result = self.generate_content(prompt, max_tokens=2000)
        
        if result['success']:
            try:
                content = result['content']
                if '```json' in content:
                    json_start = content.find('```json') + 7
                    json_end = content.find('```', json_start)
                    content = content[json_start:json_end].strip()
                elif '```' in content:
                    json_start = content.find('```') + 3
                    json_end = content.find('```', json_start)
                    content = content[json_start:json_end].strip()
                
                parsed_data = json.loads(content)
                return {
                    'success': True,
                    'validation': parsed_data,
                    'raw_content': result['content']
                }
            except json.JSONDecodeError:
                return {
                    'success': True,
                    'validation': None,
                    'raw_content': result['content'],
                    'note': 'Could not parse as JSON, returning raw validation'
                }
        else:
            return result
    
    def suggest_transformations(self, source_field_info: Dict, dest_field_info: Dict) -> Dict[str, Any]:
        """Suggest transformations for a specific field mapping"""
        prompt = f"""
        Suggest data transformations for mapping this field:

        Source Field:
        {json.dumps(source_field_info, indent=2)}

        Destination Field:
        {json.dumps(dest_field_info, indent=2)}

        Please suggest transformations in JSON format:
        {{
            "transformations": [
                {{
                    "function": "transformation_function_name",
                    "parameters": {{"param1": "value1"}},
                    "description": "What this transformation does",
                    "example_input": "example source value",
                    "example_output": "example transformed value"
                }}
            ],
            "validation_rules": [
                {{
                    "rule": "validation_rule_name",
                    "parameters": {{}},
                    "description": "What this validation checks"
                }}
            ],
            "fallback_strategy": {{
                "on_error": "use_default|skip_record|log_error",
                "default_value": "default if needed",
                "description": "What to do if transformation fails"
            }}
        }}

        Consider common transformations like:
        - Data type conversions
        - String formatting
        - Date/time formatting
        - Value mapping
        - Mathematical operations
        - Text processing
        """
        
        result = self.generate_content(prompt, max_tokens=1000)
        
        if result['success']:
            try:
                content = result['content']
                if '```json' in content:
                    json_start = content.find('```json') + 7
                    json_end = content.find('```', json_start)
                    content = content[json_start:json_end].strip()
                elif '```' in content:
                    json_start = content.find('```') + 3
                    json_end = content.find('```', json_start)
                    content = content[json_start:json_end].strip()
                
                parsed_data = json.loads(content)
                return {
                    'success': True,
                    'transformations': parsed_data,
                    'raw_content': result['content']
                }
            except json.JSONDecodeError:
                return {
                    'success': True,
                    'transformations': None,
                    'raw_content': result['content'],
                    'note': 'Could not parse as JSON, returning raw suggestions'
                }
        else:
            return result