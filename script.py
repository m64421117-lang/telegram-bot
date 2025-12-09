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

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(text):
    """Send a message to Telegram."""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
        resp = requests.post(url, data=payload)
        if resp.status_code != 200:
            print("❌ Telegram error:", resp.text)
    except Exception as e:
        print("❌ Failed to send Telegram message:", e)

# --- Fetch Sakani API ---
try:
    conn = http.client.HTTPSConnection("sakani.sa")
    headersList = {
    "Accept": "*/*",
    "User-Agent": "Thunder Client (https://www.thunderclient.com)" 
    }
    conn.request(
        "GET",
        "/marketplaceApi/search/v3/location?filter[marketplace_purpose]=buy&filter[product_types]=lands&filter[target_segment_info]=beneficiary&filter[land_type]=moh_lands&filter[mode]=maps",
        headers=headersList
    )

    response = conn.getresponse()
    result = response.read()
    conn.close()

    try:
        data = json.loads(result.decode("utf-8"))
    except json.JSONDecodeError:
        data = {"data": []}
        send_telegram("⚠️ <b>Bot ran, but API response was invalid or empty.</b>")
        print("❌ JSON decode error.")
        print("Response content:", result.decode("utf-8"))
        raise SystemExit()

except Exception as e:
    send_telegram(f"❌ <b>Bot error fetching Sakani API:</b> {e}")
    raise SystemExit()

# --- Process results ---
new_ids = []
items = data.get("data", [])

if not items:
    send_telegram("ℹ️ <b>Bot run complete — No projects available at this time.</b>")
    print("No items found in API response.")
    raise SystemExit()

else:
    for item in items:
        item_id = item.get("id")
        if item_id not in sent_ids:
            attributes = item.get("attributes", {})
            project_name = attributes.get("project_name", "غير معروف")
            min_price = attributes.get("min_non_bene_price", "غير معروف")
            if min_price == 0: min_price = "غير معروف"
            else: min_price = f"{int(min_price):,} ريال"
            project_number = item_id.replace("project_", "")
            project_link = f"https://sakani.sa/app/land-projects/{project_number}"

            # User-friendly Telegram message
            message_text = (
                f"🏡 <b>{project_name}</b>\n"
                f"💰 السعر الابتدائي: <b>{min_price}</b>\n"
                f"🔗 <a href='{project_link}'>رابط المشروع</a>"
            )

            try:
                telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                payload = {"chat_id": CHAT_ID, "text": message_text, "parse_mode": "HTML"}
                telegram_resp = requests.post(telegram_url, data=payload)

                if telegram_resp.status_code == 200:
                    print(f"✅ Message sent for project ID: {item_id}")
                    new_ids.append(item_id)
                else:
                    print(f"❌ Telegram failed for {item_id}: {telegram_resp.text}")

            except Exception as e:
                print(f"❌ Exception sending Telegram message for {item_id}: {e}")

# --- Save new state and send summary ---
if new_ids:
    state["sent_ids"] = list(sent_ids.union(new_ids))
    save_state(state)
    print("State updated.")
else:
    send_telegram("ℹ️ <b>Bot run complete — No new projects found.</b>")
    print("No new projects.")
