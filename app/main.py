from fastapi import FastAPI, Request, HTTPException
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from app.config import LINE_CHANNEL_SECRET, LINE_CHANNEL_ACCESS_TOKEN
# 📌 นำเข้า "สมอง" ของเราจากไฟล์ ai_handler
from app.ai_handler import get_ai_response

app = FastAPI(title="UCR Chatbot AI Sandbox")

# ตั้งค่าแค่ส่วนของ LINE (ตัวจัดการ AI ถูกย้ายไป ai_handler แล้ว)
line_config = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
line_handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.get("/health")
async def health():
    return {"status": "OK"}

@app.post("/callback")
async def callback(request: Request):
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()
    try:
        line_handler.handle(body.decode("utf-8"), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature. Check your Channel Secret.")
    return "OK"

@line_handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_message = event.message.text
    reply_token = event.reply_token
    user_id = event.source.user_id   # ใครเป็นคนส่ง -> ใช้แยก history แต่ละคน

    # 📌 สั่งงานสมอง (AI) ผ่านฟังก์ชันที่เราแยกไว้
    status, ai_text = get_ai_response(user_id, user_message)

    if status == "ok":
        ai_reply_text = ai_text
        # TODO: ใส่ save_report ตรงนี้ทีหลัง (save เฉพาะตอนสำเร็จ)
    elif status == "rate_limit":
        ai_reply_text = "ตอนนี้ระบบมีคนใช้งานเยอะ ติดลิมิตชั่วคราวครับ 🙏 รอสักครู่แล้วลองใหม่นะครับ"
    else:  # "error"
        ai_reply_text = "ระบบ AI มีปัญหา ลองพิมพ์ใหม่อีกครั้งนะครับ 🙏"

    # ส่งข้อความจาก AI ตอบกลับไปหา User ใน LINE
    with ApiClient(line_config) as api_client:
        line_api = MessagingApi(api_client)
        line_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=ai_reply_text)]
            )
        )
