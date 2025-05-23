import streamlit as st
import pandas as pd
from datetime import datetime
from chatbot import ask_gemini
import streamlit.components.v1 as components
import json

# Load CSV
df = pd.read_csv('data/tsla.csv')

# Preprocess
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['Support'] = df['Support'].apply(eval)
df['Resistance'] = df['Resistance'].apply(eval)

# Prepare data for chart
chart_data = []
for _, row in df.iterrows():
    try:
        # Handle support values - use the first value if available
        support_values = row['Support'] if isinstance(row['Support'], list) else []
        support_value = float(support_values[0]) if support_values else None
        
        # Handle resistance values - use the first value if available
        resistance_values = row['Resistance'] if isinstance(row['Resistance'], list) else []
        resistance_value = float(resistance_values[0]) if resistance_values else None
        
        # Ensure all price values are valid numbers
        open_price = float(row['open'])
        close_price = float(row['close'])
        low_price = float(row['low'])
        high_price = float(row['high'])
        volume = float(row['volume'])
        
        chart_data.append({
            'timestamp': row['timestamp'].strftime('%Y-%m-%d'),
            'ohlc': [open_price, close_price, low_price, high_price],
            'volume': volume,
            'support': support_value,
            'resistance': resistance_value,
            'direction': row['direction'] if pd.notna(row['direction']) else None
        })
    except (ValueError, TypeError, IndexError) as e:
        print(f"Error processing row {row['timestamp']}: {str(e)}")
        continue

# Streamlit layout
st.set_page_config(layout="wide")

tab1, tab2 = st.tabs(["📈 TSLA Chart", "🤖 Gemini Chatbot"])

with tab1:
    st.header("Interactive TSLA Chart")
    # Pass data to the chart component
    components.html(
        f"""
        <div id="chart-data" style="display: none;">{json.dumps(chart_data)}</div>
        {open("chart_component.html").read()}
        """,
        height=700
    )

with tab2:
    st.header("Gemini-powered TSLA Chatbot")
    question = st.text_input("Ask a question about the stock data:")
    if question:
        st.write(ask_gemini(question, df))
