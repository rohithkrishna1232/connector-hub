from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print("🚀 Starting Data Integration Platform...")
    print("📱 Features included:")
    print("   • Source & Destination API Integration")
    print("   • Field Mapping with AI Suggestions")
    print("   • Data Transformations")
    print("   • Gemini AI Integration")
    print("   • API Documentation Analysis")
    print("   • Postman Collection Import")
    print(f"🌐 Server running at: http://localhost:{port}")
    print("📚 API Endpoints:")
    print("   • GET  /api/sources - Manage data sources")
    print("   • GET  /api/destinations - Manage destinations") 
    print("   • GET  /api/mappings - Field mappings")
    print("   • POST /api/ai/analyze-docs - AI doc analysis")
    print("   • POST /api/ai/suggest-mappings - AI mapping suggestions")
    
    app.run(host='0.0.0.0', port=port, debug=debug)