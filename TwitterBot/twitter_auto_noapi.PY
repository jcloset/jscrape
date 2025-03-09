from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller  # Auto-install ChromeDriver
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Function to introduce random delays to mimic human behavior
def random_delay(min_time=5, max_time=20):  # Increased delay range for better mimicry
    time.sleep(random.uniform(min_time, max_time))

# Install and setup ChromeDriver automatically
chromedriver_autoinstaller.install()
options = Options()
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")  # Spoof user agent
options.add_argument("--disable-blink-features=AutomationControlled")  # Hide automation
options.add_argument("--ignore-certificate-errors")  # Reduce SSL errors

# Remove headless mode for debugging
# options.add_argument("--headless")  # Run without UI

driver = webdriver.Chrome(options=options)
driver.implicitly_wait(25)  # Increased implicit wait time

# Open Twitter
driver.get("https://twitter.com")
random_delay()

# Print current URL for debugging
current_domain = driver.current_url.split("//")[-1].split("/")[0]  # Extract domain from URL
print("Current URL:", driver.current_url)

# Inject cookies (replace with actual values)
cookies = {
    "name": "auth_token",
    "value": "95b970f9ad14b12700001117be33c39ff2cc4a1f",
    "domain": "." + current_domain  # Automatically match the domain
}
driver.add_cookie(cookies)
random_delay()

# Refresh to apply authentication
driver.refresh()
random_delay()
print("Logged into Twitter successfully.")

# Function to dynamically scroll down
def scroll_down():
    body = driver.find_element(By.TAG_NAME, "body")
    for _ in range(random.randint(30, 50)):  # Increased random scroll count
        body.send_keys(Keys.PAGE_DOWN)
        random_delay()

# Function to check if elements exist before interacting
def safe_find_elements(by, value):
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((by, value)))
        return driver.find_elements(by, value)
    except:
        return []

# Function to like tweets
def like_tweets(keyword, count=10):  # Adjusted action count
    driver.get(f"https://twitter.com/search?q={keyword}&src=typed_query")
    random_delay()
    scroll_down()
    
    likes = safe_find_elements(By.XPATH, "//div[@data-testid='like']")
    print(f"Found {len(likes)} tweets to like")
    
    for i in range(min(count, len(likes))):
        try:
            likes[i].click()
            print(f"Liked tweet {i+1}/{count}")
            random_delay()
        except Exception as e:
            print(f"Error liking tweet {i+1}: {e}")

# Function to retweet tweets
def retweet_tweets(keyword, count=5):  # Adjusted action count
    driver.get(f"https://twitter.com/search?q={keyword}&src=typed_query")
    random_delay()
    scroll_down()
    
    retweets = safe_find_elements(By.XPATH, "//div[@data-testid='retweet']")
    print(f"Found {len(retweets)} tweets to retweet")
    
    for i in range(min(count, len(retweets))):
        try:
            retweets[i].click()
            random_delay()
            confirm = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@data-testid='retweetConfirm']"))
            )
            confirm.click()
            print(f"Retweeted tweet {i+1}/{count}")
            random_delay()
        except Exception as e:
            print(f"Error retweeting tweet {i+1}: {e}")

# Function to follow users
def follow_users(keyword, count=5):  # Adjusted action count
    driver.get(f"https://twitter.com/search?q={keyword}&src=typed_query&f=user")
    random_delay()
    scroll_down()
    
    follow_buttons = safe_find_elements(By.XPATH, "//div[@data-testid='follow']")
    print(f"Found {len(follow_buttons)} users to follow")
    
    for i in range(min(count, len(follow_buttons))):
        try:
            follow_buttons[i].click()
            print(f"Followed user {i+1}/{count}")
            random_delay()
        except Exception as e:
            print(f"Error following user {i+1}: {e}")

# Define a list of keywords to search for
keywords = ["findom", "femdom", "paypig", "goddess", "cashmaster"]
random.shuffle(keywords)  # Shuffle keywords for randomness

# Adjusted loop for multiple keywords
for keyword in keywords:
    like_tweets(keyword, count=10)
    random_delay(45, 90)
    retweet_tweets(keyword, count=5)
    random_delay(45, 90)
    follow_users(keyword, count=5)
    random_delay(45, 90)

random_delay(180, 360)  # Extra delay before quitting to mimic human behavior
driver.quit()
print("Task completed.")
