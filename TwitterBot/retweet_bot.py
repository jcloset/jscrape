import os
import tweepy
import schedule
import time
import logging
from dotenv import load_dotenv
def log_message(message):
    print(message)  # Print in console
    logging.info(message)  # Save to log file

# ✅ Manually enter your API credentials
API_KEY = "C6w6nsr80FrpYJEv2hzUAV4q6"
API_SECRET = "ixzZznRB3JSoUEsEnQCFwwdDllo71R9J847DgpBLfRet68E80t"
ACCESS_TOKEN = "1892896057220354050-m1pyToiWVDNmpSutrn4VwhMgmq2tXF"
ACCESS_SECRET = "XncSzGiO84tNyXaOTn6hZuJVOSpTRQAWFR8g4z4k97QYB"

# ✅ Authenticate with Tweepy API v1.1
auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True)

# ✅ Test Authentication
try:
    user = api.verify_credentials()
    print(f"✅ Authenticated as: {user.screen_name}")
except tweepy.TweepyException as e:
    print(f"❌ Authentication failed: {e}")
    exit()

def engage_with_tweets(keyword, count=10):
    """Searches for tweets using Twitter API v2."""
    try:
        query = f"{keyword} lang:en -is:retweet"
        tweets = api.search_recent_tweets(query=query, max_results=count)

        for tweet in tweets.data:
            tweet_id = tweet["id"]
            tweet_text = tweet["text"]
            user_id = tweet["author_id"]

            api.retweet(tweet_id)
            log_message(f"✅ Retweeted: {tweet_text}")

            api.like(tweet_id)
            log_message("❤️ Liked the tweet!")

            api.follow(user_id)
            log_message(f"🔵 Followed user {user_id}")

    except tweepy.TweepyException as e:
        log_message(f"❌ Error: {e}")


# ✅ Function for Scheduled Tweets
def tweet_scheduled():
    api.update_status("🚀 Stay motivated and achieve your goals! #Success #Motivation")
    log_message("📅 Scheduled tweet posted!")

# ✅ Schedule the Tweet Posting
schedule.every().day.at("12:00").do(tweet_scheduled)

# ✅ Run Automation
if __name__ == "__main__":
    log_message("🚀 Bot Started...")
    engage_with_tweets("networking", count=5)
    
    while True:
        schedule.run_pending()
        time.sleep(60)
