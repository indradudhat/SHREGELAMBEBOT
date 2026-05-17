from flask import Flask, request, jsonify
import anthropic
import requests
import os

app = Flask(__name__)

# ============================
# Keys - Environment Variables થી
# ============================
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")
META_ACCESS_TOKEN = os.environ.get("IGAAONFjtqWB9BZAFpLa1J5RVpVR0RqcDdyVVdHTEpKNENGS05iQTMwVEF4dkZAkMVZATYy1UUnRPN1hpRFp1YmU1YlBGNjJjaFo4X3hqN1ZAjUVVtQm9HZAHhpQnpyWWFIVU5nX1lpNEhXWWtoSnZADVjBrU3VnbTZAMcFh6QTVDQWQ5OAZDZD")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "tulsimalavbot2024")

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

# ============================
# User Sessions
# ============================
user_sessions = {}

# ============================
# System Prompt
# ============================
SYSTEM_PROMPT = """તમે "મળદી માતા પેડલ તુલસી માળા" ના Instagram Sales Bot છો.

📦 PRODUCT:
- નામ: મળદી માતા પેડલ તુલસી માળા
- કિંમત: ₹750
- For: Ladies & Gents બંને

🚚 DELIVERY RULES (આ fixed છે, customer જે કહે તે નહીં):
- Gujarat: 5-6 દિવસ
- બીજા State: 5-6 દિવસ
- Shipping Charge: ₹50 (COD)
- Payment: Cash on Delivery (COD) ફક્ત
- જો customer અલગ delivery date માગે: "અમારી standard delivery 5-6 દિવસ છે" કહો
- જો customer free delivery માગે: "₹50 shipping fixed છે" કહો

📋 ORDER FLOW:
1. Product info આપો
2. Customer interested હોય તો order લો
3. Order માટે આ ક્રમમાં પૂછો:
   - પૂરું નામ
   - Mobile Number
   - પૂરું Address
   - Pincode
4. Order confirm કરો:
   ✅ Order Confirm!
   નામ: [name]
   Phone: [phone]
   Address: [address]
   Pincode: [pincode]
   Product: મળદી માતા પેડલ તુલસી માળા
   કિંમત: ₹750 + ₹50 Shipping = ₹800 (COD)
   Delivery: 5-6 દિવસ 🚚
   જય મા! 🙏

🗣️ LANGUAGE RULES:
- હંમેશા શુદ્ધ ગુજરાતી ભાષામાં જ વાત કરો
- Devotional અને warm tone રાખો
- Emojis વાપરો 🙏🌿
- ટૂંકા અને સ્પષ્ટ જવાબ આપો"""

# ============================
# Claude Response
# ============================
def get_claude_response(user_message, user_id):
    if user_id not in user_sessions:
        user_sessions[user_id] = []

    user_sessions[user_id].append({
        "role": "user",
        "content": user_message
    })

    # Max 20 messages history
    history = user_sessions[user_id][-20:]

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=history
    )

    reply = response.content[0].text

    user_sessions[user_id].append({
        "role": "assistant",
        "content": reply
    })

    return reply

# ============================
# Instagram Message Send
# ============================
def send_message(recipient_id, text):
    url = "https://graph.facebook.com/v18.0/me/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
        "access_token": META_ACCESS_TOKEN
    }
    response = requests.post(url, json=payload)
    return response.json()

# ============================
# Welcome Message
# ============================
def send_welcome(recipient_id):
    welcome = """🙏 જય મા! નમસ્તે!

મળદી માતા પેડલ તુલસી માળા માં આપનું સ્વાગત છે! 🌿

અમારી પાસે છે:
📿 મળદી માતા પેડલ તુલસી માળા
💰 કિંમત: માત્ર ₹750
🚚 Delivery: 5-6 દિવસ
💳 Payment: COD (Cash on Delivery)

શું જાણવું છે? 😊"""
    send_message(recipient_id, welcome)

# ============================
# Webhook Verify
# ============================
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("Webhook Verified!")
        return challenge, 200
    return "Forbidden", 403

# ============================
# Webhook Receive
# ============================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print(f"Received: {data}")

    if data.get("object") == "instagram":
        for entry in data.get("entry", []):
            for event in entry.get("messaging", []):
                sender_id = event["sender"]["id"]

                if "message" in event:
                    user_msg = event["message"].get("text", "")

                    if user_msg:
                        print(f"Message from {sender_id}: {user_msg}")

                        # New user - send welcome
                        if sender_id not in user_sessions:
                            send_welcome(sender_id)

                        # Get Claude response
                        reply = get_claude_response(user_msg, sender_id)
                        send_message(sender_id, reply)
                        print(f"Reply sent: {reply}")

    return jsonify({"status": "ok"}), 200

# ============================
# Home Route
# ============================
@app.route("/")
def home():
    return "🙏 Maldi Mata Tulsi Mala Bot is Running! 🌿"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
