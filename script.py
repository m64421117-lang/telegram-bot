import json
import os
import requests

STATE_FILE = "state.json"

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"sent_ids": []}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# Load previous state
state = load_state()
sent_ids = set(state.get("sent_ids", []))

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Sakani API URL
API_URL = "https://sakani.sa/marketplaceApi/search/v3/location?filter[marketplace_purpose]=buy&filter[product_types]=lands&filter[target_segment_info]=beneficiary&filter[land_type]=moh_lands&filter[mode]=maps"

# Add headers to mimic a real browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

# Fetch data
response = requests.get(API_URL, headers=headers)
print("Status code:", response.status_code)
print("Content preview:", response.text[:500])  # first 500 chars for debugging

# Only parse JSON if response is valid
if response.status_code == 200 and response.text.strip():
    try:
        data = response.json()
    except json.JSONDecodeError:
        print("Failed to parse JSON from API")
        data = {"data": []}
else:
    print("Failed to fetch valid JSON from API")
    data = {"data": []}

# Track new projects
new_ids = []

for item in data.get("data", []):
    item_id = item.get("id")
    if item_id not in sent_ids:
        attributes = item.get("attributes", {})
        project_name = attributes.get("project_name", "Unknown")
        min_price = attributes.get("min_non_bene_price", 0)
        message = f"📢 New project: {project_name}\n💰 Starting price: {min_price}\n🌐 Link: https://sakani.sa/"

        # Send Telegram message
        telegram_response = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            params={"chat_id": CHAT_ID, "text": message}
        )

        if telegram_response.status_code == 200:
            print(f"Sent message for project ID: {item_id}")
            new_ids.append(item_id)
        else:
            print(f"Failed to send message for project ID: {item_id}. Status code: {telegram_response.status_code}")

# Update state
if new_ids:
    state["sent_ids"] = list(sent_ids.union(new_ids))
    save_state(state)
    print(f"Updated state with IDs: {new_ids}")
else:
    print("No new projects to send.")
