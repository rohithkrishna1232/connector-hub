import json
import re
from datetime import datetime, timedelta
from dateutil import parser

class TransformationService:
    """Service for handling data transformations"""
    
    def __init__(self):
        self.available_functions = {
            'uppercase': {'description': 'Convert string to uppercase', 'params': []},
            'lowercase': {'description': 'Convert string to lowercase', 'params': []},
            'trim': {'description': 'Remove leading and trailing whitespace', 'params': []},
            'replace': {'description': 'Replace substring', 'params': ['old', 'new']},
            'substring': {'description': 'Extract substring', 'params': ['start', 'end']},
            'concat': {'description': 'Concatenate strings', 'params': ['separator']},
            'split': {'description': 'Split string by delimiter', 'params': ['delimiter', 'index']},
            'format_date': {'description': 'Format date', 'params': ['format']},
            'add_days': {'description': 'Add days to date', 'params': ['days']},
            'multiply': {'description': 'Multiply number', 'params': ['factor']},
            'divide': {'description': 'Divide number', 'params': ['divisor']},
            'round': {'description': 'Round number', 'params': ['decimals']},
            'default_value': {'description': 'Set default value if empty', 'params': ['default']},
            'map_value': {'description': 'Map value using dictionary', 'params': ['mapping']},
            'regex_extract': {'description': 'Extract using regex', 'params': ['pattern', 'group']},
            'conditional': {'description': 'Conditional transformation', 'params': ['condition', 'true_value', 'false_value']}
        }
    
    def get_available_functions(self):
        """Get list of available transformation functions"""
        return self.available_functions
    
    def validate_transformations(self, transformations):
        """Validate transformation rules"""
        errors = []
        warnings = []
        
        try:
            for field_name, rules in transformations.items():
                if not isinstance(rules, list):
                    errors.append(f"Field '{field_name}': transformations must be a list")
                    continue
                
                for i, rule in enumerate(rules):
                    if not isinstance(rule, dict):
                        errors.append(f"Field '{field_name}', rule {i}: rule must be a dictionary")
                        continue
                    
                    function_name = rule.get('function')
                    if not function_name:
                        errors.append(f"Field '{field_name}', rule {i}: 'function' is required")
                        continue
                    
                    if function_name not in self.available_functions:
                        errors.append(f"Field '{field_name}', rule {i}: unknown function '{function_name}'")
                        continue
                    
                    # Validate parameters
                    required_params = self.available_functions[function_name]['params']
                    provided_params = rule.get('params', {})
                    
                    for param in required_params:
                        if param not in provided_params:
                            warnings.append(f"Field '{field_name}', rule {i}: missing parameter '{param}' for function '{function_name}'")
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings
            }
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': []
            }
    
    def transform_data(self, data, transformations):
        """Transform data using transformation rules"""
        try:
            if isinstance(data, dict):
                return self._transform_record(data, transformations)
            elif isinstance(data, list):
                return [self._transform_record(record, transformations) for record in data]
            else:
                raise ValueError("Data must be a dictionary or list of dictionaries")
                
        except Exception as e:
            raise Exception(f"Transformation failed: {str(e)}")
    
    def _transform_record(self, record, transformations):
        """Transform a single record"""
        transformed = record.copy()
        
        for field_name, rules in transformations.items():
            if not isinstance(rules, list):
                continue
            
            # Get original value
            value = record.get(field_name)
            
            # Apply transformation rules in sequence
            for rule in rules:
                function_name = rule.get('function')
                params = rule.get('params', {})
                
                if function_name in self.available_functions:
                    value = self._apply_function(value, function_name, params)
            
            # Set transformed value
            transformed[field_name] = value
        
        return transformed
    
    def _apply_function(self, value, function_name, params):
        """Apply a transformation function to a value"""
        try:
            if function_name == 'uppercase':
                return str(value).upper() if value is not None else value
            
            elif function_name == 'lowercase':
                return str(value).lower() if value is not None else value
            
            elif function_name == 'trim':
                return str(value).strip() if value is not None else value
            
            elif function_name == 'replace':
                old = params.get('old', '')
                new = params.get('new', '')
                return str(value).replace(old, new) if value is not None else value
            
            elif function_name == 'substring':
                start = params.get('start', 0)
                end = params.get('end')
                if value is not None:
                    if end is not None:
                        return str(value)[start:end]
                    else:
                        return str(value)[start:]
                return value
            
            elif function_name == 'concat':
                separator = params.get('separator', '')
                fields = params.get('fields', [])
                if isinstance(fields, list) and len(fields) > 0:
                    # This is for concatenating multiple fields
                    # For single field, just return the value
                    return str(value) if value is not None else ''
                return str(value) if value is not None else value
            
            elif function_name == 'split':
                delimiter = params.get('delimiter', ',')
                index = params.get('index', 0)
                if value is not None:
                    parts = str(value).split(delimiter)
                    if 0 <= index < len(parts):
                        return parts[index].strip()
                return value
            
            elif function_name == 'format_date':
                date_format = params.get('format', '%Y-%m-%d')
                if value is not None:
                    if isinstance(value, str):
                        try:
                            date_obj = parser.parse(value)
                            return date_obj.strftime(date_format)
                        except:
                            return value
                    elif isinstance(value, datetime):
                        return value.strftime(date_format)
                return value
            
            elif function_name == 'add_days':
                days = params.get('days', 0)
                if value is not None:
                    if isinstance(value, str):
                        try:
                            date_obj = parser.parse(value)
                            new_date = date_obj + timedelta(days=days)
                            return new_date.isoformat()
                        except:
                            return value
                    elif isinstance(value, datetime):
                        new_date = value + timedelta(days=days)
                        return new_date.isoformat()
                return value
            
            elif function_name == 'multiply':
                factor = params.get('factor', 1)
                if value is not None:
                    try:
                        return float(value) * float(factor)
                    except:
                        return value
                return value
            
            elif function_name == 'divide':
                divisor = params.get('divisor', 1)
                if value is not None and divisor != 0:
                    try:
                        return float(value) / float(divisor)
                    except:
                        return value
                return value
            
            elif function_name == 'round':
                decimals = params.get('decimals', 0)
                if value is not None:
                    try:
                        return round(float(value), decimals)
                    except:
                        return value
                return value
            
            elif function_name == 'default_value':
                default = params.get('default', '')
                return default if value is None or value == '' else value
            
            elif function_name == 'map_value':
                mapping = params.get('mapping', {})
                if value is not None and str(value) in mapping:
                    return mapping[str(value)]
                return value
            
            elif function_name == 'regex_extract':
                pattern = params.get('pattern', '')
                group = params.get('group', 0)
                if value is not None and pattern:
                    try:
                        match = re.search(pattern, str(value))
                        if match:
                            return match.group(group)
                    except:
                        pass
                return value
            
            elif function_name == 'conditional':
                condition = params.get('condition', '')
                true_value = params.get('true_value', value)
                false_value = params.get('false_value', value)
                
                # Simple condition evaluation
                if self._evaluate_condition(value, condition):
                    return true_value
                else:
                    return false_value
            
            else:
                return value
                
        except Exception as e:
            # If transformation fails, return original value
            return value
    
    def _evaluate_condition(self, value, condition):
        """Evaluate a simple condition"""
        try:
            if not condition:
                return False
            
            # Simple condition patterns
            if condition.startswith('=='):
                return str(value) == condition[2:].strip()
            elif condition.startswith('!='):
                return str(value) != condition[2:].strip()
            elif condition.startswith('contains:'):
                return condition[9:].strip() in str(value)
            elif condition.startswith('empty'):
                return value is None or value == ''
            elif condition.startswith('not_empty'):
                return value is not None and value != ''
            else:
                return False
                
        except:
            return False
    
    def preview_transformation(self, mapping, sample_data):
        """Preview transformation results on sample data"""
        try:
            # Get transformation rules from mapping
            transformations = json.loads(mapping.transformation_rules) if mapping.transformation_rules else {}
            
            # Apply transformations to sample data
            if not sample_data:
                return {
                    'success': True,
                    'preview': [],
                    'message': 'No sample data provided'
                }
            
            # Limit preview to first 10 records
            preview_data = sample_data[:10] if len(sample_data) > 10 else sample_data
            
            # Transform the data
            transformed_data = self.transform_data(preview_data, transformations)
            
            return {
                'success': True,
                'original': preview_data,
                'transformed': transformed_data,
                'transformations_applied': transformations
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }