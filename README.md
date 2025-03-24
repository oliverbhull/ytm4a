# YTM4A (YouTube Market Analysis for Algorithmic Trading)

An ML-powered pipeline that analyzes YouTube videos for market insights and generates trading signals.

## Overview

YTM4A processes YouTube videos in different categories (Finance, AI, Geopolitics) to extract insights and generate trading signals. It uses:

- Natural Language Processing (NLP) for sentiment analysis and entity extraction
- Technical analysis indicators (RSI, MACD, etc.)
- Category-specific trading strategies
- Automated audio transcription and analysis

## Features

- **Data Ingestion & Organization**
  - Automatic video downloading and categorization
  - Audio transcription using AssemblyAI
  - Structured storage of transcripts, metadata, and analysis

- **ML Pipeline**
  - Text cleaning and preprocessing
  - Named Entity Recognition (NER)
  - Sentiment analysis using multiple models
  - Technical indicator integration
  - Category-specific trading signals

- **Trading Strategies**
  - Finance: Short-term signals based on sentiment and technical indicators
  - AI: Medium-term signals focusing on company mentions and sector trends
  - Geopolitics: Long-term signals analyzing global events and impacts

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ytm4a.git
   cd ytm4a
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r __python__/requirements.txt
   python -m spacy download en_core_web_sm
   ```

4. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Add your AssemblyAI API key
   ```bash
   ASSEMBLYAI_API_KEY=your_key_here
   ```

5. Install system dependencies:
   - ffmpeg (for audio processing)
   - yt-dlp (for video downloading)

## Usage

1. Process a YouTube video:
   ```bash
   python __python__/ytm4a_api.py <youtube_url> <category> [ticker_symbol]
   ```
   
   Categories: Finance, AI, Geopolitics
   Example:
   ```bash
   python __python__/ytm4a_api.py "https://youtube.com/watch?v=..." Finance AAPL
   ```

2. Output:
   - Transcribed audio
   - Sentiment analysis
   - Entity extraction
   - Trading signals
   - Price charts (if ticker provided)

## Output Structure

For each processed video, YTM4A generates:
- `YYYYMMDD_video_title.m4a`: Compressed audio
- `YYYYMMDD_video_title.json`: Video metadata
- `YYYYMMDD_video_title_analysis.json`: ML analysis results
- `YYYYMMDD_video_title_price.png`: Price chart (if ticker provided)

## Analysis Output Format

The analysis JSON includes:
```json
{
    "processed_data": {
        "transcript": "...",
        "cleaned_transcript": "...",
        "entities": {
            "ORG": ["Apple", "Microsoft"],
            "PERSON": ["Tim Cook"],
            "GPE": ["United States"]
        },
        "sentiment": {
            "textblob": {
                "polarity": 0.2,
                "subjectivity": 0.5
            },
            "huggingface": {
                "label": "POSITIVE",
                "score": 0.85
            }
        },
        "speakers": [...],
        "chapters": [...]
    },
    "features": {
        "sentiment_polarity": 0.2,
        "org_mentions": 5,
        "person_mentions": 3,
        "rsi": 65.4,
        "macd": 0.5
    },
    "signal": {
        "direction": "BUY",
        "confidence": 0.75,
        "horizon": "SHORT_TERM",
        "reasoning": [
            "Strong positive sentiment with multiple company mentions",
            "RSI indicates momentum"
        ]
    }
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details.

## Disclaimer

This software is for educational purposes only. Always do your own research and consult with financial professionals before making investment decisions. The creators of YTM4A are not responsible for any financial losses incurred while using this software. 