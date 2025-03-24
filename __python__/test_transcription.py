# import os
# import assemblyai as aai
# from dotenv import load_dotenv
# from pathlib import Path

# # Load environment variables from the __python__ directory
# python_dir = os.path.dirname(os.path.abspath(__file__))
# load_dotenv(os.path.join(python_dir, '.env'))

# def test_transcription(audio_file_path):
#     """Test basic transcription functionality"""
#     # Convert to Path object to handle spaces and special characters properly
#     audio_path = Path(audio_file_path).resolve()
    
#     # Get API key
#     api_key = os.getenv('ASSEMBLYAI_API_KEY')
#     if not api_key:
#         print("❌ Error: ASSEMBLYAI_API_KEY not found in .env")
#         return
    
#     print(f"✓ Found API key: {api_key[:8]}...")
#     print(f"✓ Audio file: {audio_path}")
    
#     try:
#         # Initialize AssemblyAI
#         aai.settings.api_key = api_key
        
#         print("\n1. Creating transcription config...")
#         config = aai.TranscriptionConfig(
#             speaker_labels=True,
#             entity_detection=True,
#             auto_chapters=True
#         )
#         print("✓ Config created")
        
#         print("\n2. Starting transcription...")
#         transcriber = aai.Transcriber()
#         # Convert Path to string for transcription
#         transcript = transcriber.transcribe(str(audio_path), config)
        
#         print("\n3. Transcription complete!")
#         print("\nFirst 200 characters of transcript:")
#         print("-" * 50)
#         print(transcript.text[:200] + "...")
        
#         print("\nSpeakers detected:")
#         for utterance in transcript.utterances:
#             print(f"- Speaker {utterance.speaker}: {utterance.text[:50]}...")
        
#         print("\nChapters detected:")
#         for chapter in transcript.chapters:
#             print(f"- {chapter.headline}")
        
#         return transcript
        
#     except Exception as e:
#         print(f"\n❌ Error: {str(e)}")
#         return None

# if __name__ == "__main__":
#     # Test with two files from Davos directory
#     test_files = [
#         "../Davos/20250122_Anthropic CEO: More confident than ever that we're 'very close' to powerful AI capabilities.m4a",
#         "../Davos/20250122_Microsoft CEO Satya Nadella: AI simultaneously reduces the floor & raises the ceiling for all of us.m4a"
#     ]
    
#     for test_file in test_files:
#         print(f"\n\nTesting file: {test_file}")
#         print("=" * 80)
#         if not Path(test_file).exists():
#             print(f"❌ Error: Test file not found: {test_file}")
#             continue
#         test_transcription(test_file)
#         input("\nPress Enter to continue to next file...") 