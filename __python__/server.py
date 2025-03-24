from flask import Flask, request, jsonify
from flask_cors import CORS
from ytm4a_api import YTM4AProcessor
import logging
from dotenv import load_dotenv
import os

# Load environment variables from the __python__ directory
python_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(python_dir, '.env'))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize processor with API key
processor = YTM4AProcessor()
if not processor.assemblyai_api_key:
    logging.warning("⚠️ AssemblyAI API key not found. Set ASSEMBLYAI_API_KEY in .env file")

@app.route('/process', methods=['POST'])
def process_video():
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400

        youtube_url = data.get('url')
        category = data.get('category')
        ticker_symbol = data.get('ticker_symbol')
        custom_title = data.get('custom_title')

        if not youtube_url or not category:
            return jsonify({
                "status": "error",
                "message": "Missing required fields: url and category"
            }), 400

        if category == 'Economics' and not ticker_symbol:
            return jsonify({
                "status": "error",
                "message": "Ticker symbol is required for Economics category"
            }), 400

        if not processor.assemblyai_api_key:
            return jsonify({
                "status": "error",
                "message": "AssemblyAI API key not configured"
            }), 500

        # Process the video
        result = processor.process_url(youtube_url, category, ticker_symbol, custom_title)
        
        if result["status"] == "error":
            return jsonify(result), 500
        elif result["status"] == "cancelled":
            return jsonify(result), 200
            
        return jsonify(result)

    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint that also verifies API key configuration"""
    health_status = {
        "status": "healthy",
        "api_keys": {
            "assemblyai": bool(processor.assemblyai_api_key)
        }
    }
    return jsonify(health_status), 200

if __name__ == '__main__':
    # Check if API keys are configured
    if not processor.assemblyai_api_key:
        print("\n⚠️  WARNING: AssemblyAI API key not found")
        print("Set ASSEMBLYAI_API_KEY in your .env file\n")
    
    print("\n🚀 Starting YTM4A server...")
    print("📝 API Documentation:")
    print("  POST /process")
    print("    - url: YouTube video URL")
    print("    - category: 'Finance', 'AI', or 'Geopolitics'")
    print("    - ticker_symbol: Required for Finance category")
    print("\n  GET /health")
    print("    - Server health check")
    print("\n🔗 Server running at http://localhost:5555\n")
    
    app.run(host='0.0.0.0', port=5555) 