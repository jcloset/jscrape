from dotenv import load_dotenv
import os

# Debug message
print("Loading .env file...")

# Load environment variables from .env file
load_dotenv()

# Get API keys
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")

# Print API keys to check if they are loaded
print("API Key:", api_key if api_key else "Not Found")
print("API Secret:", api_secret if api_secret else "Not Found")
 
