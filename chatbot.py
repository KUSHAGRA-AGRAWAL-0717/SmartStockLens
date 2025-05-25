import google.generativeai as genai
import os
# from dotenv import load_dotenv
import time
import pandas as pd
import re

# Load environment variables from .env file
# load_dotenv()

# Get API key from environment variable
# api_key = os.getenv('GOOGLE_API_KEY')
# if not api_key:
#     raise ValueError("Please set the GOOGLE_API_KEY environment variable")

# # Configure the Gemini API
# genai.configure(api_key=api_key)

import streamlit as st
import google.generativeai as genai

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])


def calculate_bullish_days(df, year=None):
    """
    Calculate the number of bullish days in the dataset, optionally filtered by year.
    A bullish day is defined as a day where the closing price is higher than the opening price.
    
    Args:
        df (pd.DataFrame): DataFrame containing OHLC data
        year (int, optional): Year to filter the data. If None, calculates for all years.
        
    Returns:
        tuple: (total_bullish_days, total_days, bullish_percentage)
    """
    # Convert timestamp to datetime if it's not already
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Filter by year if specified
    if year is not None:
        df = df[df['timestamp'].dt.year == year]
    
    # Calculate bullish days
    df['is_bullish'] = df['close'] > df['open']
    total_days = len(df)
    total_bullish = df['is_bullish'].sum()
    bullish_percentage = (total_bullish / total_days * 100) if total_days > 0 else 0
    
    return total_bullish, total_days, bullish_percentage


def extract_year_from_prompt(prompt):
    """
    Extract year from a prompt using regex.
    Returns None if no year is found.
    """
    year_match = re.search(r'20\d{2}', prompt)
    return int(year_match.group()) if year_match else None


def ask_gemini(prompt, df):
    try:
        # Check if the prompt is about bullish days
        if 'bullish' in prompt.lower() and 'day' in prompt.lower():
            year = extract_year_from_prompt(prompt)
            total_bullish, total_days, bullish_percentage = calculate_bullish_days(df, year)
            
            if year:
                response = f"In {year}, TSLA had {total_bullish} bullish days out of {total_days} trading days, representing {bullish_percentage:.2f}% of all trading days."
            else:
                response = f"TSLA had {total_bullish} bullish days out of {total_days} trading days, representing {bullish_percentage:.2f}% of all trading days."
            
            return response
        
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
