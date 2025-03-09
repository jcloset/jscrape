import tweepy
import os
import requests
from dotenv import load_dotenv

# Load API keys
load_dotenv(dotenv_path=r"C:\Users\Wende\TwitterBot\.env")
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("ACCESS_SECRET")
BEARER_TOKEN = os.getenv("BEARER_TOKEN")

# Authenticate
client = tweepy.Client(bearer_token=BEARER_TOKEN, consumer_key=API_KEY, consumer_secret=API_SECRET,
                       access_token=ACCESS_TOKEN, access_token_secret=ACCESS_SECRET)

# Get rate limit status (API v2 does not have get_rate_limit_status())
def check_rate_limit():
    url = "https://api.twitter.com/2/tweets/search/recent"
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    response = requests.get(url, headers=headers)
    
    print("Rate Limit Remaining:", response.headers.get("x-rate-limit-remaining"))
    print("Rate Limit Reset Time:", response.headers.get("x-rate-limit-reset"))

check_rate_limit()
