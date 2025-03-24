import os
import logging
import nltk
import assemblyai as aai
from dotenv import load_dotenv
from transformers import pipeline
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta
import re

class MLPipeline:
    def __init__(self):
        """Initialize ML pipeline with necessary models and configurations."""
        # Load environment variables
        load_dotenv()
        
        # Initialize sentiment analysis pipeline
        self.sentiment_pipeline = pipeline("sentiment-analysis", device="mps")
        
        # Initialize AssemblyAI client
        self.transcriber = aai.Transcriber()
        
        # Initialize regression model
        self.model = LinearRegression()

    def get_stock_data(self, ticker, days=30):
        """Get historical stock data for the specified period."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Fetch stock data
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)
        
        # Calculate daily returns
        df['Returns'] = df['Close'].pct_change()
        
        return df

    def predict_future_returns(self, sentiment_score, stock_data):
        """
        Predict future returns using linear regression.
        Formula: future_return = β₀ + β₁ * sentiment_score + β₂ * avg_past_returns
        """
        try:
            # Prepare features
            X = pd.DataFrame()
            
            # Add sentiment score (repeated for each day)
            X['sentiment'] = [sentiment_score] * len(stock_data)
            
            # Add rolling average of past returns (5-day window)
            X['past_returns'] = stock_data['Returns'].rolling(window=5).mean()
            
            # Target variable: next day's returns
            y = stock_data['Returns'].shift(-1)
            
            # Remove NaN values
            mask = ~X['past_returns'].isna() & ~y.isna()
            X = X[mask]
            y = y[mask]
            
            if len(X) < 2:
                raise ValueError("Insufficient data for prediction")
            
            # Fit model
            self.model.fit(X, y)
            
            # Print the formula with actual coefficients
            print("\n📊 Prediction Formula:")
            print(f"future_return = {self.model.intercept_:.4f} + "
                  f"({self.model.coef_[0]:.4f} × sentiment_score) + "
                  f"({self.model.coef_[1]:.4f} × avg_past_returns)")
            
            # Predict next 5 days
            last_features = pd.DataFrame({
                'sentiment': [sentiment_score],
                'past_returns': [stock_data['Returns'].tail(5).mean()]
            })
            
            base_prediction = self.model.predict(last_features)[0]
            predictions = []
            current_price = stock_data['Close'].iloc[-1]
            
            for i in range(5):
                predicted_return = base_prediction * (1 - 0.1 * i)  # Decay factor
                predicted_price = current_price * (1 + predicted_return)
                predictions.append({
                    'day': i + 1,
                    'predicted_return': predicted_return,
                    'predicted_price': predicted_price
                })
                current_price = predicted_price
            
            return {
                'model_coefficients': {
                    'intercept': float(self.model.intercept_),
                    'sentiment_coef': float(self.model.coef_[0]),
                    'returns_coef': float(self.model.coef_[1])
                },
                'r_squared': float(self.model.score(X, y)),
                'predictions': predictions
            }
            
        except Exception as e:
            logging.error(f"Error in prediction: {str(e)}")
            return None

    def process_transcript(self, audio_file_path, ticker):
        """Process audio file through ML pipeline and make predictions."""
        try:
            # Get API key and transcribe
            api_key = os.getenv("ASSEMBLYAI_API_KEY")
            if not api_key:
                raise ValueError("AssemblyAI API key not found in environment variables")

            # Configure transcription
            config = aai.TranscriptionConfig(
                speaker_labels=True,
                entity_detection=True,
                auto_chapters=True
            )

            # Create transcript
            transcript = self.transcriber.transcribe(audio_file_path, config)

            # Get sentiment
            sentiment = self.analyze_sentiment(transcript.text)
            
            # Get stock data and make predictions
            stock_data = self.get_stock_data(ticker)
            predictions = self.predict_future_returns(sentiment['score'], stock_data)

            return {
                "transcript": transcript.text,
                "sentiment": sentiment,
                "speakers": transcript.speaker_labels,
                "chapters": transcript.chapters,
                "predictions": predictions
            }

        except Exception as e:
            logging.error(f"Error in ML pipeline: {str(e)}")
            raise

    def analyze_sentiment(self, text):
        """Analyze sentiment of the text using DistilBERT."""
        try:
            # Split text into sentences
            sentences = nltk.sent_tokenize(text)
            
            # Initialize variables for sentiment aggregation
            total_score = 0
            sentiment_counts = {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0}
            results = []
            
            # Process each sentence individually to ensure we stay under token limit
            for sentence in sentences:
                # Skip empty sentences
                if not sentence.strip():
                    continue
                    
                try:
                    # Process one sentence at a time
                    result = self.sentiment_pipeline(sentence)[0]
                    results.append(result)
                except Exception as e:
                    logging.warning(f"Error analyzing sentence: {str(e)}")
                    # If the sentence is too long, split it by punctuation
                    if "sequence length is longer than" in str(e):
                        sub_sentences = re.split('[,;]', sentence)
                        for sub_sent in sub_sentences:
                            if sub_sent.strip():
                                try:
                                    result = self.sentiment_pipeline(sub_sent.strip())[0]
                                    results.append(result)
                                except Exception as e2:
                                    logging.warning(f"Error analyzing sub-sentence: {str(e2)}")
            
            # Aggregate results
            if results:
                for result in results:
                    sentiment_counts[result['label']] += 1
                    if result['label'] == "POSITIVE":
                        total_score += result['score']
                    elif result['label'] == "NEGATIVE":
                        total_score += (1 - result['score'])
                    else:
                        total_score += 0.5
                
                # Calculate dominant sentiment and average score
                dominant_sentiment = max(sentiment_counts.items(), key=lambda x: x[1])[0]
                average_score = total_score / len(results)
                
                print(f"\n📊 Sentiment Analysis:")
                print(f"Sentences analyzed: {len(results)}")
                print(f"Sentiment distribution: {sentiment_counts}")
                print(f"Average score: {average_score:.4f}")
                
                return {
                    "label": dominant_sentiment,
                    "score": float(average_score),
                    "distribution": sentiment_counts
                }
            else:
                print("\n⚠️ No sentiment results could be obtained")
                return {
                    "label": "NEUTRAL",
                    "score": 0.5,
                    "distribution": {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 1}
                }
                
        except Exception as e:
            logging.error(f"Error in sentiment analysis: {str(e)}")
            return {
                "label": "NEUTRAL",
                "score": 0.5,
                "distribution": {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 1}
            }