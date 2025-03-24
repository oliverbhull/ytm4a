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
                    result["audio_url"] = f"{base_url}/download/temp/{os.path.basename(audio_path)}?temp_file_path={audio_path}"
                    
                if metadata_path and os.path.exists(metadata_path):
                    result["metadata_url"] = f"{base_url}/download/temp/{os.path.basename(metadata_path)}?temp_file_path={metadata_path}"
        
        return jsonify(result)

    except Exception as e:
        logging.error(f"Error processing request: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

def process_for_mac_download(youtube_url, category, custom_title=None):
    """Process YouTube URL for direct Mac download without saving on the Pi"""
    try:
        # Create temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            os.chdir(temp_path)
            
            # Extract video ID
            from urllib.parse import urlparse, parse_qs
            parsed_url = urlparse(youtube_url)
            video_id = None
            
            if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
                if parsed_url.path == '/watch':
                    video_id = parse_qs(parsed_url.query)['v'][0]
            elif parsed_url.hostname == 'youtu.be':
                video_id = parsed_url.path[1:]
                
            if not video_id:
                raise ValueError("Invalid YouTube URL")
            
            # Download video and metadata
            logging.info(f"Downloading video: {youtube_url}")
            result = subprocess.run([
                "yt-dlp",
                "--geo-bypass",
                "-x",
                "--audio-format", "m4a",
                "-o", "og_%(title)s.%(ext)s",
                "--print-json",
                youtube_url
            ], capture_output=True, text=True, check=True)
            
            # Parse metadata
            metadata = json.loads(result.stdout)
            
            # Process title
            def sanitize_filename(title):
                """Convert title to safe filename"""
                import re
                # Remove invalid characters
                safe_title = re.sub(r'[<>:"/\\|?*\']', '_', title)
                # Replace spaces with underscores
                safe_title = safe_title.replace(' ', '_')
                # Remove multiple underscores
                safe_title = re.sub(r'_+', '_', safe_title)
                # Remove leading/trailing underscores
                safe_title = safe_title.strip('_')
                # Limit length
                return safe_title[:100]
            
            # Use custom title if provided, otherwise use YouTube title
            if custom_title:
                video_title = sanitize_filename(custom_title)
            else:
                video_title = sanitize_filename(metadata['title'])
                
            # Use YYMMDD date format
            date_prefix = datetime.now().strftime('%y%m%d')
            final_filename = f"{date_prefix}_{video_title}"
            
            # Find downloaded file
            original_file = list(temp_path.glob('og_*.m4a'))[0]
            if not original_file.exists():
                raise FileNotFoundError("Could not find downloaded audio file")
            
            # Save metadata
            metadata_file = temp_path / f"{final_filename}.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=4)
            
            # Compress audio
            audio_file = temp_path / f"{final_filename}.m4a"
            subprocess.run([
                "ffmpeg",
                "-i", str(original_file),
                "-b:a", "64k",
                str(audio_file)
            ], check=True)
            
            # Store files in memory
            temp_files = {
                "audio": str(audio_file),
                "metadata": str(metadata_file)
            }
            
            # Return success info
            return {
                "status": "success",
                "message": "Audio processing complete, ready for Mac download",
                "filename": final_filename,
                "category": category,
                "temp_files": temp_files
            }
            
    except subprocess.CalledProcessError as e:
        error_msg = f"Command failed: {e.cmd}\nOutput: {e.output}"
        logging.error(error_msg)
        return {"status": "error", "message": error_msg}
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error in process_for_mac_download: {error_msg}")
        return {"status": "error", "message": error_msg}

@app.route('/download/<category>/<filename>', methods=['GET'])
def download_file(category, filename):
    """Serve files for download"""
    try:
        # Check if this is a temp file from process_for_mac_download
        if 'temp_file_path' in request.args:
            temp_file_path = request.args.get('temp_file_path')
            if os.path.exists(temp_file_path):
                return send_from_directory(os.path.dirname(temp_file_path), 
                                         os.path.basename(temp_file_path), 
                                         as_attachment=True)
            else:
                return jsonify({"status": "error", "message": "Temporary file not found"}), 404
        
        # Regular file from Pi storage
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