import os
import time
import json
import requests
import sys
from datetime import datetime
import subprocess
import shutil

# **CONFIGURATION**
ASSEMBLYAI_API_KEY = "b6a3096b4a314f339a068d02b41ffd7d"  #enter your assemblyai api key here. this is mine. 0.37 cents per hr
BASE_FOLDER = "/Users/oliverhull/Desktop/ytm4a"  #enter your destination main folder here
PYTHON_FOLDER = os.path.join(BASE_FOLDER, "__python__")

def convert_to_mp3(input_path):
    output_path = input_path.rsplit('.', 1)[0] + '.mp3'
    print(f"🔄 Converting audio to MP3 format...")
    try:
        subprocess.run(['ffmpeg', '-i', input_path, '-acodec', 'libmp3lame', '-q:a', '2', output_path], 
                      check=True, capture_output=True, text=True)
        print("✅ Conversion successful")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"❌ Conversion error: {e.stderr}")
        return None

def transcribe_audio(category_folder_name, ticker_symbol):
    # Category folder path (AI, Finance, or Geopolitics)
    category_path = os.path.join(BASE_FOLDER, category_folder_name)
    
    # Find the .m4a file in the category folder
    audio_files = [f for f in os.listdir(category_path) if f.endswith(".m4a")]
    if not audio_files:
        print(f"❌ Error: No .m4a file found in {category_path}")
        return

    m4a_filename = audio_files[0]
    source_file_path = os.path.join(category_path, m4a_filename)
    
    # Create destination folder with same name as m4a file (minus extension)
    destination_folder_name = os.path.splitext(m4a_filename)[0]
    destination_folder_path = os.path.join(category_path, destination_folder_name)
    os.makedirs(destination_folder_path, exist_ok=True)
    
    # Move m4a file to new folder
    destination_file_path = os.path.join(destination_folder_path, m4a_filename)
    shutil.move(source_file_path, destination_file_path)
    
    # Move metadata.json if it exists
    source_metadata_path = os.path.join(category_path, "metadata.json")
    if os.path.exists(source_metadata_path):
        destination_metadata_path = os.path.join(destination_folder_path, "metadata.json")
        shutil.move(source_metadata_path, destination_metadata_path)
        with open(destination_metadata_path, "r") as f:
            metadata = json.load(f)
    else:
        print(f"⚠️ Warning: No metadata found")
        metadata = {}

    # Extract metadata fields
    video_title = metadata.get("title", "Unknown Title")
    raw_upload_date = metadata.get("upload_date", "Unknown Date")
    uploader = metadata.get("uploader", "Unknown Uploader")

    # Convert upload date to YYYY-MM-DD
    try:
        upload_date = datetime.strptime(raw_upload_date, "%Y%m%d").strftime("%Y-%m-%d")
    except ValueError:
        upload_date = "Unknown Date"

    print(f"✅ Created folder and moved files: {destination_folder_path}")

    # Convert to MP3 before uploading
    mp3_path = convert_to_mp3(destination_file_path)
    if not mp3_path:
        print("❌ Failed to convert audio file")
        return

    # Upload file to AssemblyAI
    print("📤 Uploading file to AssemblyAI...")
    headers = {"authorization": ASSEMBLYAI_API_KEY}
    
    try:
        with open(mp3_path, "rb") as f:
            files = {
                "file": ("audio.mp3", f, "audio/mpeg")
            }
            response = requests.post("https://api.assemblyai.com/v2/upload", 
                                  headers=headers, 
                                  files=files)
            response.raise_for_status()
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        return
    finally:
        # Clean up the temporary MP3 file
        if os.path.exists(mp3_path):
            os.remove(mp3_path)

    audio_url = response.json()["upload_url"]
    print("✅ File uploaded successfully")

    # Request transcription
    print("🎯 Requesting transcription...")
    data = {
        "audio_url": audio_url,
        "speaker_labels": True,
        "format_text": True
    }
    
    try:
        response = requests.post("https://api.assemblyai.com/v2/transcript",
                              headers=headers,
                              json=data)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Transcription request error: {str(e)}")
        return

    transcript_id = response.json()["id"]
    print("✅ Transcription requested. ID:", transcript_id)

    # Poll for transcription completion
    print("⏳ Waiting for transcription to complete...")
    while True:
        try:
            response = requests.get(f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                                 headers=headers)
            response.raise_for_status()
            result = response.json()
            status = result["status"]
            print(f"Status: {status}")

            if status == "completed":
                transcript_text = format_transcription(result)
                transcript_data = {
                    "title": video_title,
                    "uploader": uploader,
                    "upload_date": upload_date,
                    "ticker_symbol": ticker_symbol,
                    "transcription": transcript_text
                }
                
                # Save JSON with same name as the folder
                transcript_path = os.path.join(destination_folder_path, f"{destination_folder_name}.json")
                
                with open(transcript_path, "w") as f:
                    json.dump(transcript_data, f, indent=4)
                
                print(f"✅ Transcription saved: {transcript_path}")

                # Run ML model if inside Finance folder
                if category_folder_name.lower() == "finance":
                    print("🤖 Running finance ML analysis...")
                    if not ticker_symbol or ticker_symbol.strip() == "" or ticker_symbol == "%Variable%TickerSymbol%":
                        print("ℹ️ No specific ticker provided. Analyzing S&P 500 (SPY) for market context...")
                        
                        # First analyze SPY
                        try:
                            subprocess.run(["python3", os.path.join(PYTHON_FOLDER, "finance_ml.py"), 
                                          transcript_path, "SPY"], check=True)
                        except subprocess.CalledProcessError as e:
                            print(f"❌ S&P 500 analysis failed: {str(e)}")
                        
                        # Then show relevant stock suggestions
                        suggested_tickers = []
                        if "nuclear" in video_title.lower():
                            suggested_tickers = [
                                ("NE", "NuScale Power - Small Modular Reactor company"),
                                ("BWC", "Brookfield/Westinghouse - AP1000 reactor manufacturer"),
                                ("GE", "General Electric - Nuclear technology provider"),
                                ("SO", "Southern Company - Plant Vogtle owner")
                            ]
                        
                        if suggested_tickers:
                            print("\n💡 For specific stock analysis related to this video, try:")
                            for ticker, description in suggested_tickers:
                                print(f"   - {ticker} ({description})")
                            print("\nTo analyze any of these stocks, run:")
                            print(f"python3 {os.path.join(PYTHON_FOLDER, 'finance_ml.py')} \"{transcript_path}\" TICKER")
                        return
                    print(f"📈 Analyzing ticker symbol: {ticker_symbol}")
                    try:
                        subprocess.run(["python3", os.path.join(PYTHON_FOLDER, "finance_ml.py"), 
                                      transcript_path, ticker_symbol], check=True)
                    except subprocess.CalledProcessError as e:
                        print(f"❌ Finance analysis failed: {str(e)}")
                        print("Please check the ticker symbol and try again.")
                return

            elif status in ["error", "failed"]:
                print("❌ Transcription failed.")
                print("Error details:", result.get("error"))
                return

        except Exception as e:
            print(f"❌ Error checking transcription status: {str(e)}")
            return

        time.sleep(5)

def format_transcription(transcript_data):
    output = []
    for utterance in transcript_data.get("utterances", []):
        speaker = f"[Speaker {utterance['speaker']}]" if "speaker" in utterance else "[Unknown]"
        start_time = f"{int(utterance['start']) // 1000:02}:{int(utterance['start']) % 1000:02}"
        output.append(f"{speaker} | {start_time}\n{utterance['text']}\n")
    return "\n".join(output)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("❌ Error: No folder name or ticker symbol provided")
        sys.exit(1)

    folder_name = sys.argv[1]
    ticker_symbol = sys.argv[2]
    
    # Handle empty or Keyboard Maestro variable placeholder
    if ticker_symbol in ["", "%Variable%TickerSymbol%"]:
        ticker_symbol = ""
        
    transcribe_audio(folder_name, ticker_symbol)