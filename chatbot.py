import google.generativeai as genai
import os
from dotenv import load_dotenv
import time
import pandas as pd

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    raise ValueError("Please set the GOOGLE_API_KEY environment variable")

# Configure the Gemini API
genai.configure(api_key=api_key)

def ask_gemini(prompt, df):
    try:
        # Calculate key statistics for the entire dataset
        df['is_bullish'] = df['close'] > df['open']
        df['daily_return'] = ((df['close'] - df['open']) / df['open'] * 100)
        
        # Calculate statistics by year
        df['year'] = pd.to_datetime(df['timestamp']).dt.year
        yearly_stats = df.groupby('year').agg({
            'is_bullish': ['count', 'sum'],
            'daily_return': ['mean', 'std', 'min', 'max'],
            'volume': 'mean'
        }).round(2)
        
        # Calculate overall statistics
        total_days = len(df)
        total_bullish = df['is_bullish'].sum()
        avg_daily_return = df['daily_return'].mean()
        max_price = df['high'].max()
        min_price = df['low'].min()
        
        # Prepare comprehensive context
        context = f"""TSLA Stock Data Analysis:

Overall Statistics:
- Total trading days: {total_days}
- Total bullish days: {total_bullish}
- Bullish percentage: {(total_bullish/total_days*100):.2f}%
- Average daily return: {avg_daily_return:.2f}%
- Highest price: ${max_price:.2f}
- Lowest price: ${min_price:.2f}

Yearly Statistics:
{yearly_stats.to_string()}

Sample Data (First 5 and Last 5 days):
{df.head().to_string()}
...
{df.tail().to_string()}

Question: {prompt}

Please analyze the data and provide a detailed answer based on the statistics and trends shown above."""

        # Initialize the model with the flash version for better rate limits
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Generate response with retry logic
        max_retries = 3
        retry_delay = 60  # seconds
        
        for attempt in range(max_retries):
            try:
                response = model.generate_content(context)
                return response.text
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    print(f"Rate limit hit, waiting {retry_delay} seconds before retry...")
                    time.sleep(retry_delay)
                    continue
                raise e
                
    except Exception as e:
        print(f"Detailed error: {str(e)}")
        return f"Error: {str(e)}"
