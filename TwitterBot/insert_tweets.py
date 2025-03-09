import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ---------------- Setup Google Sheets API ---------------- #
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDENTIALS_FILE = "credentials.json"  # Ensure this file is in your project directory
SPREADSHEET_KEY = "1S0TTmWvc2ki6xKsoHPM4ADu0n94GML7EgynU46AwtIU"  # Replace with your actual Google Sheet key

# Authenticate with Google Sheets
credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPE)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key(SPREADSHEET_KEY).sheet1

# ---------------- List of 50 Dominant Female Tweets ---------------- #
dominant_tweets = [
    "👑 Worship Me properly—tribute first, words later. #Findom #ObeyMe",
    "💰 A true pay pig doesn’t ask questions. He just pays. Tribute NOW.",
    "🐷 Every coin you earn is mine. Send what belongs to Me. #FindomGoddess",
    "🔥 Weak men exist to serve strong women. Pay up or stay pathetic.",
    "💎 I’m not expensive—you’re just broke. Tribute & prove your worth.",
    "🔑 Your paycheck, My playground. Unlock your wallet & let Me drain you.",
    "💳 Real subs pay without hesitation. Show your devotion—tribute NOW.",
    "💅 You work hard so I don’t have to. Send your paycheck & know your place.",
    "🏦 Every dollar you own should already have My name on it. Fix that now.",
    "💵 The best feeling in the world? Watching a pig beg Me to take his money.",
    "🎀 Kneel, obey, and pay. That’s all you’re good for, loser. Tribute now.",
    "🥂 Want My attention? Buy it. Want My love? You can’t afford it. Pay.",
    "👠 I step on weak men & take everything they have. Tribute or be ignored.",
    "🔗 True submission starts with financial surrender. Pay up, piggy.",
    "💖 My existence is your privilege. The least you can do is pay for it.",
    "🛑 No free attention. No free messages. Just TRIBUTE & silence. #ObeyMe",
    "💎 A queen like Me shouldn’t have to ask. Send & impress Me. #FindomLife",
    "🥀 Weak men pay. Strong women take. You know your role. Tribute now.",
    "💼 Your job is to make money. My job is to take it. Do your part.",
    "💰 Watching your balance drop gives Me power. Send your sacrifice.",
    "🔮 Obey, pay, repeat. It’s that simple, little pay pig. #FindomFantasy",
    "👛 My handbag is hungry & your wallet is full. Let’s fix that mistake.",
    "🔥 Don’t be shy—empty your bank account like a good little servant.",
    "💳 If you truly serve Me, prove it financially. Tribute now.",
    "🏆 Only the weakest men resist. Give in, send, and surrender.",
    "🖤 You belong to Me. Your money belongs to Me. Accept your fate.",
    "💄 If you can’t afford Me, you’re irrelevant. Tribute or disappear.",
    "🌹 Nothing gets Me going like a loser draining himself for Me. Tribute!",
    "🥵 Worship is nice, but payment is better. Send & kneel properly.",
    "💌 Love letters? Boring. Money transfers? That’s the real devotion.",
    "🐷 The sound of a pig whining while paying? Music to My ears.",
    "🛍️ Every tribute funds My luxury. Be useful & make My life easier.",
    "🕶️ The only thing I care about? Your wallet & how fast you empty it.",
    "💵 A real pay pig doesn’t ask—he just sends. Do better. Pay now.",
    "👑 I deserve your money. You don’t. Hand it over, little loser.",
    "🔞 Pay or stay silent. That’s how My world works. Obey Me.",
    "💰 You exist for one reason—to finance My desires. Send now.",
    "🛑 Broke men don’t belong in My mentions. Pay up or get blocked.",
    "🔥 No excuses. No delays. Just send & prove your loyalty. #FindomAddict",
    "💳 Want My time? Pay first. Want My attention? Double it. Tribute.",
    "💎 Every queen deserves a kingdom funded by her pay pigs. Send NOW.",
    "👠 Crawl into My DMs only if you’re bringing cash. No free chat.",
    "🔑 Obedience is money. I own your wallet now—pay tribute.",
    "💖 If you love Me, you pay. If you worship Me, you pay MORE.",
    "💼 Your hard work = My luxury. Accept it, embrace it, and PAY.",
    "👛 What’s sexier than a man going broke for Me? NOTHING. Tribute NOW.",
    "💎 Be useful for once in your life—send money and impress Me.",
    "🛑 I only talk to men who tribute first. Pay or be ignored forever.",
    "💰 No free attention, no freebies, no exceptions. Send & obey.",
    "🥂 I live like a goddess because My pigs fund it. Be next. Tribute."  
]

# ---------------- Upload Tweets to Google Sheets ---------------- #
try:
    sheet.update("A1", [[tweet] for tweet in dominant_tweets])  # Insert tweets into Column A
    print("✅ Dominant Goddess Tweets successfully added to Google Sheet.")
except Exception as e:
    print(f"❌ Error updating Google Sheet: {e}")
