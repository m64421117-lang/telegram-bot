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

# Load state
state = load_state()
sent_ids = set(state.get("sent_ids", []))

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Fetch data from Sakani API
API_URL = "https://sakani.sa/marketplaceApi/search/v3/location?filter[marketplace_purpose]=buy&filter[product_types]=lands&filter[target_segment_info]=beneficiary&filter[land_type]=moh_lands&filter[mode]=maps"
response = requests.get(API_URL)
data = response.json()

new_ids = []

for item in data.get("data", []):
    item_id = item.get("id")
    if item_id not in sent_ids:
        # Build message
        attributes = item.get("attributes", {})
        project_name = attributes.get("project_name", "Unknown")
        min_price = attributes.get("min_non_bene_price", 0)
        message = f"New project: {project_name}\nStarting price: {min_price}\nLink: https://sakani.sa/"

        # Send Telegram message
        requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            params={"chat_id": CHAT_ID, "text": message}
        )

        # Add to new_ids
        new_ids.append(item_id)

if new_ids:
    # Update state with new sent IDs
    state["sent_ids"] = list(sent_ids.union(new_ids))
    save_state(state)
    print(f"Sent messages for IDs: {new_ids}")
else:
    print("No new projects to send.")
