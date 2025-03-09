import tweepy
import os
import requests
import time
import threading
import gspread
import logging
import csv
import json
from datetime import datetime, timezone
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, render_template_string, Response, jsonify
from textblob import TextBlob  # For sentiment analysis

# ---------------------------- Sentry Setup ----------------------------
import sentry_sdk
from sentry_sdk.integrations.gcp import GcpIntegration

sentry_sdk.init(
    dsn="https://e73caf746bcfb35db64c01cf34d5cf5f@o4508916071071744.ingest.us.sentry.io/4508916079722496",
    integrations=[GcpIntegration()],
    send_default_pii=True,
    traces_sample_rate=1.0,
    _experiments={
        "continuous_profiling_auto_start": True,
    },
)
logging.info("Sentry is initialized.")

# ---------------------------- Additional Imports for Analytics ----------------------------
from prometheus_client import start_http_server, Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# ---------------------------- Logging Setup ----------------------------
# Updated logging configuration with an absolute path to the log file.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("C:/Users/Wende/TwitterBot/app.log", mode="a")
    ]
)
logger = logging.getLogger(__name__)

# ---------------------------- Audit Logging Function ----------------------------
def audit_action(action, details):
    """Log audit actions to audit.log."""
    with open("audit.log", "a") as audit_file:
        audit_file.write(f"{datetime.now(timezone.utc).isoformat()} - {action} - {details}\n")

logger.info("Main script started - test message.")
for handler in logger.handlers:
    if hasattr(handler, 'flush'):
        handler.flush()

# ---------------------------- Load Environment Variables ----------------------------
load_dotenv(dotenv_path=r"C:\Users\Wende\TwitterBot\.env")
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("ACCESS_SECRET")
BEARER_TOKEN = os.getenv("BEARER_TOKEN")

# ---------------------------- Initialize Tweepy Clients ----------------------------
client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_SECRET
)
auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth)

# ---------------------------- Google Sheets Setup ----------------------------
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDENTIALS_FILE = "credentials.json"  # Ensure this file is in your project directory
SPREADSHEET_KEY = "1Mlwg7cNCKqo7NrsRLrZcGI9g08pKrAxHxnuUuN5rKv0"  # Your spreadsheet key
credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPE)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key(SPREADSHEET_KEY).sheet1
logger.info("Successfully opened the sheet: %s", sheet.title)

# ---------------------------- Global Metrics (for in-app use) ----------------------------
metrics = {
    'tweets_processed': 0,
    'users_followed': 0,
    'tweets_liked': 0,
    'tweets_retweeted': 0,
    'tweets_replied': 0,
    'duplicates': 0,
    'errors': 0,
    'tweets_positive': 0,
    'tweets_negative': 0,
    'tweets_neutral': 0
}

# ---------------------------- Prometheus Metrics ----------------------------
PROM_TWEETS_PROCESSED = Counter('tweets_processed', 'Number of tweets processed')
PROM_USERS_FOLLOWED = Counter('users_followed', 'Number of users followed')
PROM_TWEETS_LIKED = Counter('tweets_liked', 'Number of tweets liked')
PROM_TWEETS_RETWEETED = Counter('tweets_retweeted', 'Number of tweets retweeted')
PROM_TWEETS_REPLIED = Counter('tweets_replied', 'Number of tweets replied to')
PROM_DUPLICATES = Counter('duplicates', 'Number of duplicate tweets skipped')
PROM_ERRORS = Counter('errors', 'Number of errors encountered')
PROM_API_LATENCY = Histogram('api_latency_seconds', 'Latency for API calls')
PROM_TWEETS_POSITIVE = Counter('tweets_positive', 'Number of positive tweets')
PROM_TWEETS_NEGATIVE = Counter('tweets_negative', 'Number of negative tweets')
PROM_TWEETS_NEUTRAL  = Counter('tweets_neutral',  'Number of neutral tweets')

# ---------------------------- Rate Limit Settings ----------------------------
RATE_LIMIT_THRESHOLD = 3

# ---------------------------- Utility Functions ----------------------------
def check_rate_limit():
    url = "https://api.twitter.com/2/tweets/search/recent"
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    start_time = time.time()
    response = requests.get(url, headers=headers)
    duration = time.time() - start_time
    PROM_API_LATENCY.observe(duration)
    remaining = response.headers.get("x-rate-limit-remaining")
    reset_time = response.headers.get("x-rate-limit-reset")
    if reset_time:
        reset_time = int(reset_time)
        readable_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(reset_time))
    else:
        readable_time = "Unknown"
    logger.info("Rate Limit Remaining: %s, Resets At: %s", remaining, readable_time)
    return int(remaining) if remaining is not None else 0, reset_time

def wait_until_reset(reset_time):
    current_time = int(time.time())
    wait_time = reset_time - current_time
    if wait_time > 0:
        logger.info("Waiting %d seconds until rate limit resets...", wait_time)
        time.sleep(wait_time)

def send_notification(message):
    # Placeholder for sending notifications (email, Slack, etc.)
    logger.info("Notification: %s", message)

def is_duplicate(profile_url):
    try:
        existing = sheet.col_values(1)  # Get all values from the first column
        return profile_url in existing
    except Exception as e:
        logger.error("Error checking duplicate: %s", e)
        return False

def save_to_google_sheets(profile_url):
    if is_duplicate(profile_url):
        logger.info("Duplicate found, not saving: %s", profile_url)
        metrics['duplicates'] += 1
        PROM_DUPLICATES.inc()
    else:
        try:
            sheet.append_row([profile_url])
            logger.info("Saved to Google Sheets: %s", profile_url)
            audit_action("SAVE", f"Saved {profile_url} to Google Sheets")
        except Exception as e:
            logger.error("Error saving to Google Sheets: %s", e)
            metrics['errors'] += 1
            PROM_ERRORS.inc()

def exponential_backoff(func, *args, **kwargs):
    max_retries = 5
    delay = 10
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error("Error in %s: %s. Retrying in %d seconds...", func.__name__, e, delay)
            metrics['errors'] += 1
            PROM_ERRORS.inc()
            time.sleep(delay)
            delay *= 2
    logger.error("Max retries reached for %s.", func.__name__)
    return None

def store_metrics_to_csv():
    """Store metrics to a CSV file for historical analysis."""
    fieldnames = list(metrics.keys())
    file_exists = os.path.isfile("metrics_history.csv")
    try:
        with open("metrics_history.csv", mode="a", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["timestamp"] + fieldnames)
            if not file_exists:
                writer.writeheader()
            row = {"timestamp": datetime.now(timezone.utc).isoformat()}
            row.update(metrics)
            writer.writerow(row)
        logger.info("Stored metrics to CSV.")
    except Exception as e:
        logger.error("Error storing metrics to CSV: %s", e)

def read_metrics_history():
    """Read the stored CSV metrics and return as JSON."""
    history = []
    if os.path.isfile("metrics_history.csv"):
        try:
            with open("metrics_history.csv", mode="r", newline="") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    history.append(row)
        except Exception as e:
            logger.error("Error reading metrics CSV: %s", e)
    return history

# ---------------------------- Additional Feature: User Segmentation ----------------------------
def segment_user(user_id):
    """Segment a user based on their follower count."""
    try:
        user = api.get_user(user_id=user_id)
        followers = user.followers_count
        if followers > 10000:
            segment = "influencer"
        elif followers > 1000:
            segment = "established"
        else:
            segment = "normal"
        logger.info("User %s segmented as: %s", user_id, segment)
        audit_action("SEGMENT", f"User {user_id} with {followers} followers segmented as {segment}")
        return segment
    except Exception as e:
        logger.error("Error segmenting user %s: %s", user_id, e)
        return "unknown"

# ---------------------------- Automated Reporting ----------------------------
def automated_reporting():
    error_threshold = 5
    if metrics['errors'] > error_threshold:
        send_notification(f"High error rate detected: {metrics['errors']} errors")
        audit_action("REPORT", f"Automated report: {metrics['errors']} errors detected")

# ---------------------------- Dynamic Scheduling Placeholder ----------------------------
def adjust_scheduling_based_on_rate_limit():
    # Placeholder: Here you could adjust APScheduler job intervals based on rate limit consumption.
    remaining, _ = check_rate_limit()
    logger.info("Dynamic scheduling check: %d requests remaining", remaining)
    # Example: If remaining is very low, you might extend the interval of certain jobs.
    return

# ---------------------------- Twitter Bot Functions ----------------------------
def twitter_scraper():
    logger.info("twitter_scraper() triggered.")
    for handler in logger.handlers:
        if hasattr(handler, 'flush'):
            handler.flush()
            
    remaining, reset_time = check_rate_limit()
    if remaining < RATE_LIMIT_THRESHOLD:
        logger.info("Low rate limit, waiting until reset to be extra cautious.")
        for handler in logger.handlers:
            if hasattr(handler, 'flush'):
                handler.flush()
        wait_until_reset(reset_time)
        return

    query = "findom lang:en -is:retweet"
    logger.info("Searching for tweets with query: %s", query)
    for handler in logger.handlers:
        if hasattr(handler, 'flush'):
            handler.flush()

    try:
        tweets = exponential_backoff(client.search_recent_tweets, query=query, max_results=10, user_fields=["username", "text"])
        if not tweets or not tweets.data:
            logger.info("No tweets found.")
            for handler in logger.handlers:
                if hasattr(handler, 'flush'):
                    handler.flush()
            return
        for tweet in tweets.data:
            polarity = TextBlob(tweet.text).sentiment.polarity
            if polarity > 0.1:
                sentiment = "positive"
                metrics['tweets_positive'] += 1
                PROM_TWEETS_POSITIVE.inc()
            elif polarity < -0.1:
                sentiment = "negative"
                metrics['tweets_negative'] += 1
                PROM_TWEETS_NEGATIVE.inc()
            else:
                sentiment = "neutral"
                metrics['tweets_neutral'] += 1
                PROM_TWEETS_NEUTRAL.inc()
            logger.info("Tweet %s sentiment: %s (polarity: %.2f)", tweet.id, sentiment, polarity)
            for handler in logger.handlers:
                if hasattr(handler, 'flush'):
                    handler.flush()
            
            profile_url = f"https://twitter.com/i/user/{tweet.author_id}"
            save_to_google_sheets(profile_url)
            metrics['tweets_processed'] += 1
            PROM_TWEETS_PROCESSED.inc()
            
            try:
                api.create_favorite(tweet.id)
                logger.info("Liked tweet: %s", tweet.id)
                metrics['tweets_liked'] += 1
                PROM_TWEETS_LIKED.inc()
                audit_action("LIKE", f"Tweet {tweet.id} liked")
            except Exception as e:
                logger.error("Error liking tweet %s: %s", tweet.id, e)
            try:
                api.retweet(tweet.id)
                logger.info("Retweeted tweet: %s", tweet.id)
                metrics['tweets_retweeted'] += 1
                PROM_TWEETS_RETWEETED.inc()
                audit_action("RETWEET", f"Tweet {tweet.id} retweeted")
            except Exception as e:
                logger.error("Error retweeting tweet %s: %s", tweet.id, e)
            try:
                reply_text = "Interesting tweet!"
                api.update_status(status=reply_text, in_reply_to_status_id=tweet.id, auto_populate_reply_metadata=True)
                logger.info("Replied to tweet: %s", tweet.id)
                metrics['tweets_replied'] += 1
                PROM_TWEETS_REPLIED.inc()
                audit_action("REPLY", f"Replied to tweet {tweet.id}")
            except Exception as e:
                logger.error("Error replying to tweet %s: %s", tweet.id, e)
            segment_user(tweet.author_id)
        logger.info("Finished processing batch; pausing briefly before next call.")
        for handler in logger.handlers:
            if hasattr(handler, 'flush'):
                handler.flush()
        time.sleep(10)
    except tweepy.errors.TooManyRequests:
        logger.error("Too Many Requests - waiting for reset")
        for handler in logger.handlers:
            if hasattr(handler, 'flush'):
                handler.flush()
        wait_until_reset(reset_time)

    # Advanced tweet filtering: English tweets only, excluding retweets.
    query = "findom lang:en -is:retweet"
    logger.info("Searching for tweets with query: %s", query)

    try:
        tweets = exponential_backoff(client.search_recent_tweets, query=query, max_results=10, user_fields=["username", "text"])
        if not tweets or not tweets.data:
            logger.info("No tweets found.")
            return
        for tweet in tweets.data:
            # Perform sentiment analysis on tweet text.
            polarity = TextBlob(tweet.text).sentiment.polarity
            if polarity > 0.1:
                sentiment = "positive"
                metrics['tweets_positive'] += 1
                PROM_TWEETS_POSITIVE.inc()
            elif polarity < -0.1:
                sentiment = "negative"
                metrics['tweets_negative'] += 1
                PROM_TWEETS_NEGATIVE.inc()
            else:
                sentiment = "neutral"
                metrics['tweets_neutral'] += 1
                PROM_TWEETS_NEUTRAL.inc()
            logger.info("Tweet %s sentiment: %s (polarity: %.2f)", tweet.id, sentiment, polarity)
            
            profile_url = f"https://twitter.com/i/user/{tweet.author_id}"
            save_to_google_sheets(profile_url)
            metrics['tweets_processed'] += 1
            PROM_TWEETS_PROCESSED.inc()
            
            # Additional Twitter actions: like, retweet, reply.
            try:
                api.create_favorite(tweet.id)
                logger.info("Liked tweet: %s", tweet.id)
                metrics['tweets_liked'] += 1
                PROM_TWEETS_LIKED.inc()
                audit_action("LIKE", f"Tweet {tweet.id} liked")
            except Exception as e:
                logger.error("Error liking tweet %s: %s", tweet.id, e)
            try:
                api.retweet(tweet.id)
                logger.info("Retweeted tweet: %s", tweet.id)
                metrics['tweets_retweeted'] += 1
                PROM_TWEETS_RETWEETED.inc()
                audit_action("RETWEET", f"Tweet {tweet.id} retweeted")
            except Exception as e:
                logger.error("Error retweeting tweet %s: %s", tweet.id, e)
            try:
                reply_text = "Interesting tweet!"
                api.update_status(status=reply_text, in_reply_to_status_id=tweet.id, auto_populate_reply_metadata=True)
                logger.info("Replied to tweet: %s", tweet.id)
                metrics['tweets_replied'] += 1
                PROM_TWEETS_REPLIED.inc()
                audit_action("REPLY", f"Replied to tweet {tweet.id}")
            except Exception as e:
                logger.error("Error replying to tweet %s: %s", tweet.id, e)
            # Optionally segment user based on follower count.
            segment_user(tweet.author_id)
        logger.info("Finished processing batch; pausing briefly before next call.")
        time.sleep(10)
    except tweepy.errors.TooManyRequests:
        logger.error("Too Many Requests - waiting for reset")
        wait_until_reset(reset_time)

def auto_follow():
    remaining, reset_time = check_rate_limit()
    if remaining < RATE_LIMIT_THRESHOLD:
        logger.info("Low rate limit, waiting until reset to be extra cautious.")
        wait_until_reset(reset_time)
        return
    logger.info("Searching for tweets to follow users")
    try:
        tweets = exponential_backoff(client.search_recent_tweets, query="findom lang:en -is:retweet", max_results=5)
        if not tweets or not tweets.data:
            logger.info("No tweets found.")
            return
        for tweet in tweets.data:
            user_id = tweet.author_id
            try:
                api.create_friendship(user_id=user_id)
                logger.info("Followed user: %s", user_id)
                metrics['users_followed'] += 1
                PROM_USERS_FOLLOWED.inc()
                audit_action("FOLLOW", f"Followed user {user_id}")
                time.sleep(300)  # Delay between follow actions.
            except tweepy.errors.Forbidden:
                logger.error("Cannot follow %s (Account protected or rate-limited)", user_id)
            except Exception as e:
                logger.error("Error following user %s: %s", user_id, e)
        time.sleep(90)
    except tweepy.errors.TooManyRequests:
        logger.error("Too Many Requests - waiting for reset")
        wait_until_reset(reset_time)

def auto_unfollow():
    logger.info("Checking for users to unfollow")
    try:
        # Updated to use the new get_friend_ids() method for Tweepy
        friends = api.get_friend_ids()
        for user_id in friends:
            # Placeholder: Insert your actual unfollow criteria here.
            if False:
                api.destroy_friendship(user_id=user_id)
                logger.info("Unfollowed user: %s", user_id)
                audit_action("UNFOLLOW", f"Unfollowed user {user_id}")
            time.sleep(10)
    except Exception as e:
        logger.error("Error in auto_unfollow: %s", e)

# ---------------------------- Flask Web Dashboard ----------------------------
app = Flask(__name__)

@app.route('/')
def dashboard():
    dashboard_html = """
    <html>
        <head>
            <title>Twitter Bot Dashboard</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        </head>
        <body>
            <h1>Twitter Bot Metrics</h1>
            <ul>
                <li>Tweets Processed: {{ tweets_processed }}</li>
                <li>Users Followed: {{ users_followed }}</li>
                <li>Tweets Liked: {{ tweets_liked }}</li>
                <li>Tweets Retweeted: {{ tweets_retweeted }}</li>
                <li>Tweets Replied: {{ tweets_replied }}</li>
                <li>Duplicates Skipped: {{ duplicates }}</li>
                <li>Errors: {{ errors }}</li>
                <li>Positive Tweets: {{ tweets_positive }}</li>
                <li>Negative Tweets: {{ tweets_negative }}</li>
                <li>Neutral Tweets: {{ tweets_neutral }}</li>
            </ul>
            <h2>Prometheus Metrics</h2>
            <pre>{{ prometheus_metrics }}</pre>
            <h2>Historical Metrics</h2>
            <canvas id="historyChart" width="600" height="400"></canvas>
            <script>
              fetch('/history')
                .then(response => response.json())
                .then(data => {
                    const labels = data.map(item => item.timestamp);
                    const tweetData = data.map(item => parseInt(item.tweets_processed));
                    const ctx = document.getElementById('historyChart').getContext('2d');
                    new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: labels,
                            datasets: [{
                                label: 'Tweets Processed Over Time',
                                data: tweetData,
                                borderColor: 'rgba(75, 192, 192, 1)',
                                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                                fill: true
                            }]
                        }
                    });
                });
            </script>
        </body>
    </html>
    """
    prometheus_metrics = generate_latest().decode("utf-8")
    return render_template_string(dashboard_html, prometheus_metrics=prometheus_metrics, **metrics)

@app.route('/metrics')
def metrics_endpoint():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route('/history')
def history_endpoint():
    history = read_metrics_history()
    return jsonify(history)

def run_dashboard():
    app.run(host="0.0.0.0", port=5000)

# ---------------------------- Main Execution ----------------------------
if __name__ == "__main__":
    # Start Prometheus metrics server on a separate thread (optional, as /metrics endpoint is available)
    prometheus_thread = threading.Thread(target=lambda: start_http_server(8000))
    prometheus_thread.daemon = True
    prometheus_thread.start()
    
    # Setup scheduler for periodic tasks with max_instances set to 2
    scheduler = BackgroundScheduler()
    scheduler.add_job(twitter_scraper, 'interval', minutes=5, id='twitter_scraper', max_instances=2)
    scheduler.add_job(auto_follow, 'interval', minutes=10, id='auto_follow', max_instances=2)
    scheduler.add_job(auto_unfollow, 'interval', hours=1, id='auto_unfollow', max_instances=2)
    scheduler.add_job(store_metrics_to_csv, 'interval', minutes=15, id='store_metrics', max_instances=2)
    scheduler.add_job(automated_reporting, 'interval', hours=1, id='automated_reporting', max_instances=2)
    scheduler.add_job(adjust_scheduling_based_on_rate_limit, 'interval', minutes=10, id='dynamic_scheduling', max_instances=2)
    scheduler.start()
    
    # Start the Flask dashboard in a separate thread
    dashboard_thread = threading.Thread(target=run_dashboard)
    dashboard_thread.daemon = True
    dashboard_thread.start()
    
    logger.info("Scheduler and dashboard started. Bot is running.")
    
    try:
        while True:
            time.sleep(60)
            # Periodically flush logger handlers to ensure logs are written out
            for handler in logger.handlers:
                if hasattr(handler, 'flush'):
                    handler.flush()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Bot stopped.")
