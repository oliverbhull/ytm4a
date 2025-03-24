from flask import Flask, request, jsonify, send_from_directory, url_for, Response
from flask_cors import CORS
from ytm4a_api import YTM4AProcessor
import logging
from dotenv import load_dotenv
import os
from pathlib import Path
import requests
import subprocess
import tempfile
import json
from datetime import datetime
import urllib.parse

# Load environment variables from the __python__ directory
python_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(python_dir, '.env'))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Dictionary to keep track of temporary files
temp_file_registry = {}

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
        download_only = data.get('download_only', False)
        mac_download = data.get('mac_download', False)

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

        # For Mac downloads, don't save files on the Pi
        save_to_pi = not mac_download
        
        # Process the video
        result = processor.process_url(youtube_url, category, ticker_symbol, custom_title, save_to_pi=save_to_pi)
        
        if result["status"] == "error":
            return jsonify(result), 500
        elif result["status"] == "cancelled":
            return jsonify(result), 200
            
        # Add download URLs to the result
        if "filename" in result:
            base_url = request.host_url.rstrip('/')
            filename = result["filename"]
            category_path = result["category"]
            
            if save_to_pi:
                # Regular file paths on Pi
                audio_file = f"{filename}.m4a"
                result["audio_url"] = f"{base_url}/download/{category_path}/{audio_file}"
                
                metadata_file = f"{filename}.json"
                result["metadata_url"] = f"{base_url}/download/{category_path}/{metadata_file}"
            else:
                # Temporary file paths for Mac download
                temp_files = result.get("temp_files", {})
                audio_path = temp_files.get("audio_path", "")
                metadata_path = temp_files.get("metadata_path", "")
                
                if audio_path and os.path.exists(audio_path):
                    # Generate a unique key for the temporary file
                    audio_key = f"audio_{datetime.now().timestamp()}"
                    # Store the full path in the registry
                    temp_file_registry[audio_key] = audio_path
                    # Create a URL with the key
                    audio_filename = os.path.basename(audio_path)
                    result["audio_url"] = f"{base_url}/download/temp/{audio_filename}?key={audio_key}"
                    
                if metadata_path and os.path.exists(metadata_path):
                    # Generate a unique key for the temporary file
                    metadata_key = f"metadata_{datetime.now().timestamp()}"
                    # Store the full path in the registry
                    temp_file_registry[metadata_key] = metadata_path
                    # Create a URL with the key
                    metadata_filename = os.path.basename(metadata_path)
                    result["metadata_url"] = f"{base_url}/download/temp/{metadata_filename}?key={metadata_key}"
                
                logging.info(f"Temporary files registered: {temp_file_registry}")
        
        return jsonify(result)

    except Exception as e:
        logging.error(f"Error processing request: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/download/temp/<path:filename>', methods=['GET'])
def download_temp_file(filename):
    """Download temporary files using the registry key"""
    try:
        # Get the key from the query parameters
        key = request.args.get('key', '')
        
        logging.info(f"Download request for: {filename} with key: {key}")
        logging.info(f"Current temp registry: {temp_file_registry}")
        
        if not key or key not in temp_file_registry:
            return jsonify({"status": "error", "message": "Invalid or expired download key"}), 404
        
        # Get the full path from the registry
        full_path = temp_file_registry[key]
        
        if not os.path.exists(full_path):
            logging.error(f"File not found at path: {full_path}")
            return jsonify({"status": "error", "message": "Temporary file not found"}), 404
        
        # Ensure the requested filename matches the stored filename
        if os.path.basename(full_path) != filename:
            logging.error(f"Filename mismatch: requested {filename}, stored {os.path.basename(full_path)}")
            return jsonify({"status": "error", "message": "Filename mismatch"}), 404
        
        dir_path = os.path.dirname(full_path)
        
        logging.info(f"Serving file from: {dir_path}, filename: {filename}")
        return send_from_directory(dir_path, filename, as_attachment=True)
    
    except Exception as e:
        logging.error(f"Download temp error: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Error downloading file: {str(e)}"
        }), 500

@app.route('/download/<category>/<filename>', methods=['GET'])
def download_file(category, filename):
    """Serve regular files for download"""
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
        "download_only_mode": True,
        "temp_files": len(temp_file_registry)
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
    print("\n  GET /download/temp/<filename>?key=<key>")
    print("    - Download temporary files")
    print("\n  GET /health")
    print("    - Server health check")
    print("\n🔗 Server running at http://localhost:5555\n")
    
    app.run(host='0.0.0.0', port=5555) 