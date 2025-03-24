# import os
# import json
# import spacy
# import nltk
# import assemblyai as aai
# from textblob import TextBlob
# from datetime import datetime, timedelta
# import pandas as pd
# import numpy as np
# from transformers import pipeline
# from tqdm import tqdm
# import yfinance as yf
# import ta
# from pathlib import Path

# # Download required NLTK data
# nltk.download('punkt')
# nltk.download('stopwords')
# nltk.download('averaged_perceptron_tagger')
# nltk.download('maxent_ne_chunker')
# nltk.download('words')

# class TranscriptProcessor:
#     def __init__(self, assemblyai_api_key=None):
#         """Initialize the transcript processor with necessary models and API keys"""
#         self.nlp = spacy.load("en_core_web_sm")
#         self.sentiment_analyzer = pipeline("sentiment-analysis")
        
#         # Initialize AssemblyAI client if API key is provided
#         if assemblyai_api_key:
#             aai.settings.api_key = assemblyai_api_key
#             self.transcriber = aai.Transcriber()
#         else:
#             self.transcriber = None
        
#         # Load stopwords
#         self.stop_words = set(nltk.corpus.stopwords.words('english'))
        
#     def clean_text(self, text):
#         """Clean and standardize text"""
#         # Convert to lowercase
#         text = text.lower()
        
#         # Remove filler words and stopwords
#         words = nltk.word_tokenize(text)
#         words = [w for w in words if w not in self.stop_words]
        
#         # Rejoin text
#         return " ".join(words)
    
#     def extract_entities(self, text):
#         """Extract named entities using spaCy"""
#         doc = self.nlp(text)
#         entities = {
#             'ORG': [],  # Organizations
#             'PERSON': [],  # People
#             'GPE': [],  # Countries, cities
#             'MONEY': [],  # Monetary values
#             'PERCENT': []  # Percentages
#         }
        
#         for ent in doc.ents:
#             if ent.label_ in entities:
#                 entities[ent.label_].append(ent.text)
        
#         return entities
    
#     def analyze_sentiment(self, text):
#         """Analyze sentiment using both TextBlob and Hugging Face"""
#         # TextBlob sentiment (gives polarity and subjectivity)
#         blob = TextBlob(text)
#         textblob_sentiment = {
#             'polarity': blob.sentiment.polarity,
#             'subjectivity': blob.sentiment.subjectivity
#         }
        
#         # Hugging Face sentiment (more nuanced classification)
#         # Split text into chunks of 500 tokens for the model's limit
#         sentences = nltk.sent_tokenize(text)
#         chunks = []
#         current_chunk = []
#         current_length = 0
        
#         for sentence in sentences:
#             # Rough estimation of tokens (words + punctuation)
#             sentence_length = len(sentence.split())
#             if current_length + sentence_length > 500:
#                 chunks.append(' '.join(current_chunk))
#                 current_chunk = [sentence]
#                 current_length = sentence_length
#             else:
#                 current_chunk.append(sentence)
#                 current_length += sentence_length
        
#         if current_chunk:
#             chunks.append(' '.join(current_chunk))
        
#         # Analyze sentiment for each chunk
#         chunk_sentiments = [self.sentiment_analyzer(chunk)[0] for chunk in chunks]
        
#         # Aggregate sentiments
#         if chunk_sentiments:
#             # Count labels
#             label_counts = {}
#             total_score = 0
#             for sentiment in chunk_sentiments:
#                 label = sentiment['label']
#                 score = sentiment['score']
#                 label_counts[label] = label_counts.get(label, 0) + 1
#                 total_score += score
            
#             # Get most common label and average score
#             most_common_label = max(label_counts.items(), key=lambda x: x[1])[0]
#             average_score = total_score / len(chunk_sentiments)
            
#             hf_sentiment = {
#                 'label': most_common_label,
#                 'score': average_score,
#                 'chunk_count': len(chunks)
#             }
#         else:
#             hf_sentiment = {
#                 'label': 'NEUTRAL',
#                 'score': 0.5,
#                 'chunk_count': 0
#             }
        
#         return {
#             'textblob': textblob_sentiment,
#             'huggingface': hf_sentiment
#         }
    
#     def process_transcript(self, audio_file_path, category):
#         """Process audio file to get transcript and extract features"""
#         if not self.transcriber:
#             raise ValueError("AssemblyAI transcriber not initialized. Please provide an API key.")
            
#         # Convert to Path object to handle spaces properly
#         audio_path = Path(audio_file_path).resolve()
            
#         # Transcribe audio using AssemblyAI
#         config = aai.TranscriptionConfig(
#             speaker_labels=True,
#             entity_detection=True,
#             auto_chapters=True
#         )
        
#         transcript = self.transcriber.transcribe(str(audio_path), config)
        
#         # Extract text and clean it
#         text = transcript.text
#         cleaned_text = self.clean_text(text)
        
#         # Extract features
#         entities = self.extract_entities(cleaned_text)
#         sentiment = self.analyze_sentiment(cleaned_text)
        
#         # Get speaker segments
#         speakers = []
#         for utterance in transcript.utterances:
#             speakers.append({
#                 'speaker': utterance.speaker,
#                 'text': utterance.text,
#                 'start': utterance.start,
#                 'end': utterance.end
#             })
        
#         # Get auto-generated chapters/topics
#         chapters = []
#         for chapter in transcript.chapters:
#             chapters.append({
#                 'headline': chapter.headline,
#                 'summary': chapter.summary,
#                 'start': chapter.start,
#                 'end': chapter.end
#             })
        
#         return {
#             'transcript': text,
#             'cleaned_transcript': cleaned_text,
#             'entities': entities,
#             'sentiment': sentiment,
#             'speakers': speakers,
#             'chapters': chapters,
#             'category': category,
#             'processed_date': datetime.now().isoformat()
#         }

# class FeatureEngineering:
#     def __init__(self):
#         """Initialize feature engineering with necessary components"""
#         self.price_cache = {}
    
#     def get_market_data(self, symbol, start_date, end_date):
#         """Fetch market data for a symbol"""
#         cache_key = f"{symbol}_{start_date}_{end_date}"
#         if cache_key in self.price_cache:
#             return self.price_cache[cache_key]
        
#         # Fetch data from yfinance
#         ticker = yf.Ticker(symbol)
#         df = ticker.history(start=start_date, end=end_date)
        
#         # Add technical indicators
#         df['RSI'] = ta.momentum.RSIIndicator(df['Close']).rsi()
#         df['MACD'] = ta.trend.MACD(df['Close']).macd()
#         df['BB_upper'] = ta.volatility.BollingerBands(df['Close']).bollinger_hband()
#         df['BB_lower'] = ta.volatility.BollingerBands(df['Close']).bollinger_lband()
        
#         # Calculate returns
#         df['returns_1d'] = df['Close'].pct_change()
#         df['returns_5d'] = df['Close'].pct_change(periods=5)
#         df['returns_30d'] = df['Close'].pct_change(periods=30)
        
#         self.price_cache[cache_key] = df
#         return df
    
#     def create_feature_set(self, processed_transcript, market_data):
#         """Create feature set from transcript and market data"""
#         features = {
#             # Sentiment features
#             'sentiment_polarity': processed_transcript['sentiment']['textblob']['polarity'],
#             'sentiment_subjectivity': processed_transcript['sentiment']['textblob']['subjectivity'],
#             'hf_sentiment_label': processed_transcript['sentiment']['huggingface']['label'],
#             'hf_sentiment_score': processed_transcript['sentiment']['huggingface']['score'],
            
#             # Entity counts
#             'person_mentions': len(processed_transcript['entities']['PERSON']),
#             'org_mentions': len(processed_transcript['entities']['ORG']),
#             'location_mentions': len(processed_transcript['entities']['GPE']),
#             'money_mentions': len(processed_transcript['entities']['MONEY']),
            
#             # Market features (if market_data is provided)
#             'rsi': market_data['RSI'].iloc[-1] if market_data is not None else None,
#             'macd': market_data['MACD'].iloc[-1] if market_data is not None else None,
#             'volatility': market_data['Close'].pct_change().std() if market_data is not None else None,
            
#             # Category-specific features can be added here
#             'category': processed_transcript['category']
#         }
        
#         return features

# class CategoryStrategy:
#     def __init__(self, category):
#         """Initialize strategy for a specific category"""
#         self.category = category
#         self.processor = None  # Initialize later when we have the API key
#         self.feature_eng = FeatureEngineering()
    
#     def process_video(self, video_path, ticker_symbol=None, assemblyai_api_key=None):
#         """Process a video and generate trading signals"""
#         # Initialize processor with API key
#         self.processor = TranscriptProcessor(assemblyai_api_key)
        
#         # Process transcript
#         processed_data = self.processor.process_transcript(video_path, self.category)
        
#         # Get market data if ticker is provided
#         market_data = None
#         if ticker_symbol:
#             end_date = datetime.now()
#             start_date = end_date - timedelta(days=60)
#             market_data = self.feature_eng.get_market_data(ticker_symbol, start_date, end_date)
        
#         # Create feature set
#         features = self.feature_eng.create_feature_set(processed_data, market_data)
        
#         # Generate trading signal based on category-specific logic
#         signal = self.generate_signal(features, market_data)
        
#         return {
#             'processed_data': processed_data,
#             'features': features,
#             'signal': signal
#         }
    
#     def generate_signal(self, features, market_data):
#         """Generate trading signal based on category-specific logic"""
#         if self.category == "Finance":
#             return self._generate_finance_signal(features, market_data)
#         elif self.category == "AI":
#             return self._generate_ai_signal(features, market_data)
#         elif self.category == "Geopolitics":
#             return self._generate_geopolitics_signal(features, market_data)
#         else:
#             raise ValueError(f"Unknown category: {self.category}")
    
#     def _generate_finance_signal(self, features, market_data):
#         """Generate trading signal for finance category"""
#         signal = {
#             'direction': 'NEUTRAL',
#             'confidence': 0.0,
#             'horizon': 'SHORT_TERM',
#             'reasoning': []
#         }
        
#         # Example logic for finance signals
#         if features['sentiment_polarity'] > 0.3 and features['rsi'] < 30:
#             signal['direction'] = 'BUY'
#             signal['confidence'] = min(abs(features['sentiment_polarity']) * 2, 1.0)
#             signal['reasoning'].append('Strong positive sentiment with oversold conditions')
#         elif features['sentiment_polarity'] < -0.3 and features['rsi'] > 70:
#             signal['direction'] = 'SELL'
#             signal['confidence'] = min(abs(features['sentiment_polarity']) * 2, 1.0)
#             signal['reasoning'].append('Strong negative sentiment with overbought conditions')
        
#         return signal
    
#     def _generate_ai_signal(self, features, market_data):
#         """Generate trading signal for AI category"""
#         signal = {
#             'direction': 'NEUTRAL',
#             'confidence': 0.0,
#             'horizon': 'MEDIUM_TERM',
#             'reasoning': []
#         }
        
#         # Example logic for AI signals
#         if features['sentiment_polarity'] > 0.2 and features['org_mentions'] > 3:
#             signal['direction'] = 'BUY'
#             signal['confidence'] = min(features['sentiment_polarity'] + 0.1 * features['org_mentions'], 1.0)
#             signal['reasoning'].append('Positive sentiment with multiple company mentions')
        
#         return signal
    
#     def _generate_geopolitics_signal(self, features, market_data):
#         """Generate trading signal for geopolitics category"""
#         signal = {
#             'direction': 'NEUTRAL',
#             'confidence': 0.0,
#             'horizon': 'LONG_TERM',
#             'reasoning': []
#         }
        
#         # Example logic for geopolitics signals
#         if abs(features['sentiment_polarity']) > 0.4 and features['location_mentions'] > 2:
#             signal['direction'] = 'BUY' if features['sentiment_polarity'] > 0 else 'SELL'
#             signal['confidence'] = min(abs(features['sentiment_polarity']) * 1.5, 1.0)
#             signal['reasoning'].append('Strong sentiment with multiple location mentions')
        
#         return signal 