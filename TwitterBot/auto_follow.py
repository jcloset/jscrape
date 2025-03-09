import tweepy
import os
import requests
import time
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
    
    remaining = response.headers.get("x-rate-limit-remaining")
    reset_time = response.headers.get("x-rate-limit-reset")
    
    # Convert reset timestamp to readable format
    if reset_time:
        reset_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(reset_time)))
    
    print("Rate Limit Remaining:", remaining)
    print("Rate Limit Resets At:", reset_time)
    
    return int(remaining) if remaining is not None else 0, reset_time

# Auto-follow function with rate limit handling
def auto_follow():
    remaining, reset_time = check_rate_limit()
    
    if remaining == 0:
        print(f"❌ Rate limit exceeded. Waiting until {reset_time}...")
        time.sleep(15 * 60)  # Wait 15 minutes before retrying
        return
    
    print("🔍 Searching for tweets with keyword: findom")
    try:
        tweets = client.search_recent_tweets(query="findom", max_results=5)
        
        if not tweets.data:
            print("❌ No tweets found.")
            return
        
        for tweet in tweets.data:
            user_id = tweet.author_id
            try:
                api.create_friendship(user_id=user_id)
                print(f"👤 Followed user: {user_id}")
                time.sleep(120)  # Wait 2 minutes per follow to avoid rate limits
            except tweepy.errors.Forbidden:
                print(f"❌ Cannot follow {user_id} (Account protected or rate-limited)")
    except tweepy.errors.TooManyRequests:
        print("❌ Error: 429 Too Many Requests - Waiting 15 minutes...")
        time.sleep(15 * 60)

# Run the auto-follow function
auto_follow()
