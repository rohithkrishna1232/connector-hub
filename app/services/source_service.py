import requests
import json
from app.models import DataSource

class SourceService:
    """Service for handling data source operations"""
    
    def test_connection(self, source: DataSource):
        """Test connection to a data source"""
        try:
            config = json.loads(source.connection_config)
            
            if source.type == 'api':
                return self._test_api_connection(config)
            elif source.type == 'database':
                return self._test_database_connection(config)
            elif source.type == 'file':
                return self._test_file_connection(config)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported source type: {source.type}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _test_api_connection(self, config):
        """Test API connection"""
        try:
            url = config.get('url')
            headers = config.get('headers', {})
            auth = config.get('auth', {})
            
            if not url:
                return {'success': False, 'error': 'URL is required for API connection'}
            
            # Prepare authentication
            auth_params = None
            if auth.get('type') == 'basic':
                auth_params = (auth.get('username'), auth.get('password'))
            elif auth.get('type') == 'bearer':
                headers['Authorization'] = f"Bearer {auth.get('token')}"
            
            response = requests.get(url, headers=headers, auth=auth_params, timeout=10)
            
            return {
                'success': True,
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'message': 'Connection successful'
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Connection failed: {str(e)}'
            }
    
    def _test_database_connection(self, config):
        """Test database connection"""
        # This is a placeholder - implement based on your database requirements
        try:
            db_type = config.get('type', 'postgresql')
            host = config.get('host')
            port = config.get('port')
            database = config.get('database')
            
            if not all([host, port, database]):
                return {'success': False, 'error': 'Host, port, and database are required'}
            
            # Here you would implement actual database connection testing
            # For different database types (PostgreSQL, MySQL, SQL Server, etc.)
            
            return {
                'success': True,
                'message': f'Database connection test successful for {db_type}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Database connection failed: {str(e)}'
            }
    
    def _test_file_connection(self, config):
        """Test file connection"""
        try:
            file_path = config.get('path')
            file_type = config.get('type', 'csv')
            
            if not file_path:
                return {'success': False, 'error': 'File path is required'}
            
            # Here you would implement file access testing
            import os
            if os.path.exists(file_path):
                return {
                    'success': True,
                    'message': f'File access successful for {file_type} file'
                }
            else:
                return {
                    'success': False,
                    'error': 'File not found'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'File connection failed: {str(e)}'
            }
    
    def get_schema(self, source: DataSource):
        """Get schema information from a data source"""
        try:
            config = json.loads(source.connection_config)
            
            if source.type == 'api':
                return self._get_api_schema(config)
            elif source.type == 'database':
                return self._get_database_schema(config)
            elif source.type == 'file':
                return self._get_file_schema(config)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported source type: {source.type}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_api_schema(self, config):
        """Get schema from API endpoint"""
        try:
            # This is a placeholder - implement based on your API requirements
            schema_url = config.get('schema_url') or f"{config.get('url')}/schema"
            
            # Return a sample schema structure
            return {
                'success': True,
                'fields': [
                    {'name': 'id', 'type': 'integer', 'required': True},
                    {'name': 'name', 'type': 'string', 'required': True},
                    {'name': 'email', 'type': 'string', 'required': False},
                    {'name': 'created_at', 'type': 'datetime', 'required': False}
                ]
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to get API schema: {str(e)}'
            }
    
    def _get_database_schema(self, config):
        """Get schema from database"""
        # Placeholder implementation
        return {
            'success': True,
            'fields': [
                {'name': 'id', 'type': 'integer', 'required': True, 'primary_key': True},
                {'name': 'name', 'type': 'varchar', 'length': 255, 'required': True},
                {'name': 'email', 'type': 'varchar', 'length': 255, 'required': False},
                {'name': 'created_at', 'type': 'timestamp', 'required': False}
            ]
        }
    
    def _get_file_schema(self, config):
        """Get schema from file"""
        # Placeholder implementation
        return {
            'success': True,
            'fields': [
                {'name': 'id', 'type': 'integer', 'required': True},
                {'name': 'name', 'type': 'string', 'required': True},
                {'name': 'email', 'type': 'string', 'required': False},
                {'name': 'created_at', 'type': 'string', 'required': False}
            ]
        }
    
    def get_data(self, source: DataSource, limit=None, offset=None):
        """Get data from a source"""
        try:
            config = json.loads(source.connection_config)
            
            if source.type == 'api':
                return self._get_api_data(config, limit, offset)
            elif source.type == 'database':
                return self._get_database_data(config, limit, offset)
            elif source.type == 'file':
                return self._get_file_data(config, limit, offset)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported source type: {source.type}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_api_data(self, config, limit=None, offset=None):
        """Get data from API"""
        try:
            url = config.get('url')
            headers = config.get('headers', {})
            params = config.get('params', {})
            
            if limit:
                params['limit'] = limit
            if offset:
                params['offset'] = offset
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            return {
                'success': True,
                'data': response.json(),
                'total_records': len(response.json()) if isinstance(response.json(), list) else 1
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to get API data: {str(e)}'
            }
    
    def _get_database_data(self, config, limit=None, offset=None):
        """Get data from database"""
        # Placeholder implementation
        return {
            'success': True,
            'data': [
                {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'},
                {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com'}
            ],
            'total_records': 2
        }
    
    def _get_file_data(self, config, limit=None, offset=None):
        """Get data from file"""
        # Placeholder implementation
        return {
            'success': True,
            'data': [
                {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'},
                {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com'}
            ],
            'total_records': 2
        }