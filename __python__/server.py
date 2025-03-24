from flask import Flask, request, jsonify, send_from_directory, url_for
from flask_cors import CORS
from ytm4a_api import YTM4AProcessor
import logging
from dotenv import load_dotenv
import os
from pathlib import Path

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
# No need to warn about API key since we're only downloading and compressing

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

        # Process the video
        result = processor.process_url(youtube_url, category, ticker_symbol, custom_title)
        
        if result["status"] == "error":
            return jsonify(result), 500
        elif result["status"] == "cancelled":
            return jsonify(result), 200
            
        # Add download URLs to the result
        if "filename" in result:
            base_url = request.host_url.rstrip('/')
            filename = result["filename"]
            category_path = result["category"]
            
            # Add audio file URL
            audio_file = f"{filename}.m4a"
            result["audio_url"] = f"{base_url}/download/{category_path}/{audio_file}"
            
            # Add metadata file URL
            metadata_file = f"{filename}.json"
            result["metadata_url"] = f"{base_url}/download/{category_path}/{metadata_file}"
        
        return jsonify(result)

    except Exception as e:
        logging.error(f"Error processing request: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/download/<category>/<filename>', methods=['GET'])
def download_file(category, filename):
    """Download processed files"""
    try:
        base_dir = Path(python_dir).parent
        category_dir = base_dir / category
        return send_from_directory(category_dir, filename, as_attachment=True)
    except Exception as e:
        logging.error(f"Download error: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"File not found: {filename}"
        }), 404

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "download_only_mode": True
    }
    return jsonify(health_status), 200

if __name__ == '__main__':
    # Start server
    print("\n🚀 Starting YTM4A server...")
    print("📝 API Documentation:")
    print("  POST /process")
    print("    - url: YouTube video URL")
    print("    - category: 'Finance', 'AI', or 'Geopolitics'")
    print("    - ticker_symbol: Required for Finance category")
    print("\n  GET /download/<category>/<filename>")
    print("    - Download processed files")
    print("\n  GET /health")
    print("    - Server health check")
    print("\n🔗 Server running at http://localhost:5555\n")
    
    app.run(host='0.0.0.0', port=5555) 