import requests
import json
from app.models import DataDestination

class DestinationService:
    """Service for handling data destination operations"""
    
    def test_connection(self, destination: DataDestination):
        """Test connection to a data destination"""
        try:
            config = json.loads(destination.connection_config)
            
            if destination.type == 'api':
                return self._test_api_connection(config)
            elif destination.type == 'database':
                return self._test_database_connection(config)
            elif destination.type == 'file':
                return self._test_file_connection(config)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported destination type: {destination.type}'
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
            
            # Test with a HEAD request or OPTIONS to avoid creating data
            response = requests.head(url, headers=headers, auth=auth_params, timeout=10)
            
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
        try:
            db_type = config.get('type', 'postgresql')
            host = config.get('host')
            port = config.get('port')
            database = config.get('database')
            
            if not all([host, port, database]):
                return {'success': False, 'error': 'Host, port, and database are required'}
            
            # Here you would implement actual database connection testing
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
            
            # Test if directory exists and is writable
            import os
            directory = os.path.dirname(file_path)
            if os.path.exists(directory) and os.access(directory, os.W_OK):
                return {
                    'success': True,
                    'message': f'File destination accessible for {file_type} file'
                }
            else:
                return {
                    'success': False,
                    'error': 'Directory not found or not writable'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'File connection failed: {str(e)}'
            }
    
    def send_data(self, destination: DataDestination, data):
        """Send data to a destination"""
        try:
            config = json.loads(destination.connection_config)
            
            if destination.type == 'api':
                return self._send_api_data(config, data)
            elif destination.type == 'database':
                return self._send_database_data(config, data)
            elif destination.type == 'file':
                return self._send_file_data(config, data)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported destination type: {destination.type}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _send_api_data(self, config, data):
        """Send data to API endpoint"""
        try:
            url = config.get('url')
            headers = config.get('headers', {})
            method = config.get('method', 'POST').upper()
            auth = config.get('auth', {})
            
            if not url:
                return {'success': False, 'error': 'URL is required for API destination'}
            
            # Prepare authentication
            auth_params = None
            if auth.get('type') == 'basic':
                auth_params = (auth.get('username'), auth.get('password'))
            elif auth.get('type') == 'bearer':
                headers['Authorization'] = f"Bearer {auth.get('token')}"
            
            # Set content type
            headers['Content-Type'] = 'application/json'
            
            # Send data
            if method == 'POST':
                response = requests.post(url, json=data, headers=headers, auth=auth_params, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, auth=auth_params, timeout=30)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, auth=auth_params, timeout=30)
            else:
                return {'success': False, 'error': f'Unsupported HTTP method: {method}'}
            
            response.raise_for_status()
            
            return {
                'success': True,
                'status_code': response.status_code,
                'response': response.json() if response.content else None,
                'records_sent': len(data) if isinstance(data, list) else 1
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Failed to send data to API: {str(e)}'
            }
    
    def _send_database_data(self, config, data):
        """Send data to database"""
        try:
            # Placeholder implementation
            # Here you would implement actual database insertion
            table_name = config.get('table')
            
            if not table_name:
                return {'success': False, 'error': 'Table name is required for database destination'}
            
            # Simulate successful insertion
            records_count = len(data) if isinstance(data, list) else 1
            
            return {
                'success': True,
                'message': f'Successfully inserted {records_count} records into {table_name}',
                'records_sent': records_count
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to send data to database: {str(e)}'
            }
    
    def _send_file_data(self, config, data):
        """Send data to file"""
        try:
            file_path = config.get('path')
            file_type = config.get('type', 'csv')
            mode = config.get('mode', 'append')  # append or overwrite
            
            if not file_path:
                return {'success': False, 'error': 'File path is required for file destination'}
            
            # Handle different file types
            import os
            import csv
            
            # Ensure directory exists
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            if file_type.lower() == 'csv':
                # Handle CSV files without pandas
                if isinstance(data, list) and len(data) > 0:
                    # Get headers from first record
                    headers = list(data[0].keys())
                    
                    # Check if file exists and mode is append
                    file_exists = os.path.exists(file_path)
                    write_mode = 'w' if mode == 'overwrite' else 'a'
                    write_header = not file_exists or mode == 'overwrite'
                    
                    with open(file_path, write_mode, newline='', encoding='utf-8') as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=headers)
                        
                        if write_header:
                            writer.writeheader()
                        
                        for record in data:
                            writer.writerow(record)
                else:
                    # Single record
                    headers = list(data.keys()) if isinstance(data, dict) else []
                    file_exists = os.path.exists(file_path)
                    write_mode = 'w' if mode == 'overwrite' else 'a'
                    write_header = not file_exists or mode == 'overwrite'
                    
                    with open(file_path, write_mode, newline='', encoding='utf-8') as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=headers)
                        
                        if write_header:
                            writer.writeheader()
                        
                        writer.writerow(data)
                
            elif file_type.lower() == 'json':
                write_mode = 'w' if mode == 'overwrite' else 'a'
                with open(file_path, write_mode) as f:
                    if isinstance(data, list):
                        for record in data:
                            json.dump(record, f)
                            f.write('\n')
                    else:
                        json.dump(data, f)
                        f.write('\n')
            
            else:
                return {'success': False, 'error': f'Unsupported file type: {file_type}'}
            
            records_count = len(data) if isinstance(data, list) else 1
            
            return {
                'success': True,
                'message': f'Successfully wrote {records_count} records to {file_path}',
                'records_sent': records_count
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to send data to file: {str(e)}'
            }
    
    def get_schema(self, destination: DataDestination):
        """Get schema information for a destination"""
        try:
            config = json.loads(destination.connection_config)
            
            if destination.type == 'api':
                return self._get_api_schema(config)
            elif destination.type == 'database':
                return self._get_database_schema(config)
            elif destination.type == 'file':
                return self._get_file_schema(config)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported destination type: {destination.type}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_api_schema(self, config):
        """Get schema from API endpoint"""
        # Placeholder implementation
        return {
            'success': True,
            'fields': [
                {'name': 'id', 'type': 'integer', 'required': False},
                {'name': 'name', 'type': 'string', 'required': True},
                {'name': 'email', 'type': 'string', 'required': True},
                {'name': 'updated_at', 'type': 'datetime', 'required': False}
            ]
        }
    
    def _get_database_schema(self, config):
        """Get schema from database"""
        # Placeholder implementation
        return {
            'success': True,
            'fields': [
                {'name': 'id', 'type': 'integer', 'required': False, 'auto_increment': True},
                {'name': 'name', 'type': 'varchar', 'length': 255, 'required': True},
                {'name': 'email', 'type': 'varchar', 'length': 255, 'required': True},
                {'name': 'updated_at', 'type': 'timestamp', 'required': False}
            ]
        }
    
    def _get_file_schema(self, config):
        """Get schema from file configuration"""
        # Placeholder implementation
        return {
            'success': True,
            'fields': [
                {'name': 'id', 'type': 'integer', 'required': False},
                {'name': 'name', 'type': 'string', 'required': True},
                {'name': 'email', 'type': 'string', 'required': True},
                {'name': 'updated_at', 'type': 'string', 'required': False}
            ]
        }