# Data Integration Platform

A comprehensive data integration application that enables seamless data transfer between source and destination systems with AI-powered field mapping, transformations, and a user-friendly web interface.

## ✨ Features

- **🔌 Source & Destination API Integration**: Connect to various data sources and destinations
- **🗺️ AI-Powered Field Mapping**: Intelligent field mapping using Google Gemini AI
- **⚡ Data Transformations**: Apply custom transformations during data transfer
- **🌐 Web Interface**: User-friendly interface for configuration and monitoring
- **📄 API Documentation Analysis**: Upload and analyze API docs with AI
- **📮 Postman Collection Import**: Import Postman collections for automatic endpoint discovery
- **🎯 Real-time Processing**: Process data in real-time or batch mode
- **💾 Configuration Management**: Save and reuse mapping configurations

## 🚀 Quick Start

The application is ready to run with the standalone version:

```bash
python standalone_app.py
```

The server will start at: **http://localhost:5000**

## 🎯 Key Integrations

### Gemini AI Integration
- **API Key**: `AIzaSyAm1BC94o7Cym57yhz1nTp45-3wVYIM21w`
- **Smart field mapping suggestions**
- **API documentation analysis**
- **Data validation and transformation recommendations**

### Your API Documents & Postman Collections
- Upload API documentation for automatic source/destination configuration
- Import Postman collections to extract endpoints and schemas
- AI-powered analysis of your existing API workflows

## 📁 Project Structure

```
├── standalone_app.py          # Main application (ready to run)
├── app/                       # Modular application structure
│   ├── templates/            # HTML templates
│   ├── static/               # CSS, JS, images
│   ├── api/                  # API endpoints
│   └── services/             # Business logic & AI services
├── config.env               # Environment configuration
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🌐 API Endpoints

### Core Endpoints
- `GET /` - Main dashboard
- `GET /sources` - Source management page
- `GET /destinations` - Destination management page
- `GET /mappings/create` - Create field mappings

### API Endpoints
- `GET /api/sources` - List data sources
- `POST /api/sources` - Create new source
- `GET /api/destinations` - List destinations
- `POST /api/destinations` - Create new destination
- `POST /api/mappings` - Create field mapping
- `GET /api/sources/{id}/schema` - Get source schema
- `POST /api/sources/{id}/test` - Test source connection

### AI-Powered Endpoints
- `POST /api/ai/suggest-mappings` - Get AI mapping suggestions
- `POST /api/ai/analyze-docs` - Analyze API documentation
- `POST /api/ai/validate-mapping` - Validate mapping configuration

## 🛠️ Usage Examples

### 1. Create a Data Source
```javascript
POST /api/sources
{
  "name": "User API",
  "type": "api",
  "connection_config": {
    "url": "https://api.example.com/users",
    "method": "GET",
    "headers": {"Authorization": "Bearer YOUR_TOKEN"}
  }
}
```

### 2. Create a Destination
```javascript
POST /api/destinations
{
  "name": "CRM System",
  "type": "api", 
  "connection_config": {
    "url": "https://crm.example.com/contacts",
    "method": "POST",
    "headers": {"Content-Type": "application/json"}
  }
}
```

### 3. Get AI Mapping Suggestions
```javascript
POST /api/ai/suggest-mappings
{
  "source_schema": [
    {"name": "id", "type": "integer"},
    {"name": "name", "type": "string"},
    {"name": "email", "type": "string"}
  ],
  "destination_schema": [
    {"name": "contact_id", "type": "integer"},
    {"name": "full_name", "type": "string"},
    {"name": "email_address", "type": "string"}
  ]
}
```

## 🎨 Web Interface Features

- **Dashboard**: Overview of sources, destinations, and active jobs
- **Source Management**: Add, test, and configure data sources
- **Destination Management**: Configure target systems
- **Smart Mapping Builder**: Drag-and-drop field mapping with AI suggestions
- **Transformation Editor**: Configure data transformations
- **Job Monitoring**: Track data transfer progress

## 🤖 AI-Powered Features

### Document Analysis
- Upload API documentation (JSON, YAML, Markdown)
- AI extracts endpoints, schemas, and authentication details
- Automatic source/destination configuration suggestions

### Postman Integration
- Import Postman collections
- AI analyzes requests/responses
- Suggests data sources and destinations

### Smart Mapping
- Analyzes field names and types
- Suggests optimal mappings
- Recommends transformations
- Validates data compatibility

## 🔧 Configuration

Create a `.env` file with your settings:
```bash
FLASK_DEBUG=True
SECRET_KEY=your-secret-key
GEMINI_API_KEY=AIzaSyAm1BC94o7Cym57yhz1nTp45-3wVYIM21w
```

## 🚀 Running the Application

### Standalone Version (Recommended)
```bash
python standalone_app.py
```

### Full Version (with database)
```bash
pip install -r requirements.txt
python run.py
```

## 📊 Data Flow

1. **Configure Sources**: Set up APIs, databases, or files as data sources
2. **Configure Destinations**: Set up target systems for data delivery  
3. **Create Mappings**: Use AI to map fields between source and destination
4. **Add Transformations**: Configure data transformations as needed
5. **Test & Validate**: Preview mappings and validate with AI
6. **Execute Jobs**: Run data integration jobs

## 🔐 Security

- API key management for secure integrations
- Authentication support for sources and destinations
- Data validation and sanitization
- Error handling and logging

## 📈 Monitoring

- Real-time job status tracking
- Data transfer metrics
- Error logging and reporting
- Performance monitoring

## 🤝 Contributing

This is a complete data integration platform ready for your specific API integrations. Customize the source and destination configurations to match your requirements.

## 📝 License

MIT License - Feel free to modify and extend for your needs.