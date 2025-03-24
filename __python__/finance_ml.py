# import sys
# import json
# import yfinance as yf
# import datetime
# from sklearn.linear_model import LinearRegression
# import numpy as np
# import matplotlib.pyplot as plt
# import os
# from matplotlib.dates import DateFormatter
# import logging

# # Set up logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     datefmt='%Y-%m-%d %H:%M:%S'
# )

# def validate_inputs(transcript_path, ticker_symbol):
#     """Validate input parameters"""
#     logging.info(f"Validating inputs: {transcript_path}, {ticker_symbol}")
    
#     # Check if transcript path exists
#     if not os.path.exists(transcript_path):
#         logging.error(f"❌ Transcript file not found: {transcript_path}")
#         return False
        
#     # Check if it's a JSON file
#     if not transcript_path.endswith('.json'):
#         logging.error(f"❌ File is not a JSON: {transcript_path}")
#         return False
    
#     # Validate ticker symbol (basic check)
#     if not ticker_symbol.isalpha():
#         logging.error(f"❌ Invalid ticker symbol: {ticker_symbol}")
#         return False
    
#     logging.info("✅ Input validation successful")
#     return True

# def get_last_trading_day(date):
#     """Adjust date to last trading day if it's a weekend"""
#     logging.info(f"Getting last trading day for {date.strftime('%Y-%m-%d')} (weekday: {date.weekday()})")
#     original_date = date
    
#     while date.weekday() >= 5:  # Saturday = 5, Sunday = 6
#         date -= datetime.timedelta(days=1)
#         logging.info(f"Weekend detected, moving to previous day: {date.strftime('%Y-%m-%d')}")
    
#     if date != original_date:
#         logging.info(f"Adjusted from {original_date.strftime('%Y-%m-%d')} to {date.strftime('%Y-%m-%d')}")
    
#     return date

# def get_next_trading_day(date):
#     """Adjust date to next trading day if it's a weekend"""
#     while date.weekday() >= 5:  # Saturday = 5, Sunday = 6
#         date += datetime.timedelta(days=1)
#     return date

# def get_trading_days_range(num_days=10):
#     """Get start and end dates ensuring they're trading days"""
#     logging.info(f"Calculating {num_days} trading day range")
    
#     # Get date from 5 days ago as our reference point
#     reference_date = datetime.datetime.now() - datetime.timedelta(days=5)
#     logging.info(f"Reference date (5 days ago): {reference_date.strftime('%Y-%m-%d')}")
    
#     # Adjust reference date to last trading day if needed
#     reference_date = get_last_trading_day(reference_date)
#     logging.info(f"Adjusted reference date: {reference_date.strftime('%Y-%m-%d')}")
    
#     # Calculate days before reference (about half of num_days)
#     days_before = (num_days - 1) // 2
#     days_after = num_days - 1 - days_before
    
#     # Count back trading days
#     start_date = reference_date
#     trading_days_count = 0
    
#     logging.info("Counting back trading days...")
#     while trading_days_count < days_before:
#         start_date -= datetime.timedelta(days=1)
#         if start_date.weekday() < 5:  # Monday = 0, Friday = 4
#             trading_days_count += 1
#             logging.info(f"Found trading day -{trading_days_count}: {start_date.strftime('%Y-%m-%d')}")
    
#     # Count forward trading days
#     end_date = reference_date
#     trading_days_count = 0
    
#     logging.info("Counting forward trading days...")
#     while trading_days_count < days_after:
#         end_date += datetime.timedelta(days=1)
#         if end_date.weekday() < 5:  # Monday = 0, Friday = 4
#             trading_days_count += 1
#             logging.info(f"Found trading day +{trading_days_count}: {end_date.strftime('%Y-%m-%d')}")
    
#     logging.info(f"Final date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
#     return start_date, end_date, reference_date

# def get_stock_data(ticker):
#     """Get stock data for the specified ticker"""
#     logging.info(f"Fetching stock data for {ticker}")
    
#     try:
#         # Get proper trading day range
#         start_date, end_date, reference_date = get_trading_days_range(10)
        
#         print(f"📅 Analyzing trading days from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
#         # Add one day to end_date to include the last trading day
#         query_end = end_date + datetime.timedelta(days=1)
        
#         logging.info(f"Attempting to download data from Yahoo Finance...")
#         # Download data
#         data = yf.download(ticker, 
#                           start=start_date.strftime("%Y-%m-%d"),
#                           end=query_end.strftime("%Y-%m-%d"),
#                           interval="1d",
#                           progress=False)
        
#         logging.info(f"Received data with {len(data)} rows")
        
#         if data.empty:
#             logging.error(f"No data received for {ticker}")
#             raise ValueError(f"No data available for {ticker}")
        
#         # Log the actual dates we received
#         logging.info(f"Data range received: {data.index[0]} to {data.index[-1]}")
        
#         # Verify we have enough trading days
#         if len(data) < 5:
#             logging.error(f"Insufficient data: only {len(data)} days received")
#             raise ValueError(f"Insufficient trading data for {ticker}. Only found {len(data)} days.")
        
#         # Log some basic statistics
#         logging.info(f"First closing price: ${data['Close'].iloc[0]:.2f}")
#         logging.info(f"Last closing price: ${data['Close'].iloc[-1]:.2f}")
#         logging.info(f"Average volume: {data['Volume'].mean():.0f}")
            
#         return data
        
#     except Exception as e:
#         logging.error(f"Error in get_stock_data: {str(e)}")
#         print(f"❌ Error downloading stock data: {str(e)}")
#         sys.exit(1)

# def create_price_graph(data, ticker_symbol, output_path):
#     """Create and save price graph"""
#     logging.info(f"Creating price graph for {ticker_symbol}")
    
#     try:
#         plt.figure(figsize=(15, 8))
        
#         # Plot daily closing prices
#         plt.plot(data.index, data['Close'], label=f'{ticker_symbol} Price', color='blue', linewidth=2)
#         logging.info("Added price line to graph")
        
#         # Add volume bars with reference day highlighted
#         ax2 = plt.gca().twinx()
#         for i, (date, volume) in enumerate(data['Volume'].items()):
#             if i == len(data) // 2:  # Reference day (middle of the range)
#                 color = 'orange'
#                 alpha = 0.6
#             else:
#                 color = 'gray'
#                 alpha = 0.3
#             ax2.bar(date, volume, alpha=alpha, color=color)
        
#         ax2.set_ylabel('Volume', color='gray')
#         logging.info("Added volume bars to graph with reference day highlighted")
        
#         # Formatting
#         plt.title(f'{ticker_symbol} Stock Price and Volume - Trading Analysis\nReference Date: {data.index[len(data)//2].strftime("%Y-%m-%d")}', 
#                  fontsize=14, pad=20)
#         plt.gca().set_xlabel('Date', fontsize=12)
#         plt.gca().set_ylabel('Price ($)', fontsize=12)
#         plt.grid(True, linestyle='--', alpha=0.7)
        
#         # Format x-axis dates
#         plt.gcf().autofmt_xdate()
#         date_formatter = DateFormatter("%Y-%m-%d")
#         plt.gca().xaxis.set_major_formatter(date_formatter)
        
#         # Add price annotations
#         start_price = data['Close'].iloc[0]
#         end_price = data['Close'].iloc[-1]
#         ref_price = data['Close'].iloc[len(data)//2]
#         price_change = ((end_price - start_price) / start_price) * 100
        
#         plt.annotate(f'Start: ${start_price:.2f}', 
#                     xy=(data.index[0], start_price),
#                     xytext=(10, 10), textcoords='offset points',
#                     bbox=dict(boxstyle='round,pad=0.5', fc='lightgreen', alpha=0.5),
#                     arrowprops=dict(arrowstyle='->'))
        
#         plt.annotate(f'Reference: ${ref_price:.2f}', 
#                     xy=(data.index[len(data)//2], ref_price),
#                     xytext=(10, -20), textcoords='offset points',
#                     bbox=dict(boxstyle='round,pad=0.5', fc='orange', alpha=0.5),
#                     arrowprops=dict(arrowstyle='->'))
        
#         plt.annotate(f'End: ${end_price:.2f}\nChange: {price_change:.1f}%', 
#                     xy=(data.index[-1], end_price),
#                     xytext=(10, 10), textcoords='offset points',
#                     bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
#                     arrowprops=dict(arrowstyle='->'))
#         logging.info("Added price annotations")
        
#         # Add trend line
#         z = np.polyfit(range(len(data.index)), data['Close'], 1)
#         p = np.poly1d(z)
#         plt.plot(data.index, p(range(len(data.index))), "--", color='red', alpha=0.8, label='Trend')
#         logging.info("Added trend line")
        
#         plt.legend(loc='upper left')
#         plt.tight_layout()
        
#         # Ensure output directory exists
#         os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
#         # Save the graph
#         plt.savefig(output_path, dpi=300, bbox_inches='tight')
#         logging.info(f"Saved graph to: {output_path}")
#         plt.close()
        
#     except Exception as e:
#         logging.error(f"Error creating graph: {str(e)}")
#         print(f"❌ Error creating graph: {str(e)}")
#         sys.exit(1)

# def perform_ml_analysis(stock_data):
#     """Perform machine learning analysis on stock data"""
#     logging.info("Starting ML analysis")
    
#     try:
#         # Calculate prices for ML
#         price_start = stock_data['Close'].iloc[0]
#         price_end = stock_data['Close'].iloc[-1]
        
#         logging.info(f"Price range: ${price_start:.2f} to ${price_end:.2f}")
        
#         # Calculate daily returns and volatility
#         daily_returns = stock_data['Close'].pct_change()
#         volatility = daily_returns.std() * np.sqrt(252)  # Annualized volatility
#         logging.info(f"Calculated volatility: {volatility:.2f}%")
        
#         # Prepare data for ML
#         X = np.array(range(len(stock_data))).reshape(-1, 1)
#         y = stock_data['Close'].values
        
#         # Train model
#         logging.info("Training linear regression model")
#         model = LinearRegression()
#         model.fit(X, y)
        
#         # Make prediction
#         next_day = np.array([[len(stock_data)]])
#         prediction = model.predict(next_day)[0]
#         logging.info(f"Predicted next day price: ${prediction:.2f}")
        
#         return {
#             'price_start': price_start,
#             'price_end': price_end,
#             'volatility': volatility,
#             'prediction': prediction,
#             'trend': model.coef_[0]
#         }
        
#     except Exception as e:
#         logging.error(f"Error in ML analysis: {str(e)}")
#         print(f"❌ Error in ML analysis: {str(e)}")
#         sys.exit(1)

# if __name__ == "__main__":
#     logging.info("Starting finance_ml.py script")
    
#     # Check command line arguments
#     if len(sys.argv) < 3:
#         logging.error("Insufficient arguments provided")
#         print("Usage: python finance_ml.py <transcript_path> <ticker_symbol>")
#         sys.exit(1)

#     transcript_path = sys.argv[1]
#     ticker_symbol = sys.argv[2].upper()  # Convert to uppercase
    
#     logging.info(f"Processing request for transcript: {transcript_path}")
#     logging.info(f"Ticker symbol: {ticker_symbol}")
    
#     # Validate inputs
#     if not validate_inputs(transcript_path, ticker_symbol):
#         sys.exit(1)
    
#     try:
#         # Get stock data
#         stock_data = get_stock_data(ticker_symbol)
        
#         # Perform ML analysis
#         results = perform_ml_analysis(stock_data)
        
#         # Print results
#         print(f"\n📊 Stock Analysis for {ticker_symbol}:")
#         print(f"  - Starting Price (First Trading Day): ${results['price_start']:.2f}")
#         print(f"  - Current Price (Last Trading Day): ${results['price_end']:.2f}")
#         print(f"  - Change: ${(results['price_end'] - results['price_start']):.2f} "
#               f"({((results['price_end'] - results['price_start'])/results['price_start'] * 100):.2f}%)")
#         print(f"  - Trading Period Volatility: {results['volatility']:.2f}%")
        
#         print(f"\n🤖 ML Analysis:")
#         print(f"  - Trend Direction: {'Upward' if results['trend'] > 0 else 'Downward'}")
#         print(f"  - Next Trading Day Prediction: ${results['prediction']:.2f}")
#         print(f"  - Predicted Change: ${(results['prediction'] - results['price_end']):.2f} "
#               f"({((results['prediction'] - results['price_end'])/results['price_end'] * 100):.2f}%)")
        
#         # Create and save graph
#         output_folder = os.path.dirname(transcript_path)
#         graph_filename = os.path.splitext(os.path.basename(transcript_path))[0] + "_price.png"
#         graph_path = os.path.join(output_folder, graph_filename)
        
#         create_price_graph(stock_data, ticker_symbol, graph_path)
#         print(f"\n📈 Price graph saved: {graph_path}")
        
#         logging.info("Script completed successfully")
        
#     except Exception as e:
#         logging.error(f"Unexpected error in main: {str(e)}")
#         print(f"❌ An unexpected error occurred: {str(e)}")
#         sys.exit(1)