from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
CORS(app)
app.config['SECRET_KEY'] = 'dev-secret-key'

# In-memory storage
STORAGE_FILE = 'data_storage.json'

def load_storage():
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
        'jobs': [],
        'environment_variables': {},  # Global environment variables (deprecated)
        'tool_variables': {}  # Tool-level variables: {'NetSuite': {'account_id': '123', 'token': 'abc'}}
    }

def save_storage(data):
    try:
        with open(STORAGE_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except:
        return False

def analyze_postman_collection_enhanced(collection_data, gemini_service):
    """Enhanced Postman collection analysis with tool detection"""
    try:
        # Extract basic collection info
        info = collection_data.get('info', {})
        collection_name = info.get('name', 'Unknown Collection')
        collection_desc = info.get('description', '')
        
        # Process all requests
        endpoints = []
        tools_detected = set()
        auth_methods = set()
        
        def process_items(items, folder_path=""):
            for item in items:
                if 'item' in item:  # Folder
                    folder_name = item.get('name', 'Unknown Folder')
                    new_path = f"{folder_path}/{folder_name}" if folder_path else folder_name
                    process_items(item['item'], new_path)
                else:  # Request
                    endpoint_info = extract_endpoint_info(item, folder_path)
                    endpoints.append(endpoint_info)
                    
                    # Detect tools from URL
                    url = endpoint_info.get('url', '').lower()
                    detected_tools = detect_tools_from_url(url)
                    tools_detected.update(detected_tools)
                    
                    # Extract auth info
                    auth = item.get('request', {}).get('auth', {})
                    if auth and 'type' in auth:
                        auth_methods.add(auth['type'])
        
        # Process the collection
        if 'item' in collection_data:
            process_items(collection_data['item'])
        
        # Generate AI analysis
        analysis_prompt = f"""
Analyze this Postman API collection for data integration opportunities:

Collection: {collection_name}
Description: {collection_desc}
Endpoints Found: {len(endpoints)}
Tools Detected: {', '.join(tools_detected) if tools_detected else 'None detected'}

Key Endpoints:
{format_endpoints_summary(endpoints[:10])}

Please provide:
1. **API Purpose**: What does this collection do?
2. **Data Sources**: Which endpoints can provide data (suggest as sources)?
3. **Data Destinations**: Which endpoints can receive data (suggest as destinations)?
4. **Integration Workflows**: Suggest possible data flow scenarios
5. **Tool Categories**: Categorize the detected services/tools
6. **Field Mapping Hints**: Common field patterns to look for

Return as structured analysis.
"""
        
        ai_result = gemini_service.generate_content(analysis_prompt, max_tokens=2000)
        
        # Categorize endpoints
        suggested_sources = []
        suggested_destinations = []
        
        for ep in endpoints:
            if ep['method'].upper() == 'GET' and any(keyword in ep['name'].lower() 
                                                   for keyword in ['get', 'list', 'find', 'search', 'fetch']):
                suggested_sources.append({
                    'name': ep['name'],
                    'endpoint': ep['path'],
                    'method': ep['method'],
                    'url': ep['url'],
                    'folder': ep.get('folder', ''),
                    'description': ep.get('description', ''),
                    'reason': 'GET endpoint that retrieves data'
                })
            
            if ep['method'].upper() in ['POST', 'PUT', 'PATCH'] and any(keyword in ep['name'].lower() 
                                                                      for keyword in ['create', 'update', 'post', 'add', 'save']):
                suggested_destinations.append({
                    'name': ep['name'],
                    'endpoint': ep['path'],
                    'method': ep['method'],
                    'url': ep['url'],
                    'folder': ep.get('folder', ''),
                    'description': ep.get('description', ''),
                    'reason': f'{ep["method"]} endpoint that accepts data'
                })
        
        return {
            'success': True,
            'collection_info': {
                'name': collection_name,
                'description': collection_desc,
                'endpoint_count': len(endpoints),
                'folder_structure': extract_folder_structure(collection_data)
            },
            'tools_detected': list(tools_detected),
            'auth_methods': list(auth_methods),
            'endpoints': endpoints,
            'suggested_sources': suggested_sources,
            'suggested_destinations': suggested_destinations,
            'ai_analysis': ai_result.get('content', '') if ai_result.get('success') else 'AI analysis failed',
            'workflows': generate_workflow_suggestions(suggested_sources, suggested_destinations, tools_detected)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error analyzing Postman collection: {str(e)}'
        }

def extract_endpoint_info(item, folder_path=""):
    """Extract endpoint information from Postman request"""
    request = item.get('request', {})
    
    # Handle URL
    url_data = request.get('url', '')
    if isinstance(url_data, dict):
        url = url_data.get('raw', '')
        path = '/' + '/'.join(url_data.get('path', []))
        host = '.'.join(url_data.get('host', []))
    else:
        url = str(url_data)
        # Extract path from URL
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            path = parsed.path
            host = parsed.netloc
        except:
            path = url
            host = ''
    
    # Extract headers
    headers = {}
    for header in request.get('header', []):
        if not header.get('disabled', False):
            headers[header.get('key', '')] = header.get('value', '')
    
    # Extract body
    body_info = {}
    body = request.get('body', {})
    if body:
        body_info = {
            'mode': body.get('mode', 'none'),
            'content': body.get('raw', '') if body.get('mode') == 'raw' else str(body)
        }
    
    return {
        'name': item.get('name', 'Unknown Request'),
        'method': request.get('method', 'GET'),
        'url': url,
        'path': path,
        'host': host,
        'folder': folder_path,
        'headers': headers,
        'body': body_info,
        'description': item.get('description', ''),
        'auth': request.get('auth', {})
    }

def extract_variables_from_text(text):
    """Extract Postman-style variables from any text (e.g., {{variable_name}})"""
    import re
    if not text:
        return []
    text_str = str(text)
    variables = re.findall(r'\{\{([^}]+)\}\}', text_str)
    return list(set(variables))

def extract_variables_from_url(url):
    """Extract Postman-style variables from URL (e.g., {{variable_name}})"""
    return extract_variables_from_text(url)

def extract_auth_variables(auth_config):
    """Extract variables from authentication configuration"""
    variables = set()
    if not auth_config:
        return []

    # Handle OAuth1 and other auth types
    if isinstance(auth_config, dict):
        for key, value in auth_config.items():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and 'value' in item:
                        vars_found = extract_variables_from_text(item.get('value', ''))
                        variables.update(vars_found)
            else:
                vars_found = extract_variables_from_text(value)
                variables.update(vars_found)

    return list(variables)

def extract_variables_from_endpoints(endpoints):
    """Extract all unique variables from a list of endpoints"""
    all_variables = {}

    for ep in endpoints:
        # URL variables
        url = ep.get('url', '')
        url_vars = extract_variables_from_url(url)
        for var in url_vars:
            if var not in all_variables:
                all_variables[var] = {
                    'type': 'url',
                    'required': True,
                    'description': f'URL parameter from {ep.get("name", "endpoint")}'
                }

        # Auth variables
        auth = ep.get('auth', {})
        auth_vars = extract_auth_variables(auth)
        for var in auth_vars:
            if var not in all_variables:
                all_variables[var] = {
                    'type': 'auth',
                    'required': True,
                    'description': f'Authentication credential'
                }

        # Headers variables
        headers = ep.get('headers', {})
        for header_name, header_value in headers.items():
            header_vars = extract_variables_from_text(header_value)
            for var in header_vars:
                if var not in all_variables:
                    all_variables[var] = {
                        'type': 'header',
                        'required': False,
                        'description': f'Header variable for {header_name}'
                    }

        # Body variables
        body = ep.get('body', {})
        if body:
            body_content = body.get('content', '')
            body_vars = extract_variables_from_text(body_content)
            for var in body_vars:
                if var not in all_variables:
                    all_variables[var] = {
                        'type': 'body',
                        'required': False,
                        'description': f'Body parameter'
                    }

    return all_variables

def extract_schema_from_body(body_content):
    """Extract field schema from request body for mapping"""
    import json

    if not body_content:
        return []

    try:
        # Try to parse as JSON
        body_json = json.loads(body_content) if isinstance(body_content, str) else body_content

        fields = []

        def extract_fields(obj, prefix=''):
            """Recursively extract fields from JSON object"""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    field_path = f"{prefix}.{key}" if prefix else key

                    # Determine field type
                    if isinstance(value, dict):
                        fields.append({
                            'name': field_path,
                            'type': 'object',
                            'example': str(value)[:100]
                        })
                        extract_fields(value, field_path)
                    elif isinstance(value, list):
                        fields.append({
                            'name': field_path,
                            'type': 'array',
                            'example': str(value)[:100]
                        })
                        if value and len(value) > 0:
                            extract_fields(value[0], field_path)
                    else:
                        # Determine primitive type
                        value_type = type(value).__name__
                        if isinstance(value, bool):
                            value_type = 'boolean'
                        elif isinstance(value, int):
                            value_type = 'integer'
                        elif isinstance(value, float):
                            value_type = 'number'
                        elif isinstance(value, str):
                            value_type = 'string'

                        fields.append({
                            'name': field_path,
                            'type': value_type,
                            'example': str(value)
                        })

            elif isinstance(obj, list) and obj:
                extract_fields(obj[0], prefix)

        extract_fields(body_json)
        return fields

    except json.JSONDecodeError:
        # If not valid JSON, try to extract field names from text
        import re
        field_pattern = r'"([a-zA-Z_][a-zA-Z0-9_]*)"\s*:'
        fields_found = re.findall(field_pattern, body_content)
        return [{'name': f, 'type': 'unknown', 'example': ''} for f in fields_found]
    except Exception:
        return []

def detect_tools_from_url(url):
    """Detect tools/services from URL patterns"""
    tools = set()
    url_lower = url.lower()

    service_patterns = {
        'NetSuite': ['netsuite.com', 'suitetalk.api.netsuite.com'],
        'Salesforce': ['salesforce.com', 'force.com', 'lightning.force.com'],
        'HubSpot': ['hubspot.com', 'hubapi.com', 'api.hubspot.com'],
        'Stripe': ['stripe.com', 'api.stripe.com'],
        'PayPal': ['paypal.com', 'api.paypal.com'],
        'Shopify': ['shopify.com', 'myshopify.com', 'admin.shopify.com'],
        'Slack': ['slack.com', 'api.slack.com'],
        'Microsoft Graph': ['graph.microsoft.com', 'outlook.office.com'],
        'Google APIs': ['googleapis.com', 'google.com/api'],
        'AWS': ['amazonaws.com', 'aws.amazon.com'],
        'Zendesk': ['zendesk.com', 'api.zendesk.com'],
        'Jira': ['atlassian.net', 'jira.com', 'api.atlassian.com'],
        'Trello': ['trello.com', 'api.trello.com'],
        'Asana': ['asana.com', 'api.asana.com'],
        'Mailchimp': ['mailchimp.com', 'api.mailchimp.com'],
        'SendGrid': ['sendgrid.com', 'api.sendgrid.com'],
        'Twilio': ['twilio.com', 'api.twilio.com'],
        'GitHub': ['github.com', 'api.github.com'],
        'GitLab': ['gitlab.com', 'api.gitlab.com'],
        'Bitbucket': ['bitbucket.org', 'api.bitbucket.org'],
        'WordPress': ['wordpress.com', 'wp.com'],
        'WooCommerce': ['woocommerce.com', 'wc-api'],
        'QuickBooks': ['quickbooks.com', 'qbo.intuit.com'],
        'Xero': ['xero.com', 'api.xero.com'],
        'Monday.com': ['monday.com', 'api.monday.com'],
        'Notion': ['notion.so', 'api.notion.com'],
        'Airtable': ['airtable.com', 'api.airtable.com']
    }

    for tool, patterns in service_patterns.items():
        if any(pattern in url_lower for pattern in patterns):
            tools.add(tool)

    return tools

def format_endpoints_summary(endpoints):
    """Format endpoints for AI analysis"""
    if not endpoints:
        return "No endpoints found"
    
    summary = []
    for ep in endpoints:
        folder_info = f" ({ep['folder']})" if ep.get('folder') else ""
        summary.append(f"- {ep['method']} {ep['path']} - {ep['name']}{folder_info}")
    
    return '\n'.join(summary)

def extract_folder_structure(collection_data):
    """Extract folder structure from collection"""
    folders = []
    
    def process_items(items, parent_path=""):
        for item in items:
            if 'item' in item:  # It's a folder
                folder_name = item.get('name', 'Unknown Folder')
                full_path = f"{parent_path}/{folder_name}" if parent_path else folder_name
                folders.append({
                    'name': folder_name,
                    'path': full_path,
                    'item_count': len(item.get('item', []))
                })
                process_items(item['item'], full_path)
    
    if 'item' in collection_data:
        process_items(collection_data['item'])
    
    return folders

def generate_workflow_suggestions(sources, destinations, tools):
    """Generate workflow suggestions based on detected sources and destinations"""
    workflows = []
    
    # Simple workflow suggestions
    if sources and destinations:
        for source in sources[:3]:  # Limit to first 3
            for dest in destinations[:3]:  # Limit to first 3
                workflow = {
                    'name': f"Sync {source['name']} to {dest['name']}",
                    'source': source['name'],
                    'destination': dest['name'],
                    'description': f"Transfer data from {source['name']} ({source['method']} {source['endpoint']}) to {dest['name']} ({dest['method']} {dest['endpoint']})",
                    'confidence': 'Medium',
                    'tools_involved': list(tools)
                }
                workflows.append(workflow)
    
    return workflows[:5]  # Return max 5 suggestions

def analyze_postman_collection_simple(collection_data):
    """Simplified Postman collection analysis without external dependencies"""
    try:
        # Extract basic collection info
        info = collection_data.get('info', {})
        collection_name = info.get('name', 'Unknown Collection')
        collection_desc = info.get('description', '')
        
        # Process all requests
        endpoints = []
        tools_detected = set()
        auth_methods = set()
        
        def process_items(items, folder_path=""):
            for item in items:
                if 'item' in item:  # Folder
                    folder_name = item.get('name', 'Unknown Folder')
                    new_path = f"{folder_path}/{folder_name}" if folder_path else folder_name
                    process_items(item['item'], new_path)
                else:  # Request
                    endpoint_info = extract_endpoint_info(item, folder_path)
                    endpoints.append(endpoint_info)
                    
                    # Detect tools from URL
                    url = endpoint_info.get('url', '').lower()
                    detected_tools = detect_tools_from_url(url)
                    tools_detected.update(detected_tools)
                    
                    # Extract auth info
                    auth = item.get('request', {}).get('auth', {})
                    if auth and 'type' in auth:
                        auth_methods.add(auth['type'])
        
        # Process the collection
        if 'item' in collection_data:
            process_items(collection_data['item'])
        
        # Categorize endpoints by tool/service
        tools_endpoints = {}
        suggested_sources = []
        suggested_destinations = []
        
        for ep in endpoints:
            # Detect which tool this endpoint belongs to
            url = ep.get('url', '').lower()
            endpoint_tools = detect_tools_from_url(url)
            
            # If no specific tool detected, use host as grouping
            if not endpoint_tools:
                host = ep.get('host', 'Unknown')
                if host:
                    endpoint_tools = {host}
                else:
                    endpoint_tools = {'Other APIs'}
            
            # Group endpoints by tool
            for tool in endpoint_tools:
                if tool not in tools_endpoints:
                    tools_endpoints[tool] = {
                        'name': tool,
                        'endpoints': [],
                        'get_endpoints': [],
                        'post_endpoints': [],
                        'other_endpoints': []
                    }
                
                # Add endpoint to tool group
                tools_endpoints[tool]['endpoints'].append(ep)
                
                # Categorize by method for easy source/destination suggestions
                if ep['method'].upper() == 'GET':
                    tools_endpoints[tool]['get_endpoints'].append(ep)
                elif ep['method'].upper() in ['POST', 'PUT', 'PATCH']:
                    tools_endpoints[tool]['post_endpoints'].append(ep)
                else:
                    tools_endpoints[tool]['other_endpoints'].append(ep)
        
        # Create suggestions grouped by tool
        for tool_name, tool_data in tools_endpoints.items():
            # Suggest GET endpoints as sources
            for ep in tool_data['get_endpoints']:
                if any(keyword in ep['name'].lower() for keyword in ['get', 'list', 'find', 'search', 'fetch']):
                    suggested_sources.append({
                        'name': ep['name'],
                        'endpoint': ep['path'],
                        'method': ep['method'],
                        'url': ep['url'],
                        'folder': ep.get('folder', ''),
                        'description': ep.get('description', ''),
                        'tool': tool_name,
                        'reason': 'GET endpoint that retrieves data'
                    })
            
            # Suggest POST/PUT/PATCH endpoints as destinations
            for ep in tool_data['post_endpoints']:
                if any(keyword in ep['name'].lower() for keyword in ['create', 'update', 'post', 'add', 'save']):
                    suggested_destinations.append({
                        'name': ep['name'],
                        'endpoint': ep['path'],
                        'method': ep['method'],
                        'url': ep['url'],
                        'folder': ep.get('folder', ''),
                        'description': ep.get('description', ''),
                        'tool': tool_name,
                        'reason': f'{ep["method"]} endpoint that accepts data'
                    })
        
        # Generate AI analysis using the existing Gemini integration
        ai_analysis = "Collection analyzed successfully. Use the AI documentation analysis for detailed insights."
        try:
            # Try to get AI analysis
            prompt = f"""Analyze this Postman API collection:

Collection: {collection_name}
Description: {collection_desc}
Endpoints: {len(endpoints)}
Tools Detected: {', '.join(tools_detected)}

Key Endpoints:
{format_endpoints_summary(endpoints[:10])}

Provide insights on:
1. API Purpose and use cases
2. Data integration opportunities  
3. Recommended workflows
4. Field mapping suggestions"""
            
            # Use existing Gemini API call
            import requests
            gemini_url = 'https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent'
            api_key = 'AIzaSyAm1BC94o7Cym57yhz1nTp45-3wVYIM21w'
            
            response = requests.post(
                f"{gemini_url}?key={api_key}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}]
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_analysis = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'AI analysis completed')
        except:
            pass  # Use default message if AI fails
        
        return {
            'success': True,
            'collection_info': {
                'name': collection_name,
                'description': collection_desc,
                'endpoint_count': len(endpoints),
                'folder_structure': extract_folder_structure(collection_data)
            },
            'tools_detected': list(tools_detected),
            'tools_endpoints': tools_endpoints,  # Add grouped endpoints by tool
            'auth_methods': list(auth_methods),
            'endpoints': endpoints,
            'suggested_sources': suggested_sources,
            'suggested_destinations': suggested_destinations,
            'ai_analysis': ai_analysis,
            'workflows': generate_workflow_suggestions(suggested_sources, suggested_destinations, tools_detected)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error analyzing Postman collection: {str(e)}'
        }

# Main Routes
@app.route('/')
def index():
    return render_template('index_simple.html')

@app.route('/sources')
def sources():
    return render_template('sources_simple.html')

@app.route('/destinations')
def destinations():
    return render_template('destinations_simple.html')

@app.route('/mappings')
def mappings():
    return render_template('mappings_simple.html')

@app.route('/mappings/create')
def create_mapping():
    return render_template('create_mapping_simple.html')

@app.route('/jobs')
def jobs():
    return render_template('jobs.html')

# API Routes
@app.route('/api/sources', methods=['GET'])
def get_sources():
    storage = load_storage()
    # Filter only active sources
    active_sources = [s for s in storage.get('sources', []) if s.get('is_active', True)]
    return jsonify({'success': True, 'data': active_sources})

@app.route('/api/sources/<source_id>', methods=['GET'])
def get_source(source_id):
    """Get a specific data source"""
    try:
        storage = load_storage()

        # Find the source (handle both int and string IDs)
        for source in storage['sources']:
            if str(source['id']) == str(source_id):
                return jsonify({
                    'success': True,
                    'data': source
                })

        return jsonify({
            'success': False,
            'error': 'Source not found'
        }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/sources', methods=['POST'])
def create_source():
    try:
        data = request.get_json()
        storage = load_storage()

        source = {
            'id': len(storage['sources']) + 1,
            'name': data['name'],
            'type': data['type'],
            'connection_config': data['connection_config'],
            'schema_info': data.get('schema_info', {}),
            'created_at': '2024-01-01T00:00:00',
            'is_active': True
        }

        storage['sources'].append(source)
        save_storage(storage)

        return jsonify({'success': True, 'data': source}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sources/<source_id>', methods=['PUT'])
def update_source(source_id):
    """Update a data source"""
    try:
        storage = load_storage()
        data = request.get_json()

        # Find and update the source
        for source in storage['sources']:
            if str(source['id']) == str(source_id):
                # Update fields if provided
                if 'name' in data:
                    source['name'] = data['name']
                if 'type' in data:
                    source['type'] = data['type']
                if 'connection_config' in data:
                    source['connection_config'] = data['connection_config']
                if 'schema_info' in data:
                    source['schema_info'] = data['schema_info']
                if 'is_active' in data:
                    source['is_active'] = data['is_active']

                save_storage(storage)

                return jsonify({
                    'success': True,
                    'data': source
                })

        return jsonify({
            'success': False,
            'error': 'Source not found'
        }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/sources/<source_id>', methods=['DELETE'])
def delete_source(source_id):
    """Delete a data source (soft delete)"""
    try:
        storage = load_storage()

        # Find the source (handle both int and string IDs)
        source_found = False
        for source in storage['sources']:
            # Compare IDs as strings to handle both numeric and string IDs
            if str(source['id']) == str(source_id):
                source['is_active'] = False
                source_found = True
                break

        if not source_found:
            return jsonify({
                'success': False,
                'error': 'Source not found'
            }), 404

        save_storage(storage)

        return jsonify({
            'success': True,
            'message': 'Source deleted successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/destinations', methods=['GET'])
def get_destinations():
    storage = load_storage()
    # Filter only active destinations
    active_destinations = [d for d in storage.get('destinations', []) if d.get('is_active', True)]
    return jsonify({'success': True, 'data': active_destinations})

@app.route('/api/destinations/<dest_id>', methods=['GET'])
def get_destination(dest_id):
    """Get a specific data destination"""
    try:
        storage = load_storage()

        # Find the destination (handle both int and string IDs)
        for destination in storage['destinations']:
            if str(destination['id']) == str(dest_id):
                return jsonify({
                    'success': True,
                    'data': destination
                })

        return jsonify({
            'success': False,
            'error': 'Destination not found'
        }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/destinations', methods=['POST'])
def create_destination():
    try:
        data = request.get_json()
        storage = load_storage()

        destination = {
            'id': len(storage['destinations']) + 1,
            'name': data['name'],
            'type': data['type'],
            'connection_config': data['connection_config'],
            'schema_info': data.get('schema_info', {}),
            'created_at': '2024-01-01T00:00:00',
            'is_active': True
        }

        storage['destinations'].append(destination)
        save_storage(storage)

        return jsonify({'success': True, 'data': destination}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/destinations/<dest_id>', methods=['PUT'])
def update_destination(dest_id):
    """Update a data destination"""
    try:
        storage = load_storage()
        data = request.get_json()

        # Find and update the destination
        for destination in storage['destinations']:
            if str(destination['id']) == str(dest_id):
                # Update fields if provided
                if 'name' in data:
                    destination['name'] = data['name']
                if 'type' in data:
                    destination['type'] = data['type']
                if 'connection_config' in data:
                    destination['connection_config'] = data['connection_config']
                if 'schema_info' in data:
                    destination['schema_info'] = data['schema_info']
                if 'is_active' in data:
                    destination['is_active'] = data['is_active']

                save_storage(storage)

                return jsonify({
                    'success': True,
                    'data': destination
                })

        return jsonify({
            'success': False,
            'error': 'Destination not found'
        }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/destinations/<dest_id>', methods=['DELETE'])
def delete_destination(dest_id):
    """Delete a data destination (soft delete)"""
    try:
        storage = load_storage()

        # Find the destination (handle both int and string IDs)
        dest_found = False
        for destination in storage['destinations']:
            # Compare IDs as strings to handle both numeric and string IDs
            if str(destination['id']) == str(dest_id):
                destination['is_active'] = False
                dest_found = True
                break

        if not dest_found:
            return jsonify({
                'success': False,
                'error': 'Destination not found'
            }), 404

        save_storage(storage)

        return jsonify({
            'success': True,
            'message': 'Destination deleted successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tool-variables/<tool_name>', methods=['GET'])
def get_tool_variables(tool_name):
    """Get variables for a specific tool"""
    storage = load_storage()
    tool_vars = storage.get('tool_variables', {}).get(tool_name, {})
    return jsonify({'success': True, 'data': tool_vars})

@app.route('/api/tool-variables/<tool_name>', methods=['PUT'])
def update_tool_variables(tool_name):
    """Update variables for a specific tool"""
    try:
        data = request.get_json()
        storage = load_storage()

        if 'tool_variables' not in storage:
            storage['tool_variables'] = {}

        storage['tool_variables'][tool_name] = data.get('variables', {})
        save_storage(storage)

        return jsonify({
            'success': True,
            'message': f'Variables for {tool_name} updated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tool-variables/<tool_name>/assign', methods=['POST'])
def assign_variable_from_response(tool_name):
    """Assign a variable from API response"""
    try:
        data = request.get_json()
        storage = load_storage()

        if 'tool_variables' not in storage:
            storage['tool_variables'] = {}

        if tool_name not in storage['tool_variables']:
            storage['tool_variables'][tool_name] = {}

        variable_name = data.get('variable_name')
        value = data.get('value')

        storage['tool_variables'][tool_name][variable_name] = value
        save_storage(storage)

        return jsonify({
            'success': True,
            'message': f'Variable {variable_name} set to {value} for {tool_name}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/environment', methods=['GET'])
def get_environment():
    """Get global environment variables (deprecated)"""
    storage = load_storage()
    return jsonify({'success': True, 'data': storage.get('environment_variables', {})})

@app.route('/api/environment', methods=['PUT'])
def update_environment():
    """Update global environment variables (deprecated)"""
    try:
        data = request.get_json()
        storage = load_storage()

        storage['environment_variables'] = data.get('variables', {})
        save_storage(storage)

        return jsonify({
            'success': True,
            'message': 'Environment variables updated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/mappings', methods=['GET'])
def get_mappings():
    storage = load_storage()
    return jsonify({'success': True, 'data': storage.get('mappings', [])})

@app.route('/api/mappings', methods=['POST'])
def create_mapping_api():
    try:
        data = request.get_json()
        storage = load_storage()

        # Accept both field_mappings (new format) and mapping_config (old format)
        field_mappings = data.get('field_mappings', [])
        mapping_config = data.get('mapping_config', {})

        # If field_mappings provided, convert to mapping_config format
        if field_mappings and not mapping_config:
            mapping_config = {}
            for fm in field_mappings:
                mapping_config[fm['source_field']] = {
                    'destination': fm['destination_field'],
                    'transformation': fm.get('transformation', 'direct')
                }

        mapping = {
            'id': len(storage['mappings']) + 1,
            'name': data['name'],
            'description': data.get('description', ''),
            'source_id': data['source_id'],
            'destination_id': data['destination_id'],
            'field_mappings': field_mappings,  # Store new format
            'mapping_config': mapping_config,  # Store old format for compatibility
            'transformation_rules': data.get('transformation_rules', {}),
            'created_at': '2024-01-01T00:00:00',
            'is_active': True
        }

        storage['mappings'].append(mapping)
        save_storage(storage)

        return jsonify({'success': True, 'data': mapping}), 201
    except Exception as e:
        print(f"Error creating mapping: {e}")  # Debug log
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sources/<int:source_id>/schema')
def get_source_schema(source_id):
    # Sample schema
    schema = {
        'fields': [
            {'name': 'id', 'type': 'integer', 'required': True},
            {'name': 'name', 'type': 'string', 'required': True},
            {'name': 'email', 'type': 'string', 'required': False},
            {'name': 'created_at', 'type': 'datetime', 'required': False},
            {'name': 'status', 'type': 'string', 'required': False}
        ]
    }
    return jsonify({'success': True, 'data': schema})

@app.route('/api/destinations/<int:dest_id>/schema')
def get_destination_schema(dest_id):
    # Sample schema
    schema = {
        'fields': [
            {'name': 'user_id', 'type': 'integer', 'required': True},
            {'name': 'full_name', 'type': 'string', 'required': True},
            {'name': 'email_address', 'type': 'string', 'required': True},
            {'name': 'registration_date', 'type': 'date', 'required': False},
            {'name': 'account_status', 'type': 'string', 'required': True}
        ]
    }
    return jsonify({'success': True, 'data': schema})

@app.route('/api/sources/<int:source_id>/test', methods=['POST'])
def test_source(source_id):
    return jsonify({
        'success': True, 
        'data': {'status': 'connected', 'message': 'Connection successful'}
    })

@app.route('/api/destinations/<int:dest_id>/test', methods=['POST'])
def test_destination(dest_id):
    return jsonify({
        'success': True, 
        'data': {'status': 'connected', 'message': 'Connection successful'}
    })

# Gemini AI endpoints
@app.route('/api/ai/suggest-mappings', methods=['POST'])
def suggest_mappings():
    try:
        import requests
        
        data = request.get_json()
        source_schema = data.get('source_schema', [])
        dest_schema = data.get('destination_schema', [])
        
        # Call Gemini AI
        gemini_url = 'https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent'
        api_key = 'AIzaSyAm1BC94o7Cym57yhz1nTp45-3wVYIM21w'
        
        prompt = f"""
        Analyze these schemas and suggest field mappings:
        
        Source: {json.dumps(source_schema)}
        Destination: {json.dumps(dest_schema)}
        
        Return JSON with mappings array containing objects with source_field, destination_field, and confidence.
        """
        
        response = requests.post(
            f"{gemini_url}?key={api_key}",
            json={
                "contents": [{"parts": [{"text": prompt}]}]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
            
            return jsonify({
                'success': True,
                'suggestions': {'raw_content': content}
            })
        else:
            return jsonify({
                'success': False,
                'error': 'AI service unavailable'
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ai/analyze-postman', methods=['POST'])
def analyze_postman():
    """Enhanced Postman collection analysis"""
    try:
        data = request.get_json()
        collection_content = data.get('content', '')
        
        if not collection_content:
            return jsonify({'success': False, 'error': 'No content provided'})
        
        # Try to parse as JSON
        try:
            collection_data = json.loads(collection_content)
            if 'info' not in collection_data or 'item' not in collection_data:
                return jsonify({'success': False, 'error': 'Invalid Postman collection format'})
        except json.JSONDecodeError:
            return jsonify({'success': False, 'error': 'Invalid JSON format'})
        
        # Simple analysis without external dependencies
        result = analyze_postman_collection_simple(collection_data)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Analysis failed: {str(e)}'})

@app.route('/api/ai/create-from-tools', methods=['POST'])
def create_from_tools():
    """Create sources and destinations from selected tool groups"""
    try:
        data = request.get_json()
        selected_tools = data.get('selected_tools', {})
        
        if not selected_tools:
            return jsonify({'success': False, 'error': 'No tools selected'})
        
        storage = load_storage()
        created_sources = []
        created_destinations = []
        
        for tool_name, tool_config in selected_tools.items():
            if not tool_config.get('selected', False):
                continue
                
            endpoints = tool_config.get('endpoints', [])
            as_source = tool_config.get('as_source', False)
            as_destination = tool_config.get('as_destination', False)
            
            if as_source:
                # Create source from this tool
                get_endpoints = [ep for ep in endpoints if ep['method'].upper() == 'GET']

                # Extract variables from all endpoints with metadata
                variables = extract_variables_from_endpoints(get_endpoints)
                variable_config = {}
                for var_name, var_info in variables.items():
                    variable_config[var_name] = {
                        'value': '',
                        'type': var_info.get('type', 'unknown'),
                        'required': var_info.get('required', False),
                        'description': var_info.get('description', f'Variable from Postman collection')
                    }

                # Extract base URL (remove variables for display)
                base_url = endpoints[0]['url'].split(endpoints[0]['path'])[0] if endpoints else ''

                # Extract authentication config from first endpoint
                auth_config = {}
                if get_endpoints:
                    first_endpoint = get_endpoints[0]
                    auth = first_endpoint.get('auth', {})
                    if auth:
                        auth_config = {
                            'type': auth.get('type', 'none'),
                            'config': auth
                        }

                # Check if a source already exists for this tool
                existing_source = None
                for src in storage['sources']:
                    src_config = src.get('connection_config', {})
                    if src_config.get('service_type') == tool_name:
                        existing_source = src
                        break

                if existing_source:
                    # Update existing source with new endpoints
                    existing_config = existing_source['connection_config']
                    existing_endpoints = existing_config.get('endpoints', [])

                    # Merge endpoints (avoid duplicates)
                    endpoint_paths = {ep['path'] for ep in existing_endpoints}
                    for ep in get_endpoints:
                        if ep['path'] not in endpoint_paths:
                            existing_endpoints.append(ep)

                    existing_config['endpoints'] = existing_endpoints
                    existing_config['endpoint_count'] = len(existing_endpoints)

                    # Merge variables
                    existing_vars = existing_config.get('variables', {})
                    existing_vars.update(variable_config)
                    existing_config['variables'] = existing_vars

                    created_sources.append(existing_source)
                else:
                    # Create new source for this tool
                    source_data = {
                        'id': len(storage['sources']) + 1,
                        'name': tool_name,  # Just the tool name like "NetSuite"
                        'type': 'api',
                        'description': f"{tool_name} API endpoints for data retrieval",
                        'connection_config': {
                            'tool': tool_name,
                            'service_type': tool_name,
                            'endpoints': get_endpoints,
                            'base_url': base_url,
                            'variables': variable_config,
                            'auth': auth_config,
                            'postman_generated': True,
                            'endpoint_count': len(get_endpoints)
                        },
                        'schema_info': {},
                        'created_at': '2024-01-01T00:00:00',
                        'is_active': True
                    }
                    storage['sources'].append(source_data)
                    created_sources.append(source_data)
            
            if as_destination:
                # Create destination from this tool
                write_endpoints = [ep for ep in endpoints if ep['method'].upper() in ['POST', 'PUT', 'PATCH']]

                # Extract variables from all endpoints with metadata
                variables = extract_variables_from_endpoints(write_endpoints)
                variable_config = {}
                for var_name, var_info in variables.items():
                    variable_config[var_name] = {
                        'value': '',
                        'type': var_info.get('type', 'unknown'),
                        'required': var_info.get('required', False),
                        'description': var_info.get('description', f'Variable from Postman collection')
                    }

                # Extract base URL (remove variables for display)
                base_url = endpoints[0]['url'].split(endpoints[0]['path'])[0] if endpoints else ''

                # Extract authentication config from first endpoint
                auth_config = {}
                if write_endpoints:
                    first_endpoint = write_endpoints[0]
                    auth = first_endpoint.get('auth', {})
                    if auth:
                        auth_config = {
                            'type': auth.get('type', 'none'),
                            'config': auth
                        }

                # Extract schema from request bodies for field mapping
                schema_fields = []
                for ep in write_endpoints:
                    body = ep.get('body', {})
                    if body and body.get('content'):
                        fields = extract_schema_from_body(body.get('content'))
                        if fields:
                            schema_fields.extend(fields)

                # Deduplicate fields by name
                unique_fields = {}
                for field in schema_fields:
                    field_name = field['name']
                    if field_name not in unique_fields:
                        unique_fields[field_name] = field

                # Check if a destination already exists for this tool
                existing_dest = None
                for dest in storage['destinations']:
                    dest_config = dest.get('connection_config', {})
                    if dest_config.get('service_type') == tool_name:
                        existing_dest = dest
                        break

                if existing_dest:
                    # Update existing destination with new endpoints
                    existing_config = existing_dest['connection_config']
                    existing_endpoints = existing_config.get('endpoints', [])

                    # Merge endpoints (avoid duplicates)
                    endpoint_paths = {ep['path'] for ep in existing_endpoints}
                    for ep in write_endpoints:
                        if ep['path'] not in endpoint_paths:
                            existing_endpoints.append(ep)

                    existing_config['endpoints'] = existing_endpoints
                    existing_config['endpoint_count'] = len(existing_endpoints)

                    # Merge variables
                    existing_vars = existing_config.get('variables', {})
                    existing_vars.update(variable_config)
                    existing_config['variables'] = existing_vars

                    # Update schema fields
                    existing_fields = existing_dest.get('schema_info', {}).get('fields', [])
                    all_fields = {f['name']: f for f in existing_fields}
                    all_fields.update(unique_fields)
                    existing_dest['schema_info'] = {'fields': list(all_fields.values())}

                    created_destinations.append(existing_dest)
                else:
                    # Create new destination for this tool
                    dest_data = {
                        'id': len(storage['destinations']) + 1,
                        'name': tool_name,  # Just the tool name like "NetSuite"
                        'type': 'api',
                        'description': f"{tool_name} API endpoints for data submission",
                        'connection_config': {
                            'tool': tool_name,
                            'service_type': tool_name,
                            'endpoints': write_endpoints,
                            'base_url': base_url,
                            'variables': variable_config,
                            'auth': auth_config,
                            'postman_generated': True,
                            'endpoint_count': len(write_endpoints)
                        },
                        'schema_info': {
                            'fields': list(unique_fields.values())
                        },
                        'created_at': '2024-01-01T00:00:00',
                        'is_active': True
                    }
                    storage['destinations'].append(dest_data)
                    created_destinations.append(dest_data)
        
        # Save the updated storage
        save_storage(storage)
        
        return jsonify({
            'success': True,
            'created_sources': len(created_sources),
            'created_destinations': len(created_destinations),
            'sources': created_sources,
            'destinations': created_destinations,
            'message': f"Successfully created {len(created_sources)} sources and {len(created_destinations)} destinations"
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to create from tools: {str(e)}'})

@app.route('/api/ai/analyze-docs', methods=['POST'])
def analyze_docs():
    try:
        import requests
        
        data = request.get_json()
        content = data.get('content', '')
        
        print(f"📄 Analyzing document, content length: {len(content)}")
        
        if not content.strip():
            return jsonify({'success': False, 'error': 'No content provided'})
        
        # Check if it's a Postman collection
        try:
            json_data = json.loads(content)
            if 'info' in json_data and 'item' in json_data:
                print("🚀 Detected Postman collection, redirecting to enhanced analysis")
                # Call the Postman analysis function directly and return the result
                result = analyze_postman_collection_simple(json_data)
                return jsonify(result)
        except json.JSONDecodeError:
            print("📝 Not JSON, proceeding with regular doc analysis")
            pass  # Not JSON, continue with regular doc analysis
        
        # Call Gemini AI
        print("🤖 Calling Gemini AI for analysis...")
        gemini_url = 'https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent'
        api_key = 'AIzaSyAm1BC94o7Cym57yhz1nTp45-3wVYIM21w'
        
        prompt = f"""
Analyze this API documentation and provide structured insights:

Documentation Content:
{content[:3000]}  # Limit to avoid token limits

Please provide:
1. **API Overview**: What does this API do?
2. **Authentication**: Authentication methods used
3. **Key Endpoints**: List main endpoints and their purposes  
4. **Data Models**: Describe main data structures
5. **Integration Opportunities**: How this could integrate with other systems
6. **Field Mapping Hints**: Common field patterns for data integration

Provide a clear, structured analysis that would help with data integration planning.
"""
        
        response = requests.post(
            f"{gemini_url}?key={api_key}",
            json={
                "contents": [{"parts": [{"text": prompt}]}]
            },
            timeout=30
        )
        
        print(f"🔗 Gemini API response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            analysis = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
            
            print(f"✅ Analysis successful, response length: {len(analysis)}")
            
            return jsonify({
                'success': True,
                'raw_content': analysis,
                'analysis_type': 'general_documentation'
            })
        else:
            print(f"❌ Gemini API error: {response.status_code} - {response.text}")
            return jsonify({
                'success': False,
                'error': f'AI service returned error: {response.status_code}'
            })
            
    except requests.exceptions.Timeout:
        print("⏰ Request timeout")
        return jsonify({'success': False, 'error': 'Request timeout - AI service took too long to respond'})
    except requests.exceptions.RequestException as e:
        print(f"🌐 Network error: {str(e)}")
        return jsonify({'success': False, 'error': f'Network error: {str(e)}'})
    except Exception as e:
        print(f"💥 Unexpected error: {str(e)}")
        return jsonify({'success': False, 'error': f'Analysis failed: {str(e)}'})

if __name__ == '__main__':
    print("🚀 Starting Data Integration Platform...")
    print("📱 Features:")
    print("   • Source & Destination Management")
    print("   • Field Mapping with AI")
    print("   • Gemini AI Integration")
    print("   • API Documentation Analysis")
    print("🌐 Server: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)