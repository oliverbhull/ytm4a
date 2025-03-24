from pathlib import Path
import os
import subprocess
import json
from datetime import datetime
from category_strategy import CategoryStrategy

class YTMAnalyzer:
    def __init__(self, base_dir, assemblyai_api_key):
        self.base_dir = Path(base_dir)
        self.assemblyai_api_key = assemblyai_api_key

    def extract_video_id(self, youtube_url):
        # Extract video ID from YouTube URL
        pass

    def sanitize_filename(self, filename):
        # Sanitize filename to remove invalid characters
        pass

    def _generate_price_chart(self, result, ticker_symbol, final_filename):
        # Generate price chart using the result and ticker symbol
        pass

    def process_url(self, youtube_url, category, ticker_symbol=None):
        """Process YouTube URL and run the analysis pipeline"""
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
            video_title = self.sanitize_filename(metadata['title'])
            date_prefix = datetime.now().strftime('%Y%m%d')
            final_filename = f"{date_prefix}_{video_title}"

            # Get the actual downloaded filename
            original_file = Path(f"og_{video_title}.m4a")
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

            # Prompt user for confirmation before proceeding with ML analysis
            print("\n📝 Summary of processing so far:")
            print(f"- Video title: {metadata['title']}")
            print(f"- Duration: {metadata.get('duration_string', 'Unknown')}")
            print(f"- Category: {category}")
            if ticker_symbol:
                print(f"- Ticker: {ticker_symbol}")
            print("\nReady to proceed with transcription and ML analysis.")
            
            while True:
                response = input("Continue? (y/n): ").lower().strip()
                if response in ['y', 'n']:
                    break
                print("Please enter 'y' for yes or 'n' for no.")
            
            if response == 'n':
                print("\n❌ Analysis cancelled by user")
                return {
                    "status": "cancelled",
                    "message": "Analysis cancelled by user",
                    "filename": final_filename,
                    "category": category
                }

            # Initialize category strategy and process video
            print("\n🎯 Running ML pipeline analysis...")
            strategy = CategoryStrategy(category)
            result = strategy.process_video(str(audio_file), ticker_symbol, self.assemblyai_api_key)
            
            # Save analysis results
            analysis_file = Path(f"{final_filename}_analysis.json")
            with analysis_file.open('w') as f:
                json.dump(result, f, indent=4)
            
            print("✅ Analysis complete!")
            
            # Generate price chart if ticker is provided
            if ticker_symbol:
                print("📈 Generating price chart...")
                self._generate_price_chart(result, ticker_symbol, final_filename)

            return {
                "status": "success",
                "message": "Processing complete",
                "filename": final_filename,
                "category": category,
                "analysis": result
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
 