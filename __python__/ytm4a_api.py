import os
import sys
import json
import subprocess
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import re
from dotenv import load_dotenv
# from ml_pipeline import CategoryStrategy
from pathlib import Path

# Load environment variables
python_dir = Path(__file__).parent
load_dotenv(python_dir / '.env')

class YTM4AProcessor:
    def __init__(self):
        self.base_dir = python_dir.parent  # Go up one level from __python__
        self.venv_path = self.base_dir / "venv"
        self.python_dir = python_dir
        
        # Initialize ML pipeline with AssemblyAI API key
        self.assemblyai_api_key = os.getenv('ASSEMBLYAI_API_KEY')
        if not self.assemblyai_api_key:
            print("⚠️ Warning: ASSEMBLYAI_API_KEY not found in environment variables")

    def activate_venv(self):
        """Ensure we're running in the virtual environment"""
        venv_python = self.venv_path / "bin" / "python3"
        if sys.executable != str(venv_python):
            print("🔄 Restarting in virtual environment...")
            os.execl(str(venv_python), str(venv_python), *sys.argv)

    def extract_video_id(self, url):
        """Extract YouTube video ID from URL"""
        parsed_url = urlparse(url)
        
        if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
            if parsed_url.path == '/watch':
                return parse_qs(parsed_url.query)['v'][0]
        elif parsed_url.hostname == 'youtu.be':
            return parsed_url.path[1:]
        
        raise ValueError("Invalid YouTube URL")

    def sanitize_filename(self, title):
        """Convert title to safe filename"""
        # Remove invalid characters and replace with underscores
        safe_title = re.sub(r'[<>:"/\\|?*\']', '_', title)
        # Replace spaces with underscores
        safe_title = safe_title.replace(' ', '_')
        # Remove multiple underscores
        safe_title = re.sub(r'_+', '_', safe_title)
        # Remove leading/trailing underscores
        safe_title = safe_title.strip('_')
        # Limit length
        return safe_title[:100]

    def process_url(self, youtube_url, category, ticker_symbol=None, custom_title=None):
        """Process YouTube URL and download/compress audio"""
        try:
            # Validate URL and extract video ID
            video_id = self.extract_video_id(youtube_url)
            print(f"✅ Valid YouTube URL: {video_id}")

            # Create category directory if it doesn't exist
            category_path = self.base_dir / category
            category_path.mkdir(exist_ok=True)

            # Change to category directory
            os.chdir(str(category_path))
            print(f"📂 Working in: {category_path}")

            # Download video and metadata
            print("⬇️ Downloading video...")
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
            
            # Use custom title if provided, otherwise use YouTube title
            if custom_title:
                video_title = self.sanitize_filename(custom_title)
            else:
                video_title = self.sanitize_filename(metadata['title'])
                
            # Use YYMMDD date format as requested
            date_prefix = datetime.now().strftime('%y%m%d')
            final_filename = f"{date_prefix}_{video_title}"

            # Get the actual downloaded filename
            original_file = Path(f"og_{self.sanitize_filename(metadata['title'])}.m4a")
            if not original_file.exists():
                # Try to find any .m4a file starting with "og_"
                m4a_files = list(category_path.glob('og_*.m4a'))
                if m4a_files:
                    original_file = m4a_files[0]
                else:
                    raise FileNotFoundError("Could not find downloaded audio file")

            # Save metadata
            metadata_file = Path(f"{final_filename}.json")
            with metadata_file.open('w') as f:
                json.dump(metadata, f, indent=4)

            # Compress audio
            print("🔄 Compressing audio...")
            audio_file = Path(f"{final_filename}.m4a")
            subprocess.run([
                "ffmpeg",
                "-i", str(original_file),
                "-b:a", "64k",
                str(audio_file)
            ], check=True)

            # Remove original file
            original_file.unlink()
            print("✅ Audio processing complete")

            # Return success without running ML pipeline
            return {
                "status": "success",
                "message": "Audio processing complete",
                "filename": final_filename,
                "category": category
            }

        except subprocess.CalledProcessError as e:
            error_msg = f"Command failed: {e.cmd}\nOutput: {e.output}"
            print(f"❌ Error: {error_msg}")
            return {"status": "error", "message": error_msg}
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error: {error_msg}")
            return {"status": "error", "message": error_msg}
    
    def _generate_price_chart(self, analysis_result, ticker_symbol, filename_prefix):
        """Generate price chart with analysis overlay"""
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        # Get market data from the analysis
        market_data = analysis_result.get('features', {}).get('market_data')
        if market_data is None:
            return
        
        # Create figure with secondary y-axis
        fig = make_subplots(rows=2, cols=1, 
                           shared_xaxes=True,
                           vertical_spacing=0.03,
                           row_heights=[0.7, 0.3])
        
        # Add candlestick
        fig.add_trace(go.Candlestick(
            x=market_data.index,
            open=market_data['Open'],
            high=market_data['High'],
            low=market_data['Low'],
            close=market_data['Close'],
            name='Price'
        ), row=1, col=1)
        
        # Add RSI
        fig.add_trace(go.Scatter(
            x=market_data.index,
            y=market_data['RSI'],
            name='RSI',
            line=dict(color='purple')
        ), row=2, col=1)
        
        # Add MACD
        fig.add_trace(go.Scatter(
            x=market_data.index,
            y=market_data['MACD'],
            name='MACD',
            line=dict(color='blue')
        ), row=2, col=1)
        
        # Update layout
        fig.update_layout(
            title=f"{ticker_symbol} Analysis",
            yaxis_title="Price",
            yaxis2_title="Indicators",
            xaxis_rangeslider_visible=False
        )
        
        # Save chart
        fig.write_image(f"{filename_prefix}_price.png")

def main():
    if len(sys.argv) < 3:
        print("Usage: python ytm4a_api.py <youtube_url> <category> [ticker_symbol]")
        sys.exit(1)

    youtube_url = sys.argv[1]
    category = sys.argv[2]
    ticker_symbol = sys.argv[3] if len(sys.argv) > 3 else None

    processor = YTM4AProcessor()
    processor.activate_venv()
    result = processor.process_url(youtube_url, category, ticker_symbol)

    # Output JSON result for the Chrome extension
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main() 