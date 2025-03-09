import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import numpy as np
import openai
import os
from dotenv import load_dotenv

# Load API Key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
def chatgpt_query(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a financial analyst providing stock market insights."},
            {"role": "user", "content": prompt}
        ]
    )
    return response["choices"][0]["message"]["content"]# Step 1: Fetch Stock Data
def fetch_stock_data(ticker, period="1y"):
    stock = yf.Ticker(ticker)
    data = stock.history(period=period)
    data['Date'] = data.index
    return data

# Step 2: Calculate Moving Averages
def calculate_moving_averages(data, short_window=20, long_window=50):
    data['Short_MA'] = data['Close'].rolling(window=short_window).mean()
    data['Long_MA'] = data['Close'].rolling(window=long_window).mean()
    return data

# Step 3: Visualize Stock Data
def visualize_stock_data(data, ticker, short_window, long_window):
    plt.figure(figsize=(12, 6))
    plt.plot(data['Date'], data['Close'], label='Closing Price', color='blue')
    plt.plot(data['Date'], data['Short_MA'], label=f'{short_window}-Day MA', color='orange')
    plt.plot(data['Date'], data['Long_MA'], label=f'{long_window}-Day MA', color='green')
    plt.title(f'{ticker} Stock Price Analysis')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.grid()
    plt.show()

# Step 4: Predict Future Prices with Linear Regression
def predict_future_prices(data, days_to_predict=10):
    data['Days'] = np.arange(len(data))
    X = data['Days'].values.reshape(-1, 1)
    y = data['Close'].values.reshape(-1, 1)
    
    model = LinearRegression()
    model.fit(X, y)
    
    future_days = np.arange(len(data), len(data) + days_to_predict).reshape(-1, 1)
    predictions = model.predict(future_days)
    
    return future_days, predictions

# Step 5: Visualize Predictions
def visualize_predictions(data, future_days, predictions, ticker):
    plt.figure(figsize=(12, 6))
    plt.plot(data['Days'], data['Close'], label='Historical Prices', color='blue')
    plt.plot(future_days, predictions, label='Predicted Prices', color='red', linestyle='--')
    plt.title(f'{ticker} Stock Price Prediction')
    plt.xlabel('Days')
    plt.ylabel('Price')
    plt.legend()
    plt.grid()
    plt.show()

# Step 6: Compare Two Stocks
def compare_stocks(ticker1, ticker2, period="1y"):
    data1 = fetch_stock_data(ticker1, period)
    data2 = fetch_stock_data(ticker2, period)
    
    plt.figure(figsize=(12, 6))
    plt.plot(data1['Date'], data1['Close'], label=f'{ticker1} Closing Price', color='blue')
    plt.plot(data2['Date'], data2['Close'], label=f'{ticker2} Closing Price', color='red')
    plt.title(f'Comparison of {ticker1} vs {ticker2}')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.grid()
    plt.show()

# Step 7: Predict Top Mover from Top 25 Stocks
def predict_top_mover():
    top_25_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "BRK-B", "V", "JNJ",
                       "WMT", "JPM", "PG", "XOM", "MA", "HD", "ABBV", "PFE", "KO", "PEP",
                       "MRK", "COST", "DIS", "NFLX", "MCD"]
    
    max_change = 0
    top_stock = ""
    
    for ticker in top_25_tickers:
        try:
            data = fetch_stock_data(ticker, "1mo")
            if len(data) > 10:
                future_days, predictions = predict_future_prices(data, days_to_predict=5)
                change = (predictions[-1] - predictions[0]) / predictions[0] * 100
                
                if change > max_change:
                    max_change = change
                    top_stock = ticker
        except:
            continue
    
    print(f'The predicted top mover in the next 5 days is {top_stock} with an expected change of {max_change:.2f}%')

# Main Program
if __name__ == "__main__":
    ticker = input("Enter the stock ticker (e.g., AAPL, TSLA): ").upper()
    period = input("Enter the time period for historical data (e.g., 1y, 6mo): ").lower()
    short_window = int(input("Enter the short moving average window (e.g., 20): "))
    long_window = int(input("Enter the long moving average window (e.g., 50): "))
    days_to_predict = int(input("Enter the number of days to predict (e.g., 10): "))
    
    data = fetch_stock_data(ticker, period)
    data = calculate_moving_averages(data, short_window, long_window)
    
    visualize_stock_data(data, ticker, short_window, long_window)
    
    future_days, predictions = predict_future_prices(data, days_to_predict)
    visualize_predictions(data, future_days, predictions, ticker)
    
    chatgpt_analysis = chatgpt_query(f"Provide a financial analysis for {ticker} including trends and investment insights.")
    print(f"\nChatGPT Analysis:\n{chatgpt_analysis}\n")
    
    compare = input("Would you like to compare this stock with another? (yes/no): ").lower()
    if compare == "yes":
        ticker2 = input("Enter the second stock ticker: ").upper()
        compare_stocks(ticker, ticker2, period)
    
    predict_top_mover()
    print("Analysis complete. Have a great trading day!")
