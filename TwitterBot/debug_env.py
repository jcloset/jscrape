import os
from dotenv import load_dotenv

# Force load the .env file
dotenv_path = r"C:\Users\Wende\TwitterBot\.env"
if os.path.exists(dotenv_path):
    print(f"✅ Found .env file at: {dotenv_path}")
else:
    print("❌ ERROR: .env file not found!")

loaded = load_dotenv(dotenv_path=dotenv_path)

# Debug output
print("✅ .env Loaded:", loaded)
print("🔑 API Key:", os.getenv("API_KEY"))
print("🔒 API Secret:", os.getenv("API_SECRET"))
