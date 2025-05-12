from fastapi import FastAPI, Request
import httpx
import os

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "caliskanel_verify_token")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN", "DUMMY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-xxx")
WHATSAPP_LINK = "https://wa.me/905498338938"

@app.get("/webhook")
def verify(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return int(challenge)
    return {"status": "403"}

@app.post("/webhook")
async def message_handler(req: Request):
    data = await req.json()
    try:
        for entry in data.get("entry", []):
            for event in entry.get("messaging", []):
                sender_id = event["sender"]["id"]
                if "message" in event and "text" in event["message"]:
                    user_input = event["message"]["text"]
                    reply = await chatgpt_reply(user_input)
                    await send_reply(sender_id, reply)
    except Exception as e:
        print("Hata:", e)
    return {"status": "ok"}

async def chatgpt_reply(text):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "Sen bir otomotiv servis danışmanısın."},
            {"role": "user", "content": f"Müşteri şöyle diyor: '{text}'. Ne olabilir? Kısa yanıt ver ve WhatsApp yönlendirmesiyle bitir."}
        ]
    }
    async with httpx.AsyncClient() as client:
        response = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body)
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        return f"{content}\n\n👉 WhatsApp'tan randevu al: {WHATSAPP_LINK}"

async def send_reply(sender, message):
    url = f"https://graph.facebook.com/v17.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": sender},
        "message": {"text": message}
    }
    headers = {"Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        await client.post(url, headers=headers, json=payload)
