from fastapi import FastAPI, Request, HTTPException
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from google import genai

# ดึงค่า Config มาจากไฟล์ config.py ของเรา
from app.config import GEMINI_API_KEY, LINE_CHANNEL_SECRET, LINE_CHANNEL_ACCESS_TOKEN

app = FastAPI(title="UCR Chatbot AI Sandbox")

# 📌 1. ตั้งค่า LINE และ Gemini
line_config = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
line_handler = WebhookHandler(LINE_CHANNEL_SECRET)
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

@app.get("/health")
async def health():
    return {"status": "OK"}

# 📌 2. Endpoint สำหรับรับ Webhook จาก LINE
@app.post("/callback")
async def callback(request: Request):
    # อ่าน Signature จาก Header ที่ LINE ส่งมาเพื่อยืนยันตัวตน
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()
    
    try:
        # โยนให้ LINE Handler จัดการแยกประเภท Event (เช่น คนพิมพ์ข้อความ, ส่งรูป)
        line_handler.handle(body.decode("utf-8"), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature. Check your Channel Secret.")
    
    return "OK"

# 📌 3. การทำงานเมื่อมี "ข้อความ(Text)" ถูกส่งเข้ามา
@line_handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_message = event.message.text
    reply_token = event.reply_token
    
    try:
        # ส่งข้อความไปถาม Gemini (ถามมา-ตอบไป แบบง่ายสุด ไม่จำประวัติ)
        response = gemini_client.models.generate_content(
            model="gemini-3.5-flash",
            contents=user_message
        )
        ai_reply_text = response.text
        
    except Exception as e:
        ai_reply_text = f"ระบบ AI มีปัญหาครับ: {e}"

    # ส่งข้อความจาก AI ตอบกลับไปหา User ใน LINE
    with ApiClient(line_config) as api_client:
        line_api = MessagingApi(api_client)
        line_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=ai_reply_text)]
            )
        )
