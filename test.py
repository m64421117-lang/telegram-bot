import requests

BOT_TOKEN = "7999213986:AAE4i33rKw3wfvFs7ITxh3Cx4xCGUyjFzec"
CHAT_ID = "1990112196"

message = "✅ Test message from your Telegram bot!"

response = requests.get(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    params={"chat_id": CHAT_ID, "text": message}
)

print(response.status_code)
print(response.text)
