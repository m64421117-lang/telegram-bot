import http.client
import json
import os
import requests

STATE_FILE = "state.json"

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"sent_ids": []}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

# Load previous state
state = load_state()
sent_ids = set(state.get("sent_ids", []))

BOT_TOKEN = "7999213986:AAE4i33rKw3wfvFs7ITxh3Cx4xCGUyjFzec"
CHAT_ID = "1990112196"

# --- Fetch data from Sakani API using http.client ---
conn = http.client.HTTPSConnection("sakani.sa")
headersList = {
    "Accept": "*/*",
    "User-Agent": "Thunder Client (https://www.thunderclient.com)"
}
payload = ""

conn.request(
    "GET",
    "/marketplaceApi/search/v3/location?filter[marketplace_purpose]=buy&filter[product_types]=lands&filter[target_segment_info]=beneficiary&filter[land_type]=moh_lands&filter[mode]=maps",
    payload,
    headersList
)

response = conn.getresponse()
result = response.read()
conn.close()

# Parse JSON
try:
    data = json.loads(result.decode("utf-8"))
except json.JSONDecodeError:
    print("Failed to parse JSON from Sakani API")
    data = {"data": []}

# --- Send Telegram messages using requests ---
new_ids = []

for item in data.get("data", []):
    item_id = item.get("id")
    if item_id not in sent_ids:
        attributes = item.get("attributes", {})
        project_name = attributes.get("project_name", "غير معروف")
        min_price = attributes.get("min_non_bene_price", 0)

        # Remove "project_" prefix for the link
        project_number = item_id.replace("project_", "")
        project_link = f"https://sakani.sa/app/land-projects/{project_number}"

        # Telegram message in Arabic
        banner_url = attributes.get("banner_url")  # get image URL from API
        message_text = f"📢 مشروع جديد: {project_name}\n💰 السعر الابتدائي: {min_price}\n🌐 الرابط: {project_link}"

        telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        payload = {
            "chat_id": CHAT_ID,
            "photo": banner_url,
            "caption": message_text
        }

        telegram_resp = requests.post(telegram_url, data=payload)

        if telegram_resp.status_code == 200:
            print(f"✅ Message sent for project ID: {item_id}")
            new_ids.append(item_id)
        else:
            print(f"❌ Failed to send message for project ID: {item_id}. Status code: {telegram_resp.status_code}")

# Update state
if new_ids:
    state["sent_ids"] = list(sent_ids.union(new_ids))
    save_state(state)
    print(f"✅ State updated with project IDs: {new_ids}")
else:
    print("No new projects to send.")
